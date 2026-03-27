"""Symptoms API endpoints — manage symptom check sessions.

Routes:
    POST /api/v1/symptoms/session              — Start a new session
    POST /api/v1/symptoms/session/<id>/message — Send a message in a session
    GET  /api/v1/symptoms/session/<id>         — Get session details
    PUT  /api/v1/symptoms/session/<id>/complete — Complete a session
    GET  /api/v1/symptoms/history/<patient_id> — Get session history
"""

import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.schemas.symptom_schema import (
    SendMessageRequest,
    SessionHistoryParams,
    StartSessionRequest,
)
from app.services.symptom_service import symptom_service

bp = Blueprint("symptoms", __name__, url_prefix="/api/v1/symptoms")


def _check_patient_access(patient_id: str) -> tuple | None:
    """Verify the current user can access this patient's symptom data.

    Returns an error tuple (response, status_code) if access is denied, or None if allowed.
    """
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    role = claims.get("role")

    if role == "patient" and str(current_user_id) != str(patient_id):
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Cannot access other patient's symptom sessions"}
        }), 403

    return None


@bp.route("/session", methods=["POST"])
@jwt_required()
def start_session():
    """Start a new symptom check session for the current patient."""
    try:
        data = StartSessionRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    current_user_id = uuid.UUID(get_jwt_identity())
    session = symptom_service.start_session(current_user_id, data)
    return jsonify(session.model_dump(mode="json")), 201


@bp.route("/session/<session_id>/message", methods=["POST"])
@jwt_required()
def send_message(session_id: str):
    """Send a message in a symptom check session."""
    try:
        data = SendMessageRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid session ID"}}), 400

    result = symptom_service.send_message(session_uuid, data)
    if result is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Session not found or not in progress"}}), 404

    return jsonify(result.model_dump(mode="json")), 200


@bp.route("/session/<session_id>", methods=["GET"])
@jwt_required()
def get_session(session_id: str):
    """Get symptom session details and diagnosis."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid session ID"}}), 400

    session = symptom_service.get_session(session_uuid)
    if session is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Session not found"}}), 404

    # Check access: patients can only see their own sessions
    access_error = _check_patient_access(session.patient_id)
    if access_error:
        return access_error

    return jsonify(session.model_dump(mode="json")), 200


@bp.route("/session/<session_id>/complete", methods=["PUT"])
@jwt_required()
def complete_session(session_id: str):
    """Complete a symptom check session."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid session ID"}}), 400

    result = symptom_service.complete_session(session_uuid)
    if result is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Session not found"}}), 404

    return jsonify(result.model_dump(mode="json")), 200


@bp.route("/history/<patient_id>", methods=["GET"])
@jwt_required()
def get_history(patient_id: str):
    """Get symptom session history for a patient."""
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    try:
        params = SessionHistoryParams.model_validate({
            "status": request.args.get("status"),
            "limit": request.args.get("limit", 50, type=int),
            "offset": request.args.get("offset", 0, type=int),
        })
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    sessions = symptom_service.get_patient_sessions(
        patient_uuid,
        status=params.status,
        limit=params.limit,
        offset=params.offset,
    )
    return jsonify([s.model_dump(mode="json") for s in sessions]), 200
