# TODO Replace Filed(default=None) to = None
#####################################################################################################

from typing import Any, Literal, Self

from pydantic import BaseModel, model_validator, UUID4

from pydantic.fields import Field

from app_types.enums import AudioContainer, AudioEncoding, ListenModel, SampleRate

#####################################################################################################

class InputSettings(BaseModel):
    encoding: AudioEncoding | None = Field(default=AudioEncoding.LINEAR16)
    sample_rate: SampleRate = Field(default=SampleRate.SAMPLE_RATE_16000)

#####################################################################################################

class OutputSettings(InputSettings):
    # bitrate: int | None = Field(default=None) # Its not applicable for streaming
    container: AudioContainer | None = Field(default=AudioContainer.NONE)

#####################################################################################################

class AudioSettings(BaseModel):
    input: InputSettings
    output: OutputSettings

#####################################################################################################

class ListenSettings(BaseModel):
    model: ListenModel | None = Field(default=ListenModel.NOVA_3)
    keyterms: list[str] | None = Field(default=None)  # TODO: investigate https://developers.deepgram.com/docs/keyterm

#####################################################################################################

class ThinkProvider(BaseModel):
    # https://developers.deepgram.com/docs/voice-agent-llm-models#passing-a-custom-llm-through-a-cloud-provider
    type: Literal["openai", "anthropic", "custom"]
    # url: str | None = Field(default=None)
    # headers: dict[str, str] | None = Field(default=None)

#####################################################################################################

class Function(BaseModel):
    name: str
    description: str
    url: str | None = Field(default=None)
    method: str | None = Field(default=None)
    headers: list[dict[str, str]] | None = Field(default=None)  # FIXME: create class for header
    parameters: dict[str, Any] | None = Field(default=None)  # FIXME: create class for parameters

#####################################################################################################

class ThinkSettings(BaseModel):
    provider: ThinkProvider
    model: str
    instructions: str
    functions: list[Function] | None = Field(default=None)

#####################################################################################################

class SpeakSettings(BaseModel):
    """
    Configuration for text-to-speech functionality. You must either:
    - Specify a model (for default provider), OR
    - Specify a provider with its corresponding voice_id
    """
    model: str | None = Field(default=None, description="TTS model identifier when using default provider")
    provider: Literal["eleven_labs", "open_ai"] | None = Field(default=None, description="External TTS provider")
    voice_id: str | None = Field(default=None, description="Voice identifier for the specified provider")
    
    @model_validator(mode="after")
    def validate_model_provider(self) -> Self:
        if not any([self.model, self.provider, self.voice_id]):
            raise ValueError("At least one of model, provider, or voice_id must be provided")
        if self.model is not None and (self.provider is not None or self.voice_id is not None):
            raise ValueError("If model is specified, provider and voice_id must be None")
        if self.provider is not None:
            if self.model is not None:
                raise ValueError("If provider is specified, model must be None")
            if self.voice_id is None:
                raise ValueError("If provider is specified, voice_id must be provided")
        return self
#####################################################################################################

class Context(BaseModel):
    messages: list[tuple[str, str]] | None = Field(default=None)
    replay: bool = Field(default=False)

#####################################################################################################

class DeepgramAgentSettings(BaseModel):
    listen: ListenSettings
    think: ThinkSettings
    speak: SpeakSettings

#####################################################################################################

class DeepgramAgentSettingsIn(BaseModel):
    listen: ListenSettings
    speak: SpeakSettings

#####################################################################################################

class AgencySettings(BaseModel):
    audio: AudioSettings
    agent: DeepgramAgentSettings

#####################################################################################################

class AgencySettingsIn(BaseModel):
    agent: DeepgramAgentSettingsIn

#####################################################################################################

class BaseAgency(BaseModel):
    id: UUID4
    assistant_name: str
    agency_name: str
    agency_location: str
    agency_timezone: str
    agency_description: str

#####################################################################################################

class Agency(BaseAgency):
    settings: AgencySettings

#####################################################################################################

class AgencyIn(BaseAgency):
    settings: AgencySettingsIn

#####################################################################################################

class AgencyCreate(AgencyIn):
    viewing_task: bool
    valuation_task: bool

#####################################################################################################

class AgencyUpdate(AgencyIn):
    pass

#####################################################################################################

class AgencyDetail(AgencyIn):
    pass

#####################################################################################################

class AgencyOut(AgencyIn):
    pass
