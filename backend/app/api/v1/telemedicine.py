"""Telemedicine API endpoints — session management for video consultations.

Routes:
    POST /api/v1/telemedicine/session                — Create session
    GET  /api/v1/telemedicine/session/<id>            — Get session
    POST /api/v1/telemedicine/session/<id>/join       — Join session
    PUT  /api/v1/telemedicine/session/<id>/end        — End session
    GET  /api/v1/telemedicine/session/<id>/transcript — Get transcript
    GET  /api/v1/telemedicine/session/<id>/notes      — Get notes
"""

import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError

from app.schemas.telemedicine_schema import CreateTelemedicineSessionRequest
from app.services.telemedicine_service import telemedicine_service

bp = Blueprint("telemedicine", __name__, url_prefix="/api/v1/telemedicine")


def _check_session_access(session_id: uuid.UUID) -> tuple | None:
    """Check session access. Returns error tuple if denied, None if allowed."""
    claims = get_jwt()
    current_user_id = uuid.UUID(get_jwt_identity())
    role = claims.get("role", "")

    if not telemedicine_service.check_session_access(session_id, current_user_id, role):
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Access denied to this session"}
        }), 403
    return None


@bp.route("/session", methods=["POST"])
@jwt_required()
def create_session():
    """Create a telemedicine session for an appointment."""
    claims = get_jwt()
    role = claims.get("role", "")

    if role not in ("doctor", "nurse", "admin"):
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Only providers can create telemedicine sessions"}
        }), 403

    try:
        data = CreateTelemedicineSessionRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        appointment_uuid = uuid.UUID(data.appointment_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid appointment ID"}}), 400

    try:
        session = telemedicine_service.create_session(appointment_uuid)
    except ValueError as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400

    return jsonify(session.model_dump(mode="json")), 201


@bp.route("/session/<session_id>", methods=["GET"])
@jwt_required()
def get_session(session_id: str):
    """Get telemedicine session details."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid session ID"}}), 400

    access_error = _check_session_access(session_uuid)
    if access_error:
        return access_error

    session = telemedicine_service.get_session(session_uuid)
    if not session:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Session not found"}}), 404

    return jsonify(session.model_dump(mode="json")), 200


@bp.route("/session/<session_id>/join", methods=["POST"])
@jwt_required()
def join_session(session_id: str):
    """Join a telemedicine video session."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid session ID"}}), 400

    access_error = _check_session_access(session_uuid)
    if access_error:
        return access_error

    current_user_id = uuid.UUID(get_jwt_identity())

    try:
        join_data = telemedicine_service.join_session(session_uuid, current_user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400

    return jsonify(join_data.model_dump(mode="json")), 200


@bp.route("/session/<session_id>/end", methods=["PUT"])
@jwt_required()
def end_session(session_id: str):
    """End a telemedicine session."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid session ID"}}), 400

    access_error = _check_session_access(session_uuid)
    if access_error:
        return access_error

    try:
        session = telemedicine_service.end_session(session_uuid)
    except ValueError as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400

    return jsonify(session.model_dump(mode="json")), 200


@bp.route("/session/<session_id>/transcript", methods=["GET"])
@jwt_required()
def get_transcript(session_id: str):
    """Get AI-generated transcript for a completed session."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid session ID"}}), 400

    access_error = _check_session_access(session_uuid)
    if access_error:
        return access_error

    transcript = telemedicine_service.get_transcript(session_uuid)
    return jsonify({"transcript": transcript, "message": "No transcript available yet" if transcript is None else None}), 200


@bp.route("/session/<session_id>/notes", methods=["GET"])
@jwt_required()
def get_notes(session_id: str):
    """Get AI-generated clinical notes for a completed session."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid session ID"}}), 400

    access_error = _check_session_access(session_uuid)
    if access_error:
        return access_error

    notes = telemedicine_service.get_notes(session_uuid)
    return jsonify({"notes": notes, "message": "No clinical notes available yet" if notes is None else None}), 200
