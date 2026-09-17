import secrets
from pathlib import Path

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class BaseAppSettings(BaseSettings):
    ENVIRONMENT: str = "local"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True,
    )

    APP_NAME: str = "Test API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    JWT_SECRET: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32))
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600

    DATABASE_URL: PostgresDsn = Field(
        ...,
        description="Async Database URL"
    )

    LOCAL_STORAGE_PATH: str = Field(
        default="storage",
        description="Local filesystem path for file storage",
    )

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    FRONTEND_URL: str = "https://app.nithinkcn.com"