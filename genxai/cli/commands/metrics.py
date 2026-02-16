"""Metrics API CLI commands."""

import click


@click.group()
def metrics() -> None:
    """Manage metrics API server."""
    pass


@metrics.command("serve")
@click.option("--host", default="0.0.0.0", show_default=True, help="Host to bind")
@click.option("--port", default=8001, show_default=True, help="Port to bind")
@click.option("--reload", is_flag=True, default=False, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the metrics API server."""
    try:
        import uvicorn
    except ImportError as exc:
        raise click.ClickException(
            "Uvicorn is required to serve the metrics API. Install with: pip install genxai[api]"
        ) from exc

    uvicorn.run("genxai.api.app:create_app", host=host, port=port, reload=reload, factory=True)