"""Pluggable OCR backends: local Tesseract (optional) and OpenAI Vision fallback."""

from __future__ import annotations

import io
import logging
import os
import shutil
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Cache: False = binary missing (skip Tesseract without per-page warnings)
_tesseract_available: bool | None = None


def _tesseract_binary_present() -> bool:
    global _tesseract_available
    if _tesseract_available is not None:
        return _tesseract_available
    _tesseract_available = shutil.which("tesseract") is not None
    if not _tesseract_available:
        logger.info(
            "tesseract_binary_not_in_path — skipping local OCR (install tesseract-ocr or use OpenAI Vision)"
        )
    return _tesseract_available


class OCRBackend(ABC):
    """Abstract OCR: image bytes (PNG/JPEG) -> text."""

    name: str = "base"

    @abstractmethod
    def image_to_text(self, image_bytes: bytes, mime_hint: str = "image/png") -> str:
        raise NotImplementedError


class TesseractOCRBackend(OCRBackend):
    name = "tesseract"

    def image_to_text(self, image_bytes: bytes, mime_hint: str = "image/png") -> str:
        if not _tesseract_binary_present():
            return ""

        try:
            import pytesseract
        except ImportError:
            logger.warning("pytesseract not installed")
            return ""

        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            text = pytesseract.image_to_string(img)
            return (text or "").strip()
        except Exception as exc:
            logger.warning("tesseract_ocr_failed: %s", exc)
            return ""


class OpenAIVisionOCRBackend(OCRBackend):
    name = "openai_vision"

    def __init__(self, model: str | None = None) -> None:
        self._model = model or os.getenv("OPENAI_VISION_OCR_MODEL", "gpt-4o-mini")

    def image_to_text(self, image_bytes: bytes, mime_hint: str = "image/png") -> str:
        try:
            from app.integrations.openai_client import openai_client

            img = Image.open(io.BytesIO(image_bytes))
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

            instruction = (
                "Transcribe ALL visible text from this medical lab report image. "
                "Preserve table structure using line breaks. Include test names, numeric results, "
                "units, and reference ranges. Do not summarize or interpret; output raw text only."
            )
            return openai_client.vision_transcribe_document(
                [png_bytes],
                instruction=instruction,
                model=self._model,
                max_tokens=4096,
            )
        except Exception as exc:
            logger.warning("openai_vision_ocr_failed: %s", exc)
            return ""


def get_default_ocr_chain() -> list[OCRBackend]:
    """Try Tesseract first (no API cost), then OpenAI Vision."""
    return [TesseractOCRBackend(), OpenAIVisionOCRBackend()]
