"""Appointments API endpoints — CRUD, availability, and scheduling.

Routes:
    GET  /api/v1/appointments                          — List appointments
    POST /api/v1/appointments                          — Create appointment
    GET  /api/v1/appointments/<id>                     — Get by ID
    PUT  /api/v1/appointments/<id>                     — Update
    PUT  /api/v1/appointments/<id>/cancel               — Cancel
    GET  /api/v1/appointments/availability/<doctor_id>  — Doctor availability
    GET  /api/v1/appointments/upcoming/<patient_id>     — Upcoming
"""

import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError

from app.schemas.appointment_schema import (
    AppointmentListParams,
    CancelAppointmentRequest,
    ConfirmAppointmentRequest,
    CreateAppointmentRequest,
    RecurringAppointmentRequest,
    UpdateAppointmentRequest,
)
from app.services.appointment_service import appointment_service

bp = Blueprint("appointments", __name__, url_prefix="/api/v1/appointments")


@bp.route("", methods=["GET"])
@jwt_required()
def list_appointments():
    """List appointments scoped by authenticated user's role."""
    claims = get_jwt()
    current_user_id = uuid.UUID(get_jwt_identity())
    role = claims.get("role", "")

    params: dict = {}
    if request.args.get("status"):
        params["status"] = request.args["status"]
    if request.args.get("appointment_type"):
        params["appointment_type"] = request.args["appointment_type"]
    if request.args.get("start_date"):
        try:
            params["start_date"] = datetime.fromisoformat(request.args["start_date"])
        except ValueError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid start_date"}}), 400
    if request.args.get("end_date"):
        try:
            params["end_date"] = datetime.fromisoformat(request.args["end_date"])
        except ValueError:
            return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid end_date"}}), 400

    params["limit"] = request.args.get("limit", 50, type=int)
    params["offset"] = request.args.get("offset", 0, type=int)

    try:
        list_params = AppointmentListParams.model_validate(params)
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    appointments = appointment_service.list_appointments(
        user_id=current_user_id,
        role=role,
        status=list_params.status,
        appointment_type=list_params.appointment_type,
        start_date=list_params.start_date,
        end_date=list_params.end_date,
        limit=list_params.limit,
        offset=list_params.offset,
    )
    return jsonify([a.model_dump(mode="json") for a in appointments]), 200


@bp.route("", methods=["POST"])
@jwt_required()
def create_appointment():
    """Create a new appointment."""
    try:
        data = CreateAppointmentRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    claims = get_jwt()
    current_user_id = uuid.UUID(get_jwt_identity())
    role = claims.get("role", "")

    if role == "patient" and data.patient_id != str(current_user_id):
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Patients can only book their own appointments"}
        }), 403

    try:
        appointment = appointment_service.create_appointment(data, created_by=current_user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409

    return jsonify(appointment.model_dump(mode="json")), 201


@bp.route("/<appointment_id>", methods=["GET"])
@jwt_required()
def get_appointment(appointment_id: str):
    """Get appointment details by ID."""
    try:
        appt_uuid = uuid.UUID(appointment_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid appointment ID"}}), 400

    claims = get_jwt()
    current_user_id = uuid.UUID(get_jwt_identity())
    role = claims.get("role", "")

    if not appointment_service.check_appointment_access(appt_uuid, current_user_id, role):
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403

    appointment = appointment_service.get_appointment(appt_uuid)
    if not appointment:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Appointment not found"}}), 404

    return jsonify(appointment.model_dump(mode="json")), 200


@bp.route("/<appointment_id>", methods=["PUT"])
@jwt_required()
def update_appointment(appointment_id: str):
    """Update an existing appointment."""
    try:
        appt_uuid = uuid.UUID(appointment_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid appointment ID"}}), 400

    claims = get_jwt()
    current_user_id = uuid.UUID(get_jwt_identity())
    role = claims.get("role", "")

    if not appointment_service.check_appointment_access(appt_uuid, current_user_id, role):
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403

    try:
        data = UpdateAppointmentRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        appointment = appointment_service.update_appointment(appt_uuid, data)
    except ValueError as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400

    return jsonify(appointment.model_dump(mode="json")), 200


@bp.route("/<appointment_id>/cancel", methods=["PUT"])
@jwt_required()
def cancel_appointment(appointment_id: str):
    """Cancel an appointment with a reason."""
    try:
        appt_uuid = uuid.UUID(appointment_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid appointment ID"}}), 400

    claims = get_jwt()
    current_user_id = uuid.UUID(get_jwt_identity())
    role = claims.get("role", "")

    if not appointment_service.check_appointment_access(appt_uuid, current_user_id, role):
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403

    try:
        data = CancelAppointmentRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        appointment = appointment_service.cancel_appointment_with_notification(
            appt_uuid, current_user_id, data
        )
    except ValueError as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400

    return jsonify(appointment.model_dump(mode="json")), 200


@bp.route("/availability/<doctor_id>", methods=["GET"])
@jwt_required()
def get_doctor_availability(doctor_id: str):
    """Get available time slots for a doctor on a given date."""
    try:
        doctor_uuid = uuid.UUID(doctor_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid doctor ID"}}), 400

    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "date query parameter is required"}}), 400

    try:
        date = datetime.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid date format"}}), 400

    slots = appointment_service.get_doctor_availability(doctor_uuid, date)
    return jsonify({"doctor_id": doctor_id, "date": date_str, "available_slots": slots}), 200


@bp.route("/upcoming/<patient_id>", methods=["GET"])
@jwt_required()
def get_upcoming_appointments(patient_id: str):
    """Get upcoming appointments for a patient."""
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    claims = get_jwt()
    current_user_id = uuid.UUID(get_jwt_identity())
    role = claims.get("role", "")

    if role == "patient" and str(current_user_id) != patient_id:
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403

    limit = request.args.get("limit", 10, type=int)
    appointments = appointment_service.get_upcoming(patient_uuid, limit=min(limit, 50))
    return jsonify([a.model_dump(mode="json") for a in appointments]), 200


@bp.route("/check-availability", methods=["POST"])
@jwt_required()
def check_availability():
    """Check doctor availability before booking an appointment."""
    body = request.get_json()
    if not body:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Request body is required"}}), 400
    doctor_id_str = body.get("doctor_id")
    scheduled_at_str = body.get("scheduled_at")
    duration_minutes = body.get("duration_minutes", 30)
    if not doctor_id_str or not scheduled_at_str:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "doctor_id and scheduled_at are required"}}), 400
    try:
        doctor_uuid = uuid.UUID(doctor_id_str)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid doctor ID"}}), 400
    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_str)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid scheduled_at format"}}), 400
    result = appointment_service.check_doctor_availability(doctor_uuid, scheduled_at, duration_minutes)
    return jsonify(result), 200


@bp.route("/<appointment_id>/confirm", methods=["PUT"])
@jwt_required()
def confirm_appointment(appointment_id: str):
    """Confirm a scheduled appointment and send notification."""
    try:
        appt_uuid = uuid.UUID(appointment_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid appointment ID"}}), 400
    claims = get_jwt()
    current_user_id = uuid.UUID(get_jwt_identity())
    role = claims.get("role", "")
    if not appointment_service.check_appointment_access(appt_uuid, current_user_id, role):
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403
    try:
        data = ConfirmAppointmentRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    try:
        appointment = appointment_service.confirm_appointment(appt_uuid, current_user_id, send_notification=data.send_notification)
    except ValueError as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400
    return jsonify(appointment.model_dump(mode="json")), 200


@bp.route("/recurring", methods=["POST"])
@jwt_required()
def create_recurring_appointments():
    """Create a series of recurring appointments."""
    try:
        data = RecurringAppointmentRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400
    claims = get_jwt()
    current_user_id = uuid.UUID(get_jwt_identity())
    role = claims.get("role", "")
    if role == "patient" and data.patient_id != str(current_user_id):
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Patients can only book their own appointments"}}), 403
    try:
        appointments = appointment_service.create_recurring_appointments(data, created_by=current_user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409
    return jsonify([a.model_dump(mode="json") for a in appointments]), 201
