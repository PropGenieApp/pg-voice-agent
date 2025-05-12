from typing import Final

from fastapi import APIRouter, Depends, HTTPException

from db.repositories.conversation import ConversationRepository
from dependencies.common import conv_repository
from schema.conversation import ConversationOut


#####################################################################################################

router: Final = APIRouter(tags=["Conversation"], prefix="/api/conversation")

#####################################################################################################

@router.get("/")
async def get_conversation_list(
    limit: int = 20,
    offset: int = 0,
    repository: ConversationRepository = Depends(conv_repository),
) -> list[ConversationOut]:
    conversations = await repository.get_list(limit, offset)
    return [ConversationOut.model_validate(conversation) for conversation in conversations]

#####################################################################################################

@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    repository: ConversationRepository = Depends(conv_repository),
) -> ConversationOut:
    conversation = await repository.get_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut.model_validate(conversation)

#####################################################################################################

