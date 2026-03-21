"""Vitals request/response schemas — Pydantic validation for vitals endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateVitalsRequest(BaseModel):
    """Schema for creating a new vitals reading."""

    heart_rate: int | None = Field(default=None, ge=20, le=300)
    blood_pressure_systolic: int | None = Field(default=None, ge=50, le=300)
    blood_pressure_diastolic: int | None = Field(default=None, ge=20, le=200)
    temperature: float | None = Field(default=None, ge=90.0, le=115.0)
    oxygen_saturation: float | None = Field(default=None, ge=0, le=100)
    respiratory_rate: int | None = Field(default=None, ge=4, le=60)
    blood_glucose: float | None = Field(default=None, ge=20, le=600)
    weight_kg: float | None = Field(default=None, ge=0.5, le=500)
    pain_level: int | None = Field(default=None, ge=0, le=10)
    device_id: str | None = None
    is_manual_entry: bool = True
    notes: str | None = Field(default=None, max_length=1000)
    recorded_at: datetime | None = None


class VitalsResponse(BaseModel):
    """Schema for vitals reading in responses."""

    id: str
    patient_id: str
    heart_rate: int | None = None
    blood_pressure_systolic: int | None = None
    blood_pressure_diastolic: int | None = None
    temperature: float | None = None
    oxygen_saturation: float | None = None
    respiratory_rate: int | None = None
    blood_glucose: float | None = None
    weight_kg: float | None = None
    pain_level: int | None = None
    device_id: str | None = None
    is_manual_entry: bool
    is_anomalous: bool
    notes: str | None = None
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class VitalsHistoryParams(BaseModel):
    """Schema for vitals history query parameters."""

    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
