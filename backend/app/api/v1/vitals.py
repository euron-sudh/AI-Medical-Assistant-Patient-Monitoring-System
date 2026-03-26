"""Vitals API endpoints — create, read, and query patient vitals.

Routes:
    POST /api/v1/vitals/<patient_id>          — Create a vitals reading
    GET  /api/v1/vitals/<patient_id>          — Get latest vitals for a patient
    GET  /api/v1/vitals/<patient_id>/history  — Get vitals history with time range
"""

import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError

from app.schemas.vitals_schema import CreateVitalsRequest, VitalsHistoryParams
from app.services.vitals_service import vitals_service

bp = Blueprint("vitals", __name__, url_prefix="/api/v1/vitals")


def _check_patient_access(patient_id: str) -> tuple | None:
    """Verify the current user can access this patient's vitals.

    Returns an error tuple (response, status_code) if access is denied, or None if allowed.
    """
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    role = claims.get("role")

    if role == "patient" and str(current_user_id) != str(patient_id):
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Cannot access other patient's vitals"}
        }), 403

    return None


@bp.route("/<patient_id>", methods=["POST"])
@jwt_required()
def create_vitals_reading(patient_id: str):
    """Create a new vitals reading for a patient.

    Patients can create readings for themselves. Doctors and nurses can
    create readings for their patients.
    """
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        data = CreateVitalsRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    current_user_id = uuid.UUID(get_jwt_identity())

    reading = vitals_service.create_reading(patient_uuid, data, created_by=current_user_id)
    return jsonify(reading.model_dump(mode="json")), 201


@bp.route("/<patient_id>", methods=["GET"])
@jwt_required()
def get_patient_vitals(patient_id: str):
    """Get the most recent vitals readings for a patient.

    Query params:
        limit: Maximum number of readings (default 100, max 1000).
    """
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    limit = request.args.get("limit", 100, type=int)
    limit = min(max(limit, 1), 1000)

    readings = vitals_service.get_patient_vitals(patient_uuid, limit=limit)
    return jsonify([r.model_dump(mode="json") for r in readings]), 200


@bp.route("/<patient_id>/history", methods=["GET"])
@jwt_required()
def get_vitals_history(patient_id: str):
    """Get vitals history for a patient within a time range.

    Query params:
        start_date: ISO 8601 datetime string (inclusive).
        end_date: ISO 8601 datetime string (inclusive).
        limit: Maximum number of readings (default 100, max 1000).
        offset: Number of readings to skip (default 0).
    """
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    # Parse query parameters
    params: dict = {}
    if request.args.get("start_date"):
        try:
            params["start_date"] = datetime.fromisoformat(request.args["start_date"])
        except ValueError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid start_date format"}}), 400

    if request.args.get("end_date"):
        try:
            params["end_date"] = datetime.fromisoformat(request.args["end_date"])
        except ValueError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid end_date format"}}), 400

    params["limit"] = request.args.get("limit", 100, type=int)
    params["offset"] = request.args.get("offset", 0, type=int)

    try:
        history_params = VitalsHistoryParams.model_validate(params)
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    readings = vitals_service.get_vitals_history(
        patient_uuid,
        start_date=history_params.start_date,
        end_date=history_params.end_date,
        limit=history_params.limit,
        offset=history_params.offset,
    )
    return jsonify([r.model_dump(mode="json") for r in readings]), 200
