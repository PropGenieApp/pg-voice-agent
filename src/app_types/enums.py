from enum import IntEnum, StrEnum


class AudioEncoding(StrEnum):
    """
    There are more formats but only these available for streaming
    https://developers.deepgram.com/docs/tts-media-output-settings#supported-audio-formats
    """
    LINEAR16 = "linear16"
    MULAW = "mulaw"
    ALAW = "alaw"


class AudioContainer(StrEnum):
    """
    https://developers.deepgram.com/docs/tts-media-output-settings#audio-format-combinations
    """
    NONE = "none"
    WAV = "wav"
    N_A = "n/a"
    OGG = "ogg"

class ListenModel(StrEnum):
    """
    https://developers.deepgram.com/docs/models-languages-overview
    """
    NOVA_3 = "nova-3"
    NOVA_2 = "nova-2"
    
class SampleRate(IntEnum):
    """
    https://developers.deepgram.com/docs/models-languages-overview
    """
    SAMPLE_RATE_8000 = 8000
    SAMPLE_RATE_16000 = 16000
    SAMPLE_RATE_24000 = 24000
    SAMPLE_RATE_32000 = 32000
    SAMPLE_RATE_48000 = 48000
