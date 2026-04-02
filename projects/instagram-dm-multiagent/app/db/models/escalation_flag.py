from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EscalationFlag(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("instagram_threads.id"), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("instagram_messages.id"), nullable=True)
    reason: Mapped[str] = mapped_column(String(255), index=True)
    priority: Mapped[str] = mapped_column(String(50), default="medium")
    operator_summary: Mapped[str] = mapped_column(Text())
    suggested_reply: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    conversation = relationship("Conversation", back_populates="escalations")
