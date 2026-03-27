"""Voice API endpoints - speech-to-text transcription and text-to-speech synthesis.

Routes:
    POST /api/v1/voice/transcribe  - Upload audio and get text transcription
    POST /api/v1/voice/synthesize  - Convert text to speech audio
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from app.schemas.voice_schema import SynthesizeRequest
from app.services.voice_service import voice_service

bp = Blueprint("voice", __name__, url_prefix="/api/v1/voice")


@bp.route("/transcribe", methods=["POST"])
@jwt_required()
def transcribe():
    """Accept audio file upload and return transcribed text.

    Expects a multipart form upload with an 'audio' file field.
    Supported formats: wav, mp3, mp4, m4a, webm, ogg, flac.
    """
    if "audio" not in request.files:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "No audio file provided. Upload a file with field name 'audio'.",
            }
        }), 400

    audio_file = request.files["audio"]

    if not audio_file.filename:
        return jsonify({
            "error": {"code": "BAD_REQUEST", "message": "Audio file has no filename"}
        }), 400

    allowed_extensions = {"wav", "mp3", "mp4", "m4a", "webm", "ogg", "flac"}
    ext = audio_file.filename.rsplit(".", 1)[-1].lower() if "." in audio_file.filename else ""
    if ext not in allowed_extensions:
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": f"Unsupported audio format '.{ext}'. Allowed: {', '.join(sorted(allowed_extensions))}",
            }
        }), 400

    audio_data = audio_file.read()
    if len(audio_data) == 0:
        return jsonify({
            "error": {"code": "BAD_REQUEST", "message": "Audio file is empty"}
        }), 400

    # Max 25MB (OpenAI Whisper limit)
    if len(audio_data) > 25 * 1024 * 1024:
        return jsonify({
            "error": {"code": "BAD_REQUEST", "message": "Audio file exceeds 25MB limit"}
        }), 400

    try:
        result = voice_service.transcribe(audio_data, filename=audio_file.filename)
    except ValueError as e:
        return jsonify({"error": {"code": "PROCESSING_ERROR", "message": str(e)}}), 500

    return jsonify(result.model_dump(mode="json")), 200


@bp.route("/synthesize", methods=["POST"])
@jwt_required()
def synthesize():
    """Convert text to speech audio.

    Accepts JSON body with text, optional voice selection, and speed.
    Returns audio data (base64-encoded) or a placeholder message.
    """
    try:
        data = SynthesizeRequest.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "details": e.errors()}}), 400

    try:
        result = voice_service.synthesize(data)
    except ValueError as e:
        return jsonify({"error": {"code": "PROCESSING_ERROR", "message": str(e)}}), 500

    return jsonify(result.model_dump(mode="json")), 200
