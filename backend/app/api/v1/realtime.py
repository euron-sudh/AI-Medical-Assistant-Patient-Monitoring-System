"""Realtime Voice API endpoints.

Provides an authenticated endpoint to mint an ephemeral OpenAI Realtime session
token for the frontend. This keeps the server API key off the client.

Voice features use a dedicated OpenAI API key (OPENAI_VOICE_API_KEY) so they
always hit the real OpenAI endpoint, even when the rest of the platform routes
through the EURI gateway.
"""

from __future__ import annotations

import io
import os
from datetime import datetime, timezone
from typing import Any

import requests
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.config import BaseConfig
from app.integrations.openai_client import OpenAIClientError
from app.middleware.auth_middleware import require_role
from app.services.lab_recommendation_service import generate_lab_report_markdown, utc_now_iso

bp = Blueprint("realtime", __name__, url_prefix="/api/v1/realtime")

LISTENING_PROFILES: dict[str, dict[str, Any]] = {
    # Calm room: headset / close mic — balanced VAD
    "quiet": {
        "noise_reduction_type": "near_field",
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.58,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 550,
            "create_response": True,
            "interrupt_response": True,
        },
    },
    # Hospital, TV, fan, street — stricter VAD, more patience before end-of-turn
    "noisy": {
        "noise_reduction_type": "near_field",
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.72,
            "prefix_padding_ms": 320,
            "silence_duration_ms": 850,
            "create_response": True,
            "interrupt_response": True,
        },
    },
    # Laptop / room mic / farther from mic
    "speaker": {
        "noise_reduction_type": "far_field",
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.68,
            "prefix_padding_ms": 350,
            "silence_duration_ms": 750,
            "create_response": True,
            "interrupt_response": True,
        },
    },
}

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


def _voice_base_url() -> str:
    """Return the base URL for OpenAI voice/realtime endpoints.

    Uses the dedicated voice base URL which defaults to https://api.openai.com/v1,
    ensuring voice traffic always hits the real OpenAI API.
    """
    base = BaseConfig.OPENAI_VOICE_BASE_URL or "https://api.openai.com/v1"
    base = base.rstrip("/")
    # Strip /v1 suffix since the caller appends /v1/realtime/sessions
    if base.endswith("/v1"):
        base = base[:-3]
    return base


@bp.route("/session", methods=["POST"])
@jwt_required()
@require_role(["patient"])
def create_realtime_session():
    """Create an ephemeral Realtime session for the authenticated patient."""
    api_key = BaseConfig.OPENAI_VOICE_API_KEY or BaseConfig.OPENAI_API_KEY or ""
    if not api_key:
        return jsonify({"error": {"code": "CONFIG_ERROR", "message": "OPENAI_API_KEY not configured"}}), 500

    body: dict[str, Any] = request.get_json(silent=True) or {}
    model = body.get("model") or os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime")
    # Voices to try: alloy, echo, shimmer, marin, cedar (OpenAI Realtime)
    voice = body.get("voice") or os.getenv("OPENAI_REALTIME_VOICE", "marin")
    listening_profile = (body.get("listening_profile") or os.getenv("OPENAI_LISTENING_PROFILE") or "quiet").strip().lower()
    if listening_profile not in LISTENING_PROFILES:
        listening_profile = "quiet"
    profile_cfg = LISTENING_PROFILES[listening_profile]
    noise_type = profile_cfg["noise_reduction_type"]
    profile_turn = dict(profile_cfg["turn_detection"])

    # Keep identity for server-side logs/authorization decisions only
    _patient_id = get_jwt_identity()

    # Session-level instructions should NOT hardcode the intro. The client sends
    # a dedicated intro-only response on connect to avoid mixed-language followups
    # being appended to the greeting.
    instructions = body.get("instructions") or (
        "Voice and pacing:\n"
        "- Speak naturally, like a calm clinician—not robotic or overly formal.\n"
        "- Use short, clear sentences. Pause briefly before important medical points.\n"
        "- Do not answer until the patient has clearly finished their turn; tolerate natural pauses.\n"
        "- Ask one question at a time.\n\n"
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

    # Client may override full turn_detection; else use profile (server_vad + tuned for noise).
    turn_detection: dict[str, Any] = dict(body.get("turn_detection") or profile_turn)

    # POST /v1/realtime/sessions accepts top-level turn_detection + input_audio_noise_reduction
    # (not nested "audio", which is response-only on some API versions / gateways).
    input_audio_noise_reduction: dict[str, Any] = {"type": noise_type}
    if isinstance(body.get("audio_input"), dict):
        ai = body["audio_input"]
        if isinstance(ai.get("turn_detection"), dict):
            turn_detection = dict(ai["turn_detection"])
        if isinstance(ai.get("noise_reduction"), dict):
            input_audio_noise_reduction = dict(ai["noise_reduction"])
    if isinstance(body.get("input_audio_noise_reduction"), dict):
        input_audio_noise_reduction = dict(body["input_audio_noise_reduction"])

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
        "turn_detection": turn_detection,
        "input_audio_noise_reduction": input_audio_noise_reduction,
    }

    try:
        res = requests.post(
            f"{_voice_base_url()}/v1/realtime/sessions",
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
        "listening_profile": listening_profile,
        "noise_reduction": noise_type,
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


@bp.route("/lab-recommendations/pdf", methods=["POST"])
@jwt_required()
@require_role(["patient"])
def create_lab_recommendations_pdf():
    """Generate lab test suggestions and return a formatted PDF."""
    from app.extensions import db
    from app.models.user import User
    from app.utils.pdf_export import build_lab_tests_pdf

    user_id = get_jwt_identity()
    body: dict[str, Any] = request.get_json(silent=True) or {}
    report_markdown_in = (body.get("report_markdown") or "").strip()
    transcript = (body.get("transcript") or "").strip()
    if not report_markdown_in and not transcript:
        return jsonify({
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "report_markdown or transcript is required",
            },
        }), 400

    user = db.session.get(User, user_id)
    patient_name = user.full_name if user else None

    try:
        report_markdown = report_markdown_in or generate_lab_report_markdown(transcript)
        pdf_bytes = build_lab_tests_pdf(
            patient_name=patient_name,
            recommendation_markdown=report_markdown,
        )
    except OpenAIClientError as exc:
        return jsonify({
            "error": {"code": "LAB_GENERATION_ERROR", "message": str(exc)},
        }), 502
    except Exception as exc:
        return jsonify({
            "error": {"code": "PDF_EXPORT_ERROR", "message": str(exc)},
        }), 500

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"medassist-lab-tests-{stamp}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
        max_age=0,
    )

