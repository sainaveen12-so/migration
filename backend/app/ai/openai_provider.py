from openai import AsyncOpenAI

from app.ai.base import AIProvider, AIResponse
from app.core.config import settings


class OpenAIProvider(AIProvider):
  COST_PER_1K_INPUT = 0.005
  COST_PER_1K_OUTPUT = 0.015

  def __init__(self, api_key: str | None = None, model: str | None = None):
    self.api_key = api_key or settings.OPENAI_API_KEY
    self.model = model or settings.OPENAI_MODEL
    self.client = AsyncOpenAI(api_key=self.api_key)

  @property
  def provider_name(self) -> str:
    return "openai"

  async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
    messages = []
    if system_prompt:
      messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = await self.client.chat.completions.create(
      model=self.model,
      messages=messages,
      temperature=temperature,
      max_tokens=max_tokens,
    )
    usage = response.usage
    tokens_in = usage.prompt_tokens if usage else 0
    tokens_out = usage.completion_tokens if usage else 0
    content = response.choices[0].message.content or ""

    return AIResponse(
      content=content,
      tokens_input=tokens_in,
      tokens_output=tokens_out,
      model=self.model,
      provider=self.provider_name,
      cost=self.estimate_cost(tokens_in, tokens_out),
    )

  async def chat(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
    response = await self.client.chat.completions.create(
      model=self.model,
      messages=messages,
      temperature=temperature,
      max_tokens=max_tokens,
    )
    usage = response.usage
    tokens_in = usage.prompt_tokens if usage else 0
    tokens_out = usage.completion_tokens if usage else 0

    return AIResponse(
      content=response.choices[0].message.content or "",
      tokens_input=tokens_in,
      tokens_output=tokens_out,
      model=self.model,
      provider=self.provider_name,
      cost=self.estimate_cost(tokens_in, tokens_out),
    )

  def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
    return (tokens_input / 1000 * self.COST_PER_1K_INPUT) + (tokens_output / 1000 * self.COST_PER_1K_OUTPUT)
