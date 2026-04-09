"""Realtime Voice API endpoints.

Provides an authenticated endpoint to mint an ephemeral OpenAI Realtime session
token for the frontend. This keeps the server API key off the client.
"""

from __future__ import annotations

import os
from typing import Any

import requests
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.middleware.auth_middleware import require_role

bp = Blueprint("realtime", __name__, url_prefix="/api/v1/realtime")


def _openai_base_url() -> str:
    # If OPENAI_BASE_URL is configured (or EURI), honor it; otherwise default OpenAI.
    base = os.getenv("OPENAI_BASE_URL") or os.getenv("EURI_BASE_URL") or "https://api.openai.com"
    base = base.rstrip("/")
    # Allow users to set OPENAI_BASE_URL as either "https://api.openai.com" or
    # "https://api.openai.com/v1" without double-appending /v1 below.
    if base.endswith("/v1"):
        base = base[:-3]
    return base


@bp.route("/session", methods=["POST"])
@jwt_required()
@require_role(["patient"])
def create_realtime_session():
    """Create an ephemeral Realtime session for the authenticated patient."""
    api_key = os.getenv("OPENAI_API_KEY") or ""
    if not api_key:
        return jsonify({"error": {"code": "CONFIG_ERROR", "message": "OPENAI_API_KEY not configured"}}), 500

    body: dict[str, Any] = request.get_json(silent=True) or {}
    model = body.get("model") or os.getenv("OPENAI_REALTIME_MODEL", "gpt-4o-realtime-preview")
    # Realtime voice list differs from classic TTS voices; default to a safe supported preset.
    voice = body.get("voice") or os.getenv("OPENAI_REALTIME_VOICE", "alloy")

    # Keep identity for server-side logs/authorization decisions only
    _patient_id = get_jwt_identity()

    # Session-level instructions should NOT hardcode the intro. The client sends
    # a dedicated intro-only response on connect to avoid mixed-language followups
    # being appended to the greeting.
    instructions = body.get("instructions") or (
        "You are Med Assist virtual doctor conducting a voice-based symptom assessment.\n"
        "When the patient starts speaking, detect the patient's spoken language and continue in that language.\n"
        "If you are unsure of the language, ask a short clarification question.\n\n"
        "Ask one question at a time to gather symptom details.\n"
        "When you have enough information, recommend appropriate medical tests and next steps.\n"
        "If emergency symptoms are suspected, advise calling emergency services immediately."
    )

    payload = {
        "model": model,
        "voice": voice,
        "instructions": instructions,
        # Prefer both audio + text so UI can display transcript while playing audio.
        "modalities": ["audio", "text"],
        # Ask the model to also produce text output while speaking.
        "output_audio_format": body.get("output_audio_format", "pcm16"),
        # Optional client-side transcription via the realtime service if supported
        "input_audio_transcription": body.get("input_audio_transcription", {"model": "gpt-4o-mini-transcribe"}),
    }

    try:
        res = requests.post(
            f"{_openai_base_url()}/v1/realtime/sessions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        return jsonify({"error": {"code": "UPSTREAM_ERROR", "message": str(exc)}}), 502

    if not res.ok:
        return jsonify({
            "error": {
                "code": "UPSTREAM_ERROR",
                "status": res.status_code,
                "details": res.text,
            }
        }), 502

    data = res.json()

    # Return the ephemeral token to the frontend
    client_secret = (data.get("client_secret") or {}).get("value")
    if not client_secret:
        return jsonify({"error": {"code": "UPSTREAM_ERROR", "message": "No client_secret returned"}}), 502

    return jsonify({
        "model": model,
        "voice": voice,
        "expires_at": data.get("expires_at"),
        "client_secret": client_secret,
    }), 201

