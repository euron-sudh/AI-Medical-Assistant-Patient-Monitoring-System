"""Telemedicine request/response schemas — Pydantic validation for telemedicine endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateTelemedicineSessionRequest(BaseModel):
    """Schema for creating a new telemedicine session."""

    appointment_id: str


class TelemedicineSessionResponse(BaseModel):
    """Schema for telemedicine session data in API responses."""

    id: str
    appointment_id: str
    patient_id: str
    doctor_id: str
    room_url: str
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    recording_url: str | None = None
    ai_transcript: str | None = None
    ai_summary: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JoinSessionResponse(BaseModel):
    """Schema for the response when joining a telemedicine session."""

    session_id: str
    room_url: str
    room_token: str | None = None
    status: str
