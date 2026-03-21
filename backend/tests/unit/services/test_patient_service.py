"""Unit tests for PatientService."""

import uuid
from datetime import date

import pytest

from app.models.patient import Allergy, MedicalHistory, PatientProfile
from app.models.user import User
from app.schemas.patient_schema import (
    AddAllergyRequest,
    AddMedicalHistoryRequest,
    CreatePatientProfileRequest,
    UpdatePatientProfileRequest,
)
from app.services.patient_service import PatientService


@pytest.fixture
def service() -> PatientService:
    return PatientService()


@pytest.fixture
def patient_user(db) -> User:
    """Create a patient user for testing."""
    user = User(
        email="testpatient@example.com",
        first_name="Jane",
        last_name="Doe",
        role="patient",
    )
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def doctor_user(db) -> User:
    """Create a doctor user for testing."""
    user = User(
        email="testdoctor@example.com",
        first_name="Dr. John",
        last_name="Smith",
        role="doctor",
    )
    user.set_password("testpass123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def patient_profile(db, patient_user, doctor_user) -> PatientProfile:
    """Create a patient profile assigned to the doctor."""
    profile = PatientProfile(
        user_id=patient_user.id,
        date_of_birth=date(1990, 5, 15),
        gender="female",
        blood_type="A+",
        assigned_doctor_id=doctor_user.id,
    )
    db.session.add(profile)
    db.session.commit()
    return profile


class TestCreateProfile:
    """Tests for PatientService.create_profile."""

    def test_create_profile_success(self, service, patient_user):
        data = CreatePatientProfileRequest(
            date_of_birth=date(1990, 5, 15),
            gender="female",
            blood_type="A+",
            height_cm=165.0,
            weight_kg=60.0,
        )
        result = service.create_profile(str(patient_user.id), data)

        assert result.user_id == str(patient_user.id)
        assert result.date_of_birth == date(1990, 5, 15)
        assert result.gender == "female"
        assert result.blood_type == "A+"
        assert result.height_cm == 165.0
        assert result.weight_kg == 60.0

    def test_create_profile_user_not_found(self, service, db):
        data = CreatePatientProfileRequest(date_of_birth=date(1990, 1, 1))
        with pytest.raises(ValueError, match="User not found"):
            service.create_profile(str(uuid.uuid4()), data)

    def test_create_profile_wrong_role(self, service, doctor_user):
        data = CreatePatientProfileRequest(date_of_birth=date(1990, 1, 1))
        with pytest.raises(ValueError, match="Only users with role 'patient'"):
            service.create_profile(str(doctor_user.id), data)

    def test_create_profile_duplicate(self, service, patient_user, patient_profile):
        data = CreatePatientProfileRequest(date_of_birth=date(1990, 1, 1))
        with pytest.raises(ValueError, match="already exists"):
            service.create_profile(str(patient_user.id), data)


class TestGetProfile:
    """Tests for PatientService.get_profile_by_user_id."""

    def test_get_profile_success(self, service, patient_user, patient_profile):
        result = service.get_profile_by_user_id(str(patient_user.id))
        assert result.user_id == str(patient_user.id)
        assert result.gender == "female"

    def test_get_profile_not_found(self, service, db):
        with pytest.raises(ValueError, match="not found"):
            service.get_profile_by_user_id(str(uuid.uuid4()))


class TestUpdateProfile:
    """Tests for PatientService.update_profile."""

    def test_update_profile_success(self, service, patient_user, patient_profile):
        data = UpdatePatientProfileRequest(weight_kg=65.0, blood_type="B+")
        result = service.update_profile(str(patient_user.id), data)
        assert result.weight_kg == 65.0
        assert result.blood_type == "B+"

    def test_update_profile_not_found(self, service, db):
        data = UpdatePatientProfileRequest(weight_kg=65.0)
        with pytest.raises(ValueError, match="not found"):
            service.update_profile(str(uuid.uuid4()), data)


class TestListPatients:
    """Tests for PatientService.list_patients."""

    def test_list_all_patients(self, service, patient_profile):
        results = service.list_patients()
        assert len(results) == 1

    def test_list_by_doctor(self, service, patient_profile, doctor_user):
        results = service.list_patients(doctor_id=str(doctor_user.id))
        assert len(results) == 1

    def test_list_by_unassigned_doctor(self, service, patient_profile):
        results = service.list_patients(doctor_id=str(uuid.uuid4()))
        assert len(results) == 0


class TestMedicalHistory:
    """Tests for medical history operations."""

    def test_add_medical_history(self, service, patient_user, patient_profile, doctor_user):
        data = AddMedicalHistoryRequest(
            condition_name="Hypertension",
            diagnosis_date=date(2024, 1, 10),
            status="active",
            icd_10_code="I10",
            notes="Stage 1",
        )
        result = service.add_medical_history(
            str(patient_user.id), data, str(doctor_user.id)
        )
        assert result.condition_name == "Hypertension"
        assert result.status == "active"
        assert result.icd_10_code == "I10"

    def test_get_medical_history(self, service, patient_user, patient_profile, doctor_user):
        data = AddMedicalHistoryRequest(condition_name="Diabetes", status="chronic")
        service.add_medical_history(str(patient_user.id), data, str(doctor_user.id))

        results = service.get_medical_history(str(patient_user.id))
        assert len(results) == 1
        assert results[0].condition_name == "Diabetes"

    def test_add_history_profile_not_found(self, service, doctor_user):
        data = AddMedicalHistoryRequest(condition_name="Test")
        with pytest.raises(ValueError, match="not found"):
            service.add_medical_history(str(uuid.uuid4()), data, str(doctor_user.id))


class TestAllergies:
    """Tests for allergy operations."""

    def test_add_allergy(self, service, patient_user, patient_profile, doctor_user):
        data = AddAllergyRequest(
            allergen="Penicillin",
            reaction="Rash and hives",
            severity="severe",
            diagnosed_date=date(2023, 6, 1),
        )
        result = service.add_allergy(str(patient_user.id), data, str(doctor_user.id))
        assert result.allergen == "Penicillin"
        assert result.severity == "severe"
        assert result.reaction == "Rash and hives"

    def test_get_allergies(self, service, patient_user, patient_profile, doctor_user):
        data = AddAllergyRequest(allergen="Peanuts", severity="life_threatening")
        service.add_allergy(str(patient_user.id), data, str(doctor_user.id))

        results = service.get_allergies(str(patient_user.id))
        assert len(results) == 1
        assert results[0].allergen == "Peanuts"
        assert results[0].severity == "life_threatening"

    def test_add_allergy_profile_not_found(self, service, doctor_user):
        data = AddAllergyRequest(allergen="Test", severity="mild")
        with pytest.raises(ValueError, match="not found"):
            service.add_allergy(str(uuid.uuid4()), data, str(doctor_user.id))


class TestAccessControl:
    """Tests for PatientService.check_access."""

    def test_patient_access_own_data(self, service, patient_user, patient_profile):
        assert service.check_access(
            str(patient_user.id), "patient", str(patient_user.id)
        ) is True

    def test_patient_cannot_access_other_data(self, service, patient_user, patient_profile):
        assert service.check_access(
            str(patient_user.id), "patient", str(uuid.uuid4())
        ) is False

    def test_doctor_access_assigned_patient(
        self, service, doctor_user, patient_user, patient_profile
    ):
        assert service.check_access(
            str(doctor_user.id), "doctor", str(patient_user.id)
        ) is True

    def test_doctor_cannot_access_unassigned_patient(self, service, patient_user, patient_profile):
        other_doctor_id = str(uuid.uuid4())
        assert service.check_access(
            other_doctor_id, "doctor", str(patient_user.id)
        ) is False

    def test_admin_access_any_patient(self, service, patient_user, patient_profile):
        admin_id = str(uuid.uuid4())
        assert service.check_access(admin_id, "admin", str(patient_user.id)) is True
