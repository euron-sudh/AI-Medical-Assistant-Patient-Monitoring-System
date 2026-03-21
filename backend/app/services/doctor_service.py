"""Doctor service — business logic for doctor profiles."""

import uuid

from sqlalchemy import select

from app.extensions import db
from app.models.doctor import DoctorProfile
from app.models.user import User
from app.schemas.doctor_schema import (
    CreateDoctorProfileRequest,
    DoctorProfileResponse,
    UpdateDoctorProfileRequest,
)


class DoctorService:
    """Handles doctor profile CRUD operations."""

    def create_profile(
        self, user_id: str, data: CreateDoctorProfileRequest
    ) -> DoctorProfileResponse:
        """Create a doctor profile linked to a user.

        Args:
            user_id: UUID string of the doctor user.
            data: Validated doctor profile data.

        Returns:
            DoctorProfileResponse with the created profile.

        Raises:
            ValueError: If user not found, not a doctor, or profile already exists.
        """
        uid = uuid.UUID(user_id)
        user = db.session.execute(
            select(User).where(User.id == uid)
        ).scalar_one_or_none()

        if not user:
            raise ValueError("User not found")
        if user.role != "doctor":
            raise ValueError("Only users with role 'doctor' can have a doctor profile")

        existing = db.session.execute(
            select(DoctorProfile).where(DoctorProfile.user_id == uid)
        ).scalar_one_or_none()
        if existing:
            raise ValueError("Doctor profile already exists for this user")

        profile = DoctorProfile(
            user_id=uid,
            specialization=data.specialization,
            license_number=data.license_number,
            license_state=data.license_state,
            years_of_experience=data.years_of_experience,
            department=data.department,
            consultation_fee=data.consultation_fee,
            bio=data.bio,
            availability=data.availability,
        )
        db.session.add(profile)
        db.session.commit()

        return self._to_response(profile)

    def get_profile_by_user_id(self, user_id: str) -> DoctorProfileResponse:
        """Get a doctor profile by user ID.

        Args:
            user_id: UUID string of the doctor user.

        Returns:
            DoctorProfileResponse.

        Raises:
            ValueError: If profile not found.
        """
        profile = self._get_profile_or_raise(user_id)
        return self._to_response(profile)

    def update_profile(
        self, user_id: str, data: UpdateDoctorProfileRequest
    ) -> DoctorProfileResponse:
        """Update a doctor profile.

        Args:
            user_id: UUID string of the doctor user.
            data: Validated update data (only non-None fields are applied).

        Returns:
            Updated DoctorProfileResponse.

        Raises:
            ValueError: If profile not found.
        """
        profile = self._get_profile_or_raise(user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        db.session.commit()
        return self._to_response(profile)

    def list_doctors(
        self, specialization: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[DoctorProfileResponse]:
        """List doctor profiles.

        Args:
            specialization: If provided, filter by specialization.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of DoctorProfileResponse.
        """
        stmt = select(DoctorProfile)
        if specialization:
            stmt = stmt.where(DoctorProfile.specialization.ilike(f"%{specialization}%"))
        stmt = stmt.order_by(DoctorProfile.created_at.desc()).limit(limit).offset(offset)

        profiles = db.session.execute(stmt).scalars().all()
        return [self._to_response(p) for p in profiles]

    def _get_profile_or_raise(self, user_id: str) -> DoctorProfile:
        """Get doctor profile by user_id or raise ValueError."""
        stmt = select(DoctorProfile).where(
            DoctorProfile.user_id == uuid.UUID(user_id)
        )
        profile = db.session.execute(stmt).scalar_one_or_none()
        if not profile:
            raise ValueError("Doctor profile not found")
        return profile

    @staticmethod
    def _to_response(profile: DoctorProfile) -> DoctorProfileResponse:
        return DoctorProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            specialization=profile.specialization,
            license_number=profile.license_number,
            license_state=profile.license_state,
            years_of_experience=profile.years_of_experience,
            department=profile.department,
            consultation_fee=float(profile.consultation_fee) if profile.consultation_fee else None,
            bio=profile.bio,
            availability=profile.availability,
        )


# Module-level instance for use by routes
doctor_service = DoctorService()
