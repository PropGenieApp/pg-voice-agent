

from typing import Any
from sqlalchemy import select
from db.models.lead import Lead
from db.repositories.base import AbstractRepository


class LeadRepository(AbstractRepository):

    async def create(self, name: str, email: str | None, phone: str | None) -> Lead:
        lead = Lead(name=name, email=email, phone=phone)
        self.session.add(lead)
        await self.session.commit()
        return lead

    async def get_by_id(self, id: Any) -> Lead | None:
        stmt = select(Lead).where(Lead.id == id)
        lead = await self.session.execute(stmt)
        return lead.scalar_one_or_none()

    async def get_list(self, *args, **kwargs):
        pass

    async def delete(self, id: Any):
        pass
