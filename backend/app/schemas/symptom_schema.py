"""Symptom session request/response schemas — Pydantic validation for symptom endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StartSessionRequest(BaseModel):
    """Schema for starting a new symptom check session."""

    chief_complaint: str = Field(..., min_length=1, max_length=2000)
    symptoms: dict | list | None = None


class SendMessageRequest(BaseModel):
    """Schema for sending a message in a symptom session."""

    message: str = Field(..., min_length=1, max_length=5000)


class SymptomSessionResponse(BaseModel):
    """Schema for a symptom session in responses."""

    id: str
    patient_id: str
    status: str
    chief_complaint: str | None = None
    symptoms: Any = None
    ai_analysis: dict | None = None
    triage_level: str | None = None
    recommended_action: str | None = None
    escalated_to: str | None = None
    conversation_log: list | dict | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionHistoryParams(BaseModel):
    """Schema for session history query parameters."""

    status: str | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
