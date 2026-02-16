try:
    from enterprise.genxai.connectors.base import Connector, ConnectorEvent, ConnectorStatus
    from enterprise.genxai.connectors.registry import ConnectorRegistry
    from enterprise.genxai.connectors.webhook import WebhookConnector
    from enterprise.genxai.connectors.kafka import KafkaConnector
    from enterprise.genxai.connectors.sqs import SQSConnector
    from enterprise.genxai.connectors.postgres_cdc import PostgresCDCConnector
    from enterprise.genxai.connectors.slack import SlackConnector
    from enterprise.genxai.connectors.github import GitHubConnector
    from enterprise.genxai.connectors.notion import NotionConnector
    from enterprise.genxai.connectors.jira import JiraConnector
    from enterprise.genxai.connectors.google_workspace import GoogleWorkspaceConnector
except ModuleNotFoundError:
    from .base import Connector, ConnectorEvent, ConnectorStatus
    from .registry import ConnectorRegistry
    from .webhook import WebhookConnector
    from .kafka import KafkaConnector
    from .sqs import SQSConnector
    from .postgres_cdc import PostgresCDCConnector
    from .slack import SlackConnector
    from .github import GitHubConnector
    from .notion import NotionConnector
    from .jira import JiraConnector
    from .google_workspace import GoogleWorkspaceConnector

__all__ = [
    "Connector",
    "ConnectorEvent",
    "ConnectorStatus",
    "ConnectorRegistry",
    "WebhookConnector",
    "KafkaConnector",
    "SQSConnector",
    "PostgresCDCConnector",
    "SlackConnector",
    "GitHubConnector",
    "NotionConnector",
    "JiraConnector",
    "GoogleWorkspaceConnector",
]