"""Unit tests for appointment and telemedicine services."""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.appointment import Appointment
from app.models.patient import PatientProfile
from app.models.user import User
from app.schemas.appointment_schema import (
    CancelAppointmentRequest,
    CreateAppointmentRequest,
    UpdateAppointmentRequest,
)
from app.services.appointment_service import AppointmentService
from app.services.telemedicine_service import TelemedicineService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def appt_service():
    return AppointmentService()


@pytest.fixture
def tele_service():
    return TelemedicineService()


@pytest.fixture
def patient(db):
    """Create a patient user."""
    user = User(
        email="appt-patient@test.com",
        first_name="Test",
        last_name="Patient",
        role="patient",
    )
    user.set_password("pass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def doctor(db):
    """Create a doctor user."""
    user = User(
        email="appt-doctor@test.com",
        first_name="Dr. Test",
        last_name="Doctor",
        role="doctor",
    )
    user.set_password("pass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def other_patient(db):
    """Create another patient for access control tests."""
    user = User(
        email="other-patient@test.com",
        first_name="Other",
        last_name="Patient",
        role="patient",
    )
    user.set_password("pass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def future_time():
    """Return a timezone-aware datetime 2 days in the future at 10:00 AM."""
    return (datetime.now(timezone.utc) + timedelta(days=2)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )


@pytest.fixture
def create_request(patient, doctor, future_time):
    """Create a valid appointment creation request."""
    return CreateAppointmentRequest(
        patient_id=str(patient.id),
        doctor_id=str(doctor.id),
        appointment_type="in_person",
        scheduled_at=future_time,
        duration_minutes=30,
        reason="Annual checkup",
    )


@pytest.fixture
def patient_with_profile(db, patient):
    """Patient user with a profile row (required for assign_primary_doctor on confirm)."""
    profile = PatientProfile(
        user_id=patient.id,
        date_of_birth=date(1990, 1, 15),
        gender="other",
        blood_type="O+",
    )
    db.session.add(profile)
    db.session.commit()
    return profile


@pytest.fixture
def sample_appointment(db, patient, doctor, future_time):
    """Create a sample appointment in the database."""
    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_type="in_person",
        status="scheduled",
        scheduled_at=future_time,
        duration_minutes=30,
        reason="Annual checkup",
        created_by=patient.id,
    )
    db.session.add(appt)
    db.session.commit()
    return appt


@pytest.fixture
def telemedicine_appointment(db, patient, doctor, future_time):
    """Create a telemedicine appointment."""
    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_type="telemedicine",
        status="confirmed",
        scheduled_at=future_time,
        duration_minutes=30,
        reason="Follow-up consultation",
        created_by=doctor.id,
    )
    db.session.add(appt)
    db.session.commit()
    return appt


# ---------------------------------------------------------------------------
# Appointment Service Tests
# ---------------------------------------------------------------------------


class TestCreateAppointment:

    def test_create_appointment_success(self, appt_service, create_request, patient):
        """Creating an appointment returns 'scheduled' status."""
        result = appt_service.create_appointment(create_request, created_by=patient.id)
        assert result.id is not None
        assert result.patient_id == str(patient.id)
        assert result.status == "scheduled"
        assert result.appointment_type == "in_person"
        assert result.reason == "Annual checkup"
        assert result.duration_minutes == 30

    def test_create_appointment_adds_placeholder_profile(
        self, appt_service, db, patient, doctor, future_time
    ):
        """Patients without a profile get a minimal row when booking so confirm can assign."""
        assert (
            db.session.execute(
                select(PatientProfile).where(PatientProfile.user_id == patient.id)
            ).scalar_one_or_none()
            is None
        )
        req = CreateAppointmentRequest(
            patient_id=str(patient.id),
            doctor_id=str(doctor.id),
            appointment_type="in_person",
            scheduled_at=future_time,
            duration_minutes=30,
            reason="Checkup",
        )
        appt_service.create_appointment(req, created_by=patient.id)
        profile = db.session.execute(
            select(PatientProfile).where(PatientProfile.user_id == patient.id)
        ).scalar_one_or_none()
        assert profile is not None

    def test_create_appointment_scheduling_conflict(
        self, appt_service, create_request, patient, sample_appointment
    ):
        """Scheduling conflict raises ValueError."""
        with pytest.raises(ValueError, match="scheduling conflict"):
            appt_service.create_appointment(create_request, created_by=patient.id)

    def test_create_telemedicine_appointment(
        self, appt_service, patient, doctor, future_time
    ):
        """Telemedicine appointment type is stored correctly."""
        req = CreateAppointmentRequest(
            patient_id=str(patient.id),
            doctor_id=str(doctor.id),
            appointment_type="telemedicine",
            scheduled_at=future_time,
            duration_minutes=30,
            reason="Video consultation",
        )
        result = appt_service.create_appointment(req, created_by=patient.id)
        assert result.appointment_type == "telemedicine"


class TestListAppointments:

    def test_patient_sees_own_appointments(
        self, appt_service, patient, sample_appointment
    ):
        """Patients see only their own appointments."""
        results = appt_service.list_appointments(user_id=patient.id, role="patient")
        assert len(results) == 1
        assert results[0].patient_id == str(patient.id)

    def test_patient_cannot_see_other_appointments(
        self, appt_service, other_patient, sample_appointment
    ):
        """Patients cannot see other patients' appointments."""
        results = appt_service.list_appointments(user_id=other_patient.id, role="patient")
        assert len(results) == 0

    def test_doctor_sees_assigned_appointments(
        self, appt_service, doctor, sample_appointment
    ):
        """Doctors see appointments where they are the assigned doctor."""
        results = appt_service.list_appointments(user_id=doctor.id, role="doctor")
        assert len(results) == 1
        assert results[0].doctor_id == str(doctor.id)

    def test_filter_by_status(self, appt_service, patient, sample_appointment):
        """Status filter works correctly."""
        results = appt_service.list_appointments(
            user_id=patient.id, role="patient", status="scheduled"
        )
        assert len(results) == 1

        results = appt_service.list_appointments(
            user_id=patient.id, role="patient", status="completed"
        )
        assert len(results) == 0


class TestGetUpcoming:

    def test_get_upcoming_returns_future_appointments(
        self, appt_service, patient, sample_appointment
    ):
        """get_upcoming returns future scheduled appointments."""
        results = appt_service.get_upcoming(patient.id)
        assert len(results) == 1
        assert results[0].status == "scheduled"


class TestUpdateAppointment:

    def test_update_appointment_notes(self, appt_service, sample_appointment):
        """Updating notes succeeds."""
        data = UpdateAppointmentRequest(notes="Bring lab results")
        result = appt_service.update_appointment(sample_appointment.id, data)
        assert result.notes == "Bring lab results"

    def test_valid_status_transition(self, appt_service, sample_appointment):
        """scheduled → confirmed is valid."""
        data = UpdateAppointmentRequest(status="confirmed")
        result = appt_service.update_appointment(sample_appointment.id, data)
        assert result.status == "confirmed"

    def test_confirm_via_update_sets_assigned_doctor(
        self, appt_service, db, patient, doctor, patient_with_profile, sample_appointment
    ):
        """scheduled → confirmed assigns the appointment doctor on the patient profile."""
        data = UpdateAppointmentRequest(status="confirmed")
        appt_service.update_appointment(sample_appointment.id, data)
        profile = db.session.execute(
            select(PatientProfile).where(PatientProfile.user_id == patient.id)
        ).scalar_one()
        assert profile.assigned_doctor_id == doctor.id

    def test_invalid_status_transition(self, appt_service, sample_appointment):
        """scheduled → completed is invalid."""
        data = UpdateAppointmentRequest(status="completed")
        with pytest.raises(ValueError, match="Cannot transition"):
            appt_service.update_appointment(sample_appointment.id, data)

    def test_update_nonexistent_appointment(self, appt_service, db):
        """Updating a non-existent appointment raises ValueError."""
        data = UpdateAppointmentRequest(notes="test")
        with pytest.raises(ValueError, match="not found"):
            appt_service.update_appointment(uuid.uuid4(), data)


class TestConfirmAppointment:
    def test_confirm_sets_assigned_doctor(
        self, appt_service, db, patient, doctor, patient_with_profile, sample_appointment
    ):
        """PUT confirm path: patient profile is linked to the appointment doctor."""
        appt_service.confirm_appointment(sample_appointment.id, doctor.id, send_notification=False)
        profile = db.session.execute(
            select(PatientProfile).where(PatientProfile.user_id == patient.id)
        ).scalar_one()
        assert profile.assigned_doctor_id == doctor.id


class TestCancelAppointment:

    def test_cancel_appointment_success(
        self, appt_service, sample_appointment, patient
    ):
        """Cancelling sets status, reason, and cancelled_by."""
        cancel_data = CancelAppointmentRequest(reason="Schedule conflict")
        result = appt_service.cancel_appointment(
            sample_appointment.id, patient.id, cancel_data
        )
        assert result.status == "cancelled"
        assert result.cancelled_reason == "Schedule conflict"
        assert result.cancelled_by == str(patient.id)

    def test_cancel_already_completed_fails(
        self, appt_service, db, patient, doctor, future_time
    ):
        """Cannot cancel a completed appointment."""
        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_type="in_person",
            status="completed",
            scheduled_at=future_time,
            duration_minutes=30,
            created_by=patient.id,
        )
        db.session.add(appt)
        db.session.commit()

        cancel_data = CancelAppointmentRequest(reason="Too late")
        with pytest.raises(ValueError, match="Cannot cancel"):
            appt_service.cancel_appointment(appt.id, patient.id, cancel_data)

    def test_cancel_nonexistent_fails(self, appt_service, patient, db):
        """Cancelling a non-existent appointment raises ValueError."""
        cancel_data = CancelAppointmentRequest(reason="N/A")
        with pytest.raises(ValueError, match="not found"):
            appt_service.cancel_appointment(uuid.uuid4(), patient.id, cancel_data)


class TestDoctorAvailability:

    def test_availability_returns_slots(self, appt_service, doctor, future_time):
        """Full day returns 16 half-hour slots (9:00-17:00)."""
        slots = appt_service.get_doctor_availability(doctor.id, future_time)
        assert len(slots) == 16

    def test_availability_excludes_booked_slots(
        self, appt_service, doctor, sample_appointment, future_time
    ):
        """Booked slots are excluded."""
        slots = appt_service.get_doctor_availability(doctor.id, future_time)
        assert len(slots) == 15


class TestAppointmentAccessControl:

    def test_patient_can_access_own(self, appt_service, patient, sample_appointment):
        assert appt_service.check_appointment_access(
            sample_appointment.id, patient.id, "patient"
        ) is True

    def test_patient_cannot_access_other(
        self, appt_service, other_patient, sample_appointment
    ):
        assert appt_service.check_appointment_access(
            sample_appointment.id, other_patient.id, "patient"
        ) is False

    def test_doctor_can_access_assigned(self, appt_service, doctor, sample_appointment):
        assert appt_service.check_appointment_access(
            sample_appointment.id, doctor.id, "doctor"
        ) is True

    def test_nonexistent_returns_false(self, appt_service, db):
        assert appt_service.check_appointment_access(
            uuid.uuid4(), uuid.uuid4(), "patient"
        ) is False


# ---------------------------------------------------------------------------
# Telemedicine Service Tests
# ---------------------------------------------------------------------------


class TestTelemedicineSession:

    def test_create_session_success(self, tele_service, telemedicine_appointment):
        """Creating a session for a telemedicine appointment succeeds."""
        result = tele_service.create_session(telemedicine_appointment.id)
        assert result.id is not None
        assert result.appointment_id == str(telemedicine_appointment.id)
        assert result.status == "waiting"
        assert "daily.co" in result.room_url

    def test_create_session_not_telemedicine_type_fails(
        self, tele_service, sample_appointment
    ):
        """Cannot create session for non-telemedicine appointment."""
        with pytest.raises(ValueError, match="not a telemedicine type"):
            tele_service.create_session(sample_appointment.id)

    def test_create_duplicate_session_fails(
        self, tele_service, telemedicine_appointment
    ):
        """Cannot create second session for same appointment."""
        tele_service.create_session(telemedicine_appointment.id)
        with pytest.raises(ValueError, match="already exists"):
            tele_service.create_session(telemedicine_appointment.id)

    def test_create_session_nonexistent_appointment_fails(self, tele_service, db):
        """Cannot create session for non-existent appointment."""
        with pytest.raises(ValueError, match="not found"):
            tele_service.create_session(uuid.uuid4())

    def test_join_session_transitions_to_in_progress(
        self, tele_service, telemedicine_appointment, patient
    ):
        """Joining a waiting session transitions to in_progress."""
        session = tele_service.create_session(telemedicine_appointment.id)
        join_result = tele_service.join_session(uuid.UUID(session.id), patient.id)
        assert join_result.status == "in_progress"
        assert join_result.room_url is not None

    def test_join_completed_session_fails(
        self, tele_service, telemedicine_appointment, patient
    ):
        """Cannot join a completed session."""
        session = tele_service.create_session(telemedicine_appointment.id)
        session_uuid = uuid.UUID(session.id)
        tele_service.join_session(session_uuid, patient.id)
        tele_service.end_session(session_uuid)

        with pytest.raises(ValueError, match="already completed"):
            tele_service.join_session(session_uuid, patient.id)

    def test_end_session_calculates_duration(
        self, tele_service, telemedicine_appointment, patient
    ):
        """Ending a session sets completed status and duration."""
        session = tele_service.create_session(telemedicine_appointment.id)
        session_uuid = uuid.UUID(session.id)
        tele_service.join_session(session_uuid, patient.id)
        result = tele_service.end_session(session_uuid)

        assert result.status == "completed"
        assert result.ended_at is not None
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0

    def test_end_session_nonexistent_fails(self, tele_service, db):
        """Cannot end a non-existent session."""
        with pytest.raises(ValueError, match="not found"):
            tele_service.end_session(uuid.uuid4())

    def test_get_session_by_appointment(
        self, tele_service, telemedicine_appointment
    ):
        """Can retrieve session by appointment ID."""
        created = tele_service.create_session(telemedicine_appointment.id)
        result = tele_service.get_session_by_appointment(telemedicine_appointment.id)
        assert result is not None
        assert result.id == created.id

    def test_session_access_patient(
        self, tele_service, telemedicine_appointment, patient, other_patient
    ):
        """Patient can access own session but not another's."""
        session = tele_service.create_session(telemedicine_appointment.id)
        session_uuid = uuid.UUID(session.id)
        assert tele_service.check_session_access(session_uuid, patient.id, "patient") is True
        assert tele_service.check_session_access(session_uuid, other_patient.id, "patient") is False

    def test_session_access_doctor(
        self, tele_service, telemedicine_appointment, doctor
    ):
        """Doctor can access assigned sessions."""
        session = tele_service.create_session(telemedicine_appointment.id)
        session_uuid = uuid.UUID(session.id)
        assert tele_service.check_session_access(session_uuid, doctor.id, "doctor") is True

    def test_transcript_returns_none_initially(
        self, tele_service, telemedicine_appointment
    ):
        """Transcript is None before AI processing."""
        session = tele_service.create_session(telemedicine_appointment.id)
        assert tele_service.get_transcript(uuid.UUID(session.id)) is None

    def test_notes_returns_none_initially(
        self, tele_service, telemedicine_appointment
    ):
        """Clinical notes are None before AI processing."""
        session = tele_service.create_session(telemedicine_appointment.id)
        assert tele_service.get_notes(uuid.UUID(session.id)) is None
