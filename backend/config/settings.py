"""
settings.py — Application configuration via Pydantic Settings

All environment variables are validated and typed here.
Import `settings` anywhere in the app to access config values.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server
    environment: str = "development"
    port: int = 3001

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "hvac_db"
    db_user: str = "hvac_user"
    db_password: str = "hvacpassword"

    # JWT
    jwt_secret: str = "replace_with_a_long_random_secret"
    jwt_expires_in: str = "8h"

    # Internal service secret (Python ai-service → this backend)
    internal_api_secret: str = ""

    # CORS
    frontend_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
