from typing import Literal

from pydantic import BaseModel, Field


class ClassifierOutput(BaseModel):
    intent: Literal["faq", "lead", "support", "generic", "complaint", "sensitive", "spam", "unknown"]
    language: str
    sentiment: Literal["positive", "neutral", "negative"]
    priority: Literal["low", "medium", "high"]
    requires_human: bool
    confidence: float = Field(ge=0, le=1)
    reasoning_summary: str


class RetrievalOutput(BaseModel):
    conversation_summary: str
    relevant_faq_entries: list[dict[str, str]]
    known_customer_data: dict[str, str]
    missing_information: list[str]


class PolicyOutput(BaseModel):
    allowed_to_auto_reply: bool
    risk_level: Literal["low", "medium", "high"]
    policy_flags: list[str]
    requires_human_approval: bool
    safe_response_constraints: list[str]


class DraftOutput(BaseModel):
    draft_response: str
    response_style: str
    used_sources: list[str]
    open_questions: list[str]


class QAOutput(BaseModel):
    approved: bool
    qa_score: float = Field(ge=0, le=1)
    issues: list[str]
    revised_response: str
    final_decision: Literal["send", "revise", "escalate"]


class EscalationOutput(BaseModel):
    escalation_reason: str
    operator_summary: str
    suggested_reply: str
    priority: Literal["low", "medium", "high"]
