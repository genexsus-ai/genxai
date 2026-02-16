"""Application settings for GenXBot backend."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment and .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "GenXBot"
    environment: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"

    auto_approve_safe_actions: bool = False
    max_steps_per_run: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
