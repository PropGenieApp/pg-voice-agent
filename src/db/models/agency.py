import uuid

from sqlalchemy import JSON, String, Text

from db.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from schema.agency import AgencySettings


class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=False), primary_key=True)
    assistant_name: Mapped[str] = mapped_column(String(255), nullable=False)
    agency_name: Mapped[str] = mapped_column(String(255), nullable=False)
    agency_location: Mapped[str] = mapped_column(String(255), nullable=False)
    agency_timezone: Mapped[str] = mapped_column(String(255), nullable=False)
    agency_description: Mapped[str] = mapped_column(Text, nullable=True)
    settings: Mapped[AgencySettings] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:
        return f"<Agency {self.agency_name}>"
