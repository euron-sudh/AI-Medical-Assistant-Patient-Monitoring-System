"""Admin API endpoints for user management, audit logs, and analytics."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt

from app.extensions import db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation
from app.models.alert import MonitoringAlert

bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")
monitoring_bp = Blueprint("monitoring", __name__, url_prefix="/api/v1/monitoring")


def _require_admin():
    """Check that the current user has admin role."""
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Admin access required"}}), 403
    return None


@bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    """List all users with optional role filter."""
    err = _require_admin()
    if err:
        return err

    role = request.args.get("role")
    query = User.query
    if role:
        query = query.filter_by(role=role)
    query = query.order_by(User.created_at.desc())

    users = query.all()
    return jsonify({
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": u.role,
                "phone": u.phone,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
        "total": len(users),
    }), 200


@bp.route("/audit-logs", methods=["GET"])
@jwt_required()
def list_audit_logs():
    """List audit logs with optional filters."""
    err = _require_admin()
    if err:
        return err

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    action = request.args.get("action")

    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    if action:
        query = query.filter_by(action=action)

    logs = query.limit(per_page).offset((page - 1) * per_page).all()
    total = query.count()

    # Fetch user names for display
    user_ids = {str(log.user_id) for log in logs}
    users_map = {}
    if user_ids:
        users = User.query.filter(User.id.in_(user_ids)).all()
        users_map = {str(u.id): f"{u.first_name} {u.last_name}" for u in users}

    return jsonify({
        "logs": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "user_name": users_map.get(str(log.user_id), "Unknown"),
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "patient_id": str(log.patient_id) if log.patient_id else None,
                "ip_address": log.ip_address,
                "request_method": log.request_method,
                "request_path": log.request_path,
                "status_code": log.status_code,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }), 200


@bp.route("/analytics/ai-usage", methods=["GET"])
@jwt_required()
def ai_usage_analytics():
    """Return AI usage analytics for the admin dashboard."""
    err = _require_admin()
    if err:
        return err

    total_conversations = Conversation.query.count()
    active_conversations = Conversation.query.filter_by(status="active").count()

    # Count by agent type
    agent_types = db.session.query(
        Conversation.agent_type, db.func.count(Conversation.id)
    ).group_by(Conversation.agent_type).all()

    return jsonify({
        "total_conversations": total_conversations,
        "active_conversations": active_conversations,
        "by_agent_type": {atype: count for atype, count in agent_types},
        "total_users": User.query.count(),
        "total_patients": User.query.filter_by(role="patient").count(),
        "total_doctors": User.query.filter_by(role="doctor").count(),
    }), 200


# ── Monitoring alerts (shared helper) ─────────────────────────────────────

def _get_alerts_response(require_admin_role=True):
    """Shared logic for monitoring alerts."""
    if require_admin_role:
        err = _require_admin()
        if err:
            return err

    status = request.args.get("status")
    query = MonitoringAlert.query.order_by(MonitoringAlert.created_at.desc())
    if status:
        query = query.filter_by(status=status)

    alerts = query.all()

    patient_ids = {str(a.patient_id) for a in alerts}
    patients_map = {}
    if patient_ids:
        users = User.query.filter(User.id.in_(patient_ids)).all()
        patients_map = {str(u.id): f"{u.first_name} {u.last_name}" for u in users}

    return jsonify({
        "alerts": [
            {
                "id": str(a.id),
                "patient_id": str(a.patient_id),
                "patient_name": patients_map.get(str(a.patient_id), "Unknown"),
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "status": a.status,
                "escalation_level": a.escalation_level,
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
        "total": len(alerts),
    }), 200


@bp.route("/monitoring/alerts", methods=["GET"])
@jwt_required()
def admin_monitoring_alerts():
    return _get_alerts_response(require_admin_role=True)


@monitoring_bp.route("/alerts", methods=["GET"])
@jwt_required()
def monitoring_alerts():
    return _get_alerts_response(require_admin_role=False)
