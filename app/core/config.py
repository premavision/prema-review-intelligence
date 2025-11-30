from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: Literal["local", "dev", "prod"] = "local"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/app.db"
    data_dir: str = "./data"

    max_themes: int = 6
    summary_cache_ttl_minutes: int = 120

    llm_provider: Literal["mock", "openai"] = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # Security settings
    cors_allowed_origins: str = ""
    max_upload_size: int = 10485760  # 10MB default
    max_ingestion_rows: int = 50000  # DoS protection
    llm_rate_limit_rpm: int = 60  # Rate limit for LLM API calls

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_path.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()

