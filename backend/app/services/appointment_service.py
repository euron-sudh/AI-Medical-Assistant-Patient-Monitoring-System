"""Appointment service — business logic for scheduling and managing appointments."""

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select

from app.extensions import db
from app.models.appointment import Appointment
from app.schemas.appointment_schema import (
    AppointmentResponse,
    CancelAppointmentRequest,
    CreateAppointmentRequest,
    UpdateAppointmentRequest,
)

logger = structlog.get_logger(__name__)

# Valid status transitions
VALID_STATUS_TRANSITIONS = {
    "scheduled": {"confirmed", "cancelled", "no_show"},
    "confirmed": {"in_progress", "cancelled", "no_show"},
    "in_progress": {"completed"},
    "completed": set(),
    "cancelled": set(),
    "no_show": set(),
}


def _utcnow() -> datetime:
    """Return current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


class AppointmentService:
    """Handles creating, querying, updating, and cancelling appointments."""

    def create_appointment(
        self, data: CreateAppointmentRequest, created_by: uuid.UUID
    ) -> AppointmentResponse:
        """Create a new appointment.

        Args:
            data: Validated appointment creation data.
            created_by: UUID of the user creating the appointment.

        Returns:
            AppointmentResponse with the created appointment.

        Raises:
            ValueError: If there's a scheduling conflict.
        """
        patient_id = uuid.UUID(data.patient_id)
        doctor_id = uuid.UUID(data.doctor_id)

        conflict = self._check_scheduling_conflict(
            doctor_id=doctor_id,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
        )
        if conflict:
            raise ValueError("Doctor has a scheduling conflict at the requested time")

        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_type=data.appointment_type,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
            reason=data.reason,
            notes=data.notes,
            created_by=created_by,
        )

        db.session.add(appointment)
        db.session.commit()

        logger.info(
            "appointment_created",
            appointment_id=str(appointment.id),
            patient_id=str(patient_id),
            doctor_id=str(doctor_id),
            appointment_type=data.appointment_type,
        )

        return self._to_response(appointment)

    def get_appointment(self, appointment_id: uuid.UUID) -> AppointmentResponse | None:
        """Get a single appointment by ID.

        Args:
            appointment_id: UUID of the appointment.

        Returns:
            AppointmentResponse if found, None otherwise.
        """
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        appointment = db.session.execute(stmt).scalar_one_or_none()
        if not appointment:
            return None
        return self._to_response(appointment)

    def list_appointments(
        self,
        user_id: uuid.UUID,
        role: str,
        status: str | None = None,
        appointment_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AppointmentResponse]:
        """List appointments for a user, scoped by their role.

        Patients see only their own. Doctors see their assigned appointments.

        Args:
            user_id: UUID of the authenticated user.
            role: User's role (patient, doctor, nurse, admin).
            status: Optional status filter.
            appointment_type: Optional type filter.
            start_date: Optional start of date range.
            end_date: Optional end of date range.
            limit: Maximum results to return.
            offset: Number of results to skip.

        Returns:
            List of AppointmentResponse matching the filters.
        """
        stmt = select(Appointment)

        if role == "patient":
            stmt = stmt.where(Appointment.patient_id == user_id)
        elif role in ("doctor", "nurse"):
            stmt = stmt.where(Appointment.doctor_id == user_id)

        if status:
            stmt = stmt.where(Appointment.status == status)
        if appointment_type:
            stmt = stmt.where(Appointment.appointment_type == appointment_type)
        if start_date:
            stmt = stmt.where(Appointment.scheduled_at >= start_date)
        if end_date:
            stmt = stmt.where(Appointment.scheduled_at <= end_date)

        stmt = stmt.order_by(Appointment.scheduled_at.asc()).offset(offset).limit(limit)
        appointments = db.session.execute(stmt).scalars().all()
        return [self._to_response(a) for a in appointments]

    def get_upcoming(
        self, patient_id: uuid.UUID, limit: int = 10
    ) -> list[AppointmentResponse]:
        """Get upcoming appointments for a patient.

        Args:
            patient_id: UUID of the patient.
            limit: Maximum results to return.

        Returns:
            List of future appointments ordered by scheduled time.
        """
        now = _utcnow()
        stmt = (
            select(Appointment)
            .where(
                Appointment.patient_id == patient_id,
                Appointment.scheduled_at > now,
                Appointment.status.in_(["scheduled", "confirmed"]),
            )
            .order_by(Appointment.scheduled_at.asc())
            .limit(limit)
        )
        appointments = db.session.execute(stmt).scalars().all()
        return [self._to_response(a) for a in appointments]

    def update_appointment(
        self, appointment_id: uuid.UUID, data: UpdateAppointmentRequest
    ) -> AppointmentResponse:
        """Update an existing appointment.

        Args:
            appointment_id: UUID of the appointment.
            data: Validated update data (only non-None fields are applied).

        Returns:
            Updated AppointmentResponse.

        Raises:
            ValueError: If appointment not found or status transition is invalid.
        """
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        appointment = db.session.execute(stmt).scalar_one_or_none()

        if not appointment:
            raise ValueError("Appointment not found")

        if data.status and data.status != appointment.status:
            valid_transitions = VALID_STATUS_TRANSITIONS.get(appointment.status, set())
            if data.status not in valid_transitions:
                raise ValueError(
                    f"Cannot transition from '{appointment.status}' to '{data.status}'"
                )
            appointment.status = data.status

        if data.scheduled_at is not None:
            appointment.scheduled_at = data.scheduled_at
        if data.duration_minutes is not None:
            appointment.duration_minutes = data.duration_minutes
        if data.reason is not None:
            appointment.reason = data.reason
        if data.notes is not None:
            appointment.notes = data.notes

        db.session.commit()

        logger.info(
            "appointment_updated",
            appointment_id=str(appointment_id),
            status=appointment.status,
        )

        return self._to_response(appointment)

    def cancel_appointment(
        self,
        appointment_id: uuid.UUID,
        cancelled_by: uuid.UUID,
        data: CancelAppointmentRequest,
    ) -> AppointmentResponse:
        """Cancel an appointment.

        Args:
            appointment_id: UUID of the appointment to cancel.
            cancelled_by: UUID of the user performing the cancellation.
            data: Cancellation reason.

        Returns:
            Updated AppointmentResponse with cancelled status.

        Raises:
            ValueError: If appointment not found or cannot be cancelled.
        """
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        appointment = db.session.execute(stmt).scalar_one_or_none()

        if not appointment:
            raise ValueError("Appointment not found")

        if appointment.status in ("completed", "cancelled"):
            raise ValueError(f"Cannot cancel appointment with status '{appointment.status}'")

        appointment.status = "cancelled"
        appointment.cancelled_by = cancelled_by
        appointment.cancelled_reason = data.reason

        db.session.commit()

        logger.info(
            "appointment_cancelled",
            appointment_id=str(appointment_id),
            cancelled_by=str(cancelled_by),
        )

        return self._to_response(appointment)

    def get_doctor_availability(
        self, doctor_id: uuid.UUID, date: datetime
    ) -> list[dict]:
        """Get a doctor's available time slots for a given date.

        Args:
            doctor_id: UUID of the doctor.
            date: The date to check availability for.

        Returns:
            List of available time slot dicts with start and end times.
        """
        day_start = date.replace(hour=9, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=17, minute=0, second=0, microsecond=0)

        stmt = (
            select(Appointment)
            .where(
                Appointment.doctor_id == doctor_id,
                Appointment.scheduled_at >= day_start,
                Appointment.scheduled_at < day_end,
                Appointment.status.not_in(["cancelled"]),
            )
            .order_by(Appointment.scheduled_at.asc())
        )
        booked = db.session.execute(stmt).scalars().all()

        booked_ranges = []
        for appt in booked:
            appt_end = appt.scheduled_at + timedelta(minutes=appt.duration_minutes)
            booked_ranges.append((appt.scheduled_at, appt_end))

        available_slots = []
        current = day_start
        while current < day_end:
            slot_end = current + timedelta(minutes=30)
            is_available = not any(
                current < booked_end and slot_end > booked_start
                for booked_start, booked_end in booked_ranges
            )
            if is_available:
                available_slots.append({
                    "start": current.isoformat(),
                    "end": slot_end.isoformat(),
                })
            current = slot_end

        return available_slots

    def check_appointment_access(
        self, appointment_id: uuid.UUID, user_id: uuid.UUID, role: str
    ) -> bool:
        """Check if a user has access to a specific appointment.

        Args:
            appointment_id: UUID of the appointment.
            user_id: UUID of the requesting user.
            role: User's role.

        Returns:
            True if the user can access this appointment.
        """
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        appointment = db.session.execute(stmt).scalar_one_or_none()

        if not appointment:
            return False
        if role == "admin":
            return True
        if role == "patient":
            return appointment.patient_id == user_id
        if role in ("doctor", "nurse"):
            return appointment.doctor_id == user_id
        return False

    def _check_scheduling_conflict(
        self,
        doctor_id: uuid.UUID,
        scheduled_at: datetime,
        duration_minutes: int,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        """Check if the doctor has a conflicting appointment."""
        appointment_end = scheduled_at + timedelta(minutes=duration_minutes)

        stmt = select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.status.not_in(["cancelled", "no_show"]),
            Appointment.scheduled_at < appointment_end,
        )

        if exclude_id:
            stmt = stmt.where(Appointment.id != exclude_id)

        appointments = db.session.execute(stmt).scalars().all()

        for appt in appointments:
            appt_end = appt.scheduled_at + timedelta(minutes=appt.duration_minutes)
            if appt.scheduled_at < appointment_end and appt_end > scheduled_at:
                return True

        return False

    def _to_response(self, appointment: Appointment) -> AppointmentResponse:
        """Convert an Appointment model to an AppointmentResponse schema."""
        return AppointmentResponse(
            id=str(appointment.id),
            patient_id=str(appointment.patient_id),
            doctor_id=str(appointment.doctor_id),
            appointment_type=appointment.appointment_type,
            status=appointment.status,
            scheduled_at=appointment.scheduled_at,
            duration_minutes=appointment.duration_minutes,
            reason=appointment.reason,
            notes=appointment.notes,
            cancelled_by=str(appointment.cancelled_by) if appointment.cancelled_by else None,
            cancelled_reason=appointment.cancelled_reason,
            created_by=str(appointment.created_by),
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
        )


# Module-level instance for use by routes
appointment_service = AppointmentService()
