from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "docustruct-ai"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "sqlite:///./docustruct.db"
    redis_url: str = "redis://localhost:6379/0"

    storage_root: Path = Field(default=Path("./data/storage"))
    artifacts_root: Path = Field(default=Path("./data/artifacts"))
    templates_dir: Path = Field(default=Path("./src/docustruct_ai/templates"))

    execution_mode: str = "inline"
    accept_threshold: float = 0.85
    review_threshold: float = 0.55
    reject_threshold: float = 0.25

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_root.mkdir(parents=True, exist_ok=True)
    settings.artifacts_root.mkdir(parents=True, exist_ok=True)
    return settings
