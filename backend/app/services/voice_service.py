"""Voice service - speech-to-text and text-to-speech using OpenAI APIs.

Voice features (TTS, STT, Realtime) use a dedicated OpenAI API key/base URL
so they hit the real OpenAI endpoint even when the rest of the platform uses
the EURI gateway for chat/embedding models.
"""

import base64
import os
from io import BytesIO

import structlog

from app.schemas.voice_schema import SynthesizeRequest, SynthesizeResponse, TranscribeResponse
from app.config import BaseConfig

logger = structlog.get_logger(__name__)

# Voice-specific key falls back to the general OPENAI_API_KEY
VOICE_API_KEY = BaseConfig.OPENAI_VOICE_API_KEY or BaseConfig.OPENAI_API_KEY
VOICE_BASE_URL = BaseConfig.OPENAI_VOICE_BASE_URL  # defaults to https://api.openai.com/v1
OPENAI_WHISPER_MODEL = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1")


class VoiceService:
    """Handles speech-to-text transcription and text-to-speech synthesis."""

    def transcribe(
        self,
        audio_data: bytes,
        filename: str = "audio.wav",
        language: str | None = None,
    ) -> TranscribeResponse:
        """Transcribe audio to text using OpenAI Whisper API.

        Args:
            audio_data: Raw audio bytes.
            filename: Filename hint so Whisper can infer the container/codec.
            language: Optional ISO-639-1 language hint (e.g. 'en', 'hi', 'es').
                When omitted Whisper auto-detects the language.
        """
        if VOICE_API_KEY:
            try:
                return self._transcribe_with_openai(audio_data, filename, language=language)
            except Exception as e:
                logger.error("openai_transcription_failed", error=str(e))
                raise ValueError(f"Transcription failed: {str(e)}")
        logger.info(
            "voice_transcribe_placeholder",
            filename=filename,
            audio_size=len(audio_data),
            language=language,
        )
        return TranscribeResponse(
            text="[Placeholder] Audio transcription would appear here. Configure OPENAI_VOICE_API_KEY to enable.",
            language=language or "en",
            duration_seconds=0.0,
            confidence=0.0,
        )

    def synthesize(self, data: SynthesizeRequest) -> SynthesizeResponse:
        """Synthesize text to speech using OpenAI TTS API."""
        if VOICE_API_KEY:
            try:
                return self._synthesize_with_openai(data)
            except Exception as e:
                logger.error("openai_synthesis_failed", error=str(e))
                raise ValueError(f"Synthesis failed: {str(e)}")
        logger.info("voice_synthesize_placeholder", text_length=len(data.text), voice=data.voice)
        return SynthesizeResponse(
            audio_url=None, audio_base64=None, format="mp3",
            message="[Placeholder] Audio synthesis not available. Configure OPENAI_VOICE_API_KEY to enable.",
        )

    def _get_voice_client(self):
        """Return an OpenAI client configured for voice (TTS/STT).

        Uses the dedicated voice API key and base URL so voice calls always
        hit the real OpenAI endpoint, even when chat/embedding traffic is
        routed through the EURI gateway.
        """
        from openai import OpenAI
        return OpenAI(api_key=VOICE_API_KEY, base_url=VOICE_BASE_URL)

    def _transcribe_with_openai(
        self,
        audio_data: bytes,
        filename: str,
        language: str | None = None,
    ) -> TranscribeResponse:
        """Call OpenAI Whisper API for transcription."""
        client = self._get_voice_client()
        audio_file = BytesIO(audio_data)
        audio_file.name = filename
        kwargs = {
            "model": OPENAI_WHISPER_MODEL,
            "file": audio_file,
            "response_format": "verbose_json",
        }
        if language:
            kwargs["language"] = language
        result = client.audio.transcriptions.create(**kwargs)
        return TranscribeResponse(
            text=result.text, language=getattr(result, "language", language),
            duration_seconds=getattr(result, "duration", None), confidence=None,
        )

    def _synthesize_with_openai(self, data: SynthesizeRequest) -> SynthesizeResponse:
        """Call OpenAI TTS API for speech synthesis."""
        client = self._get_voice_client()
        response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL, voice=data.voice, input=data.text, speed=data.speed,
        )
        audio_b64 = base64.b64encode(response.content).decode("utf-8")
        return SynthesizeResponse(audio_url=None, audio_base64=audio_b64, format="mp3")


voice_service = VoiceService()
