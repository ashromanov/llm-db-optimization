from enum import StrEnum

from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OPENAI_COMPATIBLE = "openai_compatible"


class AppSettings(BaseSettings):
    llm_provider: LLMProvider = LLMProvider.GEMINI

    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    openai_api_key: str = ""
    openai_base_url: str = "https://openrouter.ai/api/v1"
    openai_model: str = "google/gemini-2.5-flash"

    llm_temperature: float = 0.0
    llm_analyst_temperature: float = 0.2

    task_ttl_seconds: int = 3600
    task_cleanup_interval_seconds: int = 300

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    workers: int = 1
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = AppSettings()
