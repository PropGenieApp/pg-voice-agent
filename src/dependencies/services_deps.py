from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.common import get_db
from services.agency import AgencyService


def get_agency_service(session: AsyncSession = Depends(get_db)) -> AgencyService:
    return AgencyService(session=session)
