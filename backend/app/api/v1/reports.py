"""Reports API endpoints — upload, read, analyze, and manage medical reports.

Routes:
    GET    /api/v1/reports/<patient_id>                        — List patient reports
    POST   /api/v1/reports/<patient_id>/upload                 — Upload a report
    GET    /api/v1/reports/<patient_id>/<report_id>            — Get report details
    POST   /api/v1/reports/<patient_id>/<report_id>/analyze    — Trigger AI analysis
    GET    /api/v1/reports/<patient_id>/<report_id>/lab-values — Get lab values
    GET    /api/v1/reports/<patient_id>/<report_id>/summary    — Get AI summary
    DELETE /api/v1/reports/<patient_id>/<report_id>            — Delete report
"""

import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.schemas.report_schema import (
    CreateLabValueRequest,
    CreateReportRequest,
    ReportListParams,
)
from app.services.report_service import report_service

bp = Blueprint("reports", __name__, url_prefix="/api/v1/reports")


def _check_patient_access(patient_id: str) -> tuple | None:
    """Verify the current user can access this patient's reports.

    Returns an error tuple (response, status_code) if access is denied, or None if allowed.
    """
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    role = claims.get("role")

    if role == "patient" and current_user_id != patient_id:
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Cannot access other patient's reports"}
        }), 403

    return None


@bp.route("/<patient_id>", methods=["GET"])
@jwt_required()
def list_reports(patient_id: str):
    """List medical reports for a patient."""
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    try:
        params = ReportListParams.model_validate({
            "report_type": request.args.get("report_type"),
            "status": request.args.get("status"),
            "limit": request.args.get("limit", 50, type=int),
            "offset": request.args.get("offset", 0, type=int),
        })
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    reports = report_service.get_patient_reports(
        patient_uuid,
        report_type=params.report_type,
        status=params.status,
        limit=params.limit,
        offset=params.offset,
    )
    return jsonify([r.model_dump(mode="json") for r in reports]), 200


@bp.route("/<patient_id>/upload", methods=["POST"])
@jwt_required()
def upload_report(patient_id: str):
    """Upload a new medical report for a patient."""
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        data = CreateReportRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    current_user_id = uuid.UUID(get_jwt_identity())
    report = report_service.create_report(patient_uuid, data, created_by=current_user_id)
    return jsonify(report.model_dump(mode="json")), 201


@bp.route("/<patient_id>/<report_id>", methods=["GET"])
@jwt_required()
def get_report(patient_id: str, report_id: str):
    """Get a specific report with AI analysis details."""
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid report ID"}}), 400

    report = report_service.get_report(report_uuid)
    if report is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Report not found"}}), 404

    if report.patient_id != patient_id:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Report does not belong to this patient"}}), 403

    return jsonify(report.model_dump(mode="json")), 200


@bp.route("/<patient_id>/<report_id>/analyze", methods=["POST"])
@jwt_required()
def trigger_analysis(patient_id: str, report_id: str):
    """Trigger AI analysis for a report."""
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid report ID"}}), 400

    report = report_service.trigger_analysis(report_uuid)
    if report is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Report not found"}}), 404

    return jsonify(report.model_dump(mode="json")), 200


@bp.route("/<patient_id>/<report_id>/lab-values", methods=["GET"])
@jwt_required()
def get_lab_values(patient_id: str, report_id: str):
    """Get extracted lab values for a report."""
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid report ID"}}), 400

    lab_values = report_service.get_report_lab_values(report_uuid)
    return jsonify([lv.model_dump(mode="json") for lv in lab_values]), 200


@bp.route("/<patient_id>/<report_id>/summary", methods=["GET"])
@jwt_required()
def get_report_summary(patient_id: str, report_id: str):
    """Get the AI-generated summary for a report."""
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid report ID"}}), 400

    report = report_service.get_report(report_uuid)
    if report is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Report not found"}}), 404

    return jsonify({
        "report_id": report.id,
        "ai_summary": report.ai_summary,
        "status": report.status,
    }), 200


@bp.route("/<patient_id>/<report_id>", methods=["DELETE"])
@jwt_required()
def delete_report(patient_id: str, report_id: str):
    """Delete a medical report."""
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid report ID"}}), 400

    deleted = report_service.delete_report(report_uuid)
    if not deleted:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Report not found"}}), 404

    return "", 204
