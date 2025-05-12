import uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID, String

from db.models.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=False), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(length=50), nullable=True)

    conversation: Mapped["Conversation"] = relationship(
        back_populates="lead",
        uselist=False,
    )

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, name={self.name})>"
