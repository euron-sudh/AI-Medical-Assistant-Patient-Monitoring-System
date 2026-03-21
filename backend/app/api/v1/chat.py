"""Chat API — AI-powered medical chat using EURI/OpenAI gateway."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from openai import OpenAI

bp = Blueprint("chat", __name__, url_prefix="/api/v1/chat")


@bp.route("/message", methods=["POST"])
@jwt_required()
def send_message():
    """Send a message to the AI assistant and get a response.

    Accepts an optional X-Euri-Api-Key header for client-provided API keys.
    Falls back to server-configured key if not provided.
    """
    data = request.get_json()
    if not data or not data.get("message"):
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "message is required"}}), 400

    user_message = data["message"]
    conversation_history = data.get("history", [])

    # Use client-provided key or fall back to server key
    api_key = request.headers.get("X-Euri-Api-Key", "")
    if not api_key:
        from app.config import BaseConfig
        api_key = BaseConfig.OPENAI_API_KEY

    if not api_key:
        return jsonify({"error": {"code": "NO_API_KEY", "message": "No EURI API key configured. Click 'Set API Key' to add yours."}}), 400

    base_url = "https://api.euron.one/api/v1/euri"

    try:
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=30)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are MedAssist AI, a medical assistant. Provide helpful, "
                    "accurate health information. Always remind users to consult "
                    "healthcare providers for medical advice. Be empathetic and clear. "
                    "Use plain language at a 6th-8th grade reading level."
                ),
            }
        ]
        messages.extend(conversation_history[-10:])  # Keep last 10 messages for context
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.3,
        )

        ai_message = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else 0

        return jsonify({
            "response": ai_message,
            "tokens_used": tokens_used,
            "model": response.model,
        }), 200

    except Exception as e:
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            return jsonify({"error": {"code": "INVALID_KEY", "message": "Invalid EURI API key. Check your key at euron.one/euri"}}), 401
        return jsonify({"error": {"code": "AI_ERROR", "message": f"AI service error: {error_msg[:100]}"}}), 500
