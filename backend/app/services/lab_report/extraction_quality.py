"""Heuristics for judging whether native PDF text is usable vs needing OCR."""


def page_text_quality(text: str | None) -> dict:
    """Return quality metrics for one page's extracted text.

    Returns:
        dict with keys: usable (bool), score (float 0-1), char_count, reason (str).
    """
    if not text:
        return {"usable": False, "score": 0.0, "char_count": 0, "reason": "empty"}

    stripped = text.strip()
    n = len(stripped)
    if n < 40:
        return {"usable": False, "score": 0.0, "char_count": n, "reason": "too_short"}

    alnum = sum(1 for c in stripped if c.isalnum() or c.isspace())
    ratio = alnum / max(n, 1)
    letters = sum(1 for c in stripped if c.isalpha())
    digits = sum(1 for c in stripped if c.isdigit())

    # Born-digital lab PDFs usually have letters + some digits and reasonable alnum ratio
    usable = letters >= 25 and ratio >= 0.55 and (digits >= 1 or letters >= 60)

    if not usable and letters >= 15 and ratio >= 0.4:
        usable = True  # borderline: allow if not garbage

    score = min(1.0, (ratio * 0.6) + (min(letters, 200) / 200 * 0.4))

    reason = "ok" if usable else "weak_or_garbled"
    return {"usable": usable, "score": float(score), "char_count": n, "reason": reason}


def overall_native_weak(pages: list[dict]) -> bool:
    """True if native extraction across pages looks too poor to trust."""
    if not pages:
        return True
    usable_count = sum(1 for p in pages if p.get("native_usable"))
    total_chars = sum(int(p.get("char_count") or 0) for p in pages)
    if usable_count < len(pages) * 0.5:
        return True
    if total_chars < 80:
        return True
    return False
