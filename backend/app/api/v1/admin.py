"""Admin API endpoints — user management, system health, AI config, audit logs.

Tasks #16, #17, #18 (Pallavi Sindkar):
    GET    /api/v1/admin/users                — List users (paginated, filterable)
    GET    /api/v1/admin/users/<id>           — Get user detail
    PATCH  /api/v1/admin/users/<id>           — Update user role/status
    POST   /api/v1/admin/users                — Create user (admin-only)
    GET    /api/v1/admin/system/health        — System health dashboard
    GET    /api/v1/admin/ai/config            — Current AI configuration
    PUT    /api/v1/admin/ai/config            — Update AI configuration
    GET    /api/v1/admin/audit-logs           — Paginated audit logs
    GET    /api/v1/admin/audit-logs/export    — Export audit logs as CSV
    GET    /api/v1/admin/analytics/ai-usage   — AI usage analytics
    GET    /api/v1/admin/monitoring/alerts     — Monitoring alerts
"""

import csv
import io
import time
import uuid
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation
from app.models.alert import MonitoringAlert
from app.models.vitals import VitalsReading
from app.models.appointment import Appointment
from app.models.notification import Notification

bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


def _require_admin():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Admin access required"}}), 403
    return None


def _log_audit(action: str, resource_type: str, resource_id=None, details=None):
    """Helper to create audit log entry."""
    try:
        log = AuditLog(
            user_id=get_jwt_identity(),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent", "")[:500],
            request_method=request.method,
            request_path=request.path,
            status_code=200,
            details=details,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


# ── Task #16: User Management ────────────────────────────────────────────────

@bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    """List all users with pagination, role filter, and search."""
    err = _require_admin()
    if err:
        return err

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    role = request.args.get("role")
    status = request.args.get("status")
    search = request.args.get("search", "").strip()

    query = User.query
    if role:
        query = query.filter_by(role=role)
    if status == "active":
        query = query.filter_by(is_active=True)
    elif status == "inactive":
        query = query.filter_by(is_active=False)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(User.email.ilike(like), User.first_name.ilike(like), User.last_name.ilike(like))
        )
    query = query.order_by(User.created_at.desc())
    total = query.count()
    users = query.limit(per_page).offset((page - 1) * per_page).all()

    return jsonify({
        "users": [_user_to_dict(u) for u in users],
        "total": total,
        "page": page,
        "per_page": per_page,
    }), 200


@bp.route("/users/<user_id>", methods=["GET"])
@jwt_required()
def get_user(user_id: str):
    """Get single user detail with activity summary."""
    err = _require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404

    data = _user_to_dict(user)
    # Activity summary
    data["activity"] = {
        "total_appointments": Appointment.query.filter(
            db.or_(Appointment.patient_id == user.id, Appointment.doctor_id == user.id)
        ).count(),
        "total_notifications": Notification.query.filter_by(user_id=user.id).count(),
        "total_conversations": Conversation.query.filter_by(patient_id=user.id).count(),
    }

    _log_audit("read", "user", resource_id=user.id)
    return jsonify(data), 200


@bp.route("/users/<user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id: str):
    """Update user role or active status (admin only)."""
    err = _require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404

    data = request.get_json() or {}
    changes = {}

    if "role" in data and data["role"] in ("patient", "doctor", "nurse", "admin"):
        changes["role"] = data["role"]
        user.role = data["role"]
    if "is_active" in data and isinstance(data["is_active"], bool):
        changes["is_active"] = data["is_active"]
        user.is_active = data["is_active"]

    if not changes:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "No valid fields to update"}}), 400

    db.session.commit()
    _log_audit("update", "user", resource_id=user.id, details={"changes": changes})
    return jsonify(_user_to_dict(user)), 200


@bp.route("/users", methods=["POST"])
@jwt_required()
def create_user():
    """Create a new user (admin can create doctors/nurses)."""
    err = _require_admin()
    if err:
        return err

    data = request.get_json() or {}
    required = ["email", "password", "first_name", "last_name", "role"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": f"Missing fields: {', '.join(missing)}"}}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": {"code": "CONFLICT", "message": "Email already registered"}}), 409

    user = User(
        email=data["email"],
        first_name=data["first_name"],
        last_name=data["last_name"],
        role=data["role"],
        phone=data.get("phone"),
        is_active=True,
        is_verified=True,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    _log_audit("create", "user", resource_id=user.id, details={"role": data["role"]})
    return jsonify(_user_to_dict(user)), 201


def _user_to_dict(u: User) -> dict:
    return {
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


# ── Task #17: System Health + AI Config ───────────────────────────────────────

@bp.route("/system/health", methods=["GET"])
@jwt_required()
def system_health():
    """Return health status of all dependencies."""
    err = _require_admin()
    if err:
        return err

    services = []

    # PostgreSQL
    try:
        start = time.time()
        db.session.execute(db.text("SELECT 1"))
        latency = int((time.time() - start) * 1000)
        services.append({"name": "postgresql", "status": "healthy", "latency_ms": latency})
    except Exception as e:
        services.append({"name": "postgresql", "status": "unhealthy", "error": str(e)})

    # Redis
    try:
        import redis
        from flask import current_app
        redis_url = current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, socket_timeout=3)
        start = time.time()
        r.ping()
        latency = int((time.time() - start) * 1000)
        services.append({"name": "redis", "status": "healthy", "latency_ms": latency})
    except Exception as e:
        services.append({"name": "redis", "status": "unhealthy", "error": str(e)[:100]})

    # OpenAI / EURI API
    try:
        from flask import current_app
        api_key = current_app.config.get("OPENAI_API_KEY", "")
        services.append({
            "name": "openai_api",
            "status": "healthy" if api_key else "not_configured",
            "model": current_app.config.get("OPENAI_MODEL_PRIMARY", "gpt-4o-mini"),
            "base_url": current_app.config.get("OPENAI_BASE_URL", ""),
        })
    except Exception as e:
        services.append({"name": "openai_api", "status": "unhealthy", "error": str(e)[:100]})

    # Overall status
    statuses = [s["status"] for s in services]
    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall = "degraded"
    else:
        overall = "healthy"

    # Stats
    stats = {
        "total_users": User.query.count(),
        "total_patients": User.query.filter_by(role="patient").count(),
        "total_doctors": User.query.filter_by(role="doctor").count(),
        "total_appointments": Appointment.query.count(),
        "total_vitals_readings": VitalsReading.query.count(),
        "total_conversations": Conversation.query.count(),
        "total_alerts": MonitoringAlert.query.count(),
    }

    return jsonify({
        "status": overall,
        "services": services,
        "stats": stats,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200


@bp.route("/ai/config", methods=["GET"])
@jwt_required()
def get_ai_config():
    """Return current AI configuration."""
    err = _require_admin()
    if err:
        return err

    from flask import current_app
    return jsonify({
        "model_primary": current_app.config.get("OPENAI_MODEL_PRIMARY", "gpt-4o-mini"),
        "model_fast": current_app.config.get("OPENAI_MODEL_FAST", "gpt-4o-mini"),
        "base_url": current_app.config.get("OPENAI_BASE_URL", ""),
        "embedding_model": current_app.config.get("OPENAI_EMBEDDING_MODEL", ""),
        "temperature": 0.3,
        "max_tokens": 4096,
        "api_key_configured": bool(current_app.config.get("OPENAI_API_KEY")),
        "specialties_available": 8,
        "agents_registered": ["symptom_analyst", "report_reader", "triage", "general_physician",
                              "cardiology", "orthopedics", "gynecology", "dermatology",
                              "pediatrics", "neurology", "psychiatry"],
    }), 200


@bp.route("/ai/config", methods=["PUT"])
@jwt_required()
def update_ai_config():
    """Update AI configuration (stored in memory for this session)."""
    err = _require_admin()
    if err:
        return err

    from flask import current_app
    data = request.get_json() or {}
    changes = {}

    if "model_primary" in data:
        current_app.config["OPENAI_MODEL_PRIMARY"] = data["model_primary"]
        changes["model_primary"] = data["model_primary"]
    if "model_fast" in data:
        current_app.config["OPENAI_MODEL_FAST"] = data["model_fast"]
        changes["model_fast"] = data["model_fast"]
    if "api_key" in data and data["api_key"]:
        current_app.config["OPENAI_API_KEY"] = data["api_key"]
        changes["api_key"] = "***updated***"

    _log_audit("update", "ai_config", details=changes)
    return jsonify({"message": "AI configuration updated", "changes": changes}), 200


# ── Task #18: Audit Logs ──────────────────────────────────────────────────────

@bp.route("/audit-logs", methods=["GET"])
@jwt_required()
def list_audit_logs():
    """Paginated audit logs with filters."""
    err = _require_admin()
    if err:
        return err

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    action = request.args.get("action")
    resource_type = request.args.get("resource_type")
    user_id = request.args.get("user_id")
    patient_id = request.args.get("patient_id")

    query = AuditLog.query.order_by(AuditLog.created_at.desc())
    if action:
        query = query.filter_by(action=action)
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if patient_id:
        query = query.filter(AuditLog.patient_id == patient_id)

    total = query.count()
    logs = query.limit(per_page).offset((page - 1) * per_page).all()

    user_ids = {str(log.user_id) for log in logs}
    users_map = {}
    if user_ids:
        users = User.query.filter(User.id.in_(user_ids)).all()
        users_map = {str(u.id): {"name": f"{u.first_name} {u.last_name}", "email": u.email} for u in users}

    return jsonify({
        "logs": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "user_name": users_map.get(str(log.user_id), {}).get("name", "Unknown"),
                "user_email": users_map.get(str(log.user_id), {}).get("email", ""),
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


@bp.route("/audit-logs/export", methods=["GET"])
@jwt_required()
def export_audit_logs():
    """Export audit logs as CSV. The export itself is audit-logged."""
    err = _require_admin()
    if err:
        return err

    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(1000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "user_id", "action", "resource_type", "resource_id",
                     "patient_id", "ip_address", "request_method", "request_path",
                     "status_code", "created_at"])
    for log in logs:
        writer.writerow([
            str(log.id), str(log.user_id), log.action, log.resource_type,
            str(log.resource_id) if log.resource_id else "",
            str(log.patient_id) if log.patient_id else "",
            log.ip_address or "", log.request_method or "", log.request_path or "",
            log.status_code or "", log.created_at.isoformat() if log.created_at else "",
        ])

    _log_audit("export", "audit_logs", details={"rows_exported": len(logs)})

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"},
    )


# ── AI Usage Analytics ────────────────────────────────────────────────────────

@bp.route("/analytics/ai-usage", methods=["GET"])
@jwt_required()
def ai_usage_analytics():
    err = _require_admin()
    if err:
        return err

    total_conversations = Conversation.query.count()
    active_conversations = Conversation.query.filter_by(status="active").count()

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


# ── Monitoring Alerts ─────────────────────────────────────────────────────────

@bp.route("/monitoring/alerts", methods=["GET"])
@jwt_required()
def admin_monitoring_alerts():
    err = _require_admin()
    if err:
        return err
    return _get_alerts_response()


def _get_alerts_response():
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
