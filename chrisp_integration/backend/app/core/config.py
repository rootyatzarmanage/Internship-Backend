from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    CRISP_IDENTIFIER: str
    CRISP_KEY: str
    CRISP_WEBSITE_ID: str

    FRONTEND_ORIGINS: str = (
        "http://127.0.0.1:5500,http://localhost:5500"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.FRONTEND_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()