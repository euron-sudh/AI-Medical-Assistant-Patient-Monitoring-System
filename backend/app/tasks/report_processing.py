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

    Uses hybrid native PDF + OCR pipeline for pdf/png/jpg; plain decode for text files.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        file_type: File extension hint (pdf, png, etc.).

    Returns:
        Extracted plain-text content.
    """
    if file_type in ("txt", "csv", "json"):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            pass

    ext = (file_type or "bin").lower().lstrip(".")
    fname = f"upload.{ext}" if ext else "upload.bin"
    from app.services.lab_report.hybrid_extract import hybrid_extract, validate_lab_file

    ok, err = validate_lab_file(fname, file_bytes)
    if ok is None:
        logger.warning("hybrid_extract_skip: %s", err)
        return f"[Invalid or unsupported file: {err}]"

    try:
        result = hybrid_extract(file_bytes, ok)
        return result.cleaned_text or result.raw_text
    except Exception as exc:
        logger.warning("hybrid_extract_failed: %s", exc)
        return f"[Extraction failed — {len(file_bytes)} bytes, type={file_type}]"


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


def _suggest_appointment(
    report_type: str,
    summary: str,
    abnormal_findings: list[str],
) -> dict:
    """Use the LLM to suggest a follow-up appointment based on report findings.

    Returns a dict with keys: needs_appointment (bool), specialist (str|None),
    urgency (str: routine|soon|urgent|emergency), rationale (str).
    """
    if not abnormal_findings and not summary:
        return {
            "needs_appointment": False,
            "specialist": None,
            "urgency": "routine",
            "rationale": "",
        }

    try:
        from app.integrations.openai_client import openai_client

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a medical triage assistant. Given a report summary and "
                    "abnormal findings, decide whether the patient should book an "
                    "appointment and with what specialist. Return JSON with keys: "
                    "needs_appointment (boolean), specialist (string, e.g. "
                    "'Cardiologist', 'Endocrinologist', 'General Practitioner'), "
                    "urgency ('routine' | 'soon' | 'urgent' | 'emergency'), "
                    "rationale (one short sentence). Err on the side of caution."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Report type: {report_type}\n"
                    f"AI summary: {summary}\n"
                    f"Abnormal findings:\n- "
                    + "\n- ".join(abnormal_findings[:10])
                ),
            },
        ]
        response = openai_client.chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=512,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.content or "{}") if response.content else {}
        return {
            "needs_appointment": bool(parsed.get("needs_appointment", False)),
            "specialist": parsed.get("specialist"),
            "urgency": parsed.get("urgency", "routine"),
            "rationale": parsed.get("rationale", ""),
        }
    except Exception as exc:
        logger.warning("appointment_suggestion_failed: %s", exc)
        if abnormal_findings:
            return {
                "needs_appointment": True,
                "specialist": "General Practitioner",
                "urgency": "soon",
                "rationale": "Abnormal findings detected — follow-up recommended.",
            }
        return {
            "needs_appointment": False,
            "specialist": None,
            "urgency": "routine",
            "rationale": "",
        }


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

        # Step 5 — appointment suggestion based on findings
        abnormal_findings: list[str] = []
        if report.report_type == "lab":
            from app.models.report import LabValue as _LV

            abnormal_values = (
                db.session.query(_LV)
                .filter(_LV.report_id == report.id, _LV.is_abnormal.is_(True))
                .all()
            )
            for lv in abnormal_values:
                unit = lv.unit or ""
                val = f"{lv.value} {unit}".strip() if lv.value is not None else "abnormal"
                abnormal_findings.append(f"{lv.test_name}: {val}")

        suggestion = _suggest_appointment(
            report_type=report.report_type,
            summary=report.ai_summary or "",
            abnormal_findings=abnormal_findings,
        )

        # Persist the appointment suggestion and abnormal findings into ai_analysis JSONB
        report.ai_analysis = {
            "abnormal_findings": abnormal_findings,
            "appointment_suggestion": suggestion,
        }

        # Step 6 — mark completed
        report.status = "completed"
        report.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # Step 7 — notify the patient (in-app + email)
        _create_notification(report.patient_id, report.id, report.title)

        try:
            from app.tasks.notification_tasks import send_report_ready_email

            urgency_label = {
                "routine": "Routine",
                "soon": "Within 1-2 weeks",
                "urgent": "Urgent (within 48 hours)",
                "emergency": "Emergency — seek care now",
            }.get(str(suggestion.get("urgency", "routine")), "Routine")

            send_report_ready_email.delay(
                report_id=str(report.id),
                abnormal_findings=abnormal_findings,
                recommended_specialist=suggestion.get("specialist"),
                urgency_label=urgency_label,
            )
        except Exception as exc:
            logger.warning("report_ready_email_dispatch_failed: %s", exc)

        return {
            "status": "completed",
            "report_id": report_id,
            "lab_values_count": lab_values_count,
            "appointment_suggested": suggestion.get("needs_appointment", False),
            "recommended_specialist": suggestion.get("specialist"),
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
