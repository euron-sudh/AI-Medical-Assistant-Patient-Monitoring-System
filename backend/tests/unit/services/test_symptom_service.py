"""Unit tests for SymptomService — symptom session management."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.symptom_schema import (
    SendMessageRequest,
    SessionHistoryParams,
    StartSessionRequest,
    SymptomSessionResponse,
)
from app.services.symptom_service import SymptomService


class TestStartSessionRequestValidation:
    """Schema validation tests for StartSessionRequest."""

    def test_valid_complaint(self):
        data = StartSessionRequest(chief_complaint="I have a headache and fever.")
        assert data.chief_complaint == "I have a headache and fever."

    def test_empty_complaint_rejected(self):
        with pytest.raises(ValidationError):
            StartSessionRequest(chief_complaint="")

    def test_complaint_too_long_rejected(self):
        with pytest.raises(ValidationError):
            StartSessionRequest(chief_complaint="x" * 2001)

    def test_optional_symptoms_default_none(self):
        data = StartSessionRequest(chief_complaint="headache")
        assert data.symptoms is None

    def test_symptoms_dict_accepted(self):
        data = StartSessionRequest(
            chief_complaint="headache",
            symptoms={"location": "frontal", "severity": 7},
        )
        assert data.symptoms["severity"] == 7


class TestSendMessageRequestValidation:
    """Schema validation tests for SendMessageRequest."""

    def test_valid_message(self):
        data = SendMessageRequest(message="The pain started yesterday.")
        assert data.message == "The pain started yesterday."

    def test_empty_message_rejected(self):
        with pytest.raises(ValidationError):
            SendMessageRequest(message="")

    def test_message_too_long_rejected(self):
        with pytest.raises(ValidationError):
            SendMessageRequest(message="x" * 5001)


class TestSessionHistoryParamsValidation:
    """Schema validation tests for SessionHistoryParams."""

    def test_defaults(self):
        params = SessionHistoryParams()
        assert params.limit == 50
        assert params.offset == 0
        assert params.status is None

    def test_limit_bounds(self):
        with pytest.raises(ValidationError):
            SessionHistoryParams(limit=0)
        with pytest.raises(ValidationError):
            SessionHistoryParams(limit=501)

    def test_negative_offset_rejected(self):
        with pytest.raises(ValidationError):
            SessionHistoryParams(offset=-1)


class TestSymptomSessionResponseSchema:
    """Schema validation for SymptomSessionResponse."""

    def test_valid_response(self):
        resp = SymptomSessionResponse(
            id=str(uuid.uuid4()),
            patient_id=str(uuid.uuid4()),
            status="in_progress",
            chief_complaint="headache",
            created_at="2026-03-20T10:00:00Z",
            updated_at="2026-03-20T10:00:00Z",
        )
        assert resp.status == "in_progress"
        assert resp.triage_level is None


class TestSymptomServiceStartSession:
    """Test SymptomService.start_session with database."""

    def test_start_session_creates_record(self, app, db):
        with app.app_context():
            from app.models.user import User

            user = User(email="sym@test.com", first_name="S", last_name="T", role="patient")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            service = SymptomService()
            data = StartSessionRequest(chief_complaint="Persistent headache for 3 days")
            result = service.start_session(user.id, data)

            assert result.status == "in_progress"
            assert result.chief_complaint == "Persistent headache for 3 days"
            assert result.patient_id == str(user.id)
            assert result.conversation_log is not None

    def test_get_session_returns_none_for_missing(self, app, db):
        with app.app_context():
            service = SymptomService()
            result = service.get_session(uuid.uuid4())
            assert result is None


class TestSymptomServiceSendMessage:
    """Test SymptomService.send_message."""

    def test_send_message_appends_to_log(self, app, db):
        with app.app_context():
            from app.models.user import User

            user = User(email="sym2@test.com", first_name="S", last_name="T", role="patient")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            service = SymptomService()
            start_data = StartSessionRequest(chief_complaint="Chest pain")
            session = service.start_session(user.id, start_data)

            msg_data = SendMessageRequest(message="It started after exercise")
            result = service.send_message(uuid.UUID(session.id), msg_data)

            assert result is not None
            # The log should contain at least the original complaint + the new
            # user message. The service may also append an assistant reply (or
            # an error fallback message when no OpenAI key is configured in
            # tests), so accept any number >= 2 as long as the new message is
            # present.
            assert len(result.conversation_log) >= 2
            assert any(
                m.get("content") == "It started after exercise"
                for m in result.conversation_log
            )

    def test_send_message_to_nonexistent_session(self, app, db):
        with app.app_context():
            service = SymptomService()
            msg_data = SendMessageRequest(message="test")
            result = service.send_message(uuid.uuid4(), msg_data)
            assert result is None


class TestSymptomServiceCompleteSession:
    """Test SymptomService.complete_session."""

    def test_complete_session_sets_completed(self, app, db):
        with app.app_context():
            from app.models.user import User

            user = User(email="sym3@test.com", first_name="S", last_name="T", role="patient")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            service = SymptomService()
            start_data = StartSessionRequest(chief_complaint="Nausea")
            session = service.start_session(user.id, start_data)

            result = service.complete_session(uuid.UUID(session.id))
            assert result is not None
            assert result.status == "completed"
            assert result.completed_at is not None

    def test_complete_nonexistent_session(self, app, db):
        with app.app_context():
            service = SymptomService()
            result = service.complete_session(uuid.uuid4())
            assert result is None


class TestSymptomServiceHistory:
    """Test SymptomService.get_patient_sessions."""

    def test_get_empty_history(self, app, db):
        with app.app_context():
            service = SymptomService()
            result = service.get_patient_sessions(uuid.uuid4())
            assert result == []

    def test_get_patient_sessions_returns_sessions(self, app, db):
        with app.app_context():
            from app.models.user import User

            user = User(email="sym4@test.com", first_name="S", last_name="T", role="patient")
            user.set_password("pass123")
            db.session.add(user)
            db.session.commit()

            service = SymptomService()
            service.start_session(user.id, StartSessionRequest(chief_complaint="Headache"))
            service.start_session(user.id, StartSessionRequest(chief_complaint="Fever"))

            result = service.get_patient_sessions(user.id)
            assert len(result) == 2
