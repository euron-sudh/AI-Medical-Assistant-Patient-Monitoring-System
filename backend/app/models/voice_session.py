"""Voice Session model — tracks voice-based symptom analysis conversations."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.extensions import db


class VoiceSession(db.Model):
    """Voice symptom analysis session tracking.

    Stores conversation history, session state, and final assessment
    for voice-based symptom checker interactions.
    """

    __tablename__ = "voice_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), db.ForeignKey("users.id"), nullable=False, index=True)
    
    # Session state
    status = Column(String(20), nullable=False, default="in_progress")  # in_progress, completed, cancelled
    language = Column(String(10), nullable=False, default="en")
    voice_preset = Column(String(20), nullable=False, default="nova")
    
    # Conversation tracking
    conversation_turn = Column(Integer, nullable=False, default=0)
    conversation_history = Column(JSONB, nullable=False, default=list)
    
    # Final assessment (populated when session completes)
    final_assessment = Column(JSONB, nullable=True)
    
    # Audio metadata
    total_audio_duration_seconds = Column(Integer, nullable=True)
    transcription_provider = Column(String(50), nullable=True)  # whisper, google, etc.
    tts_provider = Column(String(50), nullable=True)  # openai, google, etc.
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    
    def __repr__(self) -> str:
        return f"<VoiceSession {self.id} - {self.status}>"
    
    def model_dump(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "status": self.status,
            "language": self.language,
            "voice_preset": self.voice_preset,
            "conversation_turn": self.conversation_turn,
            "conversation_history": self.conversation_history,
            "final_assessment": self.final_assessment,
            "total_audio_duration_seconds": self.total_audio_duration_seconds,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
