#####################################################################################################

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from db.models.enums import ConversationPurpose
from schema.lead import LeadInfo, LeadOut


#####################################################################################################

class ConversationOut(BaseModel):
    id: int
    duration: int
    started_at: datetime
    topic: str | None
    purpose: ConversationPurpose | None
    lead_created: bool
    tool_calls: list[str]
    transcript: list[dict]
    lead: LeadOut | None

    class Config:
        from_attributes = True

#####################################################################################################

class ConversationState(BaseModel):
    started_at: datetime
    topic: str | None = None
    purpose: ConversationPurpose | None = None
    lead_created: bool = False
    tool_calls: set[str] = set()
    transcript: list[dict] = []
    lead_info: LeadInfo | None = None

    def set_purpose_by_event_type(self, event_type: Literal['Viewing', 'Valuation']) -> None:
        match event_type:
            case 'Viewing':
                self.purpose = ConversationPurpose.VIEWING
            case 'Valuation':
                self.purpose = ConversationPurpose.VALUATION

    def __bool__(self) -> bool:
        if self.started_at:
            return True
        return False
