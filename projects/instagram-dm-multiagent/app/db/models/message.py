from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Message(Base):
    __tablename__ = "instagram_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("instagram_threads.id"), index=True)
    external_message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    direction: Mapped[str] = mapped_column(String(50))
    sender_id: Mapped[str] = mapped_column(String(255), index=True)
    recipient_id: Mapped[str] = mapped_column(String(255), index=True)
    text: Mapped[str] = mapped_column(Text())
    raw_payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    message_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    delivery_status: Mapped[str] = mapped_column(String(50), default="received")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    conversation = relationship("Conversation", back_populates="messages")
