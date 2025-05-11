from pydantic import BaseModel, UUID4

class _DevOptions(BaseModel):
    voice_model: str | None
    provider: str | None
    voice_id: str | None

class ClientJsonMessage(BaseModel):
    type: str
    client_id: UUID4 | None
    dev_mode: bool = False
    dev_options: _DevOptions | None = None
