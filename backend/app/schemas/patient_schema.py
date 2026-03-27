"""Patient request/response schemas -- Pydantic validation for patient endpoints."""

from datetime import date

from pydantic import BaseModel, Field


class CreatePatientProfileRequest(BaseModel):
    """Schema for creating a patient profile."""

    date_of_birth: date
    gender: str | None = Field(default=None, max_length=20)
    blood_type: str | None = Field(default=None, max_length=5)
    height_cm: float | None = Field(default=None, ge=0, le=300)
    weight_kg: float | None = Field(default=None, ge=0, le=500)
    emergency_contact: dict | None = None
    insurance_info: dict | None = None


class UpdatePatientProfileRequest(BaseModel):
    """Schema for updating a patient profile."""

    gender: str | None = Field(default=None, max_length=20)
    blood_type: str | None = Field(default=None, max_length=5)
    height_cm: float | None = Field(default=None, ge=0, le=300)
    weight_kg: float | None = Field(default=None, ge=0, le=500)
    emergency_contact: dict | None = None
    insurance_info: dict | None = None


class PatientProfileResponse(BaseModel):
    """Schema for patient profile in responses."""

    id: str
    user_id: str
    date_of_birth: date
    gender: str | None = None
    blood_type: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    emergency_contact: dict | None = None
    insurance_info: dict | None = None
    assigned_doctor_id: str | None = None

    class Config:
        from_attributes = True


class AddMedicalHistoryRequest(BaseModel):
    """Schema for adding a medical history entry."""

    condition_name: str = Field(min_length=1, max_length=255)
    diagnosis_date: date | None = None
    status: str = Field(default="active", pattern=r"^(active|resolved|chronic|managed)$")
    icd_10_code: str | None = Field(default=None, max_length=10)
    notes: str | None = None


class MedicalHistoryResponse(BaseModel):
    """Schema for medical history entry in responses."""

    id: str
    patient_id: str
    condition_name: str
    diagnosis_date: date | None = None
    status: str
    icd_10_code: str | None = None
    notes: str | None = None

    class Config:
        from_attributes = True


class AddAllergyRequest(BaseModel):
    """Schema for adding an allergy."""

    allergen: str = Field(min_length=1, max_length=255)
    reaction: str | None = None
    severity: str = Field(pattern=r"^(mild|moderate|severe|life_threatening)$")
    diagnosed_date: date | None = None


class AllergyResponse(BaseModel):
    """Schema for allergy in responses."""

    id: str
    patient_id: str
    allergen: str
    reaction: str | None = None
    severity: str
    diagnosed_date: date | None = None

    class Config:
        from_attributes = True


class UpdateMedicalHistoryStatusRequest(BaseModel):
    """Schema for updating a medical history entry status."""

    status: str = Field(pattern=r"^(active|resolved|chronic|managed)$")
    notes: str | None = None


class TimelineEntryResponse(BaseModel):
    """Schema for a single patient timeline entry."""

    timestamp: str
    event_type: str
    title: str
    description: str
    data: dict | None = None


class AISummaryResponse(BaseModel):
    """Schema for AI-generated patient health summary."""

    patient_id: str
    summary: str
    generated_at: str
