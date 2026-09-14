import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "GEORUSH SEO"
    app_env: str = "production"
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", "8000"))
    database_url: str = "sqlite:///./georush_seo.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings = Settings()
