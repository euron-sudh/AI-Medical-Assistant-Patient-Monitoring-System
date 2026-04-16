"""Modular lab report pipeline: hybrid PDF + OCR, parsing, patient-facing AI analysis."""

from app.services.lab_report.pipeline import run_lab_report_pipeline

__all__ = ["run_lab_report_pipeline"]
