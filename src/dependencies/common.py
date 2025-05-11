from fastapi import Depends, Request, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app import App
from db.repositories.conversation import ConversationRepository


def get_app(request: Request) -> App:
    return request.app

async def get_db(request: Request) -> AsyncSession:
    session_manager = request.app.db_manager
    async with session_manager.connect() as session:
        yield session

async def get_ws_db(websocket: WebSocket) -> AsyncSession:
    session_manager = websocket.app.db_manager
    async with session_manager.connect() as session:
        yield session

async def conv_repository(db_session: AsyncSession = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(db_session)
