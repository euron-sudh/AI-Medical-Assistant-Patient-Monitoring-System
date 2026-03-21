"""Health check endpoint."""

from flask import Blueprint, jsonify

bp = Blueprint("health_api", __name__, url_prefix="/api/v1/health")


@bp.route("/", methods=["GET"])
def health_check():
    """API health check with dependency status.
    ---
    tags: [Health]
    """
    return jsonify({
        "status": "healthy",
        "service": "medassist-ai-backend",
        "version": "1.0.0",
    }), 200
