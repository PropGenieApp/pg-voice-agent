from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import App


def get_app(request: Request) -> App:
    return request.app

async def get_db(request: Request) -> AsyncSession:
    session_manager = request.app.db_manager
    async with session_manager.connect() as session:
        yield session
