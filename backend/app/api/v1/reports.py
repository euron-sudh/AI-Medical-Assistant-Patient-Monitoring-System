"""Reports API endpoints — upload, read, analyze, and manage medical reports.

Routes:
    GET    /api/v1/reports/<patient_id>                        — List patient reports
    POST   /api/v1/reports/<patient_id>/upload                 — Upload a report (JSON)
    POST   /api/v1/reports/upload                              — Upload a report (multipart file)
    GET    /api/v1/reports/<patient_id>/<report_id>            — Get report details
    GET    /api/v1/reports/<report_id>/download                — Get presigned download URL
    POST   /api/v1/reports/<patient_id>/<report_id>/analyze    — Trigger AI analysis
    GET    /api/v1/reports/<patient_id>/<report_id>/lab-values — Get lab values
    GET    /api/v1/reports/<patient_id>/<report_id>/summary    — Get AI summary
    DELETE /api/v1/reports/<patient_id>/<report_id>            — Delete report
"""

import logging
import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.schemas.report_schema import (
    CreateLabValueRequest,
    CreateReportRequest,
    ReportListParams,
)
from app.services.report_service import report_service

logger = logging.getLogger(__name__)

bp = Blueprint("reports", __name__, url_prefix="/api/v1/reports")


def _check_patient_access(patient_id: str) -> tuple | None:
    """Verify the current user can access this patient's reports.

    Returns an error tuple (response, status_code) if access is denied, or None if allowed.
    """
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    role = claims.get("role")

    if role == "patient" and str(current_user_id) != str(patient_id):
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Cannot access other patient's reports"}
        }), 403

    return None


# ---------------------------------------------------------------------------
# Task #30 — Direct file upload (multipart)
# ---------------------------------------------------------------------------

@bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_report_file():
    """Upload a medical report as a multipart file.

    Accepts multipart/form-data with:
        - file: The report file (required)
        - patient_id: UUID of the patient (required)
        - report_type: One of lab, imaging, pathology, etc. (required)
        - title: Report title (required)

    The file is stored in S3 via s3_client, a MedicalReport record is created,
    and a Celery task is dispatched for async AI processing.

    Returns:
        201 with report_id and status.
    """
    # Validate file presence
    if "file" not in request.files:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "No file provided"}}), 400

    file = request.files["file"]
    if file.filename == "" or file.filename is None:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Empty filename"}}), 400

    # Read form fields
    patient_id = request.form.get("patient_id")
    report_type = request.form.get("report_type")
    title = request.form.get("title")

    if not patient_id or not report_type or not title:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "patient_id, report_type, and title are required form fields",
            }
        }), 400

    # Validate patient_id
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    # Access check
    access_error = _check_patient_access(patient_id)
    if access_error:
        return access_error

    # Determine file type from extension
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"

    file_bytes = file.read()
    file_url = None

    # Try S3 upload first, fall back to local storage if S3 is unavailable
    try:
        from app.integrations.s3_client import s3_client
        file_url = s3_client.upload_file(file_bytes, patient_id, file_ext)
    except Exception as s3_err:
        logger.warning("S3 upload failed, falling back to local storage: %s", s3_err)
        # Store locally as fallback
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "uploads", "reports", patient_id,
        )
        os.makedirs(upload_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        unique = uuid.uuid4().hex[:12]
        filename = f"{ts}_{unique}.{file_ext}"
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(file_bytes)
        file_url = f"local://{filepath}"
        logger.info("File stored locally at %s", filepath)

    # Create report record via service
    current_user_id = uuid.UUID(get_jwt_identity())
    report_data = CreateReportRequest(
        report_type=report_type,
        title=title,
        file_url=file_url,
        file_type=file_ext,
    )
    report = report_service.create_report(patient_uuid, report_data, created_by=current_user_id)

    # Try to dispatch async processing (may fail if Celery/Redis not running)
    try:
        from app.tasks.report_processing import process_medical_report
        process_medical_report.delay(report.id)
    except Exception as celery_err:
        logger.warning("Celery task dispatch failed (report will need manual analysis): %s", celery_err)

    return jsonify({
        "report_id": report.id,
        "status": report.status,
        "file_url": report.file_url,
        "message": "Report uploaded successfully. Processing has been queued.",
    }), 201


# ---------------------------------------------------------------------------
# Task #30 — Presigned download URL
# ---------------------------------------------------------------------------

@bp.route("/<report_id>/download", methods=["GET"])
@jwt_required()
def download_report(report_id: str):
    """Get a presigned URL to download a report file.

    Args:
        report_id: UUID of the report.

    Returns:
        200 with download_url (presigned, 15 min expiry).
    """
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid report ID"}}), 400

    report = report_service.get_report(report_uuid)
    if report is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Report not found"}}), 404

    # Access check — use patient_id from the report
    access_error = _check_patient_access(report.patient_id)
    if access_error:
        return access_error

    if not report.file_url:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Report has no associated file"}}), 400

    from app.integrations.s3_client import s3_client

    download_url = s3_client.generate_presigned_url(report.file_url, expiry=900)

    return jsonify({
        "report_id": report.id,
        "download_url": download_url,
        "expires_in": 900,
    }), 200


# ---------------------------------------------------------------------------
# Existing endpoints
# ---------------------------------------------------------------------------

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
