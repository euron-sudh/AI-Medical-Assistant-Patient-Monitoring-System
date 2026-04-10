"""Voice symptom analysis service — manages conversational voice sessions."""

import base64
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import select

from app.agents.base_agent import AgentInput
from app.agents.voice_symptom_analyst import VoiceSymptomAnalystAgent
from app.extensions import db
from app.models.voice_session import VoiceSession
from app.schemas.voice_session_schema import (
    VoiceSessionStartRequest,
    VoiceSessionMessageRequest,
    VoiceSessionResponse,
    VoiceSessionState,
)
from app.services.voice_service import voice_service

logger = structlog.get_logger(__name__)


class VoiceSymptomService:
    """Manages voice-based symptom analysis sessions."""

    def __init__(self):
        self.agent = VoiceSymptomAnalystAgent()
        self._session_states: dict[str, VoiceSessionState] = {}

    def start_session(self, data: VoiceSessionStartRequest) -> VoiceSessionState:
        """Start a new voice symptom analysis session.

        Args:
            data: Session start request with patient info and preferences.

        Returns:
            VoiceSessionState with session ID and initial state.
        """
        session_id = str(uuid.uuid4())
        
        # Create in-memory session state
        state = VoiceSessionState(
            session_id=session_id,
            patient_id=data.patient_id,
            language=data.language,
            voice_preset=data.voice_preset,
        )
        
        # Store in memory cache
        self._session_states[session_id] = state
        
        # Persist to database
        voice_session = VoiceSession(
            id=session_id,
            patient_id=data.patient_id,
            status="in_progress",
            language=data.language,
            voice_preset=data.voice_preset,
        )
        db.session.add(voice_session)
        db.session.commit()
        
        logger.info(
            "voice_symptom_session_started",
            session_id=session_id,
            patient_id=data.patient_id,
        )
        
        return state

    def process_message(
        self, data: VoiceSessionMessageRequest
    ) -> VoiceSessionResponse:
        """Process a voice/text message and generate doctor response.

        Args:
            data: Message request with audio or text.

        Returns:
            VoiceSessionResponse with doctor's voice/text response.
        """
        session_id = data.session_id
        
        # Get session state
        if session_id not in self._session_states:
            raise ValueError(f"Session {session_id} not found")
        
        state = self._session_states[session_id]
        
        # Transcribe audio if provided
        user_message = data.text_message
        if data.audio_base64:
            try:
                audio_data = base64.b64decode(data.audio_base64)
                # Browser MediaRecorder typically produces WebM/Opus. Provide a filename hint
                # so the upstream STT client can infer container/codec correctly.
                transcription = voice_service.transcribe(
                    audio_data,
                    filename="audio.webm",
                    language=state.language,
                )
                user_message = transcription.text
                logger.info(
                    "voice_audio_transcribed",
                    session_id=session_id,
                    text_length=len(user_message),
                )
            except Exception as e:
                logger.error("voice_transcription_failed", error=str(e))
                raise ValueError(f"Audio transcription failed: {str(e)}")
        
        if not user_message:
            raise ValueError("No message content provided")
        
        # Add user message to conversation history
        state.conversation_history.append({
            "role": "user",
            "content": user_message,
        })
        state.current_turn += 1
        
        # Determine if this is the first message
        is_first_message = len(state.conversation_history) == 1
        
        # Build agent input
        agent_input = AgentInput(
            session_id=session_id,
            user_id=state.patient_id,
            patient_id=state.patient_id,
            message=user_message,
            conversation_history=state.conversation_history[:-1],
            metadata={
                "language": state.language,
                "voice_preset": state.voice_preset,
                "is_first_message": is_first_message,
            },
        )
        
        # Run the voice symptom analyst agent
        result = self.agent.run(agent_input)
        
        # Extract doctor's response
        doctor_message = result.response_text
        is_final = bool(result.differential_diagnoses)
        
        # Generate voice response
        doctor_audio_base64 = None
        try:
            synthesis_result = voice_service.synthesize(
                type("obj", (object,), {
                    "text": doctor_message,
                    "voice": state.voice_preset,
                    "speed": 1.0,
                })()
            )
            doctor_audio_base64 = synthesis_result.audio_base64
            logger.info(
                "voice_response_synthesized",
                session_id=session_id,
                text_length=len(doctor_message),
            )
        except Exception as e:
            logger.error("voice_synthesis_failed", error=str(e))
        
        # Add doctor response to conversation history
        state.conversation_history.append({
            "role": "assistant",
            "content": doctor_message,
        })
        state.updated_at = datetime.now(timezone.utc)
        
        # If final assessment, mark session as completed
        if is_final:
            state.status = "completed"
            state.final_assessment = {
                "differential_diagnoses": result.differential_diagnoses,
                "urgency_score": result.urgency_score,
                "recommended_action": result.recommended_action,
                "recommended_specialist": result.recommended_specialist,
                "sources": [src.model_dump() for src in result.sources],
            }
            
            # Update database
            voice_session = db.session.get(VoiceSession, session_id)
            if voice_session:
                voice_session.status = "completed"
                voice_session.final_assessment = state.final_assessment
                voice_session.completed_at = datetime.now(timezone.utc)
                voice_session.updated_at = datetime.now(timezone.utc)
                db.session.commit()
        
        logger.info(
            "voice_symptom_message_processed",
            session_id=session_id,
            turn=state.current_turn,
            is_final=is_final,
        )
        
        return VoiceSessionResponse(
            session_id=session_id,
            doctor_message=doctor_message,
            doctor_audio_base64=doctor_audio_base64,
            conversation_turn=state.current_turn,
            is_final_assessment=is_final,
            assessment_data=state.final_assessment,
        )

    def get_session_state(self, session_id: str) -> VoiceSessionState:
        """Get the current state of a voice session."""
        if session_id not in self._session_states:
            raise ValueError(f"Session {session_id} not found")
        
        return self._session_states[session_id]

    def cancel_session(self, session_id: str) -> None:
        """Cancel an in-progress voice session."""
        if session_id not in self._session_states:
            raise ValueError(f"Session {session_id} not found")
        
        state = self._session_states[session_id]
        state.status = "cancelled"
        state.updated_at = datetime.now(timezone.utc)
        
        # Update database
        voice_session = db.session.get(VoiceSession, session_id)
        if voice_session:
            voice_session.status = "cancelled"
            voice_session.updated_at = datetime.now(timezone.utc)
            db.session.commit()
        
        del self._session_states[session_id]
        
        logger.info("voice_symptom_session_cancelled", session_id=session_id)


voice_symptom_service = VoiceSymptomService()
