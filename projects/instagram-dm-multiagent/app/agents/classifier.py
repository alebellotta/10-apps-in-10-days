from app.agents.prompts.classifier_prompt import build_classifier_prompt
from app.domain.schemas.agent import ClassifierOutput
from app.integrations.llm.base import LLMAdapter


class IntentClassifierAgent:
    def __init__(self, llm: LLMAdapter) -> None:
        self.llm = llm

    async def run(self, text: str, history: list[dict[str, str]], user_metadata: dict[str, str]) -> ClassifierOutput:
        prompt = build_classifier_prompt(text=text, history=history, user_metadata=user_metadata)
        return await self.llm.generate_structured(prompt, ClassifierOutput)
