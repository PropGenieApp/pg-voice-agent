#####################################################################################################

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession

#####################################################################################################

class DatabaseManager:
    def __init__(self, engine: AsyncEngine, session_maker: async_sessionmaker) -> None:
        self._engine = engine
        self._session_maker = session_maker

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    async def close(self) -> None:
        if self._engine:
            await self._engine.dispose()

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[AsyncSession, None]:
        session = self._session_maker()
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
        finally:
            await session.close()

#####################################################################################################
