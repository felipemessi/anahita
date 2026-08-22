"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings model for all environment-driven configuration."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/anahita"

    secret_key: str = "change-me-in-production-please-32b"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    storage_type: str = "local"
    storage_local_path: str = "/data/uploads"


settings = Settings()
