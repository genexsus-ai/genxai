"""Approval management CLI commands."""

import click
from rich.console import Console
from rich.table import Table

from genxai.security.audit import get_approval_service

console = Console()


@click.group()
def approval():
    """Manage approval requests."""
    pass


@approval.command("list")
def list_approvals():
    """List approval requests."""
    approvals = get_approval_service()._requests.values()
    if not approvals:
        console.print("[yellow]No approval requests found.[/yellow]")
        return

    table = Table(title="Approval Requests")
    table.add_column("Request ID", style="cyan")
    table.add_column("Action", style="white")
    table.add_column("Resource", style="green")
    table.add_column("Actor", style="magenta")
    table.add_column("Status", style="yellow")

    for request in approvals:
        table.add_row(
            request.request_id,
            request.action,
            request.resource_id,
            request.actor_id,
            request.status,
        )

    console.print(table)


@approval.command("submit")
@click.option("--action", required=True)
@click.option("--resource", required=True)
@click.option("--actor", required=True)
def submit_approval(action: str, resource: str, actor: str):
    """Submit a new approval request."""
    request = get_approval_service().submit(action, resource, actor)
    console.print(f"[green]✓ Approval submitted: {request.request_id}[/green]")


@approval.command("approve")
@click.argument("request_id")
def approve_request(request_id: str):
    """Approve a request."""
    request = get_approval_service().approve(request_id)
    if not request:
        console.print(f"[red]Request '{request_id}' not found.[/red]")
        raise click.Abort()
    console.print(f"[green]✓ Approved {request_id}[/green]")


@approval.command("reject")
@click.argument("request_id")
def reject_request(request_id: str):
    """Reject a request."""
    request = get_approval_service().reject(request_id)
    if not request:
        console.print(f"[red]Request '{request_id}' not found.[/red]")
        raise click.Abort()
    console.print(f"[yellow]✓ Rejected {request_id}[/yellow]")


@approval.command("clear")
def clear_requests():
    """Clear all approval requests."""
    get_approval_service().clear()
    console.print("[green]✓ Cleared approval requests[/green]")


if __name__ == "__main__":
    approval()