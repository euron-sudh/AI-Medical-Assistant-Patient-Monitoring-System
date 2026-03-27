"""Notifications API endpoints — list, mark read, and manage notifications.

Routes:
    GET  /api/v1/notifications              — List user's notifications
    PUT  /api/v1/notifications/<id>/read     — Mark a notification as read
    PUT  /api/v1/notifications/read-all      — Mark all notifications as read
    GET  /api/v1/notifications/unread-count  — Get unread notification count
"""

import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.services.notification_service import notification_service

bp = Blueprint("notifications", __name__, url_prefix="/api/v1/notifications")


@bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    """List notifications for the current user.

    Query params:
        unread_only: If 'true', only return unread notifications.
        limit: Maximum number of notifications (default 50, max 200).
        offset: Number of notifications to skip (default 0).
    """
    current_user_id = uuid.UUID(get_jwt_identity())

    unread_only = request.args.get("unread_only", "false").lower() == "true"
    limit = request.args.get("limit", 50, type=int)
    limit = min(max(limit, 1), 200)
    offset = request.args.get("offset", 0, type=int)
    offset = max(offset, 0)

    notifications = notification_service.get_user_notifications(
        user_id=current_user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )

    return jsonify([n.model_dump(mode="json") for n in notifications]), 200


@bp.route("/<notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_notification_read(notification_id: str):
    """Mark a single notification as read."""
    current_user_id = uuid.UUID(get_jwt_identity())

    try:
        notif_uuid = uuid.UUID(notification_id)
    except ValueError:
        return jsonify({
            "error": {"code": "BAD_REQUEST", "message": "Invalid notification ID"}
        }), 400

    result = notification_service.mark_as_read(notif_uuid, current_user_id)

    if result is None:
        return jsonify({
            "error": {"code": "NOT_FOUND", "message": "Notification not found"}
        }), 404

    return jsonify(result.model_dump(mode="json")), 200


@bp.route("/read-all", methods=["PUT"])
@jwt_required()
def mark_all_notifications_read():
    """Mark all unread notifications as read for the current user."""
    current_user_id = uuid.UUID(get_jwt_identity())

    count = notification_service.mark_all_as_read(current_user_id)

    return jsonify({"updated_count": count}), 200


@bp.route("/unread-count", methods=["GET"])
@jwt_required()
def get_unread_count():
    """Get the count of unread notifications for the current user."""
    current_user_id = uuid.UUID(get_jwt_identity())

    count = notification_service.get_unread_count(current_user_id)

    return jsonify({"unread_count": count}), 200


@bp.route("/bulk", methods=["POST"])
@jwt_required()
def create_bulk_notifications():
    """Create notifications for multiple users at once.

    Requires admin role. Accepts JSON body with:
        user_ids: List of user ID strings.
        type: Notification type.
        title: Notification title.
        message: Notification body.
        data: Optional JSON payload.
        channel: Delivery channel (default: in_app).
    """
    claims = get_jwt()
    role = claims.get("role", "")

    if role != "admin":
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Only admins can create bulk notifications"}
        }), 403

    body = request.get_json()
    if not body:
        return jsonify({
            "error": {"code": "BAD_REQUEST", "message": "Request body is required"}
        }), 400

    user_ids = body.get("user_ids")
    if not user_ids or not isinstance(user_ids, list):
        return jsonify({
            "error": {"code": "BAD_REQUEST", "message": "'user_ids' must be a non-empty list"}
        }), 400

    notif_type = body.get("type")
    title = body.get("title")
    message = body.get("message")

    if not all([notif_type, title, message]):
        return jsonify({
            "error": {"code": "BAD_REQUEST", "message": "'type', 'title', and 'message' are required"}
        }), 400

    # Validate all user_ids are valid UUIDs
    for uid in user_ids:
        try:
            uuid.UUID(uid)
        except (ValueError, AttributeError):
            return jsonify({
                "error": {"code": "BAD_REQUEST", "message": f"Invalid user ID: {uid}"}
            }), 400

    try:
        notifications = notification_service.create_bulk_notifications(
            user_ids=user_ids,
            type=notif_type,
            title=title,
            message=message,
            data=body.get("data"),
            channel=body.get("channel", "in_app"),
        )
    except Exception as e:
        return jsonify({
            "error": {"code": "INTERNAL_ERROR", "message": str(e)}
        }), 500

    return jsonify({
        "created_count": len(notifications),
        "notifications": [n.model_dump(mode="json") for n in notifications],
    }), 201

