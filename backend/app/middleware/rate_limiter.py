"""Rate Limiter Middleware — role-based API rate limiting.

Task #19 (Pallavi Sindkar):
- Patient: 60 requests/minute
- Doctor/Nurse: 120 requests/minute
- Admin: 200 requests/minute
- AI endpoints: 20 requests/minute per user
- Auth endpoints: 10 requests/minute per IP

Uses Flask-Limiter with Redis backend (falls back to in-memory).
"""

from flask_jwt_extended import get_jwt, verify_jwt_in_request
from app.extensions import limiter


# ── Role-based rate limit key functions ───────────────────────────────────────

def _get_user_id_or_ip():
    """Get user ID from JWT for authenticated requests, or IP for anonymous."""
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt()
        if claims:
            return claims.get("sub", "anonymous")
    except Exception:
        pass
    from flask import request
    return f"ip:{request.remote_addr}"


def _get_role_limit():
    """Return rate limit string based on user role."""
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt()
        role = claims.get("role", "patient")
        limits = {
            "admin": "200/minute",
            "doctor": "120/minute",
            "nurse": "120/minute",
            "patient": "60/minute",
        }
        return limits.get(role, "60/minute")
    except Exception:
        return "30/minute"


# ── Decorators for specific endpoint types ────────────────────────────────────

# AI endpoints (costly — limit to 20/min)
ai_rate_limit = limiter.limit(
    "20/minute",
    key_func=_get_user_id_or_ip,
    error_message="AI request rate limit exceeded. Please wait before sending another request.",
)

# Auth endpoints (brute force protection — 10/min per IP)
auth_rate_limit = limiter.limit(
    "10/minute",
    key_func=lambda: f"ip:{__import__('flask').request.remote_addr}",
    error_message="Too many authentication attempts. Please wait before trying again.",
)

# General API rate limit (role-based)
api_rate_limit = limiter.limit(
    _get_role_limit,
    key_func=_get_user_id_or_ip,
    error_message="API rate limit exceeded. Please slow down your requests.",
)
