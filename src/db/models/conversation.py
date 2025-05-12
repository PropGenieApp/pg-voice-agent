
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, ForeignKey, Integer, String, JSON, TIMESTAMP

from db.models.base import Base
from db.models.enums import ConversationPurpose


class Conversation(Base):
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    topic: Mapped[str] = mapped_column(String(length=100), nullable=True)
    purpose: Mapped[ConversationPurpose] = mapped_column(String(length=50), nullable=True)
    lead_created: Mapped[bool] = mapped_column(Boolean, default=False)
    tool_calls: Mapped[list[str]] = mapped_column(JSON, nullable=True)
    transcript: Mapped[list[dict]] = mapped_column(JSON, nullable=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, unique=True)

    lead: Mapped["Lead"] = relationship(back_populates="conversation")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id})>"
