"""
Settings module for LLM service.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """
    Settings for FastAPI application.
    """

    openai_api_key: str = "EMPTY"
    openai_base_url: str = "http://213.219.215.222:8000/v1"
    google_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = AppSettings()
