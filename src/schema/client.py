from pydantic import BaseModel, UUID4


class ClientJsonMessage(BaseModel):
    type: str
    client_id: UUID4 | None
    dev_mode: bool = False
    # voice_id: str | None = None
