from typing import Any, TypedDict

from app.domain.schemas.agent import ClassifierOutput, DraftOutput, EscalationOutput, PolicyOutput, QAOutput, RetrievalOutput


class GraphState(TypedDict, total=False):
    event_id: int
    thread_id: int
    incoming_message_id: int
    incoming_text: str
    conversation_history: list[dict[str, str]]
    classifier_output: ClassifierOutput
    retrieval_output: RetrievalOutput
    policy_output: PolicyOutput
    draft_output: DraftOutput
    qa_output: QAOutput
    escalation_output: EscalationOutput
    dispatch_result: dict[str, Any]
    final_status: str
    errors: list[str]
    retry_count: int
    recipient_id: str
