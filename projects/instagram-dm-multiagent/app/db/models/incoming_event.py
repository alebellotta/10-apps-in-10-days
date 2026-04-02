from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IncomingEvent(Base):
    __tablename__ = "incoming_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
