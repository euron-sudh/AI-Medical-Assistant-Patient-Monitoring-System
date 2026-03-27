"""Analytics endpoints for dashboards."""

import uuid
from flask import Blueprint, jsonify

from app.middleware.auth_middleware import require_auth, require_role
from app.services.analytics_service import analytics_service

bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


@bp.route("/patient/<uuid:patient_id>/overview", methods=["GET"])
@require_auth
def get_patient_overview(patient_id: uuid.UUID):
    """Get patient health analytics overview."""
    # Note: In a real app, we would add authorization checks to ensure the user
    # can access this patient's data (e.g. is the patient themselves, or their assigned doctor)
    data = analytics_service.get_patient_overview(patient_id)
    return jsonify(data), 200


@bp.route("/doctor/<uuid:doctor_id>/overview", methods=["GET"])
@require_role(["doctor", "admin"])
def get_doctor_overview(doctor_id: uuid.UUID):
    """Get doctor metrics overview."""
    data = analytics_service.get_doctor_overview(doctor_id)
    return jsonify(data), 200


@bp.route("/system/overview", methods=["GET"])
@require_role(["admin"])
def get_system_overview():
    """Get system-wide metrics overview."""
    data = analytics_service.get_system_overview()
    return jsonify(data), 200


@bp.route("/ai/usage", methods=["GET"])
@require_role(["admin"])
def get_ai_usage():
    """Get AI usage stats."""
    data = analytics_service.get_ai_usage()
    return jsonify(data), 200
