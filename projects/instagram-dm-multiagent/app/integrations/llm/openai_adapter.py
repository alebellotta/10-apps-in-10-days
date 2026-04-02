import json

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.integrations.llm.base import LLMAdapter, StructuredT


class OpenAIAdapter(LLMAdapter):
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate_text(self, prompt: str) -> str:
        response = await self.client.responses.create(model=self.model, input=prompt)
        return response.output_text

    async def generate_structured(self, prompt: str, schema: type[StructuredT]) -> StructuredT:
        response = await self.client.responses.create(
            model=self.model,
            input=prompt,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                },
            },
        )
        return schema.model_validate(json.loads(response.output_text))
