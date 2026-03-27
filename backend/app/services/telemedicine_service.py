"""Telemedicine service — business logic for video consultation sessions."""

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.extensions import db
from app.models.appointment import Appointment
from app.models.telemedicine import TelemedicineSession
from app.schemas.telemedicine_schema import (
    JoinSessionResponse,
    TelemedicineSessionResponse,
)

logger = structlog.get_logger(__name__)


def _utcnow() -> datetime:
    """Return current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


class TelemedicineService:
    """Handles creating, joining, and managing telemedicine video sessions."""

    def create_session(
        self, appointment_id: uuid.UUID
    ) -> TelemedicineSessionResponse:
        """Create a telemedicine session for an appointment.

        Args:
            appointment_id: UUID of the telemedicine appointment.

        Returns:
            TelemedicineSessionResponse with session details.

        Raises:
            ValueError: If appointment not found, not a telemedicine type,
                        or session already exists.
        """
        stmt = select(Appointment).where(Appointment.id == appointment_id)
        appointment = db.session.execute(stmt).scalar_one_or_none()

        if not appointment:
            raise ValueError("Appointment not found")

        if appointment.appointment_type != "telemedicine":
            raise ValueError("Appointment is not a telemedicine type")

        existing_stmt = select(TelemedicineSession).where(
            TelemedicineSession.appointment_id == appointment_id
        )
        existing = db.session.execute(existing_stmt).scalar_one_or_none()
        if existing:
            raise ValueError("Telemedicine session already exists for this appointment")

        room_url = f"https://medassist.daily.co/session-{appointment_id}"

        session = TelemedicineSession(
            appointment_id=appointment_id,
            patient_id=appointment.patient_id,
            doctor_id=appointment.doctor_id,
            room_url=room_url,
            status="waiting",
        )

        db.session.add(session)
        db.session.commit()

        logger.info(
            "telemedicine_session_created",
            session_id=str(session.id),
            appointment_id=str(appointment_id),
        )

        return self._to_response(session)

    def get_session(
        self, session_id: uuid.UUID
    ) -> TelemedicineSessionResponse | None:
        """Get a telemedicine session by ID."""
        stmt = select(TelemedicineSession).where(TelemedicineSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()
        if not session:
            return None
        return self._to_response(session)

    def get_session_by_appointment(
        self, appointment_id: uuid.UUID
    ) -> TelemedicineSessionResponse | None:
        """Get a telemedicine session by its appointment ID."""
        stmt = select(TelemedicineSession).where(
            TelemedicineSession.appointment_id == appointment_id
        )
        session = db.session.execute(stmt).scalar_one_or_none()
        if not session:
            return None
        return self._to_response(session)

    def join_session(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> JoinSessionResponse:
        """Join a telemedicine session.

        Args:
            session_id: UUID of the session.
            user_id: UUID of the joining user.

        Returns:
            JoinSessionResponse with room URL and token.

        Raises:
            ValueError: If session not found or already completed/failed.
        """
        stmt = select(TelemedicineSession).where(TelemedicineSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()

        if not session:
            raise ValueError("Telemedicine session not found")

        if session.status in ("completed", "failed"):
            raise ValueError(f"Session is already {session.status}")

        if session.status == "waiting":
            session.status = "in_progress"
            session.started_at = _utcnow()
            db.session.commit()

        logger.info(
            "telemedicine_session_joined",
            session_id=str(session_id),
            user_id=str(user_id),
        )

        return JoinSessionResponse(
            session_id=str(session.id),
            room_url=session.room_url,
            room_token=session.room_token,
            status=session.status,
        )

    def end_session(
        self, session_id: uuid.UUID
    ) -> TelemedicineSessionResponse:
        """End a telemedicine session.

        Args:
            session_id: UUID of the session.

        Returns:
            Updated TelemedicineSessionResponse.

        Raises:
            ValueError: If session not found or not in progress.
        """
        stmt = select(TelemedicineSession).where(TelemedicineSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()

        if not session:
            raise ValueError("Telemedicine session not found")

        if session.status not in ("waiting", "in_progress"):
            raise ValueError(f"Cannot end session with status '{session.status}'")

        now = _utcnow()
        session.status = "completed"
        session.ended_at = now

        if session.started_at:
            delta = now - session.started_at
            session.duration_seconds = int(delta.total_seconds())

        appt_stmt = select(Appointment).where(Appointment.id == session.appointment_id)
        appointment = db.session.execute(appt_stmt).scalar_one_or_none()
        if appointment and appointment.status == "in_progress":
            appointment.status = "completed"

        db.session.commit()

        logger.info(
            "telemedicine_session_ended",
            session_id=str(session_id),
            duration_seconds=session.duration_seconds,
        )

        return self._to_response(session)

    def get_transcript(self, session_id: uuid.UUID) -> str | None:
        """Get the AI-generated transcript for a session."""
        stmt = select(TelemedicineSession).where(TelemedicineSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()
        if not session:
            return None
        return session.ai_transcript

    def get_notes(self, session_id: uuid.UUID) -> str | None:
        """Get the AI-generated clinical notes for a session."""
        stmt = select(TelemedicineSession).where(TelemedicineSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()
        if not session:
            return None
        return session.ai_summary

    def list_sessions(
        self,
        user_id: uuid.UUID,
        role: str,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TelemedicineSessionResponse]:
        """List telemedicine sessions for a user, scoped by role.

        Patients see sessions where they are the patient.
        Doctors/nurses see sessions where they are the doctor.
        Admins see all sessions.

        Args:
            user_id: UUID of the authenticated user.
            role: User role.
            status: Optional status filter.
            limit: Maximum results to return.
            offset: Number of results to skip.

        Returns:
            List of TelemedicineSessionResponse matching the filters.
        """
        stmt = select(TelemedicineSession)

        if role == "patient":
            stmt = stmt.where(TelemedicineSession.patient_id == user_id)
        elif role in ("doctor", "nurse"):
            stmt = stmt.where(TelemedicineSession.doctor_id == user_id)
        # admin sees all

        if status:
            stmt = stmt.where(TelemedicineSession.status == status)

        stmt = (
            stmt.order_by(TelemedicineSession.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        sessions = db.session.execute(stmt).scalars().all()
        return [self._to_response(s) for s in sessions]

    def save_transcript(
        self, session_id: uuid.UUID, transcript: str
    ) -> TelemedicineSessionResponse:
        """Save or update the transcript for a session.

        Args:
            session_id: UUID of the session.
            transcript: The transcript text to save.

        Returns:
            Updated TelemedicineSessionResponse.

        Raises:
            ValueError: If session not found.
        """
        stmt = select(TelemedicineSession).where(TelemedicineSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()

        if not session:
            raise ValueError("Telemedicine session not found")

        session.ai_transcript = transcript
        db.session.commit()

        logger.info(
            "telemedicine_transcript_saved",
            session_id=str(session_id),
            transcript_length=len(transcript),
        )

        return self._to_response(session)

    def save_notes(
        self, session_id: uuid.UUID, notes: str
    ) -> TelemedicineSessionResponse:
        """Save or update clinical notes for a session.

        Args:
            session_id: UUID of the session.
            notes: The clinical notes text to save.

        Returns:
            Updated TelemedicineSessionResponse.

        Raises:
            ValueError: If session not found.
        """
        stmt = select(TelemedicineSession).where(TelemedicineSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()

        if not session:
            raise ValueError("Telemedicine session not found")

        session.ai_summary = notes
        db.session.commit()

        logger.info(
            "telemedicine_notes_saved",
            session_id=str(session_id),
            notes_length=len(notes),
        )

        return self._to_response(session)

    def check_session_access(
        self, session_id: uuid.UUID, user_id: uuid.UUID, role: str
    ) -> bool:
        """Check if a user has access to a telemedicine session."""
        stmt = select(TelemedicineSession).where(TelemedicineSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()

        if not session:
            return False
        if role == "admin":
            return True
        if role == "patient":
            return session.patient_id == user_id
        if role in ("doctor", "nurse"):
            return session.doctor_id == user_id
        return False

    def _to_response(self, session: TelemedicineSession) -> TelemedicineSessionResponse:
        """Convert a TelemedicineSession model to a response schema."""
        return TelemedicineSessionResponse(
            id=str(session.id),
            appointment_id=str(session.appointment_id),
            patient_id=str(session.patient_id),
            doctor_id=str(session.doctor_id),
            room_url=session.room_url,
            status=session.status,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_seconds=session.duration_seconds,
            recording_url=session.recording_url,
            ai_transcript=session.ai_transcript,
            ai_summary=session.ai_summary,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


# Module-level instance for use by routes
telemedicine_service = TelemedicineService()
