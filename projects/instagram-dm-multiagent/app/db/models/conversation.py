from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class Conversation(TimestampMixin, Base):
    __tablename__ = "instagram_threads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    instagram_account_id: Mapped[int] = mapped_column(ForeignKey("instagram_accounts.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("instagram_users.id"), index=True)
    user_external_id: Mapped[str] = mapped_column(String(255), index=True)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    thread_status: Mapped[str] = mapped_column(String(50), default="open")
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)

    instagram_account = relationship("InstagramAccount", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    conversation_state = relationship("ConversationState", back_populates="conversation", uselist=False, cascade="all, delete-orphan")
    escalations = relationship("EscalationFlag", back_populates="conversation", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="conversation", cascade="all, delete-orphan")
