"""FastAPI entrypoint."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_strategy import router as strategy_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    if settings.openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    logger = logging.getLogger("uvicorn")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        logger.info("OPENAI_API_KEY loaded (last4=%s)", openai_key[-4:])
    else:
        logger.warning("OPENAI_API_KEY not set")

    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(strategy_router)

    @app.get("/")
    def root() -> dict:
        return {"status": "ok"}

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}
    return app


app = create_app()