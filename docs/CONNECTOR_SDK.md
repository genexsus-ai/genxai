# Connector SDK (Enterprise)

The Connector SDK is part of the enterprise edition and lives under `enterprise/`.

## Key Concepts
- **Connector**: A long‑lived integration that emits events.
- **ConnectorEvent**: Payload + metadata emitted to subscribers.
- **ConnectorRegistry**: Optional registry for reuse.
- **Lifecycle Helpers**: `start_all()` / `stop_all()` for bulk ops.
- **Validation**: `validate_config()` runs before connector startup.

## Webhook Connector Example

```python
from genxai.connectors import WebhookConnector

connector = WebhookConnector(connector_id="webhook_1", secret="my-secret")

async def handle(event):
    print(event.payload)

connector.on_event(handle)
await connector.start()

# In your FastAPI route:
# await connector.handle_request(payload, raw_body=raw, headers=request.headers)
```

## Registry Lifecycle Example

```python
from genxai.connectors import ConnectorRegistry, WebhookConnector

connector = WebhookConnector(connector_id="webhook_1", secret="my-secret")
ConnectorRegistry.register(connector)

await ConnectorRegistry.start_all()
await ConnectorRegistry.stop_all()
```

## Available Connectors

The following connectors are available:
- **KafkaConnector** (`genxai.connectors.kafka`) — uses aiokafka
- **SQSConnector** (`genxai.connectors.sqs`) — uses aioboto3
- **PostgresCDCConnector** (`genxai.connectors.postgres_cdc`) — uses asyncpg + wal2json
- **SlackConnector** (`genxai.connectors.slack`) — uses Slack Web API
- **GitHubConnector** (`genxai.connectors.github`) — uses GitHub REST API v3
- **NotionConnector** (`genxai.connectors.notion`) — uses Notion API
- **JiraConnector** (`genxai.connectors.jira`) — uses Jira Cloud REST API v3
- **GoogleWorkspaceConnector** (`genxai.connectors.google_workspace`) — uses Google APIs

## Slack Connector Example

```python
from genxai.connectors import SlackConnector

connector = SlackConnector(
    connector_id="slack_alerts",
    bot_token="xoxb-your-bot-token",
)

await connector.start()
await connector.send_message(channel="#alerts", text="Deployment complete ✅")
```

## GitHub Connector Example

```python
from genxai.connectors import GitHubConnector

connector = GitHubConnector(
    connector_id="github_ops",
    token="ghp_your_token",
)

await connector.start()
issue = await connector.create_issue(
    owner="genxai",
    repo="genxai",
    title="Investigate agent latency",
    body="See metrics dashboard for spikes.",
)
print(issue["html_url"])
```

## Notion Connector Example

```python
from genxai.connectors import NotionConnector

connector = NotionConnector(
    connector_id="notion_docs",
    token="secret_123",
)

await connector.start()
page = await connector.get_page(page_id="your-page-id")
print(page["id"])
```

## Jira Connector Example

```python
from genxai.connectors import JiraConnector

connector = JiraConnector(
    connector_id="jira_ops",
    email="you@company.com",
    api_token="jira_api_token",
    base_url="https://your-domain.atlassian.net",
)

await connector.start()
issue = await connector.create_issue(
    {
        "fields": {
            "project": {"key": "OPS"},
            "summary": "Agent latency spike",
            "issuetype": {"name": "Task"},
        }
    }
)
print(issue["key"])
```

## Google Workspace Connector Example

```python
from genxai.connectors import GoogleWorkspaceConnector

connector = GoogleWorkspaceConnector(
    connector_id="gws_ops",
    access_token="ya29.your_token",
)

await connector.start()
events = await connector.get_calendar_events(max_results=5)
print(events["items"])
```