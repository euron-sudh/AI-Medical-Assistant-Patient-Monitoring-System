"""Reusable PDF export utilities for MedAssist.

This module generates actual PDF bytes (not markdown renamed to .pdf) with a
clean healthcare-oriented layout usable across multiple exports.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


_BLUE = colors.HexColor("#0F4C81")
_TEAL = colors.HexColor("#0F766E")
_MUTED = colors.HexColor("#475569")


def _now_local_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _escape_basic(text: str) -> str:
    # ReportLab Paragraph supports a small HTML-like markup; escape the rest.
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _markdown_inline_to_para(text: str) -> str:
    """Convert a small subset of markdown inline to ReportLab paragraph markup."""
    safe = _escape_basic(text)
    safe = _BOLD_RE.sub(r"<b>\1</b>", safe)
    return safe


@dataclass(frozen=True)
class PDFSection:
    title: str
    body: list[str]


def build_medassist_pdf(
    *,
    title: str,
    patient_name: str | None,
    sections: list[PDFSection],
    footer_note: str | None = None,
) -> bytes:
    """Build a MedAssist-styled PDF and return PDF bytes."""
    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=title,
        author="MedAssist",
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "MedAssistH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=_BLUE,
        spaceAfter=6,
    )
    sub = ParagraphStyle(
        "MedAssistSub",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=_MUTED,
        spaceAfter=10,
    )
    h2 = ParagraphStyle(
        "MedAssistH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=_TEAL,
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "MedAssistBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=colors.black,
        spaceAfter=4,
    )
    bullet = ParagraphStyle(
        "MedAssistBullet",
        parent=body,
        leftIndent=14,
        bulletIndent=2,
        spaceAfter=2,
    )

    story: list[Any] = []
    story.append(Paragraph(_markdown_inline_to_para(title), h1))

    pn = (patient_name or "").strip() or "Patient"
    story.append(Paragraph(_markdown_inline_to_para(pn), sub))
    story.append(Paragraph(_markdown_inline_to_para(f"Generated: {_now_local_stamp()}"), sub))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1")))
    story.append(Spacer(1, 12))

    for sec in sections:
        if sec.title.strip():
            story.append(Paragraph(_markdown_inline_to_para(sec.title.strip()), h2))
        for raw_line in sec.body:
            line = (raw_line or "").strip()
            if not line:
                story.append(Spacer(1, 6))
                continue
            if line.startswith(("-", "*")) and len(line) > 2 and line[1] == " ":
                story.append(Paragraph(_markdown_inline_to_para(line[2:]), bullet, bulletText="•"))
            else:
                story.append(Paragraph(_markdown_inline_to_para(line), body))

    if footer_note:
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0")))
        story.append(Spacer(1, 8))
        story.append(Paragraph(_markdown_inline_to_para(footer_note), sub))

    doc.build(story)
    return buf.getvalue()


def _split_markdown_into_sections(markdown: str) -> list[PDFSection]:
    """Best-effort mapping of markdown to PDF sections."""
    lines = (markdown or "").replace("\r\n", "\n").split("\n")
    sections: list[PDFSection] = []
    current_title = ""
    current_body: list[str] = []

    def flush() -> None:
        nonlocal current_title, current_body
        if current_title or any(x.strip() for x in current_body):
            sections.append(PDFSection(title=current_title, body=current_body))
        current_title = ""
        current_body = []

    for ln in lines:
        s = ln.strip()
        if s.startswith("### "):
            flush()
            current_title = s[4:].strip()
            continue
        if s.startswith("## "):
            flush()
            current_title = s[3:].strip()
            continue
        if s.startswith("# "):
            # treat as top-level section title (doc title is separate)
            flush()
            current_title = s[2:].strip()
            continue
        current_body.append(ln)

    flush()
    if not sections:
        sections = [PDFSection(title="", body=lines)]
    return sections


def build_lab_tests_pdf(*, patient_name: str | None, recommendation_markdown: str) -> bytes:
    sections = _split_markdown_into_sections(recommendation_markdown)
    return build_medassist_pdf(
        title="MedAssist Lab Tests",
        patient_name=patient_name,
        sections=sections,
        footer_note="This handout is educational and not a diagnosis. For urgent symptoms, seek emergency care.",
    )


def build_lab_report_analysis_pdf(*, patient_name: str | None, analysis: dict[str, Any]) -> bytes:
    pf = (analysis or {}).get("patient_facing") or {}
    if not isinstance(pf, dict):
        pf = {}

    def _lines(v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
        return [str(v)]

    sections: list[PDFSection] = []
    sections.append(PDFSection("Report summary", _lines(pf.get("report_summary"))))
    sections.append(PDFSection("Key abnormal findings", _lines(pf.get("key_abnormal_findings"))))
    sections.append(PDFSection("What this may indicate", _lines(pf.get("what_this_may_indicate"))))
    sections.append(PDFSection("Precautions", _lines(pf.get("precautions"))))
    sections.append(PDFSection("General advice", _lines(pf.get("general_advice"))))
    sections.append(PDFSection("Recommended next steps", _lines(pf.get("recommended_next_steps"))))

    urgency = (pf.get("urgency") or analysis.get("urgency") or "").strip()
    if urgency:
        sections.append(PDFSection("Urgency", [urgency]))

    dc = (pf.get("doctor_consultation") or "").strip()
    if dc and dc.lower() != "none":
        sections.append(PDFSection("Doctor consultation guidance", [dc]))

    eg = pf.get("emergency_guidance")
    if eg:
        sections.append(PDFSection("Emergency recommendation", _lines(eg)))

    if pf.get("extraction_confidence_note"):
        sections.append(PDFSection("Extraction confidence note", _lines(pf.get("extraction_confidence_note"))))

    disclaimer = pf.get("medical_disclaimer") or (
        "This report is educational and not a medical diagnosis. Always follow your clinician’s advice."
    )

    sections = [s for s in sections if any(x.strip() for x in s.body)]
    if not sections:
        sections = [PDFSection("Analysis", ["No analysis content available for this report yet."])]

    return build_medassist_pdf(
        title="MedAssist Lab Report Analysis",
        patient_name=patient_name,
        sections=sections,
        footer_note=str(disclaimer),
    )


def build_image_analysis_pdf(*, patient_name: str | None, analysis: dict[str, Any]) -> bytes:
    """Build PDF for X-Ray / MRI image analysis."""
    img = (analysis or {}).get("image_analysis") or analysis or {}
    if not isinstance(img, dict):
        img = {}

    def _lines(v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
        return [str(v)]

    sections: list[PDFSection] = []
    sections.append(PDFSection("Summary", _lines(img.get("summary"))))
    sections.append(PDFSection("Possible findings / anomalies", _lines(img.get("findings"))))
    sections.append(PDFSection("What this may indicate", _lines(img.get("what_this_may_indicate"))))
    sections.append(PDFSection("Precautions", _lines(img.get("precautions"))))
    sections.append(PDFSection("Next steps", _lines(img.get("next_steps"))))

    urgency = str(img.get("urgency") or "").strip()
    if urgency:
        sections.append(PDFSection("Urgency level", [urgency]))

    consult = str(img.get("consultation_recommendation") or "").strip()
    if consult:
        sections.append(PDFSection("Consultation recommendation", [consult]))

    conf = str(img.get("confidence_note") or "").strip()
    if conf:
        sections.append(PDFSection("Confidence / limitations", [conf]))

    disclaimer = str(img.get("safety_disclaimer") or "").strip() or (
        "This AI image review is informational only and not a diagnosis. "
        "Imaging should be interpreted by a qualified clinician/radiologist."
    )

    sections = [s for s in sections if any(x.strip() for x in s.body)]
    if not sections:
        sections = [PDFSection("Image analysis", ["No analysis content available yet."])]

    return build_medassist_pdf(
        title="MedAssist Image Analysis Report",
        patient_name=(patient_name or "").strip() or "Patient",
        sections=sections,
        footer_note=disclaimer,
    )

