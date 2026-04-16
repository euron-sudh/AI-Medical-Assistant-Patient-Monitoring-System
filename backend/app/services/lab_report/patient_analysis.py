"""Patient-facing AI analysis, precautions, and normalized urgency (separate from free-form prose)."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

URGENCY_LEVELS = frozenset({"normal", "mild", "moderate", "urgent", "emergency"})


def _keyword_urgency_bump(text: str, current: str) -> str:
    """Conservative rule layer: escalate if critical patterns appear in extraction."""
    t = text.lower()
    critical = (
        "troponin", "st elevation", "hyperkalemia", "k+ 6", "potassium 6",
        "severe hypoglycemia", "glucose 40", "d-dimer", "pe ", "pulmonary embolism",
        "acute kidney injury", "creatinine 10", "bilirubin", "icu",
    )
    if any(c in t for c in critical):
        if current in ("normal", "mild"):
            return "urgent"
        if current == "moderate":
            return "urgent"
    emerg = (
        "cardiac arrest", "stemi", "hemoglobin 5", "hb 5", "severe anemia",
        "altered mental status", "septic shock",
    )
    if any(c in t for c in emerg):
        return "emergency"
    return current


def generate_patient_lab_analysis(
    cleaned_text: str,
    structured_items: list[dict[str, Any]],
    extraction_low_confidence: bool,
) -> dict[str, Any]:
    """Produce structured sections + urgency for UI. Always includes safety disclaimer."""
    items_json = json.dumps(structured_items[:60], ensure_ascii=False)[:8000]
    snippet = cleaned_text[:6000]

    conf_note_low = (
        "Text extraction may be incomplete; results should be verified against your original report."
        if extraction_low_confidence
        else None
    )
    default = {
        "report_summary": "We could not fully analyze this report. Please review the document with your clinician.",
        "key_abnormal_findings": [],
        "what_this_may_indicate": "",
        "precautions": ["Do not change medications or diet based on this summary alone."],
        "general_advice": "Bring a copy of your full report to your next appointment.",
        "recommended_next_steps": "Schedule follow-up with your doctor to review these results.",
        "urgency": "moderate" if extraction_low_confidence else "mild",
        "doctor_consultation": "soon" if extraction_low_confidence else "routine",
        "emergency_guidance": None,
        "extraction_confidence_note": conf_note_low,
        "medical_disclaimer": (
            "This information is educational only and is not a medical diagnosis. "
            "It does not replace advice from a qualified healthcare professional."
        ),
    }

    try:
        from app.integrations.openai_client import openai_client

        messages = [
            {
                "role": "system",
                "content": (
                    "You help patients understand lab results in plain language. "
                    "You must NOT state a definitive diagnosis. Use cautious wording "
                    "(may, might, could). Be conservative: when unsure, recommend doctor review. "
                    "Return ONLY valid JSON with keys: "
                    "report_summary (string), "
                    "key_abnormal_findings (array of strings), "
                    "what_this_may_indicate (string), "
                    "precautions (array of strings), "
                    "general_advice (string), "
                    "recommended_next_steps (string), "
                    "urgency (one of: normal, mild, moderate, urgent, emergency), "
                    "doctor_consultation (one of: none, routine, soon, urgent, emergency), "
                    "emergency_guidance (string or null — only if urgency is urgent/emergency; "
                    "tell user to seek prompt in-person or emergency care when appropriate)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Structured items (JSON):\n{items_json}\n\n"
                    f"Extracted report text (may be partial):\n{snippet}\n\n"
                    f"Extraction_low_confidence: {extraction_low_confidence}\n"
                    "If extraction_low_confidence is true, say conclusions are uncertain and "
                    "urge manual review with a clinician."
                ),
            },
        ]
        response = openai_client.chat_completion(
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.content or "{}")
        if not isinstance(data, dict):
            return default

        urgency = str(data.get("urgency", "mild")).lower()
        if urgency not in URGENCY_LEVELS:
            urgency = "mild"

        urgency = _keyword_urgency_bump(snippet + " " + items_json, urgency)

        consult = str(data.get("doctor_consultation", "routine")).lower()
        if consult not in ("none", "routine", "soon", "urgent", "emergency"):
            consult = "routine"
        if urgency == "emergency":
            consult = "emergency"
        elif urgency == "urgent" and consult in ("none", "routine", "soon"):
            consult = "urgent"

        conf_note = conf_note_low
        return {
            "report_summary": data.get("report_summary") or default["report_summary"],
            "key_abnormal_findings": data.get("key_abnormal_findings") or [],
            "what_this_may_indicate": data.get("what_this_may_indicate") or "",
            "precautions": data.get("precautions") or default["precautions"],
            "general_advice": data.get("general_advice") or default["general_advice"],
            "recommended_next_steps": data.get("recommended_next_steps") or default["recommended_next_steps"],
            "urgency": urgency,
            "doctor_consultation": consult,
            "emergency_guidance": data.get("emergency_guidance"),
            "extraction_confidence_note": conf_note,
            "medical_disclaimer": default["medical_disclaimer"],
        }
    except Exception as exc:
        logger.warning("patient_lab_analysis_failed: %s", exc)
        return default
