"""Minimal FastAPI app for GenXAI observability endpoints."""

from fastapi import FastAPI, Response

from genxai.observability.metrics import get_prometheus_metrics


def create_app() -> FastAPI:
    """Create a FastAPI app exposing observability endpoints.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(title="GenXAI Observability API", version="0.1.0")

    @app.get("/metrics", response_class=Response)
    async def metrics() -> Response:
        """Expose Prometheus metrics."""
        return Response(content=get_prometheus_metrics(), media_type="text/plain")

    return app