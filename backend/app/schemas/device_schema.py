"""Device request/response schemas — Pydantic validation for device endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DeviceResponse(BaseModel):
    id: str
    patient_id: str
    device_type: str
    device_name: str
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    firmware_version: str | None = None
    status: str
    last_sync_at: datetime | None = None
    battery_level: int | None = None
    configuration: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class RegisterDeviceRequest(BaseModel):
    device_type: str = Field(..., min_length=1, max_length=50)
    device_name: str = Field(..., min_length=1, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)


class UpdateDeviceRequest(BaseModel):
    firmware_version: str | None = Field(default=None, max_length=50)
    # Soft state transition to "retired" is handled by DELETE endpoint,
    # but we also accept it here for convenience.
    status: str | None = Field(default=None)


class DeviceVitalsIngestItem(BaseModel):
    vital_type: str = Field(..., min_length=1, max_length=50)
    value: float = Field(..., ge=-1e6, le=1e6)
    timestamp: datetime


class DeviceVitalsBatchRequest(BaseModel):
    items: list[DeviceVitalsIngestItem]


