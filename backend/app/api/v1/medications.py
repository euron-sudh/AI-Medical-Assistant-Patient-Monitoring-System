"""Medication API endpoints — CRUD, interactions, schedule, adherence.

Routes:
    GET    /api/v1/medications/<patient_id>                       — List medications
    POST   /api/v1/medications/<patient_id>                       — Create medication
    PUT    /api/v1/medications/detail/<medication_id>              — Update medication
    DELETE /api/v1/medications/detail/<medication_id>              — Discontinue (soft-delete)
    POST   /api/v1/medications/interaction-check                   — Check drug interactions
    POST   /api/v1/medications/<patient_id>/interaction-check      — Patient-scoped interaction check
    GET    /api/v1/medications/<patient_id>/schedule               — Get medication schedule
    POST   /api/v1/medications/<patient_id>/adherence              — Record medication taken
    POST   /api/v1/medications/detail/<med_id>/adherence           — Log adherence (legacy)
    GET    /api/v1/medications/search                              — Search drug database

Task #31 — Vikash Kumar (patient-scoped interaction check, daily schedule, adherence recording)
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.middleware.auth_middleware import require_role
from app.schemas.medication_schema import (
    AdherenceLogRequest,
    AdherenceRecordRequest,
    CreateMedicationRequest,
    InteractionCheckRequest,
    PatientInteractionCheckRequest,
    UpdateMedicationRequest,
)
from app.services.medication_service import medication_service

bp = Blueprint("medications", __name__, url_prefix="/api/v1/medications")


def _check_med_access(patient_id: str) -> tuple | None:
    requester_id, claims = get_jwt_identity(), get_jwt()
    if not medication_service.check_access(requester_id, claims.get("role", ""), patient_id):
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403
    return None


@bp.route("/<patient_id>", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def list_medications(patient_id: str):
    denied = _check_med_access(patient_id)
    if denied:
        return denied
    meds = medication_service.list_medications(
        patient_id, status=request.args.get("status"),
        limit=request.args.get("limit", 50, type=int),
        offset=request.args.get("offset", 0, type=int),
    )
    return jsonify([m.model_dump() for m in meds]), 200


@bp.route("/<patient_id>", methods=["POST"])
@jwt_required()
@require_role(["doctor", "admin"])
def create_medication(patient_id: str):
    try:
        body = request.get_json()
        body["patient_id"] = patient_id
        data = CreateMedicationRequest.model_validate(body)
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    med = medication_service.create_medication(data, get_jwt_identity())
    return jsonify(med.model_dump()), 201


@bp.route("/detail/<medication_id>", methods=["PUT"])
@jwt_required()
@require_role(["doctor", "admin"])
def update_medication(medication_id: str):
    try:
        data = UpdateMedicationRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    try:
        med = medication_service.update_medication(medication_id, data)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404
    return jsonify(med.model_dump()), 200


@bp.route("/detail/<medication_id>", methods=["DELETE"])
@jwt_required()
@require_role(["doctor", "admin"])
def discontinue_medication(medication_id: str):
    try:
        med = medication_service.discontinue_medication(medication_id)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404
    return jsonify(med.model_dump()), 200


@bp.route("/interaction-check", methods=["POST"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def interaction_check():
    try:
        data = InteractionCheckRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    result = medication_service.check_interactions(data.medication_names, data.patient_id)
    return jsonify(result.model_dump()), 200


# ---------------------------------------------------------------------------
# Task #31 — Patient-scoped interaction check
# ---------------------------------------------------------------------------

@bp.route("/<patient_id>/interaction-check", methods=["POST"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def patient_interaction_check(patient_id: str):
    """Check drug interactions for a patient, including their active medications.

    Accepts a list of drug names and checks for known interactions among those
    drugs and the patient's currently active prescriptions.

    Args:
        patient_id: UUID of the patient.

    Request body:
        {"medication_names": ["warfarin", "aspirin"]}

    Returns:
        200 with interaction check results.
    """
    denied = _check_med_access(patient_id)
    if denied:
        return denied

    try:
        data = PatientInteractionCheckRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    result = medication_service.check_interactions(data.medication_names, patient_id)
    return jsonify(result.model_dump()), 200


# ---------------------------------------------------------------------------
# Task #31 — Enhanced daily schedule
# ---------------------------------------------------------------------------

@bp.route("/<patient_id>/schedule", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def get_schedule(patient_id: str):
    """Get a structured daily medication schedule for a patient.

    Maps each active prescription's frequency to time-of-day slots
    (morning, afternoon, evening, night) and returns a sorted schedule.

    Args:
        patient_id: UUID of the patient.

    Returns:
        200 with daily schedule including time slots and total doses.
    """
    denied = _check_med_access(patient_id)
    if denied:
        return denied
    schedule = medication_service.get_daily_schedule(patient_id)
    return jsonify(schedule.model_dump()), 200


# ---------------------------------------------------------------------------
# Task #31 — Record adherence (patient-scoped)
# ---------------------------------------------------------------------------

@bp.route("/<patient_id>/adherence", methods=["POST"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def record_adherence(patient_id: str):
    """Record that a patient has taken a specific medication.

    Args:
        patient_id: UUID of the patient.

    Request body:
        {"medication_id": "<uuid>", "taken_at": "2026-03-26T08:00:00Z", "notes": "..."}

    Returns:
        201 with adherence confirmation.
    """
    denied = _check_med_access(patient_id)
    if denied:
        return denied

    try:
        data = AdherenceRecordRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        result = medication_service.record_adherence(
            patient_id=patient_id,
            medication_id=data.medication_id,
            taken_at=data.taken_at,
            notes=data.notes,
        )
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify(result.model_dump()), 201


# ---------------------------------------------------------------------------
# Legacy adherence endpoint
# ---------------------------------------------------------------------------

@bp.route("/detail/<medication_id>/adherence", methods=["POST"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def log_adherence(medication_id: str):
    try:
        data = AdherenceLogRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    return jsonify({"medication_id": medication_id, "taken": data.taken, "logged": True}), 201


@bp.route("/search", methods=["GET"])
@jwt_required()
@require_role(["doctor", "nurse", "admin"])
def search_medications():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Query 'q' is required"}}), 400
    results = medication_service.search_medications(query, request.args.get("limit", 20, type=int))
    return jsonify([m.model_dump() for m in results]), 200
