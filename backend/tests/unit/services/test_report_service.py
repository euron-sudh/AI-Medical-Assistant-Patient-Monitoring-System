"""Unit tests for ReportService — medical report and lab value management."""

import uuid

import pytest
from pydantic import ValidationError

from app.models.report import LabValue, MedicalReport
from app.schemas.report_schema import (
    CreateLabValueRequest,
    CreateReportRequest,
    LabValueResponse,
    ReportListParams,
    ReportResponse,
)
from app.services.report_service import ReportService


class TestCreateReportRequestValidation:
    """Schema validation tests for CreateReportRequest."""

    def test_valid_lab_report(self):
        data = CreateReportRequest(
            report_type="lab",
            title="CBC Results",
            content="Complete blood count results.",
        )
        assert data.report_type == "lab"
        assert data.title == "CBC Results"

    def test_valid_imaging_report(self):
        data = CreateReportRequest(
            report_type="imaging",
            title="Chest X-Ray",
            file_url="https://s3.example.com/reports/chest-xray.pdf",
            file_type="pdf",
        )
        assert data.report_type == "imaging"
        assert data.file_url is not None

    def test_all_valid_report_types(self):
        valid_types = [
            "lab", "imaging", "pathology", "radiology",
            "discharge", "consultation", "progress", "other",
        ]
        for rt in valid_types:
            data = CreateReportRequest(report_type=rt, title="Test")
            assert data.report_type == rt

    def test_invalid_report_type_rejected(self):
        with pytest.raises(ValidationError):
            CreateReportRequest(report_type="invalid_type", title="Test")

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            CreateReportRequest(report_type="lab", title="")

    def test_title_too_long_rejected(self):
        with pytest.raises(ValidationError):
            CreateReportRequest(report_type="lab", title="x" * 256)

    def test_optional_fields_default_to_none(self):
        data = CreateReportRequest(report_type="lab", title="Test")
        assert data.content is None
        assert data.file_url is None
        assert data.file_type is None


class TestCreateLabValueRequestValidation:
    """Schema validation tests for CreateLabValueRequest."""

    def test_valid_lab_value(self):
        data = CreateLabValueRequest(
            test_name="Hemoglobin",
            value=14.5,
            unit="g/dL",
            reference_min=12.0,
            reference_max=17.5,
            is_abnormal=False,
        )
        assert data.test_name == "Hemoglobin"
        assert data.value == 14.5

    def test_empty_test_name_rejected(self):
        with pytest.raises(ValidationError):
            CreateLabValueRequest(test_name="", value=10.0)

    def test_test_name_too_long_rejected(self):
        with pytest.raises(ValidationError):
            CreateLabValueRequest(test_name="x" * 256, value=10.0)

    def test_optional_value_defaults_to_none(self):
        data = CreateLabValueRequest(test_name="Hemoglobin")
        assert data.value is None
        assert data.unit is None
        assert data.is_abnormal is False

    def test_abnormal_flag(self):
        data = CreateLabValueRequest(
            test_name="Glucose",
            value=250.0,
            is_abnormal=True,
        )
        assert data.is_abnormal is True


class TestReportListParamsValidation:
    """Schema validation tests for ReportListParams."""

    def test_defaults(self):
        params = ReportListParams()
        assert params.limit == 50
        assert params.offset == 0
        assert params.report_type is None
        assert params.status is None

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            ReportListParams(limit=0)
        with pytest.raises(ValidationError):
            ReportListParams(limit=501)

    def test_negative_offset_rejected(self):
        with pytest.raises(ValidationError):
            ReportListParams(offset=-1)


class TestReportResponseSchema:
    """Schema validation for ReportResponse."""

    def test_valid_response(self):
        resp = ReportResponse(
            id=str(uuid.uuid4()),
            patient_id=str(uuid.uuid4()),
            report_type="lab",
            title="CBC",
            status="pending",
            created_by=str(uuid.uuid4()),
            created_at="2026-03-20T10:00:00Z",
            updated_at="2026-03-20T10:00:00Z",
        )
        assert resp.report_type == "lab"
        assert resp.ai_summary is None


class TestReportServiceCreate:
    """Test ReportService.create_report with database."""

    def test_create_report_persists(self, app, db):
        with app.app_context():
            from app.models.user import User

            user = User(email="rpt@test.com", first_name="R", last_name="T", role="patient")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            service = ReportService()
            data = CreateReportRequest(report_type="lab", title="CBC Results")
            result = service.create_report(user.id, data, created_by=user.id)

            assert result.report_type == "lab"
            assert result.title == "CBC Results"
            assert result.status == "pending"
            assert result.patient_id == str(user.id)

    def test_get_report_returns_none_for_missing(self, app, db):
        with app.app_context():
            service = ReportService()
            result = service.get_report(uuid.uuid4())
            assert result is None

    def test_delete_report_returns_false_for_missing(self, app, db):
        with app.app_context():
            service = ReportService()
            result = service.delete_report(uuid.uuid4())
            assert result is False

    def test_get_patient_reports_empty(self, app, db):
        with app.app_context():
            service = ReportService()
            result = service.get_patient_reports(uuid.uuid4())
            assert result == []

    def test_trigger_analysis_sets_processing(self, app, db):
        with app.app_context():
            from app.models.user import User

            user = User(email="rpt2@test.com", first_name="R", last_name="T", role="patient")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            service = ReportService()
            data = CreateReportRequest(report_type="lab", title="BMP")
            created = service.create_report(user.id, data, created_by=user.id)
            result = service.trigger_analysis(uuid.UUID(created.id))
            assert result is not None
            assert result.status == "processing"


class TestLabValueService:
    """Test ReportService lab value operations."""

    def test_add_and_get_lab_values(self, app, db):
        with app.app_context():
            from app.models.user import User

            user = User(email="lv@test.com", first_name="L", last_name="V", role="patient")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            service = ReportService()
            report_data = CreateReportRequest(report_type="lab", title="CBC")
            report = service.create_report(user.id, report_data, created_by=user.id)

            lv_data = CreateLabValueRequest(
                test_name="Hemoglobin",
                value=14.5,
                unit="g/dL",
                reference_min=12.0,
                reference_max=17.5,
                is_abnormal=False,
            )
            lv = service.add_lab_value(uuid.UUID(report.id), user.id, lv_data)
            assert lv.test_name == "Hemoglobin"
            assert lv.value == 14.5

            lab_values = service.get_report_lab_values(uuid.UUID(report.id))
            assert len(lab_values) == 1
            assert lab_values[0].test_name == "Hemoglobin"
