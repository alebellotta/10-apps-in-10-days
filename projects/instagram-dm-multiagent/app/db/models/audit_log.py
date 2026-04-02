from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("instagram_threads.id"), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("instagram_messages.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    actor_type: Mapped[str] = mapped_column(String(50))
    actor_name: Mapped[str] = mapped_column(String(100))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    conversation = relationship("Conversation", back_populates="audit_logs")
