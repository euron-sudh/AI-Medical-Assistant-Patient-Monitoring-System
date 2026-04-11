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

from app.integrations.openai_client import OpenAIClientError
from app.middleware.auth_middleware import require_role
from app.services.lab_recommendation_service import generate_lab_report_markdown, utc_now_iso

bp = Blueprint("realtime", __name__, url_prefix="/api/v1/realtime")

REQUEST_LAB_TOOL: dict[str, Any] = {
    "type": "function",
    "name": "request_lab_recommendations",
    "description": (
        "Call once when you have gathered enough symptom information to suggest laboratory work. "
        "Pass a structured summary of chief complaint, symptoms, timing, severity, and relevant context. "
        "The system returns suggested lab tests; you will explain them to the patient and close the session."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "symptoms_summary": {
                "type": "string",
                "description": (
                    "Concise structured summary of reported symptoms (not a diagnosis). "
                    "Include language used if relevant."
                ),
            },
        },
        "required": ["symptoms_summary"],
    },
}


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
        "Ask ONE question at a time to understand symptoms, duration, severity, and relevant history.\n"
        "Do not diagnose. Do not invent tests before calling the tool.\n\n"
        "When you have enough information to propose laboratory evaluation, call request_lab_recommendations "
        "exactly once with a clear symptoms_summary. If the patient later adds major new symptoms, you may call again.\n\n"
        "After you receive the tool output (lab_recommendations_markdown), explain the suggested tests briefly in the "
        "patient's language, remind them this is not a diagnosis, and that they should review with a licensed clinician. "
        "Tell them they can download the full lab test list using the Download lab test button in the app. "
        "Thank them, say the session is complete, and do not ask further medical questions.\n\n"
        "If emergency symptoms are suspected, advise calling emergency services immediately before anything else."
    )

    payload = {
        "model": model,
        "voice": voice,
        "instructions": instructions,
        "tools": [REQUEST_LAB_TOOL],
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


@bp.route("/lab-recommendations", methods=["POST"])
@jwt_required()
@require_role(["patient"])
def create_lab_recommendations():
    """Generate lab test suggestions from conversation text using gpt-4o-mini."""
    _patient_id = get_jwt_identity()
    body: dict[str, Any] = request.get_json(silent=True) or {}
    transcript = (body.get("transcript") or "").strip()
    if not transcript:
        return jsonify({
            "error": {"code": "VALIDATION_ERROR", "message": "transcript is required"},
        }), 400

    try:
        report_markdown = generate_lab_report_markdown(transcript)
    except OpenAIClientError as exc:
        return jsonify({
            "error": {"code": "LAB_GENERATION_ERROR", "message": str(exc)},
        }), 502

    return jsonify({
        "report_markdown": report_markdown,
        "generated_at": utc_now_iso(),
    }), 200

