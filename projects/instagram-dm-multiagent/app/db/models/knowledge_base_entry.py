from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KnowledgeBaseEntry(Base):
    __tablename__ = "knowledge_base_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    question: Mapped[str] = mapped_column(Text())
    answer: Mapped[str] = mapped_column(Text())
    language: Mapped[str] = mapped_column(String(10), default="it", index=True)
    tags: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
