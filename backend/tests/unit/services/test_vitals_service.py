"""Unit tests for VitalsService."""

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import select

from app.models.user import User
from app.models.alert import MonitoringAlert
from app.models.vitals import VitalsReading
from app.schemas.vitals_schema import CreateVitalsRequest
from app.services.vitals_service import VitalsService


@pytest.fixture
def vitals_service():
    """VitalsService instance."""
    return VitalsService()


@pytest.fixture
def patient(db):
    """Create a patient user for vitals tests."""
    user = User(
        email="vitals-patient@test.com",
        first_name="Vitals",
        last_name="Patient",
        role="patient",
    )
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    return user


class TestCreateReading:
    """Tests for VitalsService.create_reading."""

    def test_create_reading_with_valid_data(self, db, vitals_service, patient):
        """Creating a vitals reading with valid data returns a VitalsResponse."""
        data = CreateVitalsRequest(
            heart_rate=75,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            temperature=98.6,
            oxygen_saturation=98.0,
            respiratory_rate=16,
        )

        result = vitals_service.create_reading(patient.id, data, created_by=patient.id)

        assert result.heart_rate == 75
        assert result.blood_pressure_systolic == 120
        assert result.blood_pressure_diastolic == 80
        assert result.temperature == 98.6
        assert result.oxygen_saturation == 98.0
        assert result.respiratory_rate == 16
        assert result.patient_id == str(patient.id)
        assert result.is_manual_entry is True
        assert result.is_anomalous is False

    def test_create_reading_triggers_monitoring_alert_on_critical_breach(
        self, db, vitals_service, patient
    ):
        """Creating vitals outside critical range should mark anomalous + create alert."""
        data = CreateVitalsRequest(heart_rate=200)

        result = vitals_service.create_reading(patient.id, data, created_by=patient.id)

        reading = db.session.get(VitalsReading, uuid.UUID(result.id))
        assert reading is not None
        assert reading.is_anomalous is True

        alerts = db.session.execute(
            select(MonitoringAlert).where(
                MonitoringAlert.patient_id == patient.id,
                MonitoringAlert.vitals_reading_id == reading.id,
            )
        ).scalars().all()
        assert len(alerts) == 1
        assert alerts[0].status == "active"

    def test_create_reading_persists_to_database(self, db, vitals_service, patient):
        """Creating a reading persists it in the database."""
        data = CreateVitalsRequest(heart_rate=72)

        result = vitals_service.create_reading(patient.id, data, created_by=patient.id)

        reading = db.session.get(VitalsReading, uuid.UUID(result.id))
        assert reading is not None
        assert reading.heart_rate == 72
        assert reading.patient_id == patient.id

    def test_create_reading_with_partial_vitals(self, db, vitals_service, patient):
        """Creating a reading with only some vitals fields succeeds."""
        data = CreateVitalsRequest(heart_rate=80, pain_level=3)

        result = vitals_service.create_reading(patient.id, data, created_by=patient.id)

        assert result.heart_rate == 80
        assert result.pain_level == 3
        assert result.blood_pressure_systolic is None
        assert result.temperature is None

    def test_create_reading_with_custom_recorded_at(self, db, vitals_service, patient):
        """Providing a recorded_at timestamp uses that value."""
        custom_time = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        data = CreateVitalsRequest(heart_rate=68, recorded_at=custom_time)

        result = vitals_service.create_reading(patient.id, data, created_by=patient.id)

        assert result.recorded_at == custom_time


class TestGetPatientVitals:
    """Tests for VitalsService.get_patient_vitals."""

    def test_returns_readings_ordered_by_time_desc(self, db, vitals_service, patient):
        """Readings are returned in reverse chronological order."""
        now = datetime.now(timezone.utc)
        for i in range(3):
            data = CreateVitalsRequest(
                heart_rate=70 + i,
                recorded_at=now - timedelta(hours=i),
            )
            vitals_service.create_reading(patient.id, data, created_by=patient.id)

        results = vitals_service.get_patient_vitals(patient.id)

        assert len(results) == 3
        assert results[0].heart_rate == 70  # Most recent
        assert results[2].heart_rate == 72  # Oldest

    def test_returns_empty_list_for_no_readings(self, db, vitals_service, patient):
        """Returns empty list when no readings exist."""
        results = vitals_service.get_patient_vitals(patient.id)
        assert results == []

    def test_respects_limit_parameter(self, db, vitals_service, patient):
        """Only returns up to the specified limit."""
        for i in range(5):
            data = CreateVitalsRequest(heart_rate=70 + i)
            vitals_service.create_reading(patient.id, data, created_by=patient.id)

        results = vitals_service.get_patient_vitals(patient.id, limit=2)
        assert len(results) == 2


class TestGetVitalsHistory:
    """Tests for VitalsService.get_vitals_history."""

    def test_filters_by_date_range(self, db, vitals_service, patient):
        """Only returns readings within the specified date range."""
        now = datetime.now(timezone.utc)

        # Create readings at different times
        for hours_ago in [1, 6, 12, 24, 48]:
            data = CreateVitalsRequest(
                heart_rate=70 + hours_ago,
                recorded_at=now - timedelta(hours=hours_ago),
            )
            vitals_service.create_reading(patient.id, data, created_by=patient.id)

        # Query last 12 hours
        results = vitals_service.get_vitals_history(
            patient.id,
            start_date=now - timedelta(hours=12),
            end_date=now,
        )

        assert len(results) == 3  # 1h, 6h, 12h ago

    def test_history_without_date_range_returns_all(self, db, vitals_service, patient):
        """Without date filters, returns all readings."""
        for i in range(3):
            data = CreateVitalsRequest(heart_rate=70 + i)
            vitals_service.create_reading(patient.id, data, created_by=patient.id)

        results = vitals_service.get_vitals_history(patient.id)
        assert len(results) == 3

    def test_history_respects_offset(self, db, vitals_service, patient):
        """Offset skips the specified number of readings."""
        for i in range(5):
            data = CreateVitalsRequest(heart_rate=70 + i)
            vitals_service.create_reading(patient.id, data, created_by=patient.id)

        results = vitals_service.get_vitals_history(patient.id, offset=2, limit=10)
        assert len(results) == 3


class TestCreateVitalsRequestValidation:
    """Tests for Pydantic schema validation."""

    def test_rejects_heart_rate_too_high(self):
        """Heart rate above 300 is rejected."""
        with pytest.raises(Exception):
            CreateVitalsRequest(heart_rate=999)

    def test_rejects_heart_rate_too_low(self):
        """Heart rate below 20 is rejected."""
        with pytest.raises(Exception):
            CreateVitalsRequest(heart_rate=5)

    def test_rejects_pain_level_above_10(self):
        """Pain level above 10 is rejected."""
        with pytest.raises(Exception):
            CreateVitalsRequest(pain_level=15)

    def test_accepts_valid_full_vitals(self):
        """All vitals within valid ranges are accepted."""
        data = CreateVitalsRequest(
            heart_rate=75,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            temperature=98.6,
            oxygen_saturation=98.0,
            respiratory_rate=16,
            blood_glucose=100.0,
            weight_kg=70.5,
            pain_level=2,
        )
        assert data.heart_rate == 75

    def test_rejects_oxygen_saturation_above_100(self):
        """SpO2 above 100% is rejected."""
        with pytest.raises(Exception):
            CreateVitalsRequest(oxygen_saturation=105)
