import secrets
from pathlib import Path

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True,
    )
    DEBUG: bool = False  
    LOCAL_STORAGE_PATH: str = "storage" 
    ENVIRONMENT: str = "local"
    APP_NAME: str = "Test API"
    API_V1_PREFIX: str = "/api/v1"
    JWT_SECRET: SecretStr = Field(default_factory=lambda: SecretStr(secrets.token_urlsafe(32)))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: PostgresDsn = Field(...)
    DATABASE_URL_SYNC: PostgresDsn = Field(...)
    CORS_ORIGINS: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500","http://0.0.0.0:8080/","http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS: bool = True
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False
    DB_USE_SSL: bool = False
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value
