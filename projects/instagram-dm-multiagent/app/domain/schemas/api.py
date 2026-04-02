from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.domain.schemas.common import ORMModel


class WebhookVerificationResponse(BaseModel):
    challenge: str


class WebhookIngestResponse(BaseModel):
    status: str
    event_ids: list[int]


class ConversationRead(ORMModel):
    id: int
    thread_external_id: str
    user_external_id: str
    thread_status: str
    assigned_to: str | None
    last_message_at: datetime


class MessageRead(ORMModel):
    id: int
    external_message_id: str
    direction: str
    sender_id: str
    recipient_id: str
    text: str
    message_timestamp: datetime
    delivery_status: str


class EscalationRead(ORMModel):
    id: int
    thread_id: int
    reason: str
    priority: str
    operator_summary: str
    suggested_reply: str | None
    status: str
    created_at: datetime
    resolved_at: datetime | None


class ThreadDetailResponse(BaseModel):
    thread: ConversationRead
    messages: list[MessageRead]
    escalation: EscalationRead | None = None
    draft: str | None = None
    mode: str
    state: dict[str, Any] = Field(default_factory=dict)


class ApproveDraftRequest(BaseModel):
    text: str | None = None


class ManualMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class RetryProcessingResponse(BaseModel):
    status: str
    event_id: int


class UpdateModeRequest(BaseModel):
    mode: str


class KnowledgeBaseCreate(BaseModel):
    category: str
    question: str
    answer: str
    language: str = "it"
    tags: str = ""
    is_active: bool = True


class KnowledgeBaseUpdate(BaseModel):
    category: str | None = None
    question: str | None = None
    answer: str | None = None
    language: str | None = None
    tags: str | None = None
    is_active: bool | None = None


class KnowledgeBaseRead(ORMModel):
    id: int
    category: str
    question: str
    answer: str
    language: str
    tags: str
    is_active: bool
    updated_at: datetime
