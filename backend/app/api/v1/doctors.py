"""Doctor API endpoints — profiles, listings, and availability.

Routes:
    GET    /api/v1/doctors            — List doctors
    GET    /api/v1/doctors/<id>       — Get doctor profile
    POST   /api/v1/doctors            — Create doctor profile
    PUT    /api/v1/doctors/<id>       — Update doctor profile
    GET    /api/v1/doctors/<id>/availability — Get available time slots
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.middleware.auth_middleware import require_role
from app.schemas.doctor_schema import (
    CreateDoctorProfileRequest,
    UpdateDoctorProfileRequest,
)
from app.services.doctor_service import doctor_service

bp = Blueprint("doctors", __name__, url_prefix="/api/v1/doctors")


@bp.route("", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def list_doctors():
    """List doctor profiles. Accessible to all authenticated users."""
    specialization = request.args.get("specialization")
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    profiles = doctor_service.list_doctors(
        specialization=specialization, limit=limit, offset=offset
    )
    return jsonify([p.model_dump() for p in profiles]), 200


@bp.route("/<user_id>", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def get_doctor(user_id: str):
    """Get a doctor profile by user ID."""
    try:
        profile = doctor_service.get_profile_by_user_id(user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify(profile.model_dump()), 200


@bp.route("", methods=["POST"])
@jwt_required()
@require_role(["doctor", "admin"])
def create_doctor():
    """Create a doctor profile for the current user (or by admin)."""
    try:
        data = CreateDoctorProfileRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    claims = get_jwt()
    role = claims.get("role", "")
    requester_id = get_jwt_identity()

    user_id = requester_id if role == "doctor" else request.args.get("user_id", requester_id)

    try:
        profile = doctor_service.create_profile(user_id, data)
    except ValueError as e:
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409

    return jsonify(profile.model_dump()), 201


@bp.route("/<user_id>", methods=["PUT"])
@jwt_required()
@require_role(["doctor", "admin"])
def update_doctor(user_id: str):
    """Update a doctor profile. Doctors can only update their own profile."""
    claims = get_jwt()
    role = claims.get("role", "")
    requester_id = get_jwt_identity()

    if role == "doctor" and requester_id != user_id:
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Doctors can only update their own profile"}
        }), 403

    try:
        data = UpdateDoctorProfileRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        profile = doctor_service.update_profile(user_id, data)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify(profile.model_dump()), 200


@bp.route("/<user_id>/availability", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def get_availability(user_id: str):
    """Get available time slots for a doctor for the next 7 days.

    Uses the doctor's availability JSON field (weekly schedule) and subtracts
    already-booked appointments to return actual availability.
    """
    try:
        availability = doctor_service.get_availability(user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify(availability), 200
