import httpx

from app.ai.base import AIProvider, AIResponse
from app.core.config import settings


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    @property
    def provider_name(self) -> str:
        return "ollama"

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return await self.chat(messages, temperature, max_tokens)

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens},
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        tokens_in = data.get("prompt_eval_count", 0)
        tokens_out = data.get("eval_count", 0)

        return AIResponse(
            content=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            model=self.model,
            provider=self.provider_name,
            cost=0.0,
        )

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        return 0.0
