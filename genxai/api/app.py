"""FastAPI application factory for GenXAI.

This module lives under the OSS `genxai` package so that module strings like
`genxai.api.app:create_app` work in both OSS and Enterprise installs.

Behavior:
- If `enterprise.genxai` is importable, delegate to the enterprise implementation
  (`enterprise.genxai.api.app:create_app`).
- Otherwise, return a small OSS-safe app (requires FastAPI).
"""

from __future__ import annotations

from typing import Any


def create_app(*args: Any, **kwargs: Any):
    """Create and return a FastAPI application.

    Notes:
        This is designed to be used with Uvicorn's factory mode:
        `uvicorn genxai.api.app:create_app --factory`
    """

    # Prefer enterprise implementation when available.
    try:
        from enterprise.genxai.api.app import create_app as enterprise_create_app

        return enterprise_create_app(*args, **kwargs)
    except ImportError:
        pass

    # OSS fallback app.
    try:
        from fastapi import FastAPI, Response
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "FastAPI is required to serve the GenXAI API. Install with: pip install genxai[api]"
        ) from exc

    app = FastAPI(title="GenXAI API", version="0.1.0")

    @app.get("/metrics", response_class=Response)
    async def metrics() -> Response:
        # Keep the endpoint stable. In OSS-only installs we return a stub.
        return Response(
            content="# Enterprise observability package not installed.\n",
            media_type="text/plain",
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
