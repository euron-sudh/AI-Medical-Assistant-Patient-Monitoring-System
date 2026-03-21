"""MedicalReport and LabValue models — medical report storage and lab results."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import PortableJSON, PortableUUID


class MedicalReport(db.Model):
    """Medical report uploaded by a patient or care provider.

    Stores report metadata, file reference, AI-generated analysis and summary.
    Supports report types: lab, imaging, pathology, radiology, discharge,
    consultation, progress, and other.
    """

    __tablename__ = "medical_reports"
    __table_args__ = (
        CheckConstraint(
            "report_type IN ('lab', 'imaging', 'pathology', 'radiology', "
            "'discharge', 'consultation', 'progress', 'other')",
            name="ck_medical_reports_report_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'reviewed')",
            name="ck_medical_reports_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_analysis: Mapped[dict | None] = mapped_column(PortableJSON(), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="medical_reports")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    creator = relationship("User", foreign_keys=[created_by])
    lab_values = relationship("LabValue", back_populates="report", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<MedicalReport {self.id} type={self.report_type} status={self.status}>"


class LabValue(db.Model):
    """Individual lab test value extracted from a medical report.

    Stores test name, numeric value, units, reference ranges,
    and abnormality flags for clinical review.
    """

    __tablename__ = "lab_values"

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("medical_reports.id"), nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    test_name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    reference_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    loinc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    collected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    report = relationship("MedicalReport", back_populates="lab_values")
    patient = relationship("User", foreign_keys=[patient_id])

    def __repr__(self) -> str:
        return f"<LabValue {self.id} test={self.test_name} value={self.value}>"
