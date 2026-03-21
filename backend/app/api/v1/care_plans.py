"""Care plan API endpoints — CRUD, goals, adherence.

Routes:
    GET    /api/v1/care-plans             — List care plans
    POST   /api/v1/care-plans             — Create care plan
    GET    /api/v1/care-plans/<id>        — Get care plan by ID
    PUT    /api/v1/care-plans/<id>        — Update care plan
    POST   /api/v1/care-plans/<id>/goals  — Add goal
    PUT    /api/v1/care-plans/goals/<id>  — Update goal
    POST   /api/v1/care-plans/generate    — AI-generate care plan (placeholder)
    GET    /api/v1/care-plans/<id>/adherence — Adherence report
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.middleware.auth_middleware import require_role
from app.schemas.care_plan_schema import AddGoalRequest, CreateCarePlanRequest, UpdateCarePlanRequest, UpdateGoalRequest
from app.services.care_plan_service import care_plan_service

bp = Blueprint("care_plans", __name__, url_prefix="/api/v1/care-plans")


@bp.route("", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def list_care_plans():
    claims = get_jwt()
    role, requester_id = claims.get("role", ""), get_jwt_identity()
    patient_id = requester_id if role == "patient" else request.args.get("patient_id")
    doctor_id = requester_id if role in ("doctor", "nurse") else None
    plans = care_plan_service.list_care_plans(
        patient_id=patient_id, doctor_id=doctor_id,
        status=request.args.get("status"),
        limit=request.args.get("limit", 50, type=int),
        offset=request.args.get("offset", 0, type=int),
    )
    return jsonify([p.model_dump() for p in plans]), 200


@bp.route("", methods=["POST"])
@jwt_required()
@require_role(["doctor", "admin"])
def create_care_plan():
    try:
        data = CreateCarePlanRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    plan = care_plan_service.create_care_plan(data, get_jwt_identity())
    return jsonify(plan.model_dump()), 201


@bp.route("/<plan_id>", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def get_care_plan(plan_id: str):
    try:
        plan = care_plan_service.get_care_plan(plan_id)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404
    raw = care_plan_service._get_plan_or_raise(plan_id)
    claims = get_jwt()
    if not care_plan_service.check_access(get_jwt_identity(), claims.get("role", ""), plan=raw):
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403
    return jsonify(plan.model_dump()), 200


@bp.route("/<plan_id>", methods=["PUT"])
@jwt_required()
@require_role(["doctor", "admin"])
def update_care_plan(plan_id: str):
    try:
        data = UpdateCarePlanRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    try:
        plan = care_plan_service.update_care_plan(plan_id, data)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404
    return jsonify(plan.model_dump()), 200


@bp.route("/<plan_id>/goals", methods=["POST"])
@jwt_required()
@require_role(["doctor", "admin"])
def add_goal(plan_id: str):
    try:
        data = AddGoalRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    try:
        goal = care_plan_service.add_goal(plan_id, data)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404
    return jsonify(goal.model_dump()), 201


@bp.route("/goals/<goal_id>", methods=["PUT"])
@jwt_required()
@require_role(["doctor", "admin"])
def update_goal(goal_id: str):
    try:
        data = UpdateGoalRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    try:
        goal = care_plan_service.update_goal(goal_id, data)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404
    return jsonify(goal.model_dump()), 200


@bp.route("/generate", methods=["POST"])
@jwt_required()
@require_role(["doctor", "admin"])
def generate_care_plan():
    body = request.get_json() or {}
    patient_id = body.get("patient_id")
    if not patient_id:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "patient_id is required"}}), 400
    return jsonify({"message": "AI care plan generation queued", "patient_id": patient_id, "status": "pending"}), 202


@bp.route("/<plan_id>/adherence", methods=["GET"])
@jwt_required()
@require_role(["patient", "doctor", "nurse", "admin"])
def get_adherence(plan_id: str):
    try:
        adherence = care_plan_service.get_adherence(plan_id)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404
    return jsonify(adherence.model_dump()), 200
