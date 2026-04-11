"""Generate laboratory test suggestions from a symptom conversation via EURI (OpenAI-compatible)."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from app.config import BaseConfig
from app.integrations.openai_client import OpenAIClient, OpenAIClientError

SYSTEM_PROMPT = """You are a clinical documentation assistant (not a treating physician).

You receive a transcript of a voice conversation between a patient and an AI symptom intake assistant.

Task: propose a concise, evidence-informed list of **laboratory tests and panels** that a licensed clinician might consider ordering based *only* on the reported symptoms and context. Do not diagnose. Use neutral language ("may be considered", "often used to evaluate").

Output **Markdown** with this structure:
1. Title: "# Suggested laboratory evaluation"
2. Short disclaimer: not medical advice; patient must see a qualified clinician; emergency symptoms require urgent care.
3. "## Suggested tests" — bullet list. For each test: **Test name** — one-line rationale tied to reported symptoms.
4. "## Notes for your clinician" — bullet points summarizing chief complaint and key symptoms (no fabricated vitals or exam findings).

If the transcript is too vague, list only basic screening (e.g. CBC, CMP) and state what additional information would help.

Do not invent patient statements that are not in the transcript."""


def _lab_openai_client() -> OpenAIClient:
    """Chat completions for lab reports: EURI_API_KEY, EURI_BASE_URL, OPENAI_MODEL_FAST."""
    api_key = (os.getenv("EURI_API_KEY") or "").strip() or BaseConfig.OPENAI_API_KEY
    euri_base = (os.getenv("EURI_BASE_URL") or "").strip() or BaseConfig.EURI_BASE_URL
    fast_model = (os.getenv("OPENAI_MODEL_FAST") or "").strip() or BaseConfig.OPENAI_MODEL_FAST
    return OpenAIClient(
        api_key=api_key,
        default_model=fast_model,
        base_url=euri_base or None,
    )


def generate_lab_report_markdown(transcript: str) -> str:
    """Produce a markdown lab-suggestion document using OPENAI_MODEL_FAST on EURI."""
    transcript = (transcript or "").strip()
    if not transcript:
        return ""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Conversation transcript:\n\n{transcript}\n\nProduce the Markdown document now.",
        },
    ]

    client = _lab_openai_client()
    try:
        result = client.chat_completion(
            messages,
            model=None,
            temperature=0.25,
            max_tokens=4096,
        )
    except OpenAIClientError:
        raise

    text = (result.content or "").strip()
    if not text:
        raise OpenAIClientError("Empty lab recommendation response from model", retryable=False)
    return text


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
