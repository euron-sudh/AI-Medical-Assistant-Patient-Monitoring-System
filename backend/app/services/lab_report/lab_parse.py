"""Structured lab value extraction from cleaned free text (LLM-assisted)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_FALLBACK_LINE = re.compile(
    r"^[\s*]*(?P<name>[A-Za-z][A-Za-z0-9\s\-/%]{1,45}?)[\s:.\-]+"
    r"(?P<val>[<>]?\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[a-zA-Z/%μµ·]+)?"
    r"(?:\s*[\[(]?\s*(?P<ref>[\d.\-–]+\s*[-–]\s*[\d.\-]+)\s*[\])]?)?",
    re.MULTILINE,
)


def heuristic_parse_lines(text: str) -> list[dict[str, Any]]:
    """Best-effort line parse when LLM is unavailable."""
    items: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 5:
            continue
        m = _FALLBACK_LINE.match(line)
        if not m:
            continue
        name = (m.group("name") or "").strip()
        val_s = m.group("val")
        try:
            val = float(val_s.replace("<", "").replace(">", ""))
        except ValueError:
            val = None
        ref = m.group("ref")
        rmin = rmax = None
        if ref:
            parts = re.split(r"[-–]", ref)
            if len(parts) == 2:
                try:
                    rmin = float(parts[0].strip())
                    rmax = float(parts[1].strip())
                except ValueError:
                    pass
        abnormal = False
        if val is not None and rmin is not None and rmax is not None:
            abnormal = val < rmin or val > rmax
        items.append({
            "test_name": name,
            "value": val,
            "value_text": val_s,
            "unit": (m.group("unit") or "").strip() or None,
            "reference_min": rmin,
            "reference_max": rmax,
            "reference_range_text": ref,
            "abnormal_flag": "high" if abnormal and val and rmax and val > rmax else (
                "low" if abnormal and val and rmin and val < rmin else ("normal" if not abnormal else "unclear")
            ),
            "category": None,
            "confidence": 0.35,
        })
    return items[:80]


def llm_parse_labs(cleaned_text: str) -> list[dict[str, Any]]:
    """Use OpenAI JSON mode to extract structured lab rows."""
    try:
        from app.integrations.openai_client import openai_client, OpenAIClientError

        snippet = cleaned_text[:12000]
        messages = [
            {
                "role": "system",
                "content": (
                    "You extract structured laboratory results from report text. "
                    "Return JSON: {\"items\": [ {\"test_name\": str, \"value\": number|null, "
                    "\"value_text\": str|null, \"unit\": str|null, "
                    "\"reference_min\": number|null, \"reference_max\": number|null, "
                    "\"reference_range_text\": str|null, "
                    "\"abnormal_flag\": \"normal\"|\"high\"|\"low\"|\"unclear\", "
                    "\"category\": str|null, \"confidence\": number 0-1 } ] }. "
                    "category examples: CBC, lipid, thyroid, liver, kidney, glucose, electrolyte, other. "
                    "If a value is non-numeric, put it in value_text and value null. "
                    "Do not invent tests not present in the text."
                ),
            },
            {"role": "user", "content": f"Report text:\n{snippet}"},
        ]
        response = openai_client.chat_completion(
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.content or "{}")
        items = parsed.get("items") if isinstance(parsed, dict) else None
        if not isinstance(items, list):
            return []
        out: list[dict[str, Any]] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            out.append({
                "test_name": str(it.get("test_name", "")).strip() or "Unknown",
                "value": it.get("value") if it.get("value") is not None else None,
                "value_text": it.get("value_text"),
                "unit": it.get("unit"),
                "reference_min": it.get("reference_min"),
                "reference_max": it.get("reference_max"),
                "reference_range_text": it.get("reference_range_text"),
                "abnormal_flag": it.get("abnormal_flag") or "unclear",
                "category": it.get("category"),
                "confidence": float(it.get("confidence") or 0.5),
            })
        return out
    except Exception as exc:
        logger.warning("llm_lab_parse_failed: %s", exc)
        return []


def parse_structured_labs(cleaned_text: str) -> list[dict[str, Any]]:
    """Prefer LLM parse; fall back to heuristics if empty."""
    if not cleaned_text or len(cleaned_text.strip()) < 20:
        return []
    llm_items = llm_parse_labs(cleaned_text)
    if len(llm_items) >= 2:
        return llm_items
    heur = heuristic_parse_lines(cleaned_text)
    return heur if heur else llm_items
