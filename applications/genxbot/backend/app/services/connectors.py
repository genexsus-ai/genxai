"""Connector adapters for normalizing inbound provider payloads."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.schemas import ConnectorNormalizedEvent


class ConnectorAdapter(ABC):
    """Lightweight adapter interface for connector payload normalization."""

    connector: str

    @abstractmethod
    def parse(self, event_type: str, payload: dict[str, Any]) -> ConnectorNormalizedEvent:
        raise NotImplementedError

    @staticmethod
    def _as_str(value: Any) -> str | None:
        if value is None:
            return None
        return str(value)


class GitHubConnectorAdapter(ConnectorAdapter):
    connector = "github"

    def parse(self, event_type: str, payload: dict[str, Any]) -> ConnectorNormalizedEvent:
        repository = payload.get("repository", {})
        pull_request = payload.get("pull_request", {})
        issue = payload.get("issue", {})
        sender = payload.get("sender", {})

        resource_id = str(pull_request.get("number") or issue.get("number") or "") or None
        summary = pull_request.get("title") or issue.get("title")
        text = pull_request.get("body") or issue.get("body")

        return ConnectorNormalizedEvent(
            connector="github",
            event_type=event_type,
            actor_id=str(sender.get("login")) if sender.get("login") is not None else None,
            source_ref=repository.get("full_name"),
            resource_id=resource_id,
            summary=summary,
            text=text,
            metadata={
                "action": payload.get("action"),
                "repository_url": repository.get("html_url"),
                "installation_id": payload.get("installation", {}).get("id"),
            },
            raw_payload=payload,
        )


class JiraConnectorAdapter(ConnectorAdapter):
    connector = "jira"

    def parse(self, event_type: str, payload: dict[str, Any]) -> ConnectorNormalizedEvent:
        issue = payload.get("issue", {})
        fields = issue.get("fields", {})
        project = fields.get("project", {})
        user = payload.get("user", {})

        return ConnectorNormalizedEvent(
            connector="jira",
            event_type=event_type,
            actor_id=str(user.get("accountId")) if user.get("accountId") is not None else None,
            source_ref=project.get("key") or project.get("name"),
            resource_id=issue.get("key"),
            summary=fields.get("summary"),
            text=fields.get("description"),
            metadata={
                "issue_id": issue.get("id"),
                "issue_type": fields.get("issuetype", {}).get("name"),
                "priority": fields.get("priority", {}).get("name"),
                "status": fields.get("status", {}).get("name"),
            },
            raw_payload=payload,
        )


class SlackConnectorAdapter(ConnectorAdapter):
    connector = "slack"

    def parse(self, event_type: str, payload: dict[str, Any]) -> ConnectorNormalizedEvent:
        event = payload.get("event", payload)

        return ConnectorNormalizedEvent(
            connector="slack",
            event_type=event_type,
            actor_id=str(event.get("user")) if event.get("user") is not None else None,
            source_ref=str(event.get("channel")) if event.get("channel") is not None else None,
            resource_id=str(event.get("ts")) if event.get("ts") is not None else None,
            summary="Slack message event",
            text=event.get("text"),
            metadata={
                "thread_ts": event.get("thread_ts"),
                "subtype": event.get("subtype"),
                "team_id": payload.get("team_id"),
            },
            raw_payload=payload,
        )


class WebhookConnectorAdapter(ConnectorAdapter):
    """Adapter for generic webhook payloads.

    Expected payload shape is intentionally flexible to support provider-agnostic
    webhook bridges that may forward envelopes such as:

    {
      "event_type": "deployment.failed",
      "actor": {"id": "bot"},
      "source": {"ref": "repo/name"},
      "resource": {"id": "123"},
      "summary": "...",
      "text": "...",
      "metadata": {...}
    }
    """

    connector = "webhook"

    def parse(self, event_type: str, payload: dict[str, Any]) -> ConnectorNormalizedEvent:
        actor = payload.get("actor") if isinstance(payload.get("actor"), dict) else {}
        source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
        resource = payload.get("resource") if isinstance(payload.get("resource"), dict) else {}

        normalized_event_type = (
            event_type
            or self._as_str(payload.get("event_type"))
            or self._as_str(payload.get("type"))
            or "webhook.event"
        )

        actor_id = (
            self._as_str(payload.get("actor_id"))
            or self._as_str(actor.get("id"))
            or self._as_str(actor.get("name"))
        )
        source_ref = (
            self._as_str(payload.get("source_ref"))
            or self._as_str(source.get("ref"))
            or self._as_str(source.get("id"))
            or self._as_str(source.get("name"))
        )
        resource_id = (
            self._as_str(payload.get("resource_id"))
            or self._as_str(resource.get("id"))
            or self._as_str(resource.get("key"))
        )

        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        metadata = {
            **metadata,
            "provider": payload.get("provider"),
            "webhook_id": payload.get("webhook_id"),
            "headers": payload.get("headers") if isinstance(payload.get("headers"), dict) else None,
        }

        return ConnectorNormalizedEvent(
            connector="webhook",
            event_type=normalized_event_type,
            actor_id=actor_id,
            source_ref=source_ref,
            resource_id=resource_id,
            summary=self._as_str(payload.get("summary")),
            text=self._as_str(payload.get("text") or payload.get("message")),
            metadata=metadata,
            raw_payload=payload,
        )


_ADAPTERS: dict[str, ConnectorAdapter] = {
    "github": GitHubConnectorAdapter(),
    "jira": JiraConnectorAdapter(),
    "slack": SlackConnectorAdapter(),
    "webhook": WebhookConnectorAdapter(),
}


def parse_connector_event(
    connector: str,
    event_type: str,
    payload: dict[str, Any],
) -> ConnectorNormalizedEvent:
    """Normalize provider connector payloads into ConnectorNormalizedEvent."""
    connector_key = connector.strip().lower()
    adapter = _ADAPTERS.get(connector_key)
    if adapter is None:
        raise ValueError(f"Unsupported connector: {connector}")
    return adapter.parse(event_type=event_type, payload=payload)
