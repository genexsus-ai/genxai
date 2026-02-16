"""Tool management CLI commands."""

import click
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from genxai.tools.persistence import ToolService
from genxai.tools.base import ToolCategory
from genxai.tools.registry import ToolRegistry
from genxai.tools.builtin import *  # noqa: F403 - register built-in tools

console = Console()


@click.group()
def tool():
    """Manage GenXAI tools."""
    pass


@tool.command()
@click.option('--category', help='Filter by category')
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def list(category: Optional[str], format: str):
    """List all tools."""
    try:
        tools = ToolService.list_tools()
        
        # Filter by category if specified
        if category:
            tools = [t for t in tools if t.category == category]
        
        if not tools:
            console.print("[yellow]No tools found.[/yellow]")
            return
        
        if format == 'json':
            # JSON output
            output = [t.to_dict() for t in tools]
            click.echo(json.dumps(output, indent=2))
        else:
            # Table output
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
                    t.version
                )
            
            console.print(table)
            console.print(f"\n[bold]Total:[/bold] {len(tools)} tools")
            
    except Exception as e:
        console.print(f"[red]Error listing tools: {e}[/red]")
        raise click.Abort()


@tool.command()
@click.argument('name')
def info(name: str):
    """Show detailed information about a tool."""
    try:
        tool_model = ToolService.get_tool(name)
        
        if not tool_model:
            console.print(f"[red]Tool '{name}' not found.[/red]")
            raise click.Abort()
        
        # Display tool information
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
            console.print(f"\n[bold]Parameters:[/bold]")
            for param in tool_model.parameters:
                console.print(f"  • {param['name']} ({param['type']}): {param['description']}")
            
            console.print(f"\n[bold]Code:[/bold]")
            console.print(f"[dim]{tool_model.code}[/dim]")
        
        elif tool_model.tool_type == "template_based":
            console.print(f"\n[bold]Template:[/bold] {tool_model.template_name}")
            console.print(f"[bold]Configuration:[/bold]")
            console.print(json.dumps(tool_model.template_config, indent=2))
        
    except Exception as e:
        console.print(f"[red]Error getting tool info: {e}[/red]")
        raise click.Abort()


@tool.command()
@click.argument('query')
@click.option('--category', help='Filter by category')
def search(query: str, category: Optional[str]):
    """Search tools by name, description, or tags."""
    try:
        tools = ToolService.list_tools()
        
        # Filter by query
        query_lower = query.lower()
        results = [
            t for t in tools
            if query_lower in t.name.lower()
            or query_lower in t.description.lower()
            or any(query_lower in tag.lower() for tag in t.tags)
        ]
        
        # Filter by category if specified
        if category:
            results = [t for t in results if t.category == category]
        
        if not results:
            console.print(f"[yellow]No tools found matching '{query}'.[/yellow]")
            return
        
        # Display results
        table = Table(title=f"Search Results for '{query}'")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Category", style="green")
        
        for t in results:
            table.add_row(
                t.name,
                t.description[:60] + "..." if len(t.description) > 60 else t.description,
                t.category
            )
        
        console.print(table)
        console.print(f"\n[bold]Found:[/bold] {len(results)} tools")
        
    except Exception as e:
        console.print(f"[red]Error searching tools: {e}[/red]")
        raise click.Abort()


@tool.command()
@click.argument('name')
@click.option('--force', is_flag=True, help='Skip confirmation')
def delete(name: str, force: bool):
    """Delete a tool."""
    try:
        tool_model = ToolService.get_tool(name)
        
        if not tool_model:
            console.print(f"[red]Tool '{name}' not found.[/red]")
            raise click.Abort()
        
        # Confirm deletion
        if not force:
            if not click.confirm(f"Are you sure you want to delete tool '{name}'?"):
                console.print("[yellow]Deletion cancelled.[/yellow]")
                return
        
        # Delete tool
        ToolService.delete_tool(name)
        console.print(f"[green]✓ Tool '{name}' deleted successfully.[/green]")
        
    except Exception as e:
        console.print(f"[red]Error deleting tool: {e}[/red]")
        raise click.Abort()


@tool.command()
@click.argument('name')
@click.option('--output', '-o', help='Output file path')
@click.option('--format', type=click.Choice(['json', 'py']), default='json', help='Export format')
def export(name: str, output: Optional[str], format: str):
    """Export a tool to a file."""
    try:
        tool_model = ToolService.get_tool(name)
        
        if not tool_model:
            console.print(f"[red]Tool '{name}' not found.[/red]")
            raise click.Abort()
        
        # Determine output path
        if not output:
            output = f"{name}.{format}"
        
        output_path = Path(output)
        
        # Export based on format
        if format == 'json':
            data = tool_model.to_dict()
            output_path.write_text(json.dumps(data, indent=2))
        elif format == 'py':
            if tool_model.tool_type != "code_based":
                console.print("[red]Only code-based tools can be exported as Python files.[/red]")
                raise click.Abort()
            
            content = f'''"""
Tool: {tool_model.name}
Description: {tool_model.description}
Category: {tool_model.category}
"""

{tool_model.code}
'''
            output_path.write_text(content)
        
        console.print(f"[green]✓ Tool exported to {output_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error exporting tool: {e}[/red]")
        raise click.Abort()


@tool.command("export-schema")
@click.option('--output', '-o', help='Output file path', default='tool_schemas.json')
@click.option('--category', help='Filter by category')
@click.option('--stdout', is_flag=True, help='Print schema bundle to stdout')
@click.option('--format', 'output_format', type=click.Choice(['json', 'yaml']), default='json', help='Output format')
def export_schema(output: str, category: Optional[str], stdout: bool, output_format: str):
    """Export consolidated tool schema bundle to JSON."""
    try:
        category_filter = ToolCategory(category) if category else None
        bundle = ToolRegistry.export_schema_bundle(category=category_filter)

        if stdout:
            if output_format == 'yaml':
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

        if output_format == 'yaml' and not output.lower().endswith((".yaml", ".yml")):
            output = f"{output}.yaml"

        export_path = ToolRegistry.export_schema_bundle_to_file(
            output,
            category=category_filter,
        )
        console.print(
            f"[green]✓ Tool schema bundle (v{ToolRegistry.SCHEMA_VERSION}) exported to {export_path}[/green]"
        )
    except ValueError:
        console.print(f"[red]Invalid category: {category}[/red]")
        console.print(f"Valid categories: {', '.join([c.value for c in ToolCategory])}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[red]Error exporting tool schemas: {e}[/red]")
        raise click.Abort()


@tool.command()
@click.argument('file', type=click.Path(exists=True))
def import_tool(file: str):
    """Import a tool from a file."""
    try:
        file_path = Path(file)
        
        if file_path.suffix == '.json':
            # Import from JSON
            data = json.loads(file_path.read_text())
            
            # Check if tool already exists
            if ToolService.get_tool(data['name']):
                console.print(f"[red]Tool '{data['name']}' already exists.[/red]")
                raise click.Abort()
            
            # Create tool
            ToolService.save_tool(
                name=data['name'],
                description=data['description'],
                category=data['category'],
                tags=data.get('tags', []),
                version=data.get('version', '1.0.0'),
                author=data.get('author', 'GenXAI User'),
                tool_type=data['tool_type'],
                code=data.get('code'),
                parameters=data.get('parameters'),
                template_name=data.get('template_name'),
                template_config=data.get('template_config'),
            )
            
            console.print(f"[green]✓ Tool '{data['name']}' imported successfully.[/green]")
        else:
            console.print("[red]Only JSON files are supported for import.[/red]")
            raise click.Abort()
        
    except Exception as e:
        console.print(f"[red]Error importing tool: {e}[/red]")
        raise click.Abort()


@tool.command()
@click.option('--name', required=True, help='Tool name')
@click.option('--description', required=True, help='Tool description')
@click.option('--category', required=True, help='Tool category')
@click.option('--template', help='Template name for template-based tools')
@click.option('--config', help='Template configuration (JSON string)')
@click.option('--code-file', type=click.Path(exists=True), help='Python file for code-based tools')
@click.option('--tags', help='Comma-separated tags')
def create(name: str, description: str, category: str, template: Optional[str], 
           config: Optional[str], code_file: Optional[str], tags: Optional[str]):
    """Create a new tool."""
    try:
        # Check if tool already exists
        if ToolService.get_tool(name):
            console.print(f"[red]Tool '{name}' already exists.[/red]")
            raise click.Abort()
        
        # Validate category
        try:
            ToolCategory(category)
        except ValueError:
            console.print(f"[red]Invalid category: {category}[/red]")
            console.print(f"Valid categories: {', '.join([c.value for c in ToolCategory])}")
            raise click.Abort()
        
        # Parse tags
        tag_list = [t.strip() for t in tags.split(',')] if tags else []
        
        # Create tool based on type
        if template:
            # Template-based tool
            if not config:
                console.print("[red]--config is required for template-based tools.[/red]")
                raise click.Abort()
            
            config_dict = json.loads(config)
            
            ToolService.save_tool(
                name=name,
                description=description,
                category=category,
                tags=tag_list,
                version="1.0.0",
                author="GenXAI User",
                tool_type="template_based",
                template_name=template,
                template_config=config_dict,
            )
            
        elif code_file:
            # Code-based tool
            code = Path(code_file).read_text()
            
            ToolService.save_tool(
                name=name,
                description=description,
                category=category,
                tags=tag_list,
                version="1.0.0",
                author="GenXAI User",
                tool_type="code_based",
                code=code,
                parameters=[],  # TODO: Parse from code or require as input
            )
        else:
            console.print("[red]Either --template or --code-file must be provided.[/red]")
            raise click.Abort()
        
        console.print(f"[green]✓ Tool '{name}' created successfully.[/green]")
        
    except Exception as e:
        console.print(f"[red]Error creating tool: {e}[/red]")
        raise click.Abort()


if __name__ == '__main__':
    tool()
