"""Devices API endpoints — manage IoT device registry and ingest device vitals."""

import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from pydantic import ValidationError

from app.schemas.device_schema import (
    DeviceVitalsIngestItem,
    DeviceVitalsBatchRequest,
    RegisterDeviceRequest,
    SyncDeviceRequest,
    UpdateDeviceRequest,
)
from app.services.device_service import device_service

bp = Blueprint("devices", __name__, url_prefix="/api/v1/devices")


def _viewer():
    claims = get_jwt()
    role = claims.get("role", "")
    viewer_id = uuid.UUID(get_jwt_identity())
    return viewer_id, role


@bp.route("/<patient_id>", methods=["GET"])
@jwt_required()
def list_patient_devices(patient_id: str):
    viewer_id, role = _viewer()
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    items = device_service.list_patient_devices(viewer_id, role, patient_uuid)
    return jsonify(items), 200


@bp.route("/<patient_id>", methods=["POST"])
@jwt_required()
def register_device(patient_id: str):
    viewer_id, role = _viewer()
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid patient ID"}}), 400

    try:
        data = RegisterDeviceRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        device = device_service.register_device(viewer_id, role, patient_uuid, data)
    except PermissionError as e:
        return jsonify({"error": {"code": "FORBIDDEN", "message": str(e)}}), 403

    return jsonify(device_service._device_to_dict(device)), 201


@bp.route("/<device_id>", methods=["PUT"])
@jwt_required()
def update_device(device_id: str):
    viewer_id, role = _viewer()
    try:
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid device ID"}}), 400

    try:
        data = UpdateDeviceRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    device = device_service.update_device(viewer_id, role, device_uuid, data)
    if device is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Device not found or not accessible"}}), 404

    return jsonify(device_service._device_to_dict(device)), 200


@bp.route("/<device_id>", methods=["DELETE"])
@jwt_required()
def retire_device(device_id: str):
    viewer_id, role = _viewer()
    try:
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid device ID"}}), 400

    device = device_service.retire_device(viewer_id, role, device_uuid)
    if device is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Device not found or not accessible"}}), 404

    return jsonify(device_service._device_to_dict(device)), 200


@bp.route("/<device_id>/sync", methods=["POST"])
@jwt_required()
def sync_device(device_id: str):
    """Record a sync event — update last_sync_at and optionally battery_level."""
    viewer_id, role = _viewer()
    try:
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid device ID"}}), 400

    try:
        data = SyncDeviceRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    device = device_service.sync_device(viewer_id, role, device_uuid, data.battery_level)
    if device is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Device not found or not accessible"}}), 404

    return jsonify(device_service._device_to_dict(device)), 200


@bp.route("/<device_id>/data", methods=["POST"])
@jwt_required()
def ingest_device_data(device_id: str):
    viewer_id, role = _viewer()
    try:
        device_uuid = uuid.UUID(device_id)
    except ValueError:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Invalid device ID"}}), 400

    payload = request.get_json()
    # Accept either {"items":[...]} or a raw list for convenience.
    try:
        if isinstance(payload, list):
            req = DeviceVitalsBatchRequest.model_validate({"items": payload})
        else:
            req = DeviceVitalsBatchRequest.model_validate(payload or {})
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        created = device_service.ingest_device_data(
            actor_id=viewer_id,
            actor_role=role,
            device_id=device_uuid,
            items=req.items,
        )
    except ValueError as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400

    if created is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Device not found or not accessible"}}), 404

    return jsonify([{"id": str(r.id), "recorded_at": r.recorded_at, "is_anomalous": r.is_anomalous} for r in created]), 201

