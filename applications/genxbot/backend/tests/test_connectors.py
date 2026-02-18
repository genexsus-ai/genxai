from app.services.connectors import parse_connector_event


def test_parse_connector_event_github_normalizes_payload() -> None:
    event = parse_connector_event(
        connector="github",
        event_type="pull_request.opened",
        payload={
            "action": "opened",
            "repository": {"full_name": "genexsus-ai/genxai", "html_url": "https://github.com/genexsus-ai/genxai"},
            "sender": {"login": "alice"},
            "pull_request": {"number": 101, "title": "Fix flaky tests", "body": "Please review"},
            "installation": {"id": 777},
        },
    )

    assert event.connector == "github"
    assert event.actor_id == "alice"
    assert event.source_ref == "genexsus-ai/genxai"
    assert event.resource_id == "101"
    assert event.summary == "Fix flaky tests"
    assert event.text == "Please review"
    assert event.metadata["action"] == "opened"


def test_parse_connector_event_jira_normalizes_payload() -> None:
    event = parse_connector_event(
        connector="jira",
        event_type="issue.updated",
        payload={
            "user": {"accountId": "acc-1"},
            "issue": {
                "id": "9001",
                "key": "PROJ-42",
                "fields": {
                    "summary": "Backend bug",
                    "description": "Intermittent failure",
                    "project": {"key": "PROJ", "name": "Project"},
                    "issuetype": {"name": "Bug"},
                    "priority": {"name": "High"},
                    "status": {"name": "In Progress"},
                },
            },
        },
    )

    assert event.connector == "jira"
    assert event.actor_id == "acc-1"
    assert event.source_ref == "PROJ"
    assert event.resource_id == "PROJ-42"
    assert event.summary == "Backend bug"
    assert event.text == "Intermittent failure"
    assert event.metadata["issue_id"] == "9001"
    assert event.metadata["status"] == "In Progress"


def test_parse_connector_event_slack_normalizes_payload() -> None:
    event = parse_connector_event(
        connector="slack",
        event_type="message",
        payload={
            "team_id": "T1",
            "event": {
                "user": "U1",
                "channel": "C1",
                "text": "hello",
                "ts": "1710000000.123",
                "thread_ts": "1710000000.100",
            },
        },
    )

    assert event.connector == "slack"
    assert event.actor_id == "U1"
    assert event.source_ref == "C1"
    assert event.resource_id == "1710000000.123"
    assert event.text == "hello"
    assert event.metadata["team_id"] == "T1"


def test_parse_connector_event_webhook_normalizes_payload() -> None:
    event = parse_connector_event(
        connector="webhook",
        event_type="",
        payload={
            "provider": "generic",
            "webhook_id": "wh_123",
            "event_type": "deployment.failed",
            "actor": {"id": "bot-7"},
            "source": {"ref": "genexsus-ai/genxai"},
            "resource": {"id": "deploy-99"},
            "summary": "Deployment failed",
            "text": "Rollback suggested",
            "metadata": {"environment": "prod"},
            "headers": {"x-trace-id": "trace-1"},
        },
    )

    assert event.connector == "webhook"
    assert event.event_type == "deployment.failed"
    assert event.actor_id == "bot-7"
    assert event.source_ref == "genexsus-ai/genxai"
    assert event.resource_id == "deploy-99"
    assert event.summary == "Deployment failed"
    assert event.text == "Rollback suggested"
    assert event.metadata["environment"] == "prod"
    assert event.metadata["provider"] == "generic"
    assert event.metadata["webhook_id"] == "wh_123"


def test_parse_connector_event_unsupported_connector_raises() -> None:
    try:
        parse_connector_event(connector="gitlab", event_type="merge_request", payload={})
    except ValueError as exc:
        assert "Unsupported connector" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported connector")
