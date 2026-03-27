"""Auth middleware — JWT decorators and role-based access control."""

from functools import wraps
from typing import Callable

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


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


def get_current_user_role() -> str:
    """Extract the current user's role from JWT claims.

    Returns:
        Role string from the JWT token.
    """
    claims = get_jwt()
    return claims.get("role", "")
