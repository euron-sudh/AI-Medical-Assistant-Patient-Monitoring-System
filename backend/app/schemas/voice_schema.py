"""Voice request/response schemas."""

from pydantic import BaseModel, Field


class TranscribeResponse(BaseModel):
    """Schema for transcription response."""
    text: str
    language: str | None = None
    duration_seconds: float | None = None
    confidence: float | None = None


class SynthesizeRequest(BaseModel):
    """Schema for text-to-speech synthesis request."""
    text: str = Field(min_length=1, max_length=5000)
    voice: str = Field(default="alloy", pattern="^(alloy|echo|fable|onyx|nova|shimmer)$")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


class SynthesizeResponse(BaseModel):
    """Schema for synthesis response."""
    audio_url: str | None = None
    audio_base64: str | None = None
    format: str = "mp3"
    message: str | None = None
