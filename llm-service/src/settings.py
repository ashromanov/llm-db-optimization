"""
Settings module for LLM service.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """
    Settings for FastAPI application.
    """
    
    google_api_key: str
    openrouter_api_key: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = AppSettings()
