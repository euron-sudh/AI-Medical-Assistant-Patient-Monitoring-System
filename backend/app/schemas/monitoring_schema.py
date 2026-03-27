"""Monitoring request/response schemas — Pydantic validation for monitoring endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class AlertsListParams(PaginationParams):
    severity: str | None = None
    patient_id: str | None = None
    status: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class AcknowledgeAlertResponse(BaseModel):
    id: str
    status: str
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None


class ResolveAlertRequest(BaseModel):
    resolution_notes: str | None = Field(default=None, max_length=5000)


class EscalateAlertResponse(BaseModel):
    id: str
    escalation_level: int
    escalated_at: datetime | None = None


class MonitoringThresholdsRequest(BaseModel):
    thresholds: dict[str, Any] = Field(default_factory=dict)


class MonitoringThresholdsResponse(BaseModel):
    patient_id: str
    thresholds: dict[str, Any]
    updated_by: str
    updated_at: datetime


class VitalsSnapshot(BaseModel):
    recorded_at: datetime | None = None
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
    is_anomalous: bool | None = None


class MonitoredPatientItem(BaseModel):
    patient_id: str
    full_name: str
    assigned_doctor_id: str | None = None
    latest_vitals: VitalsSnapshot | None = None
    active_alert_count: int = 0


class MonitoringPatientStatusResponse(BaseModel):
    patient_id: str
    full_name: str
    assigned_doctor_id: str | None = None
    latest_vitals: VitalsSnapshot | None = None
    news2_score: int | None = None
    thresholds: MonitoringThresholdsResponse | None = None
    active_alerts: list[dict[str, Any]] = Field(default_factory=list)

