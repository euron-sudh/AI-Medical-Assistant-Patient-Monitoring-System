"""Appointment request/response schemas — Pydantic validation for appointment endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateAppointmentRequest(BaseModel):
    """Schema for creating a new appointment."""

    patient_id: str
    doctor_id: str
    appointment_type: str = Field(
        default="in_person",
        pattern="^(in_person|telemedicine|follow_up|emergency)$",
    )
    scheduled_at: datetime
    duration_minutes: int = Field(default=30, ge=5, le=480)
    reason: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)


class UpdateAppointmentRequest(BaseModel):
    """Schema for updating an existing appointment."""

    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=480)
    reason: str | None = Field(default=None, max_length=1000)
    notes: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(
        default=None,
        pattern="^(scheduled|confirmed|in_progress|completed|cancelled|no_show)$",
    )


class CancelAppointmentRequest(BaseModel):
    """Schema for cancelling an appointment."""

    reason: str = Field(min_length=1, max_length=1000)


class AppointmentResponse(BaseModel):
    """Schema for appointment data in API responses."""

    id: str
    patient_id: str
    doctor_id: str
    appointment_type: str
    status: str
    scheduled_at: datetime
    duration_minutes: int
    reason: str | None = None
    notes: str | None = None
    cancelled_by: str | None = None
    cancelled_reason: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppointmentListParams(BaseModel):
    """Schema for appointment list query parameters."""

    status: str | None = None
    appointment_type: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
