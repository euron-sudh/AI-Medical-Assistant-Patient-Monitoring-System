"""Patient service — business logic for patient profiles, medical history, and allergies."""

import uuid

from sqlalchemy import select

from app.extensions import db
from app.models.patient import Allergy, MedicalHistory, PatientProfile
from app.models.user import User
from app.schemas.patient_schema import (
    AddAllergyRequest,
    AddMedicalHistoryRequest,
    AllergyResponse,
    CreatePatientProfileRequest,
    MedicalHistoryResponse,
    PatientProfileResponse,
    UpdatePatientProfileRequest,
)


class PatientService:
    """Handles patient profile CRUD, medical history, and allergy operations."""

    def create_profile(
        self, user_id: str, data: CreatePatientProfileRequest
    ) -> PatientProfileResponse:
        """Create a patient profile linked to a user.

        Args:
            user_id: UUID string of the patient user.
            data: Validated patient profile data.

        Returns:
            PatientProfileResponse with the created profile.

        Raises:
            ValueError: If user not found, not a patient, or profile already exists.
        """
        uid = uuid.UUID(user_id)
        user = db.session.execute(
            select(User).where(User.id == uid)
        ).scalar_one_or_none()

        if not user:
            raise ValueError("User not found")
        if user.role != "patient":
            raise ValueError("Only users with role 'patient' can have a patient profile")

        existing = db.session.execute(
            select(PatientProfile).where(PatientProfile.user_id == uid)
        ).scalar_one_or_none()
        if existing:
            raise ValueError("Patient profile already exists for this user")

        profile = PatientProfile(
            user_id=uid,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            blood_type=data.blood_type,
            height_cm=data.height_cm,
            weight_kg=data.weight_kg,
            emergency_contact=data.emergency_contact,
            insurance_info=data.insurance_info,
        )
        db.session.add(profile)
        db.session.commit()

        return self._to_response(profile)

    def get_profile_by_user_id(self, user_id: str) -> PatientProfileResponse:
        """Get a patient profile by user ID.

        Args:
            user_id: UUID string of the patient user.

        Returns:
            PatientProfileResponse.

        Raises:
            ValueError: If profile not found.
        """
        profile = self._get_profile_or_raise(user_id)
        return self._to_response(profile)

    def update_profile(
        self, user_id: str, data: UpdatePatientProfileRequest
    ) -> PatientProfileResponse:
        """Update a patient profile.

        Args:
            user_id: UUID string of the patient user.
            data: Validated update data (only non-None fields are applied).

        Returns:
            Updated PatientProfileResponse.

        Raises:
            ValueError: If profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        db.session.commit()
        return self._to_response(profile)

    def list_patients(
        self, doctor_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[PatientProfileResponse]:
        """List patient profiles.

        Args:
            doctor_id: If provided, filter to patients assigned to this doctor.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of PatientProfileResponse.
        """
        stmt = select(PatientProfile)
        if doctor_id:
            stmt = stmt.where(PatientProfile.assigned_doctor_id == uuid.UUID(doctor_id))
        stmt = stmt.order_by(PatientProfile.created_at.desc()).limit(limit).offset(offset)

        profiles = db.session.execute(stmt).scalars().all()
        return [self._to_response(p) for p in profiles]

    # --- Medical History ---

    def get_medical_history(self, user_id: str) -> list[MedicalHistoryResponse]:
        """Get all medical history entries for a patient.

        Args:
            user_id: UUID string of the patient user.

        Returns:
            List of MedicalHistoryResponse.

        Raises:
            ValueError: If patient profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        stmt = (
            select(MedicalHistory)
            .where(MedicalHistory.patient_id == profile.id)
            .order_by(MedicalHistory.created_at.desc())
        )
        entries = db.session.execute(stmt).scalars().all()
        return [self._history_to_response(e) for e in entries]

    def add_medical_history(
        self, user_id: str, data: AddMedicalHistoryRequest, created_by: str
    ) -> MedicalHistoryResponse:
        """Add a medical history entry.

        Args:
            user_id: UUID string of the patient user.
            data: Validated medical history data.
            created_by: UUID string of the user creating the entry.

        Returns:
            MedicalHistoryResponse with the created entry.

        Raises:
            ValueError: If patient profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        entry = MedicalHistory(
            patient_id=profile.id,
            condition_name=data.condition_name,
            diagnosis_date=data.diagnosis_date,
            status=data.status,
            icd_10_code=data.icd_10_code,
            notes=data.notes,
            created_by=uuid.UUID(created_by),
        )
        db.session.add(entry)
        db.session.commit()

        return self._history_to_response(entry)

    # --- Allergies ---

    def get_allergies(self, user_id: str) -> list[AllergyResponse]:
        """Get all allergies for a patient.

        Args:
            user_id: UUID string of the patient user.

        Returns:
            List of AllergyResponse.

        Raises:
            ValueError: If patient profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        stmt = (
            select(Allergy)
            .where(Allergy.patient_id == profile.id)
            .order_by(Allergy.created_at.desc())
        )
        allergies = db.session.execute(stmt).scalars().all()
        return [self._allergy_to_response(a) for a in allergies]

    def add_allergy(
        self, user_id: str, data: AddAllergyRequest, created_by: str
    ) -> AllergyResponse:
        """Add an allergy record for a patient.

        Args:
            user_id: UUID string of the patient user.
            data: Validated allergy data.
            created_by: UUID string of the user creating the record.

        Returns:
            AllergyResponse with the created allergy.

        Raises:
            ValueError: If patient profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        allergy = Allergy(
            patient_id=profile.id,
            allergen=data.allergen,
            reaction=data.reaction,
            severity=data.severity,
            diagnosed_date=data.diagnosed_date,
            created_by=uuid.UUID(created_by),
        )
        db.session.add(allergy)
        db.session.commit()

        return self._allergy_to_response(allergy)

    # --- Helpers ---

    def _get_profile_or_raise(self, user_id: str) -> PatientProfile:
        """Get patient profile by user_id or raise ValueError."""
        stmt = select(PatientProfile).where(
            PatientProfile.user_id == uuid.UUID(user_id)
        )
        profile = db.session.execute(stmt).scalar_one_or_none()
        if not profile:
            raise ValueError("Patient profile not found")
        return profile

    def check_access(self, requester_id: str, requester_role: str, target_user_id: str) -> bool:
        """Check if the requester has access to the target patient's data.

        Args:
            requester_id: UUID string of the requesting user.
            requester_role: Role of the requesting user.
            target_user_id: UUID string of the patient whose data is being accessed.

        Returns:
            True if access is permitted.
        """
        if requester_role == "admin":
            return True
        if requester_role == "patient":
            return requester_id == target_user_id
        if requester_role in ("doctor", "nurse"):
            profile = db.session.execute(
                select(PatientProfile).where(
                    PatientProfile.user_id == uuid.UUID(target_user_id)
                )
            ).scalar_one_or_none()
            if not profile:
                return False
            return str(profile.assigned_doctor_id) == requester_id
        return False

    @staticmethod
    def _to_response(profile: PatientProfile) -> PatientProfileResponse:
        return PatientProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            blood_type=profile.blood_type,
            height_cm=float(profile.height_cm) if profile.height_cm else None,
            weight_kg=float(profile.weight_kg) if profile.weight_kg else None,
            emergency_contact=profile.emergency_contact,
            insurance_info=profile.insurance_info,
            assigned_doctor_id=str(profile.assigned_doctor_id) if profile.assigned_doctor_id else None,
        )

    @staticmethod
    def _history_to_response(entry: MedicalHistory) -> MedicalHistoryResponse:
        return MedicalHistoryResponse(
            id=str(entry.id),
            patient_id=str(entry.patient_id),
            condition_name=entry.condition_name,
            diagnosis_date=entry.diagnosis_date,
            status=entry.status,
            icd_10_code=entry.icd_10_code,
            notes=entry.notes,
        )

    @staticmethod
    def _allergy_to_response(allergy: Allergy) -> AllergyResponse:
        return AllergyResponse(
            id=str(allergy.id),
            patient_id=str(allergy.patient_id),
            allergen=allergy.allergen,
            reaction=allergy.reaction,
            severity=allergy.severity,
            diagnosed_date=allergy.diagnosed_date,
        )


# Module-level instance for use by routes
patient_service = PatientService()
