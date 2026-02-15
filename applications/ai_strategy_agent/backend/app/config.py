"""Application configuration settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables and .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "AI Strategy Brainstorming Agent"
    env: str = "development"
    debug: bool = True
    cors_origins: str = "*"

    openai_api_key: str | None = None
    max_rounds: int = 6
    consensus_threshold: float = 0.7
    convergence_window: int = 2
    quality_threshold: float = 0.82


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance."""

    return Settings()