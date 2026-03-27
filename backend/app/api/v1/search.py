"""Search API endpoints — cross-entity search for patients, medications, and conditions.

Routes:
    GET /api/v1/search?q=term&type=patients|medications|conditions|all
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.middleware.auth_middleware import require_role
from app.services.search_service import search_service

bp = Blueprint("search", __name__, url_prefix="/api/v1/search")


@bp.route("", methods=["GET"])
@jwt_required()
@require_role(["doctor", "nurse", "admin"])
def search():
    """Search across patients, medications, and conditions.

    Query Parameters:
        q: Search term (required, minimum 1 character).
        type: Entity type to search — 'patients', 'medications', 'conditions', or 'all'.
              Defaults to 'all'.
        limit: Maximum results per category (default 20).
        offset: Number of results to skip per category (default 0).
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({
            "error": {"code": "VALIDATION_ERROR", "message": "Query parameter 'q' is required"}
        }), 400

    search_type = request.args.get("type", "all").strip().lower()
    valid_types = ("patients", "medications", "conditions", "all")
    if search_type not in valid_types:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": f"Invalid type. Must be one of: {', '.join(valid_types)}",
            }
        }), 400

    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)

    results = search_service.search(
        query=query, search_type=search_type, limit=limit, offset=offset
    )

    return jsonify({"query": query, "type": search_type, "results": results}), 200
