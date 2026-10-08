"""Application settings (environment-driven)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str | None = None
    redis_url: str | None = None
    cache_ttl_seconds: int = 0
    morphology_engine: str = "auto"
    spacy_model: str = "de_core_news_sm"
    cors_origins: str = "http://localhost:3000"

    @property
    def effective_database_url(self) -> str:
        # Zero-setup local fallback: a SQLite file in data/.
        return self.database_url or "sqlite:///./data/dev.db"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
