import google.generativeai as genai

from app.ai.base import AIProvider, AIResponse
from app.core.config import settings


class GeminiProvider(AIProvider):
    COST_PER_1K_INPUT = 0.00125
    COST_PER_1K_OUTPUT = 0.005

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or settings.GEMINI_MODEL
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        response = await self.model.generate_content_async(
            full_prompt,
            generation_config=genai.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens),
        )
        content = response.text or ""
        tokens_in = len(full_prompt.split()) * 2
        tokens_out = len(content.split()) * 2

        return AIResponse(
            content=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            model=self.model_name,
            provider=self.provider_name,
            cost=self.estimate_cost(tokens_in, tokens_out),
        )

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.3, max_tokens: int = 4096) -> AIResponse:
        history = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]} for m in messages[:-1]]
        chat = self.model.start_chat(history=history)
        last_message = messages[-1]["content"]
        response = await chat.send_message_async(
            last_message,
            generation_config=genai.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens),
        )
        content = response.text or ""
        tokens_in = sum(len(m["content"].split()) for m in messages) * 2
        tokens_out = len(content.split()) * 2

        return AIResponse(
            content=content,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            model=self.model_name,
            provider=self.provider_name,
            cost=self.estimate_cost(tokens_in, tokens_out),
        )

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        return (tokens_input / 1000 * self.COST_PER_1K_INPUT) + (tokens_output / 1000 * self.COST_PER_1K_OUTPUT)
