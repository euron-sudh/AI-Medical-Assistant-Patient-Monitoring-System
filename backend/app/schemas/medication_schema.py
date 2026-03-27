"""Medication request/response schemas — Pydantic validation.

Task #31 — Vikash Kumar (added PatientInteractionCheckRequest, ScheduleEntry,
DailyMedicationScheduleResponse, AdherenceRecordRequest, AdherenceRecordResponse)
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class CreateMedicationRequest(BaseModel):
    patient_id: str
    name: str = Field(min_length=1, max_length=255)
    dosage: str = Field(min_length=1, max_length=100)
    frequency: str = Field(min_length=1, max_length=100)
    route: str | None = Field(default=None, max_length=50)
    start_date: date
    end_date: date | None = None
    reason: str | None = None
    side_effects: str | None = None
    refills_remaining: int = Field(default=0, ge=0)
    pharmacy_notes: str | None = None


class UpdateMedicationRequest(BaseModel):
    dosage: str | None = Field(default=None, max_length=100)
    frequency: str | None = Field(default=None, max_length=100)
    route: str | None = Field(default=None, max_length=50)
    end_date: date | None = None
    status: str | None = Field(default=None, pattern=r"^(active|completed|discontinued|on_hold)$")
    reason: str | None = None
    side_effects: str | None = None
    refills_remaining: int | None = Field(default=None, ge=0)
    pharmacy_notes: str | None = None


class MedicationResponse(BaseModel):
    id: str
    patient_id: str
    name: str
    dosage: str
    frequency: str
    route: str | None = None
    prescribed_by: str | None = None
    start_date: date
    end_date: date | None = None
    status: str
    reason: str | None = None
    side_effects: str | None = None
    refills_remaining: int = 0
    pharmacy_notes: str | None = None

    class Config:
        from_attributes = True


class InteractionCheckRequest(BaseModel):
    medication_names: list[str] = Field(min_length=2)
    patient_id: str | None = None


class InteractionCheckResponse(BaseModel):
    checked_medications: list[str]
    interactions_found: int
    interactions: list[dict]


class AdherenceLogRequest(BaseModel):
    taken: bool
    taken_at: str | None = None
    notes: str | None = None


class MedicationScheduleResponse(BaseModel):
    patient_id: str
    medications: list[MedicationResponse]


# -----------------------------------------------------------------------
# Task #31 — new schemas
# -----------------------------------------------------------------------

class PatientInteractionCheckRequest(BaseModel):
    """Request body for patient-scoped interaction check."""
    medication_names: list[str] = Field(min_length=2)


class ScheduleEntry(BaseModel):
    """A single scheduled dose in a daily medication schedule."""
    medication_id: str
    medication_name: str
    dosage: str
    frequency: str
    route: str | None = None
    time_slot: str  # e.g. "morning", "afternoon", "evening", "night"
    notes: str | None = None


class DailyMedicationScheduleResponse(BaseModel):
    """Full daily medication schedule for a patient."""
    patient_id: str
    date: str
    schedule: list[ScheduleEntry]
    total_doses: int


class AdherenceRecordRequest(BaseModel):
    """Request body for recording that a medication was taken."""
    medication_id: str
    taken_at: datetime | None = None
    notes: str | None = None


class AdherenceRecordResponse(BaseModel):
    """Response after recording medication adherence."""
    patient_id: str
    medication_id: str
    medication_name: str
    taken_at: str
    recorded: bool = True
    notes: str | None = None
