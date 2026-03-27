"""Chat API — AI-powered medical chat using EURI/OpenAI gateway."""

import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from openai import AuthenticationError, APIError
from pydantic import BaseModel, Field

from app.integrations.openai_client import openai_client, OpenAIClientError
from app.middleware.rate_limiter import ai_rate_limit

logger = logging.getLogger(__name__)

bp = Blueprint("chat", __name__, url_prefix="/api/v1/chat")


class ChatMessageRequest(BaseModel):
    """Validated request body for the chat endpoint."""

    message: str = Field(min_length=1, max_length=5000)
    history: list[dict] = Field(default_factory=list)


SYSTEM_PROMPT = (
    "You are MedAssist AI, a medical assistant. Provide helpful, "
    "accurate health information. Always remind users to consult "
    "healthcare providers for medical advice. Be empathetic and clear. "
    "Use plain language at a 6th-8th grade reading level."
)


@bp.route("/message", methods=["POST"])
@jwt_required()
@ai_rate_limit
def send_message():
    """Send a message to the AI assistant and get a response.

    Accepts an optional X-Euri-Api-Key header for client-provided API keys.
    Falls back to server-configured key if not provided.
    """
    # Validate request body
    try:
        data = ChatMessageRequest.model_validate(request.get_json())
    except Exception as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(e)}}), 400

    user_id = get_jwt_identity()

    # Build message list
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(data.history[-10:])  # Keep last 10 messages for context
    messages.append({"role": "user", "content": data.message})

    # Use client-provided API key if present, otherwise use the default singleton
    client_api_key = request.headers.get("X-Euri-Api-Key", "").strip()

    try:
        if client_api_key:
            # Create a one-off client with the user-provided key
            from app.integrations.openai_client import OpenAIClient
            custom_client = OpenAIClient(api_key=client_api_key)
            result = custom_client.chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.3,
            )
        else:
            if not openai_client._api_key:
                return jsonify({
                    "error": {
                        "code": "NO_API_KEY",
                        "message": "No EURI API key configured. Click 'Set API Key' to add yours.",
                    }
                }), 400

            result = openai_client.chat_completion(
                messages=messages,
                max_tokens=500,
                temperature=0.3,
            )

        return jsonify({
            "response": result.content,
            "tokens_used": result.usage.total_tokens,
            "model": result.model,
        }), 200

    except OpenAIClientError as e:
        logger.error("AI chat error for user=%s: %s", user_id, e)
        error_msg = str(e)
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            return jsonify({
                "error": {"code": "INVALID_KEY", "message": "Invalid EURI API key. Check your key at euron.one/euri"}
            }), 401
        return jsonify({
            "error": {"code": "AI_ERROR", "message": f"AI service error: {error_msg[:100]}"}
        }), 500
    except AuthenticationError:
        return jsonify({
            "error": {"code": "INVALID_KEY", "message": "Invalid EURI API key. Check your key at euron.one/euri"}
        }), 401
    except APIError as e:
        logger.error("OpenAI API error for user=%s: %s", user_id, e)
        return jsonify({
            "error": {"code": "AI_ERROR", "message": f"AI service error: {str(e)[:100]}"}
        }), 500
