"""Unit tests for MedicationService."""

import uuid
from datetime import date

import pytest

from app.models.medication import Medication
from app.models.user import User
from app.schemas.medication_schema import CreateMedicationRequest, UpdateMedicationRequest
from app.services.medication_service import MedicationService


@pytest.fixture
def service() -> MedicationService:
    return MedicationService()


@pytest.fixture
def patient_user(db) -> User:
    user = User(email="med_patient@test.com", first_name="Med", last_name="Patient", role="patient")
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def doctor_user(db) -> User:
    user = User(email="med_doctor@test.com", first_name="Dr. Med", last_name="Doctor", role="doctor")
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def medication(db, patient_user, doctor_user) -> Medication:
    med = Medication(
        patient_id=patient_user.id, name="Metformin", dosage="500mg",
        frequency="twice daily", route="oral", prescribed_by=doctor_user.id,
        start_date=date(2026, 1, 1), status="active", reason="Type 2 diabetes",
        refills_remaining=3, created_by=doctor_user.id,
    )
    db.session.add(med)
    db.session.commit()
    return med


class TestCreateMedication:
    def test_create_success(self, service, patient_user, doctor_user):
        data = CreateMedicationRequest(
            patient_id=str(patient_user.id), name="Lisinopril", dosage="10mg",
            frequency="once daily", start_date=date(2026, 3, 1), refills_remaining=5,
        )
        result = service.create_medication(data, str(doctor_user.id))
        assert result.name == "Lisinopril" and result.status == "active" and result.refills_remaining == 5

    def test_create_minimal(self, service, patient_user, doctor_user):
        data = CreateMedicationRequest(
            patient_id=str(patient_user.id), name="Aspirin", dosage="81mg",
            frequency="once daily", start_date=date(2026, 3, 1),
        )
        assert service.create_medication(data, str(doctor_user.id)).refills_remaining == 0


class TestGetMedication:
    def test_get_success(self, service, medication):
        assert service.get_medication(str(medication.id)).name == "Metformin"

    def test_get_not_found(self, service, db):
        with pytest.raises(ValueError, match="not found"):
            service.get_medication(str(uuid.uuid4()))


class TestUpdateMedication:
    def test_update_dosage(self, service, medication):
        assert service.update_medication(str(medication.id), UpdateMedicationRequest(dosage="1000mg")).dosage == "1000mg"

    def test_update_not_found(self, service, db):
        with pytest.raises(ValueError, match="not found"):
            service.update_medication(str(uuid.uuid4()), UpdateMedicationRequest(dosage="500mg"))


class TestDiscontinueMedication:
    def test_discontinue_sets_status(self, service, medication):
        result = service.discontinue_medication(str(medication.id))
        assert result.status == "discontinued" and result.name == "Metformin"

    def test_discontinue_not_found(self, service, db):
        with pytest.raises(ValueError, match="not found"):
            service.discontinue_medication(str(uuid.uuid4()))


class TestListMedications:
    def test_list_by_patient(self, service, medication, patient_user):
        assert len(service.list_medications(str(patient_user.id))) == 1

    def test_list_with_filter(self, service, medication, patient_user):
        assert len(service.list_medications(str(patient_user.id), status="active")) == 1
        assert len(service.list_medications(str(patient_user.id), status="discontinued")) == 0


class TestSchedule:
    def test_schedule(self, service, medication, patient_user):
        result = service.get_schedule(str(patient_user.id))
        assert len(result.medications) == 1


class TestInteractionCheck:
    def test_check(self, service, db):
        result = service.check_interactions(["Metformin", "Lisinopril"])
        assert result.interactions_found == 0


class TestAccessControl:
    def test_patient_own(self, service, patient_user):
        assert service.check_access(str(patient_user.id), "patient", str(patient_user.id)) is True

    def test_patient_other(self, service, patient_user):
        assert service.check_access(str(patient_user.id), "patient", str(uuid.uuid4())) is False

    def test_doctor(self, service, doctor_user, patient_user):
        assert service.check_access(str(doctor_user.id), "doctor", str(patient_user.id)) is True

    def test_admin(self, service, patient_user):
        assert service.check_access(str(uuid.uuid4()), "admin", str(patient_user.id)) is True
