"""Connector management CLI commands."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

import click
from rich.console import Console
from rich.table import Table

from genxai.connectors import (
    Connector,
    KafkaConnector,
    SQSConnector,
    PostgresCDCConnector,
    WebhookConnector,
    SlackConnector,
    GitHubConnector,
    NotionConnector,
    JiraConnector,
    GoogleWorkspaceConnector,
)
from genxai.connectors.config_store import ConnectorConfigEntry, ConnectorConfigStore

console = Console()


CONNECTOR_CATALOG: Dict[str, Dict[str, Any]] = {
    "kafka": {
        "class": KafkaConnector,
        "required": ["topic", "bootstrap_servers"],
        "description": "Kafka consumer connector",
    },
    "sqs": {
        "class": SQSConnector,
        "required": ["queue_url"],
        "description": "AWS SQS connector",
    },
    "postgres_cdc": {
        "class": PostgresCDCConnector,
        "required": ["dsn"],
        "description": "Postgres CDC connector",
    },
    "webhook": {
        "class": WebhookConnector,
        "required": [],
        "description": "Inbound webhook connector",
    },
    "slack": {
        "class": SlackConnector,
        "required": ["bot_token"],
        "description": "Slack Web API connector",
    },
    "github": {
        "class": GitHubConnector,
        "required": ["token"],
        "description": "GitHub REST API connector",
    },
    "notion": {
        "class": NotionConnector,
        "required": ["token"],
        "description": "Notion API connector",
    },
    "jira": {
        "class": JiraConnector,
        "required": ["email", "api_token", "base_url"],
        "description": "Jira Cloud REST API connector",
    },
    "google_workspace": {
        "class": GoogleWorkspaceConnector,
        "required": ["access_token"],
        "description": "Google Workspace APIs connector",
    },
}


@click.group()
def connector() -> None:
    """Manage GenXAI connectors."""
    pass


@connector.command("list")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
def list_connectors(output_format: str) -> None:
    """List available connector types."""
    if output_format == "json":
        payload = {
            name: {
                "required": meta["required"],
                "description": meta["description"],
            }
            for name, meta in CONNECTOR_CATALOG.items()
        }
        click.echo(json.dumps(payload, indent=2))
        return

    table = Table(title="GenXAI Connectors")
    table.add_column("Type", style="cyan")
    table.add_column("Required Fields", style="green")
    table.add_column("Description", style="white")
    for name, meta in CONNECTOR_CATALOG.items():
        table.add_row(name, ", ".join(meta["required"]) or "(none)", meta["description"])
    console.print(table)


@connector.command("validate")
@click.option("--type", "connector_type", required=True, help="Connector type")
@click.option("--connector-id", default="connector", show_default=True)
@click.option("--config", help="JSON config payload for the connector")
@click.option("--config-name", help="Use a saved connector config")
def validate(
    connector_type: str,
    connector_id: str,
    config: Optional[str],
    config_name: Optional[str],
) -> None:
    """Validate connector configuration without starting it."""
    connector_meta = CONNECTOR_CATALOG.get(connector_type)
    if not connector_meta:
        raise click.ClickException(
            f"Unknown connector type '{connector_type}'. Use 'genxai connector list' to see options."
        )

    config_data = _load_config(config, config_name)
    missing = [field for field in connector_meta["required"] if field not in config_data]
    if missing:
        raise click.ClickException(f"Missing required fields: {', '.join(missing)}")

    connector_instance = _build_connector(connector_id, connector_meta["class"], config_data)
    try:
        asyncio.run(connector_instance.validate_config())
        console.print("[green]✓ Connector configuration valid[/green]")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


@connector.command("start")
@click.option("--type", "connector_type", required=True, help="Connector type")
@click.option("--connector-id", default="connector", show_default=True)
@click.option("--config", help="JSON config payload for the connector")
@click.option("--config-name", help="Use a saved connector config")
def start(connector_type: str, connector_id: str, config: Optional[str], config_name: Optional[str]) -> None:
    """Start a connector instance for quick validation."""
    connector_instance = _build_from_cli(connector_type, connector_id, config, config_name)
    try:
        asyncio.run(connector_instance.start())
        console.print("[green]✓ Connector started[/green]")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


@connector.command("stop")
@click.option("--type", "connector_type", required=True, help="Connector type")
@click.option("--connector-id", default="connector", show_default=True)
@click.option("--config", help="JSON config payload for the connector")
@click.option("--config-name", help="Use a saved connector config")
def stop(connector_type: str, connector_id: str, config: Optional[str], config_name: Optional[str]) -> None:
    """Stop a connector instance for quick validation."""
    connector_instance = _build_from_cli(connector_type, connector_id, config, config_name)
    try:
        asyncio.run(connector_instance.stop())
        console.print("[green]✓ Connector stopped[/green]")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


@connector.command("health")
@click.option("--type", "connector_type", required=True, help="Connector type")
@click.option("--connector-id", default="connector", show_default=True)
@click.option("--config", help="JSON config payload for the connector")
@click.option("--format", "output_format", type=click.Choice(["json", "table"]), default="json")
@click.option("--config-name", help="Use a saved connector config")
def health(
    connector_type: str,
    connector_id: str,
    config: Optional[str],
    output_format: str,
    config_name: Optional[str],
) -> None:
    """Run a connector health check without starting it."""
    connector_instance = _build_from_cli(connector_type, connector_id, config, config_name)
    try:
        payload = asyncio.run(connector_instance.health_check())
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc

    if output_format == "json":
        click.echo(json.dumps(payload, indent=2))
        return

    table = Table(title="Connector Health")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    for key, value in payload.items():
        table.add_row(str(key), str(value))
    console.print(table)


@connector.command("save")
@click.option("--name", "config_name", required=True, help="Name for the saved config")
@click.option("--type", "connector_type", required=True, help="Connector type")
@click.option("--config", required=True, help="JSON config payload")
def save(config_name: str, connector_type: str, config: str) -> None:
    """Save a connector config for reuse."""
    connector_meta = CONNECTOR_CATALOG.get(connector_type)
    if not connector_meta:
        raise click.ClickException(
            f"Unknown connector type '{connector_type}'. Use 'genxai connector list' to see options."
        )
    config_data = _load_config(config, None)
    missing = [field for field in connector_meta["required"] if field not in config_data]
    if missing:
        raise click.ClickException(f"Missing required fields: {', '.join(missing)}")

    store = ConnectorConfigStore()
    store.save(
        ConnectorConfigEntry(
            name=config_name,
            connector_type=connector_type,
            config=config_data,
        )
    )
    console.print(f"[green]✓ Saved connector config '{config_name}'[/green]")


@connector.command("saved")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
def list_saved(output_format: str) -> None:
    """List saved connector configs."""
    store = ConnectorConfigStore()
    entries = store.list()
    if output_format == "json":
        payload = {
            name: {"connector_type": entry.connector_type, "config": entry.config}
            for name, entry in entries.items()
        }
        click.echo(json.dumps(payload, indent=2))
        return

    table = Table(title="Saved Connector Configs")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Config", style="white")
    for name, entry in entries.items():
        table.add_row(name, entry.connector_type, json.dumps(entry.config))
    console.print(table)


@connector.command("remove")
@click.option("--name", "config_name", required=True, help="Saved config name")
def remove(config_name: str) -> None:
    """Remove a saved connector config."""
    store = ConnectorConfigStore()
    if not store.delete(config_name):
        raise click.ClickException(f"Config '{config_name}' not found")
    console.print(f"[green]✓ Removed connector config '{config_name}'[/green]")


@connector.command("keygen")
def keygen() -> None:
    """Generate a Fernet key for encrypted connector configs."""
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise click.ClickException(
            "cryptography is required for key generation. Install with: pip install cryptography"
        ) from exc
    key = Fernet.generate_key().decode()
    click.echo(key)


def _build_connector(connector_id: str, connector_class: type[Connector], config: Dict[str, Any]) -> Connector:
    params = {"connector_id": connector_id, **config}
    return connector_class(**params)


def _build_from_cli(
    connector_type: str,
    connector_id: str,
    config: Optional[str],
    config_name: Optional[str],
) -> Connector:
    connector_meta = CONNECTOR_CATALOG.get(connector_type)
    if not connector_meta:
        raise click.ClickException(
            f"Unknown connector type '{connector_type}'. Use 'genxai connector list' to see options."
        )
    config_data = _load_config(config, config_name)
    missing = [field for field in connector_meta["required"] if field not in config_data]
    if missing:
        raise click.ClickException(f"Missing required fields: {', '.join(missing)}")
    return _build_connector(connector_id, connector_meta["class"], config_data)


def _load_config(config: Optional[str], config_name: Optional[str]) -> Dict[str, Any]:
    if config_name:
        store = ConnectorConfigStore()
        entry = store.get(config_name)
        if not entry:
            raise click.ClickException(f"Config '{config_name}' not found")
        return entry.config
    return json.loads(config) if config else {}


if __name__ == "__main__":
    connector()