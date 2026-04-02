from app.agents.prompts.critic_prompt import build_critic_prompt
from app.domain.schemas.agent import DraftOutput, PolicyOutput, QAOutput
from app.integrations.llm.base import LLMAdapter


class CriticAgent:
    def __init__(self, llm: LLMAdapter) -> None:
        self.llm = llm

    async def run(self, text: str, draft_output: DraftOutput, policy_output: PolicyOutput) -> QAOutput:
        prompt = build_critic_prompt(
            text=text,
            draft_response=draft_output.draft_response,
            policy_output=policy_output.model_dump(),
        )
        return await self.llm.generate_structured(prompt, QAOutput)
