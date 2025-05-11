from abc import ABC, abstractmethod
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession


class AbstractRepository(ABC):

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @abstractmethod
    async def create(self, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    async def get_by_id(self, id: Any) -> Any:
        pass

    @abstractmethod
    async def get_list(self, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    async def delete(self, id: Any) -> Any:
        pass
