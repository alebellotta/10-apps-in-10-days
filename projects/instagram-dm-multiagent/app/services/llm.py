from app.core.config import get_settings
from app.domain.schemas.agent import ClassifierOutput, DraftOutput, EscalationOutput, PolicyOutput, QAOutput, RetrievalOutput
from app.integrations.llm.base import LLMAdapter, StructuredT
from app.integrations.llm.openai_adapter import OpenAIAdapter


class MockLLMAdapter(LLMAdapter):
    async def generate_text(self, prompt: str) -> str:
        return prompt[:500]

    async def generate_structured(self, prompt: str, schema: type[StructuredT]) -> StructuredT:
        prompt_lower = prompt.lower()
        if schema is ClassifierOutput:
            intent = "faq"
            priority = "low"
            sentiment = "neutral"
            requires_human = False
            confidence = 0.84
            if any(word in prompt_lower for word in ["refund", "legal", "payment", "lawsuit"]):
                intent = "sensitive"
                priority = "high"
                requires_human = True
                confidence = 0.93
            elif any(word in prompt_lower for word in ["problem", "issue", "support", "help"]):
                intent = "support"
                priority = "medium"
                confidence = 0.78
            elif any(word in prompt_lower for word in ["price", "cost", "preventivo", "demo", "call"]):
                intent = "lead"
                priority = "medium"
                confidence = 0.82
            return schema.model_validate(
                {
                    "intent": intent,
                    "language": "it",
                    "sentiment": sentiment,
                    "priority": priority,
                    "requires_human": requires_human,
                    "confidence": confidence,
                    "reasoning_summary": "Heuristic mock classification",
                }
            )
        if schema is RetrievalOutput:
            return schema.model_validate(
                {
                    "conversation_summary": "Recent Instagram DM thread",
                    "relevant_faq_entries": [],
                    "known_customer_data": {},
                    "missing_information": [],
                }
            )
        if schema is PolicyOutput:
            flags = []
            allowed = True
            risk = "low"
            human = False
            if any(word in prompt_lower for word in ["refund", "payment", "legal", "sensitive"]):
                flags.append("sensitive_topic")
                allowed = False
                risk = "high"
                human = True
            return schema.model_validate(
                {
                    "allowed_to_auto_reply": allowed,
                    "risk_level": risk,
                    "policy_flags": flags,
                    "requires_human_approval": human,
                    "safe_response_constraints": ["Do not invent business policies"],
                }
            )
        if schema is DraftOutput:
            return schema.model_validate(
                {
                    "draft_response": "Ciao, grazie per averci scritto. Ti aiuto volentieri. Puoi condividere un dettaglio in piu cosi ti rispondo in modo preciso?",
                    "response_style": "friendly_professional",
                    "used_sources": [],
                    "open_questions": [],
                }
            )
        if schema is QAOutput:
            approved = "refund" not in prompt_lower and "legal" not in prompt_lower
            return schema.model_validate(
                {
                    "approved": approved,
                    "qa_score": 0.91 if approved else 0.42,
                    "issues": [] if approved else ["Sensitive topic requires human review"],
                    "revised_response": "Ciao, grazie per il messaggio. Un membro del team ti rispondera a breve." if not approved else "",
                    "final_decision": "send" if approved else "escalate",
                }
            )
        if schema is EscalationOutput:
            return schema.model_validate(
                {
                    "escalation_reason": "Policy or confidence threshold triggered",
                    "operator_summary": "The system flagged this conversation for human follow-up.",
                    "suggested_reply": "Ciao, stiamo verificando la tua richiesta e ti rispondiamo al piu presto.",
                    "priority": "high",
                }
            )
        return schema.model_validate({})


def get_llm_adapter() -> LLMAdapter:
    settings = get_settings()
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAIAdapter()
    return MockLLMAdapter()
