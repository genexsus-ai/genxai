"""Central configuration for GenXAI runtime."""

from __future__ import annotations

from typing import List, Set

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GenXAISettings(BaseSettings):
    """Global settings for GenXAI.

    Environment variables use the GENXAI_ prefix.
    """

    model_config = SettingsConfigDict(env_prefix="GENXAI_", case_sensitive=False)

    tool_allowlist: List[str] = Field(default_factory=list)
    tool_denylist: List[str] = Field(default_factory=list)

    def allowlist_set(self) -> Set[str]:
        return {name.strip() for name in self.tool_allowlist if name.strip()}

    def denylist_set(self) -> Set[str]:
        return {name.strip() for name in self.tool_denylist if name.strip()}


_settings: GenXAISettings | None = None


def get_settings() -> GenXAISettings:
    """Get cached settings instance."""
    global _settings
    if _settings is None:
        _settings = GenXAISettings()
    return _settings