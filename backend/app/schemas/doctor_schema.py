"""Doctor request/response schemas — Pydantic validation for doctor endpoints."""

from pydantic import BaseModel, Field


class CreateDoctorProfileRequest(BaseModel):
    """Schema for creating a doctor profile."""

    specialization: str = Field(min_length=1, max_length=100)
    license_number: str = Field(min_length=1, max_length=50)
    license_state: str | None = Field(default=None, max_length=5)
    years_of_experience: int | None = Field(default=None, ge=0, le=70)
    department: str | None = Field(default=None, max_length=100)
    consultation_fee: float | None = Field(default=None, ge=0)
    bio: str | None = None
    availability: dict | None = None


class UpdateDoctorProfileRequest(BaseModel):
    """Schema for updating a doctor profile."""

    specialization: str | None = Field(default=None, max_length=100)
    license_state: str | None = Field(default=None, max_length=5)
    years_of_experience: int | None = Field(default=None, ge=0, le=70)
    department: str | None = Field(default=None, max_length=100)
    consultation_fee: float | None = Field(default=None, ge=0)
    bio: str | None = None
    availability: dict | None = None


class DoctorProfileResponse(BaseModel):
    """Schema for doctor profile in responses."""

    id: str
    user_id: str
    specialization: str
    license_number: str
    license_state: str | None = None
    years_of_experience: int | None = None
    department: str | None = None
    consultation_fee: float | None = None
    bio: str | None = None
    availability: dict | None = None

    class Config:
        from_attributes = True
