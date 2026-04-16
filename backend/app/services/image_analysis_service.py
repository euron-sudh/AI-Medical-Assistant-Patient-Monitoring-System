"""X-Ray / MRI image analysis using GPT-4o Vision.

This is a best-effort interpretation assistant. It does not provide a diagnosis.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import re
from typing import Any

from app.integrations.openai_client import openai_client

logger = logging.getLogger(__name__)


ALLOWED_IMAGE_EXTS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_URGENCY = {"normal", "mild", "moderate", "urgent", "emergency"}

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def _extract_json_text(raw: str) -> str:
    """Extract a JSON object from model output (handles ```json fences)."""
    txt = (raw or "").strip()
    if not txt:
        return ""

    # Strip single leading/trailing code fences if present.
    if "```" in txt:
        txt = _FENCE_RE.sub("", txt).strip()

    # If extra prose sneaks in, try to slice the first JSON object.
    start = txt.find("{")
    end = txt.rfind("}")
    if start != -1 and end != -1 and end > start:
        return txt[start : end + 1].strip()
    return txt


def _normalize_analysis(obj: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    out["summary"] = str(obj.get("summary") or "").strip()
    findings = obj.get("findings")
    if isinstance(findings, list):
        out["findings"] = [str(x).strip() for x in findings if str(x).strip()]
    else:
        out["findings"] = []

    out["what_this_may_indicate"] = str(obj.get("what_this_may_indicate") or "").strip()
    precautions = obj.get("precautions")
    if isinstance(precautions, list):
        out["precautions"] = [str(x).strip() for x in precautions if str(x).strip()]
    else:
        out["precautions"] = []

    next_steps = obj.get("next_steps")
    if isinstance(next_steps, list):
        out["next_steps"] = [str(x).strip() for x in next_steps if str(x).strip()]
    else:
        out["next_steps"] = []

    urgency = str(obj.get("urgency") or "").strip().lower()
    out["urgency"] = urgency if urgency in ALLOWED_URGENCY else "moderate"
    out["consultation_recommendation"] = str(obj.get("consultation_recommendation") or "").strip()
    out["confidence_note"] = str(obj.get("confidence_note") or "").strip()
    out["safety_disclaimer"] = str(obj.get("safety_disclaimer") or "").strip() or (
        "This AI image review is informational only and not a diagnosis. "
        "Imaging should be interpreted by a qualified clinician/radiologist."
    )
    return out


def analyze_xray_mri_image(*, image_bytes: bytes, ext: str, model: str = "gpt-4o") -> dict[str, Any]:
    """Analyze an X-ray/MRI image and return a structured dict.

    Raises OpenAIClientError on model failures.
    """
    ext = (ext or "").lower().strip(".")

    # Convert to a PNG data URL for consistent vision input.
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))  # type: ignore[name-defined]
        img = img.convert("RGB")
        img.thumbnail((1600, 1600))
        out_buf = io.BytesIO()  # type: ignore[name-defined]
        img.save(out_buf, format="PNG", optimize=True)
        png_bytes = out_buf.getvalue()
    except Exception as exc:
        logger.warning("image_open_failed: %s", exc)
        png_bytes = image_bytes if ext == "png" else image_bytes

    b64 = base64.b64encode(png_bytes).decode("ascii")
    data_url = f"data:image/png;base64,{b64}"

    instruction = (
        "You are a careful medical imaging assistant. Analyze the provided X-ray, MRI or any other medical lab image.\n"
        "Return a medically cautious, patient-friendly, structured JSON object.\n"
        "Do NOT claim a definitive diagnosis. If image quality is insufficient, say so.\n\n"
        "Output ONLY valid JSON (no markdown), with keys:\n"
        "- summary: string\n"
        "- findings: array of strings\n"
        "- what_this_may_indicate: string\n"
        "- precautions: array of strings\n"
        "- next_steps: array of strings\n"
        "- urgency: one of normal|mild|moderate|urgent|emergency\n"
        "- consultation_recommendation: string\n"
        "- confidence_note: string\n"
        "- safety_disclaimer: string\n"
    )

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]

    res = openai_client.chat_completion(
        messages=messages,
        model=model,
        temperature=0.2,
        max_tokens=900,
    )

    raw = (res.content or "").strip()
    try:
        parsed = json.loads(_extract_json_text(raw))
        if isinstance(parsed, dict):
            return _normalize_analysis(parsed)
    except Exception:
        pass

    # Fallback: keep a safe minimal structure.
    return _normalize_analysis({
        "summary": _extract_json_text(raw)[:1800],
        "findings": [],
        "what_this_may_indicate": "",
        "precautions": [],
        "next_steps": [],
        "urgency": "moderate",
        "consultation_recommendation": "Please consult a clinician/radiologist for an official interpretation.",
        "confidence_note": "The AI output could not be parsed reliably; treat as informational only.",
        "safety_disclaimer": "",
    })

