from typing import Optional

from app.ai.base import AIProvider
from app.ai.claude_provider import ClaudeProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.ollama_provider import OllamaProvider
from app.ai.openai_provider import OpenAIProvider
from app.core.config import settings


class AIProviderFactory:
    """Factory for creating AI provider instances. Supports runtime switching."""

    _providers: dict[str, type[AIProvider]] = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
        "ollama": OllamaProvider,
    }

    _current_provider: str = settings.DEFAULT_AI_PROVIDER
    _instances: dict[str, AIProvider] = {}

    @classmethod
    def get_provider(cls, provider_name: str | None = None, **kwargs) -> AIProvider:
        name = provider_name or cls._current_provider
        if name not in cls._providers:
            raise ValueError(f"Unknown AI provider: {name}. Available: {list(cls._providers.keys())}")

        cache_key = f"{name}:{kwargs.get('model', '')}"
        if cache_key not in cls._instances:
            cls._instances[cache_key] = cls._providers[name](**kwargs)
        return cls._instances[cache_key]

    @classmethod
    def set_default_provider(cls, provider_name: str) -> None:
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown AI provider: {provider_name}")
        cls._current_provider = provider_name
        cls._instances.clear()

    @classmethod
    def get_current_provider_name(cls) -> str:
        return cls._current_provider

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def register_provider(cls, name: str, provider_class: type[AIProvider]) -> None:
        cls._providers[name] = provider_class
