from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import Sequence

from db.models.conversation import Conversation
from db.models.enums import ConversationPurpose
from db.repositories.base import AbstractRepository


class ConversationRepository(AbstractRepository):

    async def create(
        self,
        duration: int,
        started_at: datetime,
        topic: str | None,
        purpose: ConversationPurpose,
        lead_created: bool,
        tool_calls: list[str],
        transcript: list[dict],
        lead_id: int
    ) -> Conversation:
        conversation = Conversation(
            duration=duration,
            started_at=started_at,
            topic=topic,
            purpose=purpose,
            lead_created=lead_created,
            tool_calls=tool_calls,
            transcript=transcript,
            lead_id=lead_id,
        )
        self.session.add(conversation)
        await self.session.commit()
        return conversation

    async def get_by_id(self, id: Any) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(Conversation.id == id)
            .options(joinedload(Conversation.lead))
        )
        conversation = await self.session.execute(stmt)
        return conversation.scalar_one_or_none()

    async def get_list(self, limit: int = 10, offset: int = 0) -> Sequence[Conversation]:
        stmt = (
            select(Conversation)
            .options(joinedload(Conversation.lead))
            .offset(offset)
            .limit(limit)
            .order_by(Conversation.started_at.desc())
        )
        conversations = await self.session.execute(stmt)
        return conversations.scalars().all()

    async def delete(self, id: Any):
        pass
