"""Celery tasks for medical report processing.

Enhanced pipeline: S3 fetch -> text extraction -> AI summary -> lab parsing -> notification.

Task #29 — Vikash Kumar
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from celery import shared_task

logger = logging.getLogger(__name__)

__all__ = ["process_medical_report", "generate_report_summary", "extract_lab_values"]


# ---------------------------------------------------------------------------
# Helper: text extraction placeholder (OCR would go here)
# ---------------------------------------------------------------------------

def _extract_text_from_bytes(file_bytes: bytes, file_type: str | None) -> str:
    """Extract text from raw file bytes.

    This is a placeholder for a real OCR / PDF-text-extraction pipeline
    (e.g. Tesseract, AWS Textract, pdf2image + pytesseract).

    Args:
        file_bytes: Raw bytes of the uploaded file.
        file_type: File extension hint (pdf, png, etc.).

    Returns:
        Extracted plain-text content.
    """
    # Attempt naive UTF-8 decode for text-based files
    if file_type in ("txt", "csv", "json"):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            pass

    # For PDF/image files a real implementation would use OCR here
    return f"[Extracted text placeholder — {len(file_bytes)} bytes, type={file_type}]"


def _generate_ai_summary(report_type: str, text_content: str) -> str:
    """Call OpenAI to produce an AI summary of the report text.

    Args:
        report_type: Type of report (lab, imaging, etc.).
        text_content: Plain-text content extracted from the report.

    Returns:
        AI-generated summary string.
    """
    try:
        from app.integrations.openai_client import openai_client

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a medical report summarisation assistant. "
                    "Produce a concise, clinically relevant summary of the "
                    "following medical report. Highlight any abnormal findings."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Report type: {report_type}\n\n"
                    f"Report content:\n{text_content[:4000]}"
                ),
            },
        ]

        response = openai_client.chat_completion(messages=messages, temperature=0.2, max_tokens=1024)
        return response.content or f"AI summary for {report_type} report."
    except Exception as exc:
        logger.warning("AI summary generation failed, using fallback: %s", exc)
        return f"AI summary for {report_type} report (auto-generated fallback)."


def _parse_lab_values(text_content: str) -> list[dict]:
    """Parse lab values from extracted text using OpenAI.

    Args:
        text_content: Plain-text content of a lab report.

    Returns:
        List of dicts with keys: test_name, value, unit, reference_min,
        reference_max, is_abnormal.
    """
    try:
        from app.integrations.openai_client import openai_client

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a lab report parser. Extract all lab test values from "
                    "the text below. Return a JSON array of objects with keys: "
                    "test_name, value (number or null), unit, reference_min (number or null), "
                    "reference_max (number or null), is_abnormal (boolean). "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": text_content[:4000],
            },
        ]

        response = openai_client.chat_completion(
            messages=messages,
            temperature=0.0,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

        parsed = json.loads(response.content or "{}") if response.content else {}
        # Accept either top-level array or {"lab_values": [...]}
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "lab_values" in parsed:
            return parsed["lab_values"]
        return []
    except Exception as exc:
        logger.warning("Lab value parsing failed: %s", exc)
        return []


def _create_notification(patient_id: uuid.UUID, report_id: uuid.UUID, report_title: str) -> None:
    """Create an in-app notification informing the patient their report is ready.

    Args:
        patient_id: UUID of the patient.
        report_id: UUID of the completed report.
        report_title: Human-readable title of the report.
    """
    try:
        from app.extensions import db
        from app.models.notification import Notification

        notification = Notification(
            user_id=patient_id,
            type="report_ready",
            title="Medical Report Ready",
            message=f'Your report "{report_title}" has been processed and is now available for review.',
            data={"report_id": str(report_id)},
            channel="in_app",
        )
        db.session.add(notification)
        db.session.commit()
        logger.info("Notification created for patient %s — report %s", patient_id, report_id)
    except Exception as exc:
        logger.warning("Failed to create notification for patient %s: %s", patient_id, exc)


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_medical_report(self, report_id: str) -> dict:
    """Full pipeline: fetch from S3 -> extract text -> AI summary -> parse labs -> notify.

    Steps:
        1. Set status to ``processing``.
        2. If the report has a file_url, download from S3 and extract text.
        3. Generate an AI summary via OpenAI.
        4. If report_type is ``lab``, parse lab values and store them.
        5. Set status to ``completed``.
        6. Create an in-app notification for the patient.

    Args:
        report_id: UUID string of the MedicalReport to process.

    Returns:
        dict with status, report_id, and optional lab_values_count.
    """
    from app.extensions import db
    from app.models.report import LabValue, MedicalReport

    logger.info("Processing medical report %s", report_id)

    try:
        report = db.session.get(MedicalReport, uuid.UUID(report_id))
        if report is None:
            return {"status": "error", "message": "Report not found"}

        # Step 1 — mark as processing
        report.status = "processing"
        db.session.commit()

        # Step 2 — fetch file from S3 and extract text
        text_content = report.content or ""
        if report.file_url:
            try:
                from app.integrations.s3_client import s3_client

                file_bytes = s3_client.download_file(report.file_url)
                text_content = _extract_text_from_bytes(file_bytes, report.file_type)
            except Exception as exc:
                logger.warning("S3 download failed for report %s: %s", report_id, exc)
                # Continue with whatever content we have

        # Step 3 — AI summary
        summary = _generate_ai_summary(report.report_type, text_content)
        report.ai_summary = summary

        # Step 4 — parse lab values if report_type is 'lab'
        lab_values_count = 0
        if report.report_type == "lab" and text_content:
            lab_entries = _parse_lab_values(text_content)
            for entry in lab_entries:
                lv = LabValue(
                    report_id=report.id,
                    patient_id=report.patient_id,
                    test_name=entry.get("test_name", "Unknown"),
                    value=Decimal(str(entry["value"])) if entry.get("value") is not None else None,
                    unit=entry.get("unit"),
                    reference_min=(
                        Decimal(str(entry["reference_min"]))
                        if entry.get("reference_min") is not None
                        else None
                    ),
                    reference_max=(
                        Decimal(str(entry["reference_max"]))
                        if entry.get("reference_max") is not None
                        else None
                    ),
                    is_abnormal=entry.get("is_abnormal", False),
                )
                db.session.add(lv)
            lab_values_count = len(lab_entries)

        # Step 5 — mark completed
        report.status = "completed"
        report.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Step 6 — notify the patient
        _create_notification(report.patient_id, report.id, report.title)

        return {
            "status": "completed",
            "report_id": report_id,
            "lab_values_count": lab_values_count,
        }

    except Exception as exc:
        logger.exception("Error processing report %s", report_id)
        db.session.rollback()
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def generate_report_summary(self, report_id: str) -> dict:
    """Generate an AI summary for a single report."""
    from app.extensions import db
    from app.models.report import MedicalReport

    try:
        report = db.session.get(MedicalReport, uuid.UUID(report_id))
        if report is None:
            return {"status": "error", "message": "Report not found"}

        text_content = report.content or ""
        if report.file_url:
            try:
                from app.integrations.s3_client import s3_client

                file_bytes = s3_client.download_file(report.file_url)
                text_content = _extract_text_from_bytes(file_bytes, report.file_type)
            except Exception:
                pass

        summary = _generate_ai_summary(report.report_type, text_content)
        report.ai_summary = summary
        report.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return {"status": "ok", "report_id": report_id}
    except Exception as exc:
        db.session.rollback()
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def extract_lab_values(self, report_id: str) -> dict:
    """Extract lab values from a report."""
    from app.extensions import db
    from app.models.report import LabValue, MedicalReport

    try:
        report = db.session.get(MedicalReport, uuid.UUID(report_id))
        if report is None:
            return {"status": "error", "message": "Report not found"}

        text_content = report.content or ""
        if report.file_url:
            try:
                from app.integrations.s3_client import s3_client

                file_bytes = s3_client.download_file(report.file_url)
                text_content = _extract_text_from_bytes(file_bytes, report.file_type)
            except Exception:
                pass

        lab_entries = _parse_lab_values(text_content)
        for entry in lab_entries:
            lv = LabValue(
                report_id=report.id,
                patient_id=report.patient_id,
                test_name=entry.get("test_name", "Unknown"),
                value=Decimal(str(entry["value"])) if entry.get("value") is not None else None,
                unit=entry.get("unit"),
                reference_min=(
                    Decimal(str(entry["reference_min"]))
                    if entry.get("reference_min") is not None
                    else None
                ),
                reference_max=(
                    Decimal(str(entry["reference_max"]))
                    if entry.get("reference_max") is not None
                    else None
                ),
                is_abnormal=entry.get("is_abnormal", False),
            )
            db.session.add(lv)

        db.session.commit()
        return {"status": "ok", "report_id": report_id, "lab_values_extracted": len(lab_entries)}
    except Exception as exc:
        db.session.rollback()
        raise self.retry(exc=exc)
