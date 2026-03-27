"""Socket.IO event handlers for real-time vitals streaming.

Events
------
- **connect** / **disconnect** -- lifecycle hooks with logging.
- **subscribe_patient_vitals** -- join a per-patient room so the client
  receives live readings and alerts for that patient only.
- **unsubscribe_patient_vitals** -- leave the patient room.
- **new_vitals_reading** -- broadcast a new vitals reading to all
  subscribers of the patient.
- **vitals_alert** -- broadcast a vitals alert to all subscribers of
  the patient.

All events live in the ``/vitals`` Socket.IO namespace.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

logger = logging.getLogger(__name__)

NAMESPACE = "/vitals"


def _patient_room(patient_id: str) -> str:
    """Return a canonical room name for a given patient."""
    return f"patient:{patient_id}"


def register_vitals_handlers(sio: SocketIO) -> None:
    """Attach vitals-streaming Socket.IO event handlers."""

    @sio.on("connect", namespace=NAMESPACE)
    def handle_connect(auth: dict | None = None) -> None:
        """Authenticate WebSocket connections via JWT token.

        The client must provide a token either in the auth dict ({"token": "..."})
        or as a query parameter (?token=...).
        """
        token = None
        if auth and isinstance(auth, dict):
            token = auth.get("token")
        if not token:
            token = request.args.get("token")
        if not token:
            logger.warning("WebSocket connection rejected — no auth token provided")
            disconnect()
            return
        try:
            decoded = decode_token(token)
            if decoded.get("type") != "access":
                raise ValueError("Not an access token")
        except Exception as e:
            logger.warning("WebSocket connection rejected — invalid token: %s", e)
            disconnect()
            return

        sid = request.sid
        logger.info("Client connected to /vitals  sid=%s  user=%s", sid, decoded.get("sub"))
        emit("connected", {"status": "ok", "sid": sid})

    @sio.on("disconnect", namespace=NAMESPACE)
    def handle_disconnect() -> None:
        sid = request.sid
        logger.info("Client disconnected from /vitals  sid=%s", sid)

    @sio.on("subscribe_patient_vitals", namespace=NAMESPACE)
    def handle_subscribe(data: dict) -> None:
        patient_id = data.get("patient_id")
        if not patient_id:
            emit("error", {"message": "patient_id is required"})
            return
        room = _patient_room(patient_id)
        join_room(room)
        logger.info("sid=%s subscribed to patient=%s", request.sid, patient_id)
        emit("subscribed", {"patient_id": patient_id, "room": room})

    @sio.on("unsubscribe_patient_vitals", namespace=NAMESPACE)
    def handle_unsubscribe(data: dict) -> None:
        patient_id = data.get("patient_id")
        if not patient_id:
            emit("error", {"message": "patient_id is required"})
            return
        room = _patient_room(patient_id)
        leave_room(room)
        logger.info("sid=%s unsubscribed from patient=%s", request.sid, patient_id)
        emit("unsubscribed", {"patient_id": patient_id})

    @sio.on("new_vitals_reading", namespace=NAMESPACE)
    def handle_new_vitals_reading(data: dict) -> None:
        patient_id = data.get("patient_id")
        if not patient_id:
            emit("error", {"message": "patient_id is required"})
            return
        reading = data.get("reading", {})
        room = _patient_room(patient_id)
        payload = {
            "patient_id": patient_id,
            "reading": reading,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        sio.emit("vitals_update", payload, room=room, namespace=NAMESPACE)
        logger.info("Broadcast new vitals reading for patient=%s", patient_id)

    @sio.on("vitals_alert", namespace=NAMESPACE)
    def handle_vitals_alert(data: dict) -> None:
        patient_id = data.get("patient_id")
        if not patient_id:
            emit("error", {"message": "patient_id is required"})
            return
        alert = data.get("alert", {})
        room = _patient_room(patient_id)
        payload = {
            "patient_id": patient_id,
            "alert": alert,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        sio.emit("vitals_alert_notification", payload, room=room, namespace=NAMESPACE)
        logger.info("Broadcast vitals alert for patient=%s severity=%s",
                     patient_id, alert.get("severity", "unknown"))


def broadcast_vitals_update(sio: SocketIO, patient_id: str, reading: dict) -> None:
    """Emit a vitals update from outside a Socket.IO handler."""
    room = _patient_room(patient_id)
    payload = {
        "patient_id": patient_id,
        "reading": reading,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    sio.emit("vitals_update", payload, room=room, namespace=NAMESPACE)


def broadcast_vitals_alert(sio: SocketIO, patient_id: str, alert: dict) -> None:
    """Emit a vitals alert from outside a Socket.IO handler."""
    room = _patient_room(patient_id)
    payload = {
        "patient_id": patient_id,
        "alert": alert,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    sio.emit("vitals_alert_notification", payload, room=room, namespace=NAMESPACE)
