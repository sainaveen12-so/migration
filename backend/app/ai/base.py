from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AIResponse:
    content: str
    tokens_input: int = 0
    tokens_output: int = 0
    model: str = ""
    provider: str = ""
    cost: float = 0.0
    metadata: Optional[dict[str, Any]] = None


class AIProvider(ABC):
    """Abstract base class for AI providers using Strategy pattern."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
        pass

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
        pass

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        return 0.0
