"""Unit tests for AuditService — HIPAA compliance logging."""

import uuid

import pytest

from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.audit_service import AuditService


@pytest.fixture
def audit_service():
    """AuditService instance."""
    return AuditService()


@pytest.fixture
def admin_user(db):
    """Create an admin user for audit log tests."""
    user = User(
        email="admin-audit@test.com",
        first_name="Admin",
        last_name="Auditor",
        role="admin",
    )
    user.set_password("securepass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def doctor_user(db):
    """Create a doctor user for audit log tests."""
    user = User(
        email="doctor-audit@test.com",
        first_name="Dr. Audit",
        last_name="Doctor",
        role="doctor",
    )
    user.set_password("securepass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def patient_user(db):
    """Create a patient user for audit log tests."""
    user = User(
        email="patient-audit@test.com",
        first_name="Patient",
        last_name="Audited",
        role="patient",
    )
    user.set_password("securepass123")
    db.session.add(user)
    db.session.commit()
    return user


class TestCreateLog:
    """Tests for AuditService.create_log."""

    def test_create_log_persists_to_database(self, db, audit_service, doctor_user, patient_user):
        """Creating an audit log entry persists it to the database."""
        log = audit_service.create_log(
            user_id=str(doctor_user.id),
            action="view",
            resource_type="patient_record",
            patient_id=str(patient_user.id),
            ip_address="192.168.1.1",
            request_method="GET",
            request_path="/api/v1/patients/123/records",
            status_code=200,
        )

        assert log.id is not None
        persisted = db.session.get(AuditLog, log.id)
        assert persisted is not None
        assert persisted.user_id == doctor_user.id
        assert persisted.action == "view"
        assert persisted.resource_type == "patient_record"
        assert persisted.patient_id == patient_user.id
        assert persisted.ip_address == "192.168.1.1"
        assert persisted.status_code == 200

    def test_create_log_sets_created_at_automatically(self, db, audit_service, doctor_user):
        """Audit log entries get a created_at timestamp automatically."""
        log = audit_service.create_log(
            user_id=str(doctor_user.id),
            action="view",
            resource_type="vitals",
        )

        assert log.created_at is not None

    def test_create_log_with_details_json(self, db, audit_service, doctor_user):
        """Audit log entries can store additional details as JSON."""
        details = {"role": "doctor", "reason": "routine checkup"}
        log = audit_service.create_log(
            user_id=str(doctor_user.id),
            action="view",
            resource_type="patient_record",
            details=details,
        )

        persisted = db.session.get(AuditLog, log.id)
        assert persisted.details == details

    def test_create_log_with_resource_id(self, db, audit_service, doctor_user):
        """Audit log entries can reference a specific resource by ID."""
        resource_id = str(uuid.uuid4())
        log = audit_service.create_log(
            user_id=str(doctor_user.id),
            action="view",
            resource_type="medical_report",
            resource_id=resource_id,
        )

        persisted = db.session.get(AuditLog, log.id)
        assert str(persisted.resource_id) == resource_id

    def test_create_log_with_nullable_fields(self, db, audit_service, doctor_user):
        """Audit log entries work with minimal required fields."""
        log = audit_service.create_log(
            user_id=str(doctor_user.id),
            action="login",
            resource_type="auth",
        )

        assert log.patient_id is None
        assert log.resource_id is None
        assert log.ip_address is None
        assert log.user_agent is None
        assert log.details is None


class TestAuditLogImmutability:
    """Tests ensuring audit logs cannot be modified or deleted."""

    def test_audit_log_has_no_updated_at_column(self):
        """AuditLog model intentionally has no updated_at column."""
        columns = [col.name for col in AuditLog.__table__.columns]
        assert "updated_at" not in columns

    def test_audit_log_has_no_deleted_at_column(self):
        """AuditLog model intentionally has no deleted_at column."""
        columns = [col.name for col in AuditLog.__table__.columns]
        assert "deleted_at" not in columns


class TestQueryLogs:
    """Tests for AuditService.query_logs."""

    def test_query_logs_returns_all_logs(self, db, audit_service, doctor_user):
        """Querying without filters returns all logs."""
        for i in range(3):
            audit_service.create_log(
                user_id=str(doctor_user.id),
                action=f"action_{i}",
                resource_type="patient_record",
            )

        results = audit_service.query_logs()
        assert len(results) == 3

    def test_query_logs_filters_by_user_id(self, db, audit_service, doctor_user, admin_user):
        """Filtering by user_id returns only that user's logs."""
        audit_service.create_log(
            user_id=str(doctor_user.id), action="view", resource_type="vitals"
        )
        audit_service.create_log(
            user_id=str(admin_user.id), action="export", resource_type="audit_logs"
        )

        results = audit_service.query_logs(user_id=str(doctor_user.id))
        assert len(results) == 1
        assert results[0].user_id == str(doctor_user.id)

    def test_query_logs_filters_by_patient_id(self, db, audit_service, doctor_user, patient_user):
        """Filtering by patient_id returns only logs for that patient."""
        other_patient_id = str(uuid.uuid4())

        audit_service.create_log(
            user_id=str(doctor_user.id),
            action="view",
            resource_type="patient_record",
            patient_id=str(patient_user.id),
        )
        audit_service.create_log(
            user_id=str(doctor_user.id),
            action="view",
            resource_type="patient_record",
            patient_id=other_patient_id,
        )

        results = audit_service.query_logs(patient_id=str(patient_user.id))
        assert len(results) == 1
        assert results[0].patient_id == str(patient_user.id)

    def test_query_logs_filters_by_action(self, db, audit_service, doctor_user):
        """Filtering by action returns only matching logs."""
        audit_service.create_log(
            user_id=str(doctor_user.id), action="view", resource_type="vitals"
        )
        audit_service.create_log(
            user_id=str(doctor_user.id), action="create", resource_type="vitals"
        )

        results = audit_service.query_logs(action="view")
        assert len(results) == 1
        assert results[0].action == "view"

    def test_query_logs_filters_by_resource_type(self, db, audit_service, doctor_user):
        """Filtering by resource_type returns only matching logs."""
        audit_service.create_log(
            user_id=str(doctor_user.id), action="view", resource_type="vitals"
        )
        audit_service.create_log(
            user_id=str(doctor_user.id), action="view", resource_type="patient_record"
        )

        results = audit_service.query_logs(resource_type="vitals")
        assert len(results) == 1
        assert results[0].resource_type == "vitals"

    def test_query_logs_ordered_by_created_at_desc(self, db, audit_service, doctor_user):
        """Logs are returned in reverse chronological order."""
        for i in range(3):
            audit_service.create_log(
                user_id=str(doctor_user.id),
                action=f"action_{i}",
                resource_type="patient_record",
            )

        results = audit_service.query_logs()
        assert len(results) == 3
        for i in range(len(results) - 1):
            assert results[i].created_at >= results[i + 1].created_at

    def test_query_logs_respects_limit(self, db, audit_service, doctor_user):
        """Only returns up to the specified limit."""
        for i in range(5):
            audit_service.create_log(
                user_id=str(doctor_user.id),
                action="view",
                resource_type="patient_record",
            )

        results = audit_service.query_logs(limit=2)
        assert len(results) == 2

    def test_query_logs_respects_offset(self, db, audit_service, doctor_user):
        """Skips the specified number of logs."""
        for i in range(5):
            audit_service.create_log(
                user_id=str(doctor_user.id),
                action="view",
                resource_type="patient_record",
            )

        results = audit_service.query_logs(offset=3, limit=10)
        assert len(results) == 2


class TestExportCsv:
    """Tests for AuditService.export_csv."""

    def test_export_csv_includes_header_row(self, db, audit_service, doctor_user):
        """CSV export includes a header row."""
        audit_service.create_log(
            user_id=str(doctor_user.id),
            action="view",
            resource_type="patient_record",
        )

        csv_output = audit_service.export_csv()
        lines = csv_output.strip().split("\n")
        assert len(lines) == 2
        assert "id" in lines[0]
        assert "user_id" in lines[0]
        assert "action" in lines[0]

    def test_export_csv_returns_empty_with_header_when_no_logs(self, db, audit_service):
        """CSV export with no logs returns only the header."""
        csv_output = audit_service.export_csv()
        lines = csv_output.strip().split("\n")
        assert len(lines) == 1
