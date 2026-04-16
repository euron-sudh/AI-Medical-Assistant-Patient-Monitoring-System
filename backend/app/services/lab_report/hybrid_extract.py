"""Hybrid extraction: native PDF text first, per-page OCR fallback; images -> OCR."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

from app.services.lab_report.extraction_quality import overall_native_weak, page_text_quality
from app.services.lab_report.ocr_backends import get_default_ocr_chain

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg"}
PDF_EXT = {"pdf"}

LAB_REPORT_MAX_BYTES = 15 * 1024 * 1024


@dataclass
class HybridExtractionResult:
    raw_text: str
    cleaned_text: str
    document_type: str
    page_metadata: list[dict] = field(default_factory=list)
    low_confidence: bool = False
    notes: list[str] = field(default_factory=list)


def validate_lab_file(filename: str | None, file_bytes: bytes) -> tuple[str, str] | tuple[None, str]:
    """Return (extension, error_message). extension lowercased if ok."""
    if not filename or "." not in filename:
        return None, "A file with a valid extension is required."
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXT | PDF_EXT:
        return None, f"Unsupported file type .{ext}. Use PDF, PNG, or JPEG."
    if len(file_bytes) > LAB_REPORT_MAX_BYTES:
        return None, f"File too large (max {LAB_REPORT_MAX_BYTES // (1024 * 1024)} MB)."
    if len(file_bytes) == 0:
        return None, "Empty file."
    return ext, ""


def clean_extracted_text(text: str) -> str:
    """Normalize whitespace while keeping line breaks for tables."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _ocr_image_bytes(image_png: bytes, ocr_chain: list) -> tuple[str, str]:
    for backend in ocr_chain:
        out = backend.image_to_text(image_png)
        if out and len(out.strip()) > 20:
            return out.strip(), backend.name
    return "", "none"


def extract_from_image(file_bytes: bytes, ext: str, ocr_chain: list | None = None) -> HybridExtractionResult:
    chain = ocr_chain or get_default_ocr_chain()
    # Pillow can open jpeg/png
    text, method = _ocr_image_bytes(file_bytes, chain)
    notes: list[str] = []
    if not text:
        notes.append("OCR produced little or no text; image may be unreadable.")
    low = len(text.strip()) < 50
    cleaned = clean_extracted_text(text)
    meta = [{
        "page_index": 1,
        "method": f"ocr_{method}" if method != "none" else "ocr_failed",
        "char_count": len(cleaned),
    }]
    return HybridExtractionResult(
        raw_text=text,
        cleaned_text=cleaned,
        document_type="image",
        page_metadata=meta,
        low_confidence=low,
        notes=notes,
    )


def extract_from_pdf(file_bytes: bytes, ocr_chain: list | None = None) -> HybridExtractionResult:
    chain = ocr_chain or get_default_ocr_chain()
    notes: list[str] = []
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page_count = len(doc)
    page_metadata: list[dict] = []
    parts: list[str] = []

    for i in range(page_count):
        page = doc[i]
        native = page.get_text("text") or ""
        q = page_text_quality(native)
        method = "native"
        final_text = native.strip()

        if not q["usable"]:
            # Rasterize page for OCR
            try:
                pix = page.get_pixmap(dpi=150, alpha=False)
                png_bytes = pix.tobytes("png")
                ocr_text, ocr_name = _ocr_image_bytes(png_bytes, chain)
                if ocr_text:
                    final_text = ocr_text
                    method = f"ocr_{ocr_name}"
                    notes.append(f"Page {i + 1}: native text weak; used OCR ({ocr_name}).")
                else:
                    notes.append(f"Page {i + 1}: OCR failed or empty; kept weak native text.")
                    final_text = native
                    method = "native_weak"
            except Exception as exc:
                logger.warning("pdf_page_raster_failed page=%s: %s", i + 1, exc)
                notes.append(f"Page {i + 1}: raster/OCR error; using native text.")
                final_text = native
                method = "native_fallback_error"

        page_metadata.append({
            "page_index": i + 1,
            "method": method,
            "native_quality_score": round(q["score"], 3),
            "native_usable": q["usable"],
            "char_count": len(final_text),
        })
        parts.append(f"--- Page {i + 1} ---\n{final_text}")

    doc.close()
    raw = "\n\n".join(parts)
    cleaned = clean_extracted_text(raw)

    # Document-level: if still tiny, mark low confidence
    low = len(cleaned) < 80 or overall_native_weak(page_metadata)

    # Classify document type for UI
    ocr_pages = sum(1 for p in page_metadata if str(p.get("method", "")).startswith("ocr_"))
    if ocr_pages == 0:
        doc_type = "pdf_digital"
    elif ocr_pages >= page_count * 0.7:
        doc_type = "pdf_scanned"
    else:
        doc_type = "pdf_mixed"

    return HybridExtractionResult(
        raw_text=raw,
        cleaned_text=cleaned,
        document_type=doc_type,
        page_metadata=page_metadata,
        low_confidence=low,
        notes=notes,
    )


def hybrid_extract(file_bytes: bytes, ext: str, ocr_chain: list | None = None) -> HybridExtractionResult:
    ext = ext.lower().lstrip(".")
    if ext in ALLOWED_IMAGE_EXT:
        return extract_from_image(file_bytes, ext, ocr_chain)
    if ext in PDF_EXT:
        return extract_from_pdf(file_bytes, ocr_chain)
    return HybridExtractionResult(
        raw_text="",
        cleaned_text="",
        document_type="unknown",
        low_confidence=True,
        notes=["Unsupported document type."],
    )
