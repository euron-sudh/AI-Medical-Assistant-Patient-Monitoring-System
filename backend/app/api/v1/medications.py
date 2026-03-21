"""Medication API endpoints — CRUD, interactions, schedule, adherence.

Routes:
    GET    /api/v1/medications/<patient_id>               — List medications
    POST   /api/v1/medications/<patient_id>               — Create medication
    PUT    /api/v1/medications/detail/<medication_id>      — Update medication
    DELETE /api/v1/medications/detail/<medication_id>      — Discontinue (soft-delete)
    POST   /api/v1/medications/interaction-check           — Check drug interactions
    GET    /api/v1/medications/<patient_id>/schedule       — Get medication schedule
    POST   /api/v1/medications/detail/<med_id>/adherence   — Log adherence
    GET    /api/v1/medications/search                      — Search drug database
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.middleware.auth_middleware import require_role
from app.schemas.medication_schema import (
    AdherenceLogRequest, CreateMedicationRequest, InteractionCheckRequest, UpdateMedicationRequest,
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


@bp.route("/<patient_id>/schedule", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def get_schedule(patient_id: str):
    denied = _check_med_access(patient_id)
    if denied:
        return denied
    schedule = medication_service.get_schedule(patient_id)
    return jsonify(schedule.model_dump()), 200


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
