import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.api.routes_auth import router as auth_router
from app.api.routes_planner import router as planner_router
from app.config import settings
from app.db.database import Base, engine
from app.observability.metrics import export_metrics


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

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
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"] ,
        allow_headers=["*"],
    )

    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(planner_router, prefix=settings.api_prefix)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(content=export_metrics(), media_type="text/plain")

    return app


app = create_app()
