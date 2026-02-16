"""Audit log management CLI commands."""

import csv
import json
from dataclasses import asdict
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from genxai.security.audit import get_audit_log

console = Console()


@click.group()
def audit():
    """Manage audit logs."""
    pass


@audit.command("list")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
)
def list_events(output_format: str):
    """List audit events."""
    events = get_audit_log().list_events()
    if not events:
        console.print("[yellow]No audit events found.[/yellow]")
        return

    if output_format == "json":
        data = [asdict(event) for event in events]
        click.echo(json.dumps(data, default=str, indent=2))
        return

    if output_format == "csv":
        writer = csv.writer(click.get_text_stream("stdout"))
        writer.writerow(["action", "actor_id", "resource_id", "status", "timestamp"])
        for event in events:
            writer.writerow(
                [
                    event.action,
                    event.actor_id,
                    event.resource_id,
                    event.status,
                    event.timestamp.isoformat(),
                ]
            )
        return

    table = Table(title="Audit Events")
    table.add_column("Action", style="cyan")
    table.add_column("Actor", style="magenta")
    table.add_column("Resource", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Timestamp", style="white")

    for event in events:
        table.add_row(
            event.action,
            event.actor_id,
            event.resource_id,
            event.status,
            event.timestamp.isoformat(),
        )

    console.print(table)


@audit.command("export")
@click.option("--output", "output_path", required=True)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv"]),
    default="json",
)
def export_events(output_path: str, output_format: str):
    """Export audit events to a JSON/CSV file."""
    events = get_audit_log().list_events()
    export_path = Path(output_path)
    if output_format == "csv":
        if export_path.suffix.lower() != ".csv":
            export_path = export_path.with_suffix(".csv")
        with export_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["action", "actor_id", "resource_id", "status", "timestamp"])
            for event in events:
                writer.writerow(
                    [
                        event.action,
                        event.actor_id,
                        event.resource_id,
                        event.status,
                        event.timestamp.isoformat(),
                    ]
                )
    else:
        if export_path.suffix.lower() != ".json":
            export_path = export_path.with_suffix(".json")
        export_path.write_text(json.dumps([asdict(event) for event in events], default=str, indent=2))

    console.print(f"[green]✓ Exported {len(events)} events to {export_path}[/green]")


@audit.command("clear")
def clear_events():
    """Clear audit events."""
    get_audit_log().clear()
    console.print("[green]✓ Cleared audit log[/green]")


@audit.command("compact")
def compact_audit_db():
    """Compact audit database (VACUUM)."""
    get_audit_log()._store.vacuum()
    console.print("[green]✓ Compacted audit database[/green]")


if __name__ == "__main__":
    audit()