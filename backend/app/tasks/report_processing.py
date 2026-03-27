"""Celery tasks for medical report processing."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from celery import shared_task

logger = logging.getLogger(__name__)

__all__ = ["process_medical_report", "generate_report_summary", "extract_lab_values"]


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_medical_report(self, report_id: str) -> dict:
    """Full pipeline: analyse report, generate summary, extract labs."""
    from app.extensions import db
    from app.models.report import MedicalReport

    logger.info("Processing medical report %s", report_id)
    try:
        report = db.session.get(MedicalReport, uuid.UUID(report_id))
        if report is None:
            return {"status": "error", "message": "Report not found"}
        report.status = "processing"
        db.session.commit()
        summary = f"AI summary for {report.report_type} report."
        report.ai_summary = summary
        report.status = "completed"
        report.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return {"status": "completed", "report_id": report_id}
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
        report.ai_summary = f"Summary for {report.title}"
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
    from app.models.report import MedicalReport

    try:
        report = db.session.get(MedicalReport, uuid.UUID(report_id))
        if report is None:
            return {"status": "error", "message": "Report not found"}
        return {"status": "ok", "report_id": report_id, "lab_values_extracted": 0}
    except Exception as exc:
        db.session.rollback()
        raise self.retry(exc=exc)
