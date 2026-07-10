from anthropic import AsyncAnthropic

from app.ai.base import AIProvider, AIResponse
from app.core.config import settings


class ClaudeProvider(AIProvider):
    COST_PER_1K_INPUT = 0.003
    COST_PER_1K_OUTPUT = 0.015

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self.client = AsyncAnthropic(api_key=self.api_key)

    @property
    def provider_name(self) -> str:
        return "claude"

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt or "You are an expert software engineer and code migration specialist.",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        content = response.content[0].text if response.content else ""
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens

        return AIResponse(
            content=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            model=self.model,
            provider=self.provider_name,
            cost=self.estimate_cost(tokens_in, tokens_out),
        )

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        chat_messages = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system or "You are an expert software engineer.",
            messages=chat_messages,
            temperature=temperature,
        )
        content = response.content[0].text if response.content else ""

        return AIResponse(
            content=content,
            tokens_input=response.usage.input_tokens,
            tokens_output=response.usage.output_tokens,
            model=self.model,
            provider=self.provider_name,
            cost=self.estimate_cost(response.usage.input_tokens, response.usage.output_tokens),
        )

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        return (tokens_input / 1000 * self.COST_PER_1K_INPUT) + (tokens_output / 1000 * self.COST_PER_1K_OUTPUT)
