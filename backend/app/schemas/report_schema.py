"""Report request/response schemas — Pydantic validation for report endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateReportRequest(BaseModel):
    """Schema for uploading a new medical report."""

    report_type: str = Field(
        ...,
        pattern=r"^(lab|imaging|pathology|radiology|discharge|consultation|progress|other)$",
    )
    title: str = Field(..., min_length=1, max_length=255)
    content: str | None = None
    file_url: str | None = Field(default=None, max_length=500)
    file_type: str | None = Field(default=None, max_length=20)


class ReportResponse(BaseModel):
    """Schema for a medical report in responses."""

    id: str
    patient_id: str
    report_type: str
    title: str
    content: str | None = None
    file_url: str | None = None
    file_type: str | None = None
    ai_summary: str | None = None
    ai_analysis: dict | None = None
    status: str
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateLabValueRequest(BaseModel):
    """Schema for adding a lab value to a report."""

    test_name: str = Field(..., min_length=1, max_length=255)
    value: float | None = None
    unit: str | None = Field(default=None, max_length=50)
    reference_min: float | None = None
    reference_max: float | None = None
    is_abnormal: bool = False
    loinc_code: str | None = Field(default=None, max_length=20)
    collected_at: datetime | None = None


class LabValueResponse(BaseModel):
    """Schema for a lab value in responses."""

    id: str
    report_id: str
    patient_id: str
    test_name: str
    value: float | None = None
    unit: str | None = None
    reference_min: float | None = None
    reference_max: float | None = None
    is_abnormal: bool
    loinc_code: str | None = None
    collected_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListParams(BaseModel):
    """Schema for report list query parameters."""

    report_type: str | None = None
    status: str | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
