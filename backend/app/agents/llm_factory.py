import logging
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from app.config.settings import settings

logger = logging.getLogger("metricmind.agents.llm_factory")


class LLMFactory:
    @staticmethod
    def get_provider_status(provider: Literal["groq", "openai", "gemini"]) -> tuple[bool, str]:
        if provider == "groq":
            return (bool(settings.groq_api_key), "GROQ_API_KEY is configured" if settings.groq_api_key else "GROQ_API_KEY is missing")
        if provider == "openai":
            return (bool(settings.openai_api_key), "OPENAI_API_KEY is configured" if settings.openai_api_key else "OPENAI_API_KEY is missing")
        if provider == "gemini":
            return (bool(settings.gemini_api_key), "GEMINI_API_KEY is configured" if settings.gemini_api_key else "GEMINI_API_KEY is missing")
        return (False, f"Unsupported LLM provider: {provider}")

    @staticmethod
    def create_llm(
        provider: Literal["groq", "openai", "gemini"] | None = None,
        model: str | None = None,
        temperature: float = 0.1,
    ) -> BaseChatModel:
        provider = provider or settings.llm_provider
        if provider == "groq":
            if not settings.groq_api_key:
                raise ValueError("Missing API key: GROQ_API_KEY is not set in environment variables")
            model = model or settings.groq_model
            logger.info("Creating Groq LLM with model: %s", model)
            return ChatGroq(
                model=model,
                temperature=temperature,
                api_key=settings.groq_api_key,
            )
        elif provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("Missing API key: OPENAI_API_KEY is not set in environment variables")
            model = model or settings.openai_model
            logger.info("Creating OpenAI LLM with model: %s", model)
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=settings.openai_api_key,
            )
        elif provider == "gemini":
            if not settings.gemini_api_key:
                raise ValueError("Missing API key: GEMINI_API_KEY is not set in environment variables")
            model = model or settings.gemini_model
            logger.info("Creating Gemini LLM with model: %s", model)
            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=settings.gemini_api_key,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
