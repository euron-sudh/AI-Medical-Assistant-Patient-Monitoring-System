"""Pydantic schemas for voice symptom analysis sessions."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
import uuid


class VoiceSessionStartRequest(BaseModel):
    """Request to start a new voice symptom analysis session."""
    patient_id: str
    language: str = "en"
    voice_preset: str = "nova"  # nova, alloy, echo, fable, onyx, shimmer


class VoiceSessionMessageRequest(BaseModel):
    """Request to send an audio/text message in a voice session."""
    session_id: str
    audio_base64: str | None = None  # Optional: base64-encoded audio
    text_message: str | None = None  # Optional: text fallback
    language: str = "en"


class VoiceSessionResponse(BaseModel):
    """Response from a voice session interaction."""
    session_id: str
    doctor_message: str
    doctor_audio_base64: str | None = None
    conversation_turn: int
    is_final_assessment: bool = False
    assessment_data: dict[str, Any] | None = None


class VoiceSessionState(BaseModel):
    """Current state of a voice symptom analysis session."""
    session_id: str
    patient_id: str
    status: str = "in_progress"  # in_progress, completed, cancelled
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    current_turn: int = 0
    language: str = "en"
    voice_preset: str = "nova"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    final_assessment: dict[str, Any] | None = None
