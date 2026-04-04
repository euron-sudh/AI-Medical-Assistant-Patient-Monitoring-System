"""Symptom service — business logic for symptom check sessions."""

import logging
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

logger = logging.getLogger(__name__)


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
        """Send a message in a symptom session and get AI response.

        Args:
            session_id: UUID of the session.
            data: Validated message data.

        Returns:
            Updated SymptomSessionResponse with AI response, or None if session not found.
        """
        stmt = select(SymptomSession).where(SymptomSession.id == session_id)
        session = db.session.execute(stmt).scalar_one_or_none()
        if session is None:
            return None

        if session.status != "in_progress":
            return None

        # Append user message to conversation log
        conversation_log = list(session.conversation_log or [])
        conversation_log.append({"role": "user", "content": data.message})

        # Call AI agent to generate a response
        ai_response_text = self._get_ai_response(
            session, conversation_log, data.message
        )

        # Append AI response to conversation log
        conversation_log.append({"role": "assistant", "content": ai_response_text})
        session.conversation_log = conversation_log
        session.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return self._to_response(session)

    def _get_ai_response(
        self,
        session: SymptomSession,
        conversation_log: list[dict],
        user_message: str,
    ) -> str:
        """Call the AI to generate a symptom analysis response.

        Uses the SymptomAnalystAgent if available, falls back to direct
        OpenAI chat completion.

        Args:
            session: The current symptom session.
            conversation_log: Full conversation history.
            user_message: The latest user message.

        Returns:
            AI response text.
        """
        try:
            from app.agents.base_agent import AgentInput
            from app.agents.symptom_analyst import SymptomAnalystAgent

            agent = SymptomAnalystAgent()
            agent_input = AgentInput(
                session_id=str(session.id),
                user_id=str(session.patient_id),
                patient_id=str(session.patient_id),
                message=user_message,
                conversation_history=conversation_log[:-1],  # exclude the latest user msg (agent adds it)
            )
            result = agent.run(agent_input)

            # Store analysis results on the session if we got structured output
            if result.differential_diagnoses:
                session.ai_analysis = {
                    "urgency_score": result.urgency_score,
                    "differential_diagnosis": result.differential_diagnoses,
                    "recommended_action": result.recommended_action,
                    "recommended_specialist": result.recommended_specialist,
                    "follow_up_questions": result.follow_up_questions,
                    "confidence": result.confidence,
                }
                if result.urgency_score >= 8:
                    session.triage_level = "emergency"
                elif result.urgency_score >= 6:
                    session.triage_level = "urgent"
                elif result.urgency_score >= 4:
                    session.triage_level = "semi_urgent"
                else:
                    session.triage_level = "non_urgent"
                session.recommended_action = result.recommended_action

            return result.response_text

        except Exception as agent_err:
            logger.warning("Symptom agent failed, falling back to direct chat: %s", agent_err)

        # Fallback: direct OpenAI chat completion (same pattern as working /chat endpoint)
        try:
            from app.integrations.openai_client import openai_client

            system_prompt = (
                "You are MedAssist AI Symptom Analyst. Conduct a thorough symptom interview "
                "using the OLDCARTS framework (Onset, Location, Duration, Character, "
                "Alleviating/Aggravating factors, Radiation, Timing, Severity). "
                "Ask follow-up questions to narrow down the diagnosis. Be empathetic and clear. "
                "Use plain language at a 6th-8th grade reading level. "
                "Always remind users this is not a substitute for professional medical advice."
            )
            messages = [{"role": "system", "content": system_prompt}]
            # Include recent conversation history (last 20 messages for context)
            for msg in conversation_log[-20:]:
                role = msg.get("role", "user")
                if role in ("user", "assistant"):
                    messages.append({"role": role, "content": msg.get("content", "")})

            result = openai_client.chat_completion(
                messages=messages,
                max_tokens=800,
                temperature=0.3,
            )
            return result.content or "I'm processing your symptoms. Could you provide more details?"

        except Exception as chat_err:
            logger.error("Direct chat fallback also failed: %s", chat_err)
            return (
                "I'm having trouble analyzing your symptoms right now. "
                "Please try again in a moment, or contact your healthcare provider directly."
            )

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
