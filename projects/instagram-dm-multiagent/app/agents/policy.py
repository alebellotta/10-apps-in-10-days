from app.agents.prompts.policy_prompt import build_policy_prompt
from app.domain.schemas.agent import ClassifierOutput, PolicyOutput, RetrievalOutput
from app.integrations.llm.base import LLMAdapter


class PolicyAgent:
    def __init__(self, llm: LLMAdapter) -> None:
        self.llm = llm

    async def run(self, text: str, classifier_output: ClassifierOutput, retrieval_output: RetrievalOutput) -> PolicyOutput:
        prompt = build_policy_prompt(
            text=text,
            classifier_output=classifier_output.model_dump(),
            retrieval_output=retrieval_output.model_dump(),
        )
        output = await self.llm.generate_structured(prompt, PolicyOutput)
        if classifier_output.requires_human or classifier_output.confidence < 0.7:
            output.allowed_to_auto_reply = False
            output.requires_human_approval = True
            output.risk_level = "high" if classifier_output.priority == "high" else "medium"
            if "low_confidence" not in output.policy_flags and classifier_output.confidence < 0.7:
                output.policy_flags.append("low_confidence")
        return output
