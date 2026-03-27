"""Voice Agent — handles speech-to-text and text-to-speech operations.

Provides a unified agent interface for voice interactions. The actual
Whisper-based transcription and TTS synthesis are handled by the voice
service (backend/app/services/voice_service.py). This agent wraps those
capabilities into the standard BaseAgent interface for orchestrator routing.

Model: GPT-4o-mini (lightweight orchestration of voice tools)
"""

from __future__ import annotations

import json
import time
from typing import Any

import structlog

from app.agents.base_agent import AgentInput, AgentOutput, BaseAgent
from app.integrations.openai_client import OpenAIClient

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

TRANSCRIBE_AUDIO_TOOL = {
    "type": "function",
    "function": {
        "name": "transcribe_audio",
        "description": (
            "Transcribe audio input to text. Accepts a text placeholder representing "
            "audio content. In production, the actual Whisper-based transcription is "
            "handled by voice_service.py — this tool provides the agent interface."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "audio_text": {
                    "type": "string",
                    "description": "Text representation of the audio content to transcribe",
                },
                "language": {
                    "type": "string",
                    "description": "Language code (e.g., 'en', 'es', 'fr'). Default: 'en'",
                    "default": "en",
                },
            },
            "required": ["audio_text"],
        },
    },
}

SYNTHESIZE_SPEECH_TOOL = {
    "type": "function",
    "function": {
        "name": "synthesize_speech",
        "description": (
            "Convert text to speech audio. Returns a placeholder response indicating "
            "the text has been queued for speech synthesis. Actual TTS is handled by "
            "voice_service.py."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text content to convert to speech",
                },
                "voice": {
                    "type": "string",
                    "description": "Voice preset to use (e.g., 'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer')",
                    "default": "nova",
                },
                "speed": {
                    "type": "number",
                    "description": "Speech speed multiplier (0.25 to 4.0). Default: 1.0",
                    "default": 1.0,
                },
            },
            "required": ["text"],
        },
    },
}


# ---------------------------------------------------------------------------
# Tool handler functions (placeholders — actual integration in voice_service.py)
# ---------------------------------------------------------------------------


def transcribe_audio(audio_text: str, language: str = "en") -> dict:
    """Transcribe audio to text (placeholder).

    In production, this delegates to the Whisper-based voice_service.py.
    This placeholder accepts text input and returns it as a transcription result.

    Args:
        audio_text: Text representation of audio content.
        language: Language code for transcription.

    Returns:
        Transcription result dict.
    """
    logger.info(
        "transcribe_audio_called",
        language=language,
        text_length=len(audio_text),
    )

    return {
        "transcription": audio_text,
        "language": language,
        "confidence": 0.95,
        "status": "success",
        "message": "Audio transcribed successfully (placeholder — Whisper integration in voice_service.py)",
    }


def synthesize_speech(
    text: str,
    voice: str = "nova",
    speed: float = 1.0,
) -> dict:
    """Synthesize speech from text (placeholder).

    In production, this delegates to the TTS service in voice_service.py.
    This placeholder confirms the text has been processed.

    Args:
        text: Text to convert to speech.
        voice: Voice preset.
        speed: Speech speed multiplier.

    Returns:
        Synthesis confirmation dict.
    """
    logger.info(
        "synthesize_speech_called",
        text_length=len(text),
        voice=voice,
        speed=speed,
    )

    return {
        "text": text,
        "voice": voice,
        "speed": speed,
        "status": "success",
        "audio_format": "mp3",
        "message": "Speech synthesis queued (placeholder — TTS integration in voice_service.py)",
    }


# ---------------------------------------------------------------------------
# Voice Agent
# ---------------------------------------------------------------------------


class VoiceAgent(BaseAgent):
    """AI agent for voice-based medical interactions.

    Capabilities:
        - Speech-to-text transcription via Whisper (delegated to voice_service.py)
        - Text-to-speech synthesis (delegated to voice_service.py)
        - Voice-aware conversation management
        - Medical terminology pronunciation handling

    Tools:
        - transcribe_audio: Convert speech to text
        - synthesize_speech: Convert text to speech
    """

    agent_name = "voice"
    model = "gpt-4o-mini"
    max_tokens = 2048
    temperature = 0.3

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        super().__init__(openai_client=openai_client)

        # Register tool handlers
        self.register_tool("transcribe_audio", transcribe_audio)
        self.register_tool("synthesize_speech", synthesize_speech)

    def _get_system_prompt(self) -> str:
        """Return the voice agent system prompt."""
        return """You are the Voice Agent in the MedAssist AI platform.

YOUR ROLE:
- Process voice-based medical interactions
- Transcribe patient audio input to text for analysis by other agents
- Synthesize AI responses into natural speech for the patient
- Handle voice-specific concerns (unclear audio, background noise, accents)

CAPABILITIES:
- Audio transcription using the transcribe_audio tool
- Text-to-speech synthesis using the synthesize_speech tool
- Voice-optimized response formatting (shorter sentences, clearer structure)

GUIDELINES:
1. When receiving audio input, always use transcribe_audio first
2. Format responses for speech: use simple language, short sentences
3. Avoid complex formatting (tables, bullet points) in voice responses
4. Spell out abbreviations and medical terms phonetically when needed
5. For critical medical information, confirm understanding with the patient
6. If audio quality is poor, ask the patient to repeat clearly

OUTPUT should be conversational, clear, and optimized for spoken delivery."""

    def _get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for OpenAI function calling."""
        return [TRANSCRIBE_AUDIO_TOOL, SYNTHESIZE_SPEECH_TOOL]

    def run(self, agent_input: AgentInput) -> AgentOutput:
        """Execute voice processing.

        Args:
            agent_input: User message (may contain audio transcription request).

        Returns:
            AgentOutput with processed voice interaction result.
        """
        start = time.time()

        logger.info(
            "voice_agent_run_start",
            session_id=agent_input.session_id,
            patient_id=agent_input.patient_id,
        )

        # Build messages and run tool loop
        messages = self._build_messages(agent_input)
        tools = self._get_tools()
        response = self._run_tool_loop(messages, tools, max_iterations=3)

        latency_ms = int((time.time() - start) * 1000)

        # Log usage
        self._log_usage(
            usage=response.usage,
            latency_ms=latency_ms,
            session_id=agent_input.session_id,
        )

        response_text = response.content or ""

        logger.info(
            "voice_agent_run_complete",
            session_id=agent_input.session_id,
            latency_ms=latency_ms,
        )

        return AgentOutput(
            agent_name=self.agent_name,
            session_id=agent_input.session_id,
            response_text=response_text,
            confidence=0.9,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            latency_ms=latency_ms,
        )
