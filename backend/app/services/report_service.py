"""Report service — business logic for medical reports and lab values."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.extensions import db
from app.models.report import LabValue, MedicalReport
from app.schemas.report_schema import (
    CreateLabValueRequest,
    CreateReportRequest,
    LabValueResponse,
    ReportResponse,
)


class ReportService:
    """Handles creating, querying, and managing medical reports and lab values."""

    def create_report(
        self,
        patient_id: uuid.UUID,
        data: CreateReportRequest,
        created_by: uuid.UUID,
    ) -> ReportResponse:
        """Create a new medical report for a patient.

        Args:
            patient_id: UUID of the patient.
            data: Validated report data.
            created_by: UUID of the user creating the report.

        Returns:
            ReportResponse with the created report.
        """
        report = MedicalReport(
            patient_id=patient_id,
            report_type=data.report_type,
            title=data.title,
            content=data.content,
            file_url=data.file_url,
            file_type=data.file_type,
            status="pending",
            created_by=created_by,
        )
        db.session.add(report)
        db.session.commit()
        return self._to_response(report)

    def get_report(self, report_id: uuid.UUID) -> ReportResponse | None:
        """Get a single report by ID.

        Args:
            report_id: UUID of the report.

        Returns:
            ReportResponse if found, None otherwise.
        """
        stmt = select(MedicalReport).where(MedicalReport.id == report_id)
        report = db.session.execute(stmt).scalar_one_or_none()
        if report is None:
            return None
        return self._to_response(report)

    def get_patient_reports(
        self,
        patient_id: uuid.UUID,
        report_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ReportResponse]:
        """Get reports for a patient with optional filtering.

        Args:
            patient_id: UUID of the patient.
            report_type: Optional filter by report type.
            status: Optional filter by status.
            limit: Maximum number of reports to return.
            offset: Number of reports to skip.

        Returns:
            List of ReportResponse matching the criteria.
        """
        stmt = select(MedicalReport).where(MedicalReport.patient_id == patient_id)

        if report_type:
            stmt = stmt.where(MedicalReport.report_type == report_type)
        if status:
            stmt = stmt.where(MedicalReport.status == status)

        stmt = stmt.order_by(MedicalReport.created_at.desc()).offset(offset).limit(limit)
        reports = db.session.execute(stmt).scalars().all()
        return [self._to_response(r) for r in reports]

    def delete_report(self, report_id: uuid.UUID) -> bool:
        """Delete a report by ID.

        Args:
            report_id: UUID of the report to delete.

        Returns:
            True if deleted, False if not found.
        """
        stmt = select(MedicalReport).where(MedicalReport.id == report_id)
        report = db.session.execute(stmt).scalar_one_or_none()
        if report is None:
            return False
        db.session.delete(report)
        db.session.commit()
        return True

    def trigger_analysis(self, report_id: uuid.UUID) -> ReportResponse | None:
        """Trigger AI analysis for a report by updating its status to processing.

        Args:
            report_id: UUID of the report.

        Returns:
            Updated ReportResponse, or None if not found.
        """
        stmt = select(MedicalReport).where(MedicalReport.id == report_id)
        report = db.session.execute(stmt).scalar_one_or_none()
        if report is None:
            return None
        report.status = "processing"
        report.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return self._to_response(report)

    def add_lab_value(
        self,
        report_id: uuid.UUID,
        patient_id: uuid.UUID,
        data: CreateLabValueRequest,
    ) -> LabValueResponse:
        """Add a lab value to a report.

        Args:
            report_id: UUID of the report.
            patient_id: UUID of the patient.
            data: Validated lab value data.

        Returns:
            LabValueResponse with the created lab value.
        """
        lab_value = LabValue(
            report_id=report_id,
            patient_id=patient_id,
            test_name=data.test_name,
            value=Decimal(str(data.value)) if data.value is not None else None,
            unit=data.unit,
            reference_min=Decimal(str(data.reference_min)) if data.reference_min is not None else None,
            reference_max=Decimal(str(data.reference_max)) if data.reference_max is not None else None,
            is_abnormal=data.is_abnormal,
            loinc_code=data.loinc_code,
            collected_at=data.collected_at,
        )
        db.session.add(lab_value)
        db.session.commit()
        return self._lab_to_response(lab_value)

    def get_report_lab_values(self, report_id: uuid.UUID) -> list[LabValueResponse]:
        """Get all lab values for a report.

        Args:
            report_id: UUID of the report.

        Returns:
            List of LabValueResponse for the report.
        """
        stmt = (
            select(LabValue)
            .where(LabValue.report_id == report_id)
            .order_by(LabValue.created_at.asc())
        )
        lab_values = db.session.execute(stmt).scalars().all()
        return [self._lab_to_response(lv) for lv in lab_values]

    def _to_response(self, report: MedicalReport) -> ReportResponse:
        """Convert a MedicalReport model to a ReportResponse schema."""
        return ReportResponse(
            id=str(report.id),
            patient_id=str(report.patient_id),
            report_type=report.report_type,
            title=report.title,
            content=report.content,
            file_url=report.file_url,
            file_type=report.file_type,
            ai_summary=report.ai_summary,
            ai_analysis=report.ai_analysis,
            status=report.status,
            reviewed_by=str(report.reviewed_by) if report.reviewed_by else None,
            reviewed_at=report.reviewed_at,
            created_by=str(report.created_by),
            created_at=report.created_at,
            updated_at=report.updated_at,
        )

    def _lab_to_response(self, lab_value: LabValue) -> LabValueResponse:
        """Convert a LabValue model to a LabValueResponse schema."""
        return LabValueResponse(
            id=str(lab_value.id),
            report_id=str(lab_value.report_id),
            patient_id=str(lab_value.patient_id),
            test_name=lab_value.test_name,
            value=float(lab_value.value) if lab_value.value is not None else None,
            unit=lab_value.unit,
            reference_min=float(lab_value.reference_min) if lab_value.reference_min is not None else None,
            reference_max=float(lab_value.reference_max) if lab_value.reference_max is not None else None,
            is_abnormal=lab_value.is_abnormal,
            loinc_code=lab_value.loinc_code,
            collected_at=lab_value.collected_at,
            created_at=lab_value.created_at,
        )


# Module-level instance for use by routes
report_service = ReportService()
