"""Voice Symptom Analysis API endpoints — interactive voice-based symptom checker.

Routes:
    POST /api/v1/voice-symptom/start     — Start new voice symptom session
    POST /api/v1/voice-symptom/message   — Send audio/text message, get doctor response
    GET  /api/v1/voice-symptom/<id>      — Get session state
    DELETE /api/v1/voice-symptom/<id>    — Cancel session
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.middleware.auth_middleware import require_role
from app.schemas.voice_session_schema import (
    VoiceSessionStartRequest,
    VoiceSessionMessageRequest,
)
from app.services.voice_symptom_service import voice_symptom_service

bp = Blueprint("voice_symptom", __name__, url_prefix="/api/v1/voice-symptom")


@bp.route("/start", methods=["POST"])
@jwt_required()
@require_role(["patient"])
def start_voice_session():
    """Start a new voice-based symptom analysis session.

    Returns session ID and initial greeting from the AI doctor.
    """
    try:
        data = VoiceSessionStartRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    # Verify patient can only start their own session
    current_user_id = get_jwt_identity()
    if data.patient_id != current_user_id:
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Can only start sessions for yourself"}
        }), 403

    try:
        state = voice_symptom_service.start_session(data)
    except ValueError as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500

    # Generate initial greeting
    greeting_text = (
        "Hello! I'm your AI health assistant. I'm here to help you understand your symptoms. "
        "Can you please tell me what symptoms you're experiencing today? "
        "Please describe them in as much detail as you can."
    )

    # Generate greeting audio
    greeting_audio = None
    try:
        from app.services.voice_service import voice_service
        from app.schemas.voice_schema import SynthesizeRequest
        synthesis = voice_service.synthesize(SynthesizeRequest(
            text=greeting_text,
            voice=data.voice_preset,
            speed=1.0,
        ))
        greeting_audio = synthesis.audio_base64
    except Exception as e:
        pass  # Greeting still works without audio

    return jsonify({
        "session_id": state.session_id,
        "status": state.status,
        "doctor_message": greeting_text,
        "doctor_audio_base64": greeting_audio,
        "language": state.language,
        "voice_preset": state.voice_preset,
    }), 201


@bp.route("/message", methods=["POST"])
@jwt_required()
@require_role(["patient"])
def send_message():
    """Send an audio or text message to the AI doctor and get a response.

    Accepts either audio (base64) or text. Returns doctor's response
    in both text and audio format.
    """
    try:
        data = VoiceSessionMessageRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    # Verify patient ownership
    current_user_id = get_jwt_identity()
    try:
        state = voice_symptom_service.get_session_state(data.session_id)
        if state.patient_id != current_user_id:
            return jsonify({
                "error": {"code": "FORBIDDEN", "message": "Access denied to this session"}
            }), 403
    except ValueError:
        return jsonify({
            "error": {"code": "NOT_FOUND", "message": "Session not found"}
        }), 404

    try:
        response = voice_symptom_service.process_message(data)
    except ValueError as e:
        return jsonify({"error": {"code": "PROCESSING_ERROR", "message": str(e)}}), 500
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500

    return jsonify({
        "session_id": response.session_id,
        "doctor_message": response.doctor_message,
        "doctor_audio_base64": response.doctor_audio_base64,
        "conversation_turn": response.conversation_turn,
        "is_final_assessment": response.is_final_assessment,
        "assessment_data": response.assessment_data,
    }), 200


@bp.route("/<session_id>", methods=["GET"])
@jwt_required()
@require_role(["patient"])
def get_session(session_id: str):
    """Get the current state of a voice symptom session."""
    current_user_id = get_jwt_identity()

    try:
        state = voice_symptom_service.get_session_state(session_id)
        if state.patient_id != current_user_id:
            return jsonify({
                "error": {"code": "FORBIDDEN", "message": "Access denied to this session"}
            }), 403
    except ValueError:
        return jsonify({
            "error": {"code": "NOT_FOUND", "message": "Session not found"}
        }), 404

    return jsonify(state.model_dump()), 200


@bp.route("/<session_id>", methods=["DELETE"])
@jwt_required()
@require_role(["patient"])
def cancel_session(session_id: str):
    """Cancel an in-progress voice symptom session."""
    current_user_id = get_jwt_identity()

    try:
        state = voice_symptom_service.get_session_state(session_id)
        if state.patient_id != current_user_id:
            return jsonify({
                "error": {"code": "FORBIDDEN", "message": "Access denied to this session"}
            }), 403
    except ValueError:
        return jsonify({
            "error": {"code": "NOT_FOUND", "message": "Session not found"}
        }), 404

    try:
        voice_symptom_service.cancel_session(session_id)
    except ValueError as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500

    return jsonify({"message": "Session cancelled successfully"}), 200
