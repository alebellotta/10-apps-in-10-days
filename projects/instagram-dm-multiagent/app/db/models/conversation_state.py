from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConversationState(Base):
    __tablename__ = "conversation_states"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("instagram_threads.id"), unique=True, index=True)
    state_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_classifier_output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    last_policy_output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    last_qa_output_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    conversation = relationship("Conversation", back_populates="conversation_state")
