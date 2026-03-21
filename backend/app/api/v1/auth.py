"""Auth API endpoints — registration, login, token refresh, profile.

Routes:
    POST /api/v1/auth/register  — Register a new user
    POST /api/v1/auth/login     — Login and get JWT tokens
    POST /api/v1/auth/refresh   — Refresh access token
    GET  /api/v1/auth/me        — Get current user profile
    POST /api/v1/auth/change-password — Change password
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from app.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    ChangePasswordRequest,
)
from app.services.auth_service import auth_service

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@bp.route("/register", methods=["POST"])
def register():
    """Register a new user account.

    Accepts email, password, name, role. Returns the created user profile.
    Admin role cannot be self-assigned — admins are created by other admins.
    """
    try:
        data = RegisterRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    # Prevent self-registration as admin
    if data.role == "admin":
        return jsonify({
            "error": {"code": "FORBIDDEN", "message": "Cannot self-register as admin"}
        }), 403

    try:
        user = auth_service.register(data)
    except ValueError as e:
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409

    return jsonify(user.model_dump()), 201


@bp.route("/login", methods=["POST"])
def login():
    """Authenticate and return JWT access + refresh tokens.

    Returns access_token (15 min), refresh_token (7 days), and user profile.
    """
    try:
        data = LoginRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        tokens = auth_service.login(data)
    except ValueError as e:
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": str(e)}}), 401

    return jsonify(tokens.model_dump()), 200


@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Get a new access token using a valid refresh token.

    Send the refresh token in the Authorization header.
    """
    user_id = get_jwt_identity()

    try:
        result = auth_service.refresh_tokens(user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": str(e)}}), 401

    return jsonify(result), 200


@bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    """Get the current authenticated user's profile."""
    user_id = get_jwt_identity()

    try:
        user = auth_service.get_current_user(user_id)
    except ValueError as e:
        return jsonify({"error": {"code": "NOT_FOUND", "message": str(e)}}), 404

    return jsonify(user.model_dump()), 200


@bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """Change the current user's password.

    Requires current_password for verification and new_password.
    """
    try:
        data = ChangePasswordRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    user_id = get_jwt_identity()

    try:
        auth_service.change_password(user_id, data.current_password, data.new_password)
    except ValueError as e:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400

    return jsonify({"message": "Password changed successfully"}), 200
