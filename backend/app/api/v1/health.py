"""Health check endpoint."""

import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify

bp = Blueprint("health_api", __name__, url_prefix="/api/v1/health")

_start_time = time.time()


@bp.route("/", methods=["GET"])
def health_check():
    """API health check with dependency status.
    ---
    tags: [Health]
    """
    uptime_seconds = int(time.time() - _start_time)

    dependencies = {}

    # Check PostgreSQL
    try:
        from app.extensions import db
        start = time.time()
        db.session.execute(db.text("SELECT 1"))
        latency = int((time.time() - start) * 1000)
        dependencies["postgresql"] = {"status": "healthy", "latency_ms": latency}
    except Exception:
        dependencies["postgresql"] = {"status": "unhealthy"}

    # Check Redis
    try:
        import redis
        from flask import current_app
        redis_url = current_app.config.get("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, socket_timeout=2)
        start = time.time()
        r.ping()
        latency = int((time.time() - start) * 1000)
        dependencies["redis"] = {"status": "healthy", "latency_ms": latency}
    except Exception:
        dependencies["redis"] = {"status": "unhealthy"}

    statuses = [d.get("status", "unknown") for d in dependencies.values()]
    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall = "degraded"
    else:
        overall = "healthy"

    return jsonify({
        "status": overall,
        "service": "medassist-ai-backend",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": dependencies,
    }), 200
