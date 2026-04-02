from app.agents.prompts.drafter_prompt import build_drafter_prompt
from app.domain.schemas.agent import ClassifierOutput, DraftOutput, RetrievalOutput
from app.integrations.llm.base import LLMAdapter


class ResponseDraftingAgent:
    def __init__(self, llm: LLMAdapter) -> None:
        self.llm = llm

    async def run(
        self,
        text: str,
        classifier_output: ClassifierOutput,
        retrieval_output: RetrievalOutput,
        constraints: list[str],
    ) -> DraftOutput:
        prompt = build_drafter_prompt(
            text=text,
            classifier_output=classifier_output.model_dump(),
            retrieval_output=retrieval_output.model_dump(),
            constraints=constraints,
        )
        return await self.llm.generate_structured(prompt, DraftOutput)
