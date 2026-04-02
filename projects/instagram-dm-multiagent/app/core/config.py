from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    app_name: str = "instagram-dm-multiagent"
    api_rate_limit_per_minute: int = 60

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "instagram_dm"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    database_url: str | None = "sqlite+aiosqlite:///./local.db"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_url: str | None = None
    queue_name: str = "instagram_incoming_events"
    queue_mode: str = "inline"
    worker_poll_seconds: float = 1.0
    worker_enabled: bool = True

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    llm_provider: str = "mock"

    meta_app_secret: str = ""
    meta_verify_token: str = "change-me"
    meta_page_access_token: str = ""
    meta_graph_api_version: str = "v23.0"
    meta_api_base_url: str = "https://graph.facebook.com"

    default_auto_reply_mode: str = "assisted"
    default_history_limit: int = 10
    brand_voice_path: str = str(BASE_DIR / "app" / "agents" / "prompts" / "brand_voice.yaml")
    retry_draft_limit: int = 1

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_dsn(self) -> str:
        if self.redis_url:
            return self.redis_url
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
