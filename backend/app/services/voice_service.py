"""Voice service - speech-to-text and text-to-speech using OpenAI APIs."""

import base64
import os
from io import BytesIO

import structlog

from app.schemas.voice_schema import SynthesizeRequest, SynthesizeResponse, TranscribeResponse

logger = structlog.get_logger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_WHISPER_MODEL = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1")


class VoiceService:
    """Handles speech-to-text transcription and text-to-speech synthesis."""

    def transcribe(self, audio_data: bytes, filename: str = "audio.wav") -> TranscribeResponse:
        """Transcribe audio to text using OpenAI Whisper API."""
        if OPENAI_API_KEY:
            try:
                return self._transcribe_with_openai(audio_data, filename)
            except Exception as e:
                logger.error("openai_transcription_failed", error=str(e))
                raise ValueError(f"Transcription failed: {str(e)}")
        logger.info("voice_transcribe_placeholder", filename=filename, audio_size=len(audio_data))
        return TranscribeResponse(
            text="[Placeholder] Audio transcription would appear here. Configure OPENAI_API_KEY to enable.",
            language="en", duration_seconds=0.0, confidence=0.0,
        )

    def synthesize(self, data: SynthesizeRequest) -> SynthesizeResponse:
        """Synthesize text to speech using OpenAI TTS API."""
        if OPENAI_API_KEY:
            try:
                return self._synthesize_with_openai(data)
            except Exception as e:
                logger.error("openai_synthesis_failed", error=str(e))
                raise ValueError(f"Synthesis failed: {str(e)}")
        logger.info("voice_synthesize_placeholder", text_length=len(data.text), voice=data.voice)
        return SynthesizeResponse(
            audio_url=None, audio_base64=None, format="mp3",
            message="[Placeholder] Audio synthesis not available. Configure OPENAI_API_KEY to enable.",
        )

    def _transcribe_with_openai(self, audio_data: bytes, filename: str) -> TranscribeResponse:
        """Call OpenAI Whisper API for transcription."""
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        audio_file = BytesIO(audio_data)
        audio_file.name = filename
        result = client.audio.transcriptions.create(
            model=OPENAI_WHISPER_MODEL, file=audio_file, response_format="verbose_json",
        )
        return TranscribeResponse(
            text=result.text, language=getattr(result, "language", None),
            duration_seconds=getattr(result, "duration", None), confidence=None,
        )

    def _synthesize_with_openai(self, data: SynthesizeRequest) -> SynthesizeResponse:
        """Call OpenAI TTS API for speech synthesis."""
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.audio.speech.create(
            model=OPENAI_TTS_MODEL, voice=data.voice, input=data.text, speed=data.speed,
        )
        audio_b64 = base64.b64encode(response.content).decode("utf-8")
        return SynthesizeResponse(audio_url=None, audio_base64=audio_b64, format="mp3")


voice_service = VoiceService()
