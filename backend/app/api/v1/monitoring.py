"""Monitoring API endpoints — monitoring wall, alerts, and thresholds.

Routes:
    GET  /api/v1/monitoring/patients
    GET  /api/v1/monitoring/patients/<id>/status
    GET  /api/v1/monitoring/alerts
    PUT  /api/v1/monitoring/alerts/<id>/acknowledge
    PUT  /api/v1/monitoring/alerts/<id>/resolve
    PUT  /api/v1/monitoring/alerts/<id>/escalate
    POST /api/v1/monitoring/thresholds/<patient_id>
"""

import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.schemas.monitoring_schema import AlertsListParams, MonitoringThresholdsRequest, ResolveAlertRequest
from app.services.monitoring_service import monitoring_service

bp = Blueprint("monitoring", __name__, url_prefix="/api/v1/monitoring")


def _viewer() -> tuple[uuid.UUID, str]:
    claims = get_jwt()
    role = claims.get("role", "")
    viewer_id = uuid.UUID(get_jwt_identity())
    return viewer_id, role


@bp.route("/patients", methods=["GET"])
@jwt_required()
def list_monitored_patients():
    viewer_id, role = _viewer()
    items = monitoring_service.list_monitored_patients(viewer_id, role)
    return jsonify(items), 200


@bp.route("/patients/<patient_id>/status", methods=["GET"])
@jwt_required()
def get_patient_status(patient_id: str):
    viewer_id, role = _viewer()
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    result = monitoring_service.get_patient_status(viewer_id, role, patient_uuid)
    if result is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Patient not found or not accessible"}}), 404
    return jsonify(result), 200


@bp.route("/alerts", methods=["GET"])
@jwt_required()
def list_alerts():
    viewer_id, role = _viewer()

    params: dict = {
        "severity": request.args.get("severity"),
        "patient_id": request.args.get("patient_id"),
        "status": request.args.get("status"),
        "limit": request.args.get("limit", 50, type=int),
        "offset": request.args.get("offset", 0, type=int),
    }

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

    try:
        parsed = AlertsListParams.model_validate(params)
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    patient_uuid = None
    if parsed.patient_id:
        try:
            patient_uuid = uuid.UUID(parsed.patient_id)
        except ValueError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient_id"}}), 400

    alerts = monitoring_service.list_alerts(
        viewer_user_id=viewer_id,
        viewer_role=role,
        severity=parsed.severity,
        patient_id=patient_uuid,
        status=parsed.status,
        start_date=parsed.start_date,
        end_date=parsed.end_date,
        limit=parsed.limit,
        offset=parsed.offset,
    )
    return jsonify(alerts), 200


@bp.route("/alerts/<alert_id>/acknowledge", methods=["PUT"])
@jwt_required()
def acknowledge_alert(alert_id: str):
    viewer_id, role = _viewer()
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid alert ID"}}), 400

    alert = monitoring_service.acknowledge_alert(viewer_id, role, alert_uuid)
    if alert is None:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Not allowed or alert not found"}}), 403
    return jsonify({
        "id": str(alert.id),
        "status": alert.status,
        "acknowledged_by": str(alert.acknowledged_by) if alert.acknowledged_by else None,
        "acknowledged_at": alert.acknowledged_at,
    }), 200


@bp.route("/alerts/<alert_id>/resolve", methods=["PUT"])
@jwt_required()
def resolve_alert(alert_id: str):
    viewer_id, role = _viewer()
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid alert ID"}}), 400

    try:
        data = ResolveAlertRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        alert = monitoring_service.resolve_alert(viewer_id, role, alert_uuid, data.resolution_notes)
    except ValueError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(e)}}), 400

    if alert is None:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Not allowed or alert not found"}}), 403

    return jsonify({
        "id": str(alert.id),
        "status": alert.status,
        "resolved_by": str(alert.resolved_by) if alert.resolved_by else None,
        "resolved_at": alert.resolved_at,
        "resolution_notes": alert.resolution_notes,
    }), 200


@bp.route("/alerts/<alert_id>/escalate", methods=["PUT"])
@jwt_required()
def escalate_alert(alert_id: str):
    viewer_id, role = _viewer()
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid alert ID"}}), 400

    alert = monitoring_service.escalate_alert(viewer_id, role, alert_uuid)
    if alert is None:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Not allowed or alert not found"}}), 403

    return jsonify({
        "id": str(alert.id),
        "escalation_level": alert.escalation_level,
        "escalated_at": alert.escalated_at,
    }), 200


@bp.route("/thresholds/<patient_id>", methods=["POST"])
@jwt_required()
def set_thresholds(patient_id: str):
    viewer_id, role = _viewer()
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    try:
        data = MonitoringThresholdsRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    row = monitoring_service.set_thresholds(viewer_id, role, patient_uuid, data.thresholds)
    if row is None:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Not allowed"}}), 403

    return jsonify({
        "patient_id": str(row.patient_id),
        "thresholds": row.thresholds or {},
        "updated_by": str(row.updated_by),
        "updated_at": row.updated_at,
    }), 200

