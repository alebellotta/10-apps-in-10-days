from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class InstagramAccount(TimestampMixin, Base):
    __tablename__ = "instagram_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ig_business_account_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    page_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    account_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="active")
    auto_reply_mode: Mapped[str] = mapped_column(String(50), default="assisted")

    conversations = relationship("Conversation", back_populates="instagram_account")
