"""Patient API endpoints — profiles, medical history, allergies.

Routes:
    GET    /api/v1/patients            — List patients (doctor/admin)
    GET    /api/v1/patients/<id>       — Get patient profile
    POST   /api/v1/patients            — Create patient profile
    PUT    /api/v1/patients/<id>       — Update patient profile
    GET    /api/v1/patients/<id>/medical-history  — Get medical history
    POST   /api/v1/patients/<id>/medical-history  — Add medical history entry
    GET    /api/v1/patients/<id>/allergies        — Get allergies
    POST   /api/v1/patients/<id>/allergies        — Add allergy
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.middleware.auth_middleware import require_role
from app.schemas.patient_schema import (
    AddAllergyRequest,
    AddMedicalHistoryRequest,
    CreatePatientProfileRequest,
    UpdatePatientProfileRequest,
)
from app.services.patient_service import patient_service

bp = Blueprint("patients", __name__, url_prefix="/api/v1/patients")


def _check_patient_access(target_user_id: str) -> tuple | None:
    """Verify the requester has access to the target patient's data.

    Returns an error tuple (response, status) if access denied, or None if allowed.
    """
    requester_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "")

    if not patient_service.check_access(requester_id, role, target_user_id):
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "You do not have access to this patient's data"}
        }), 403
    return None


@bp.route("", methods=["GET"])
@jwt_required()
@require_role(["doctor", "nurse", "admin"])
def list_patients():
    """List patient profiles.

    Doctors and nurses see only their assigned patients.
    Admins see all patients.
    """
    claims = get_jwt()
    role = claims.get("role", "")
    requester_id = get_jwt_identity()

    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    doctor_id = requester_id if role in ("doctor", "nurse") else None
    profiles = patient_service.list_patients(doctor_id=doctor_id, limit=limit, offset=offset)
    return jsonify([p.model_dump() for p in profiles]), 200


@bp.route("/<user_id>", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def get_patient(user_id: str):
    """Get a patient profile by user ID."""
    denied = _check_patient_access(user_id)
    if denied:
        return denied

    try:
        profile = patient_service.get_profile_by_user_id(user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify(profile.model_dump()), 200


@bp.route("", methods=["POST"])
@jwt_required()
@require_role(["patient", "admin"])
def create_patient():
    """Create a patient profile for the current user (or by admin)."""
    try:
        data = CreatePatientProfileRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    claims = get_jwt()
    role = claims.get("role", "")
    requester_id = get_jwt_identity()

    # Patients can only create their own profile
    user_id = requester_id if role == "patient" else request.args.get("user_id", requester_id)

    try:
        profile = patient_service.create_profile(user_id, data)
    except ValueError as e:
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409

    return jsonify(profile.model_dump()), 201


@bp.route("/<user_id>", methods=["PUT"])
@jwt_required()
@require_role(["patient", "doctor", "admin"])
def update_patient(user_id: str):
    """Update a patient profile."""
    denied = _check_patient_access(user_id)
    if denied:
        return denied

    try:
        data = UpdatePatientProfileRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        profile = patient_service.update_profile(user_id, data)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify(profile.model_dump()), 200


@bp.route("/<user_id>/medical-history", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def get_medical_history(user_id: str):
    """Get medical history for a patient."""
    denied = _check_patient_access(user_id)
    if denied:
        return denied

    try:
        history = patient_service.get_medical_history(user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify([h.model_dump() for h in history]), 200


@bp.route("/<user_id>/medical-history", methods=["POST"])
@jwt_required()
@require_role(["doctor", "nurse", "admin"])
def add_medical_history(user_id: str):
    """Add a medical history entry for a patient."""
    denied = _check_patient_access(user_id)
    if denied:
        return denied

    try:
        data = AddMedicalHistoryRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    created_by = get_jwt_identity()

    try:
        entry = patient_service.add_medical_history(user_id, data, created_by)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify(entry.model_dump()), 201


@bp.route("/<user_id>/allergies", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def get_allergies(user_id: str):
    """Get allergies for a patient."""
    denied = _check_patient_access(user_id)
    if denied:
        return denied

    try:
        allergies = patient_service.get_allergies(user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify([a.model_dump() for a in allergies]), 200


@bp.route("/<user_id>/allergies", methods=["POST"])
@jwt_required()
@require_role(["doctor", "nurse", "admin"])
def add_allergy(user_id: str):
    """Add an allergy for a patient."""
    denied = _check_patient_access(user_id)
    if denied:
        return denied

    try:
        data = AddAllergyRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    created_by = get_jwt_identity()

    try:
        allergy = patient_service.add_allergy(user_id, data, created_by)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify(allergy.model_dump()), 201
