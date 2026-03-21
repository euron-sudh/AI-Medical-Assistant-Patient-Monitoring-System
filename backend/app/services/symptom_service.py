"""Symptom service — business logic for symptom check sessions."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.extensions import db
from app.models.symptom_session import SymptomSession
from app.schemas.symptom_schema import (
    SendMessageRequest,
    StartSessionRequest,
    SymptomSessionResponse,
)


class SymptomService:
    """Handles creating, messaging, and managing symptom check sessions."""

    def start_session(
        self, patient_id: uuid.UUID, data: StartSessionRequest
    ) -> SymptomSessionResponse:
        """Start a new symptom check session.

        Args:
            patient_id: UUID of the patient.
            data: Validated session start data.

        Returns:
            SymptomSessionResponse with the created session.
        """
        session = SymptomSession(
            patient_id=patient_id,
            status="in_progress",
            chief_complaint=data.chief_complaint,
            symptoms=data.symptoms,
            conversation_log=[
                {"role": "user", "content": data.chief_complaint}
            ],
        )
        db.session.add(session)
        db.session.commit()
        return self._to_response(session)

    def send_message(
        self, session_id: uuid.UUID, data: SendMessageRequest
    ) -> SymptomSessionResponse | None:
        """Send a message in a symptom session.

        Args:
            session_id: UUID of the session.
            data: Validated message data.

        Returns:
            Updated SymptomSessionResponse, or None if session not found.
        """
        stmt = select(SymptomSession).where(SymptomSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()
        if session is None:
            return None

        if session.status != "in_progress":
            return None

        # Append message to conversation log (create new list to trigger SQLAlchemy change detection)
        conversation_log = list(session.conversation_log or [])
        conversation_log.append({"role": "user", "content": data.message})
        session.conversation_log = conversation_log
        session.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return self._to_response(session)

    def get_session(self, session_id: uuid.UUID) -> SymptomSessionResponse | None:
        """Get a symptom session by ID.

        Args:
            session_id: UUID of the session.

        Returns:
            SymptomSessionResponse if found, None otherwise.
        """
        stmt = select(SymptomSession).where(SymptomSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()
        if session is None:
            return None
        return self._to_response(session)

    def complete_session(self, session_id: uuid.UUID) -> SymptomSessionResponse | None:
        """Complete a symptom session.

        Args:
            session_id: UUID of the session.

        Returns:
            Updated SymptomSessionResponse, or None if not found.
        """
        stmt = select(SymptomSession).where(SymptomSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()
        if session is None:
            return None

        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        session.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return self._to_response(session)

    def get_patient_sessions(
        self,
        patient_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SymptomSessionResponse]:
        """Get symptom sessions for a patient.

        Args:
            patient_id: UUID of the patient.
            status: Optional filter by session status.
            limit: Maximum number of sessions to return.
            offset: Number of sessions to skip.

        Returns:
            List of SymptomSessionResponse matching the criteria.
        """
        stmt = select(SymptomSession).where(SymptomSession.patient_id == patient_id)

        if status:
            stmt = stmt.where(SymptomSession.status == status)

        stmt = stmt.order_by(SymptomSession.created_at.desc()).offset(offset).limit(limit)
        sessions = db.session.execute(stmt).scalars().all()
        return [self._to_response(s) for s in sessions]

    def _to_response(self, session: SymptomSession) -> SymptomSessionResponse:
        """Convert a SymptomSession model to a SymptomSessionResponse schema."""
        return SymptomSessionResponse(
            id=str(session.id),
            patient_id=str(session.patient_id),
            status=session.status,
            chief_complaint=session.chief_complaint,
            symptoms=session.symptoms,
            ai_analysis=session.ai_analysis,
            triage_level=session.triage_level,
            recommended_action=session.recommended_action,
            escalated_to=str(session.escalated_to) if session.escalated_to else None,
            conversation_log=session.conversation_log,
            completed_at=session.completed_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


# Module-level instance for use by routes
symptom_service = SymptomService()
