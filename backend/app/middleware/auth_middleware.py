"""Auth middleware — JWT decorators and role-based access control.

Task #20 (Pallavi Sindkar): Enhanced RBAC with audit logging for denied access.
"""

from functools import wraps
from typing import Callable

from flask import jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request


def require_role(allowed_roles: list[str]) -> Callable:
    """Decorator that restricts endpoint access to specific roles.

    Usage:
        @bp.route("/admin/users")
        @jwt_required()
        @require_role(["admin"])
        def list_users():
            ...

    Args:
        allowed_roles: List of role strings that are permitted access.

    Returns:
        Decorated function that returns 403 if role is not in allowed_roles.
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role", "")

            if user_role not in allowed_roles:
                _log_access_denied(claims, allowed_roles)
                return jsonify({
                    "error": {
                        "code": "FORBIDDEN",
                        "message": f"Role '{user_role}' does not have access to this resource",
                    }
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def require_auth(fn: Callable) -> Callable:
    """Decorator that requires a valid JWT token (any role).

    Usage:
        @bp.route("/protected")
        @require_auth
        def protected_route():
            ...
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)

    return wrapper


def require_own_data(fn: Callable) -> Callable:
    """Decorator ensuring patients can only access their own data.

    Checks if the patient_id/user_id in the route matches the JWT identity.
    Doctors, nurses, and admins bypass this check.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        role = claims.get("role", "")
        user_id = str(get_jwt_identity())

        if role == "patient":
            # Check common route parameter names
            target_id = kwargs.get("patient_id") or kwargs.get("user_id")
            if target_id and str(target_id) != user_id:
                _log_access_denied(claims, [f"own_data:{target_id}"])
                return jsonify({
                    "error": {"code": "FORBIDDEN", "message": "Cannot access other user's data"}
                }), 403

        return fn(*args, **kwargs)

    return wrapper


def _log_access_denied(claims: dict, required: list) -> None:
    """Log failed access attempts to audit log (elevated severity)."""
    try:
        from app.extensions import db
        from app.models.audit_log import AuditLog
        log = AuditLog(
            user_id=claims.get("sub", "unknown"),
            action="access_denied",
            resource_type="api_endpoint",
            ip_address=request.remote_addr if request else None,
            request_method=request.method if request else None,
            request_path=request.path if request else None,
            status_code=403,
            details={
                "role": claims.get("role", "unknown"),
                "required_roles": required,
                "severity": "high",
            },
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass  # Don't fail the request if audit logging fails


def get_current_user_role() -> str:
    """Extract the current user's role from JWT claims.

    Returns:
        Role string from the JWT token.
    """
    claims = get_jwt()
    return claims.get("role", "")
