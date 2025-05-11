from pydantic import BaseModel, UUID4


class LeadInfo(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None


class LeadOut(LeadInfo):
    id: UUID4

    class Config:
        from_attributes = True
