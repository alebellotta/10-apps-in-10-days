from app.agents.prompts.escalation_prompt import build_escalation_prompt
from app.domain.schemas.agent import ClassifierOutput, DraftOutput, EscalationOutput, PolicyOutput
from app.integrations.llm.base import LLMAdapter


class EscalationAgent:
    def __init__(self, llm: LLMAdapter) -> None:
        self.llm = llm

    async def run(
        self,
        text: str,
        classifier_output: ClassifierOutput,
        policy_output: PolicyOutput,
        draft_output: DraftOutput | None,
    ) -> EscalationOutput:
        prompt = build_escalation_prompt(
            text=text,
            classifier_output=classifier_output.model_dump(),
            policy_output=policy_output.model_dump(),
            draft_output=draft_output.model_dump() if draft_output else None,
        )
        return await self.llm.generate_structured(prompt, EscalationOutput)
