from pathlib import Path

from pydantic_settings import BaseSettings


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "Travel Planning Agent"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60
    sqlite_path: str = str(BACKEND_ROOT / "travel_planning.db")
    openai_api_key: str | None = None
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = BACKEND_ROOT / ".env"


settings = Settings()

if settings.openai_api_key:
    print(f"OPENAI_API_KEY loaded (last4={settings.openai_api_key[-4:]})")
else:
    print("OPENAI_API_KEY not set")
