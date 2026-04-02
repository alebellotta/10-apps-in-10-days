from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class NormalizedInstagramEvent(BaseModel):
    external_event_id: str
    event_type: str = "message"
    thread_external_id: str
    message_external_id: str
    sender_id: str
    recipient_id: str
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_payload: dict[str, Any]
