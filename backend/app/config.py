"""Application configuration.

Purpose: Load runtime settings from environment variables.
Callers: FastAPI app, database setup, services needing limits or paths.
Deps: functools, pathlib, pydantic-settings.
API: Settings model and cached get_settings accessor.
Side effects: Reads .env when Settings is instantiated.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    database_url: str = 'sqlite:///./chatfilter.db'
    cors_origins: str = 'http://localhost:5173'
    rate_limit_per_minute: int = 60
    max_message_length: int = 2000
    max_batch_size: int = 25
    model_path: Path = Path('artifacts/spam_model.joblib')
    metrics_path: Path = Path('artifacts/model_metrics.json')

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
