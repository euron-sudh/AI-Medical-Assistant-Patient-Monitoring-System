"""Doctor service — business logic for doctor profiles and availability."""

import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select

from app.extensions import db
from app.models.appointment import Appointment
from app.models.doctor import DoctorProfile
from app.models.user import User
from app.schemas.doctor_schema import (
    CreateDoctorProfileRequest,
    DoctorProfileResponse,
    UpdateDoctorProfileRequest,
)


class DoctorService:
    """Handles doctor profile CRUD operations and availability computation."""

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

    def get_availability(self, user_id: str) -> list[dict]:
        """Compute available time slots for a doctor for the next 7 days.

        Uses the doctor's weekly availability schedule and subtracts
        already-booked appointments to determine open slots.

        Args:
            user_id: UUID string of the doctor user.

        Returns:
            List of dicts: [{date, slots: [{start_time, end_time, available}]}]

        Raises:
            ValueError: If doctor profile not found or no availability configured.
        """
        profile = self._get_profile_or_raise(user_id)
        uid = uuid.UUID(user_id)

        weekly_schedule = profile.availability or {}
        if not weekly_schedule:
            raise ValueError("Doctor has no availability schedule configured")

        today = date.today()
        now = datetime.now(timezone.utc)

        # Fetch booked appointments for the next 7 days
        start_dt = datetime.combine(today, time.min).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(today + timedelta(days=7), time.max).replace(tzinfo=timezone.utc)

        booked_appointments = db.session.execute(
            select(Appointment).where(
                Appointment.doctor_id == uid,
                Appointment.scheduled_at >= start_dt,
                Appointment.scheduled_at <= end_dt,
                Appointment.status.in_(["scheduled", "confirmed", "in_progress"]),
            )
        ).scalars().all()

        # Index booked times by date for quick lookup
        booked_by_date: dict[date, list[tuple[time, time]]] = {}
        for appt in booked_appointments:
            appt_date = appt.scheduled_at.date()
            appt_start = appt.scheduled_at.time()
            appt_end = (appt.scheduled_at + timedelta(minutes=appt.duration_minutes)).time()
            booked_by_date.setdefault(appt_date, []).append((appt_start, appt_end))

        # Day name mapping
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

        result = []
        for day_offset in range(7):
            current_date = today + timedelta(days=day_offset)
            day_name = day_names[current_date.weekday()]
            day_ranges = weekly_schedule.get(day_name, [])

            slots = []
            for time_range in day_ranges:
                # Parse "HH:MM-HH:MM" format
                try:
                    start_str, end_str = time_range.split("-")
                    range_start = time.fromisoformat(start_str.strip())
                    range_end = time.fromisoformat(end_str.strip())
                except (ValueError, AttributeError):
                    continue

                # Generate 30-minute slots within each range
                slot_start = datetime.combine(current_date, range_start)
                slot_end_limit = datetime.combine(current_date, range_end)

                while slot_start + timedelta(minutes=30) <= slot_end_limit:
                    slot_end = slot_start + timedelta(minutes=30)
                    s_time = slot_start.time()
                    e_time = slot_end.time()

                    # Check if this slot is booked
                    is_available = True

                    # Skip past slots for today
                    if current_date == today:
                        slot_aware = slot_start.replace(tzinfo=timezone.utc)
                        if slot_aware <= now:
                            is_available = False

                    # Check against booked appointments
                    if is_available:
                        for booked_start, booked_end in booked_by_date.get(current_date, []):
                            # Overlap check: slot overlaps if slot_start < booked_end and slot_end > booked_start
                            if s_time < booked_end and e_time > booked_start:
                                is_available = False
                                break

                    slots.append({
                        "start_time": s_time.strftime("%H:%M"),
                        "end_time": e_time.strftime("%H:%M"),
                        "available": is_available,
                    })

                    slot_start = slot_end

            result.append({
                "date": current_date.isoformat(),
                "slots": slots,
            })

        return result

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
