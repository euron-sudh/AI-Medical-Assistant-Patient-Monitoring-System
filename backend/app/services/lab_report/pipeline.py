"""End-to-end lab report pipeline for API and background tasks."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.services.lab_report.hybrid_extract import hybrid_extract, validate_lab_file
from app.services.lab_report.lab_parse import parse_structured_labs
from app.services.lab_report.patient_analysis import generate_patient_lab_analysis

logger = logging.getLogger(__name__)


@dataclass
class LabPipelineOutput:
    report_id: str | None
    extraction: dict[str, Any]
    structured_lab_values: list[dict[str, Any]]
    patient_analysis: dict[str, Any]
    ai_summary: str
    full_ai_analysis: dict[str, Any]
    status: str


def _build_ai_summary(patient: dict[str, Any]) -> str:
    parts = [
        patient.get("report_summary") or "",
        "",
        f"Urgency: {patient.get('urgency', 'unknown')}.",
        patient.get("recommended_next_steps") or "",
    ]
    return "\n".join(p for p in parts if p).strip()


def run_lab_report_pipeline(
    *,
    file_bytes: bytes,
    filename: str,
    patient_id: uuid.UUID,
    created_by: uuid.UUID,
    title: str | None = None,
    persist: bool = True,
) -> LabPipelineOutput:
    """Run hybrid extract -> parse -> patient analysis; optionally save MedicalReport + LabValues."""
    ext, err = validate_lab_file(filename, file_bytes)
    if ext is None:
        return LabPipelineOutput(
            report_id=None,
            extraction={"error": err},
            structured_lab_values=[],
            patient_analysis={},
            ai_summary="",
            full_ai_analysis={"error": err},
            status="failed",
        )

    try:
        extract = hybrid_extract(file_bytes, ext)
    except Exception as exc:
        logger.exception("hybrid_extract_error: %s", exc)
        return LabPipelineOutput(
            report_id=None,
            extraction={"error": f"Could not read this document: {exc}"},
            structured_lab_values=[],
            patient_analysis={},
            ai_summary="",
            full_ai_analysis={"error": "Document extraction failed."},
            status="failed",
        )

    structured = parse_structured_labs(extract.cleaned_text)
    low_conf = extract.low_confidence or len(extract.cleaned_text.strip()) < 80

    patient = generate_patient_lab_analysis(
        extract.cleaned_text,
        structured,
        extraction_low_confidence=low_conf,
    )
    if low_conf and patient.get("extraction_confidence_note") is None:
        patient["extraction_confidence_note"] = (
            "Extraction quality is low; please compare with your original report and ask your doctor."
        )

    extraction_meta = {
        "document_type": extract.document_type,
        "page_metadata": extract.page_metadata,
        "low_confidence": low_conf,
        "notes": extract.notes,
        "raw_text_length": len(extract.raw_text),
        "cleaned_text_length": len(extract.cleaned_text),
        "raw_text_preview": extract.cleaned_text[:2000] if extract.cleaned_text else "",
    }

    full_analysis = {
        "extraction": extraction_meta,
        "structured_lab_values": structured,
        "patient_facing": patient,
        "urgency": patient.get("urgency"),
        "pipeline_version": 1,
    }

    ai_summary = _build_ai_summary(patient)
    report_id_str: str | None = None

    if persist:
        try:
            report_id_str = _persist_report(
                patient_id=patient_id,
                created_by=created_by,
                title=title or f"Lab report {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC",
                file_bytes=file_bytes,
                ext=ext,
                content=extract.cleaned_text[:65000],
                ai_summary=ai_summary,
                full_analysis=full_analysis,
                structured=structured,
            )
        except Exception as exc:
            logger.exception("persist_lab_report_failed: %s", exc)
            full_analysis["persist_error"] = str(exc)

    return LabPipelineOutput(
        report_id=report_id_str,
        extraction=extraction_meta,
        structured_lab_values=structured,
        patient_analysis=patient,
        ai_summary=ai_summary,
        full_ai_analysis=full_analysis,
        status="completed",
    )


def _persist_report(
    *,
    patient_id: uuid.UUID,
    created_by: uuid.UUID,
    title: str,
    file_bytes: bytes,
    ext: str,
    content: str | None,
    ai_summary: str,
    full_analysis: dict[str, Any],
    structured: list[dict[str, Any]],
) -> str:
    import os

    from app.extensions import db
    from app.models.report import LabValue, MedicalReport
    from app.schemas.report_schema import CreateReportRequest
    from app.services.report_service import report_service

    file_url = None
    try:
        from app.integrations.s3_client import s3_client

        file_url = s3_client.upload_file(file_bytes, str(patient_id), ext)
    except Exception as s3_err:
        logger.warning("lab_upload_s3_fallback: %s", s3_err)
        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "uploads", "reports", str(patient_id),
        )
        os.makedirs(upload_dir, exist_ok=True)
        unique = uuid.uuid4().hex[:12]
        fname = f"lab_{unique}.{ext}"
        filepath = os.path.join(upload_dir, fname)
        with open(filepath, "wb") as f:
            f.write(file_bytes)
        file_url = f"local://{filepath}"

    data = CreateReportRequest(
        report_type="lab",
        title=title[:255],
        content=content,
        file_url=file_url,
        file_type=ext,
    )
    report = report_service.create_report(patient_id, data, created_by=created_by)

    # Replace processing path: mark completed with analysis
    stmt_report = db.session.get(MedicalReport, uuid.UUID(report.id))
    if stmt_report:
        stmt_report.status = "completed"
        stmt_report.ai_summary = ai_summary
        stmt_report.ai_analysis = full_analysis
        stmt_report.updated_at = datetime.now(timezone.utc)

    rid = uuid.UUID(report.id)
    from sqlalchemy import delete

    db.session.execute(delete(LabValue).where(LabValue.report_id == rid))

    for entry in structured:
        val = entry.get("value")
        try:
            dec_val = Decimal(str(val)) if val is not None else None
        except Exception:
            dec_val = None
        rmin = entry.get("reference_min")
        rmax = entry.get("reference_max")
        try:
            dmin = Decimal(str(rmin)) if rmin is not None else None
        except Exception:
            dmin = None
        try:
            dmax = Decimal(str(rmax)) if rmax is not None else None
        except Exception:
            dmax = None
        abnormal = entry.get("abnormal_flag") in ("high", "low")
        if dec_val is not None and dmin is not None and dmax is not None:
            abnormal = abnormal or dec_val < dmin or dec_val > dmax

        lv = LabValue(
            report_id=rid,
            patient_id=patient_id,
            test_name=str(entry.get("test_name", "Unknown"))[:255],
            value=dec_val,
            unit=(str(entry.get("unit"))[:50] if entry.get("unit") else None),
            reference_min=dmin,
            reference_max=dmax,
            is_abnormal=abnormal,
        )
        db.session.add(lv)

    db.session.commit()
    return report.id
