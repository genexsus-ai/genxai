"""Tool management CLI commands (OSS).

Thin CLI wrapper over the OSS tool registry/persistence APIs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from genxai.tools.base import ToolCategory
from genxai.tools.builtin import *  # noqa: F403 - register built-in tools
from genxai.tools.persistence import ToolService
from genxai.tools.registry import ToolRegistry

console = Console()


@click.group()
def tool() -> None:
    """Manage GenXAI tools."""


@tool.command()
@click.option("--category", help="Filter by category")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
def list(category: Optional[str], output_format: str) -> None:
    """List all tools."""

    try:
        tools = ToolService.list_tools()
        if category:
            tools = [t for t in tools if t.category == category]

        if not tools:
            console.print("[yellow]No tools found.[/yellow]")
            return

        if output_format == "json":
            click.echo(json.dumps([t.to_dict() for t in tools], indent=2))
            return

        table = Table(title="GenXAI Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Category", style="green")
        table.add_column("Type", style="magenta")
        table.add_column("Version", style="yellow")

        for t in tools:
            table.add_row(
                t.name,
                t.description[:50] + "..." if len(t.description) > 50 else t.description,
                t.category,
                t.tool_type,
                t.version,
            )

        console.print(table)
        console.print(f"\n[bold]Total:[/bold] {len(tools)} tools")
    except Exception as exc:
        console.print(f"[red]Error listing tools: {exc}[/red]")
        raise click.Abort() from exc


@tool.command()
@click.argument("name")
def info(name: str) -> None:
    """Show detailed information about a tool."""

    try:
        tool_model = ToolService.get_tool(name)
        if not tool_model:
            console.print(f"[red]Tool '{name}' not found.[/red]")
            raise click.Abort()

        console.print(f"\n[bold cyan]Tool: {tool_model.name}[/bold cyan]")
        console.print(f"[bold]Description:[/bold] {tool_model.description}")
        console.print(f"[bold]Category:[/bold] {tool_model.category}")
        console.print(f"[bold]Type:[/bold] {tool_model.tool_type}")
        console.print(f"[bold]Version:[/bold] {tool_model.version}")
        console.print(f"[bold]Author:[/bold] {tool_model.author}")
        console.print(f"[bold]Tags:[/bold] {', '.join(tool_model.tags)}")
        console.print(f"[bold]Created:[/bold] {tool_model.created_at}")
        console.print(f"[bold]Updated:[/bold] {tool_model.updated_at}")

        if tool_model.tool_type == "code_based":
            console.print("\n[bold]Parameters:[/bold]")
            for param in tool_model.parameters:
                console.print(f"  • {param['name']} ({param['type']}): {param['description']}")

            console.print("\n[bold]Code:[/bold]")
            console.print(f"[dim]{tool_model.code}[/dim]")
        elif tool_model.tool_type == "template_based":
            console.print(f"\n[bold]Template:[/bold] {tool_model.template_name}")
            console.print("[bold]Configuration:[/bold]")
            console.print(json.dumps(tool_model.template_config, indent=2))
    except Exception as exc:
        console.print(f"[red]Error getting tool info: {exc}[/red]")
        raise click.Abort() from exc


@tool.command("export-schema")
@click.option("--output", "output_path", default="tool_schemas.json")
@click.option("--category", help="Filter by category")
@click.option("--stdout", is_flag=True, help="Print schema bundle to stdout")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
def export_schema(output_path: str, category: Optional[str], stdout: bool, output_format: str) -> None:
    """Export consolidated tool schema bundle."""

    try:
        category_filter = ToolCategory(category) if category else None
        bundle = ToolRegistry.export_schema_bundle(category=category_filter)

        if stdout:
            if output_format == "yaml":
                try:
                    import yaml
                except ImportError as exc:
                    raise ImportError(
                        "PyYAML is required for YAML output. Install with: pip install PyYAML"
                    ) from exc
                click.echo(yaml.safe_dump(bundle, sort_keys=False))
            else:
                click.echo(json.dumps(bundle, indent=2))
            return

        if output_format == "yaml" and not output_path.lower().endswith((".yaml", ".yml")):
            output_path = f"{output_path}.yaml"

        export_path = ToolRegistry.export_schema_bundle_to_file(
            output_path,
            category=category_filter,
        )
        console.print(
            f"[green]✓ Tool schema bundle (v{ToolRegistry.SCHEMA_VERSION}) exported to {export_path}[/green]"
        )
    except ValueError:
        console.print(f"[red]Invalid category: {category}[/red]")
        console.print(f"Valid categories: {', '.join([c.value for c in ToolCategory])}")
        raise click.Abort()
    except Exception as exc:
        console.print(f"[red]Error exporting tool schemas: {exc}[/red]")
        raise click.Abort() from exc


if __name__ == "__main__":
    tool()
