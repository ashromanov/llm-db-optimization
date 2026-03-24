from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from src.settings import AppSettings, LLMProvider


def create_llm(
    settings: AppSettings,
    temperature: float | None = None,
) -> BaseChatModel:
    temp = temperature if temperature is not None else settings.llm_temperature

    if settings.llm_provider == LLMProvider.GEMINI:
        return ChatGoogleGenerativeAI(
            google_api_key=settings.google_api_key,
            model=settings.gemini_model,
            temperature=temp,
        )

    return ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        temperature=temp,
    )
