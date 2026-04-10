"""Branded HTML email templates for MedAssist AI transactional emails."""

from __future__ import annotations

from datetime import datetime


_BASE = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>{title}</title>
  </head>
  <body style="margin:0;padding:0;background:#f3f6fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#0f172a;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f3f6fb;padding:32px 16px;">
      <tr>
        <td align="center">
          <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.06);">
            <tr>
              <td style="background:linear-gradient(135deg,#0ea5e9,#2563eb);padding:28px 32px;color:#ffffff;">
                <div style="font-size:12px;letter-spacing:2px;text-transform:uppercase;opacity:0.85;">MedAssist AI</div>
                <div style="font-size:22px;font-weight:700;margin-top:4px;">{header}</div>
              </td>
            </tr>
            <tr>
              <td style="padding:32px;">
                {body}
              </td>
            </tr>
            <tr>
              <td style="padding:20px 32px;background:#f8fafc;border-top:1px solid #e2e8f0;color:#64748b;font-size:12px;line-height:1.5;">
                This is an automated message from MedAssist AI. Please do not reply to this email.<br />
                If you did not expect this, you can safely ignore it.<br />
                &copy; {year} MedAssist AI
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def _wrap(title: str, header: str, body_html: str) -> str:
    return _BASE.format(
        title=title,
        header=header,
        body=body_html,
        year=datetime.utcnow().year,
    )


def appointment_booked_email(
    patient_name: str,
    doctor_name: str,
    specialty: str,
    scheduled_at: datetime,
    duration_minutes: int,
    appointment_type: str,
    reason: str | None,
    appointment_url: str,
) -> tuple[str, str]:
    """Render the 'appointment booked' email. Returns (subject, html)."""
    when = scheduled_at.strftime("%A, %d %B %Y at %H:%M UTC")
    reason_html = (
        f'<p style="margin:12px 0 0;color:#475569;"><strong>Reason:</strong> {reason}</p>'
        if reason
        else ""
    )
    body = f"""
    <p style="margin:0 0 16px;font-size:16px;">Hi {patient_name},</p>
    <p style="margin:0 0 16px;color:#334155;line-height:1.6;">
      Your appointment has been booked. Here are the details:
    </p>
    <div style="border:1px solid #e2e8f0;border-radius:12px;padding:20px;background:#f8fafc;">
      <div style="font-size:14px;color:#64748b;margin-bottom:4px;">Doctor</div>
      <div style="font-size:17px;font-weight:600;color:#0f172a;">{doctor_name}</div>
      <div style="font-size:13px;color:#64748b;margin-top:2px;">{specialty}</div>

      <div style="font-size:14px;color:#64748b;margin:16px 0 4px;">When</div>
      <div style="font-size:16px;color:#0f172a;">{when}</div>

      <div style="font-size:14px;color:#64748b;margin:16px 0 4px;">Type</div>
      <div style="font-size:15px;color:#0f172a;text-transform:capitalize;">{appointment_type.replace('_', ' ')} &middot; {duration_minutes} minutes</div>
      {reason_html}
    </div>
    <div style="margin-top:24px;text-align:center;">
      <a href="{appointment_url}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:10px;font-weight:600;font-size:14px;">View in MedAssist</a>
    </div>
    <p style="margin:24px 0 0;color:#64748b;font-size:13px;line-height:1.6;">
      If you need to reschedule or cancel, please log in to your MedAssist dashboard.
    </p>
    """
    return (
        f"Appointment booked: {doctor_name} on {scheduled_at.strftime('%d %b %Y')}",
        _wrap("Appointment Confirmation", "Appointment Booked", body),
    )


def report_ready_email(
    patient_name: str,
    report_title: str,
    summary: str,
    abnormal_findings: list[str],
    recommended_specialist: str | None,
    urgency_label: str,
    report_url: str,
) -> tuple[str, str]:
    """Render the 'report ready + appointment suggestion' email."""
    findings_html = ""
    if abnormal_findings:
        items = "".join(
            f'<li style="margin-bottom:6px;">{f}</li>' for f in abnormal_findings[:8]
        )
        findings_html = f"""
        <div style="margin-top:20px;">
          <div style="font-size:14px;font-weight:600;color:#b91c1c;margin-bottom:8px;">Items needing attention</div>
          <ul style="margin:0;padding-left:20px;color:#334155;font-size:14px;line-height:1.6;">{items}</ul>
        </div>
        """

    specialist_html = ""
    if recommended_specialist:
        specialist_html = f"""
        <div style="margin-top:20px;padding:16px;border:1px solid #bae6fd;border-radius:10px;background:#f0f9ff;">
          <div style="font-size:13px;color:#0369a1;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Recommended Next Step</div>
          <div style="font-size:16px;color:#0c4a6e;margin-top:6px;">
            Book an appointment with a <strong>{recommended_specialist}</strong>
          </div>
          <div style="font-size:13px;color:#0369a1;margin-top:4px;">Urgency: {urgency_label}</div>
        </div>
        """

    body = f"""
    <p style="margin:0 0 16px;font-size:16px;">Hi {patient_name},</p>
    <p style="margin:0 0 16px;color:#334155;line-height:1.6;">
      Your medical report <strong>{report_title}</strong> has been analyzed by MedAssist AI.
    </p>
    <div style="border:1px solid #e2e8f0;border-radius:12px;padding:18px;background:#f8fafc;">
      <div style="font-size:13px;color:#64748b;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">AI Summary</div>
      <p style="margin:8px 0 0;color:#0f172a;font-size:14px;line-height:1.6;">{summary}</p>
      {findings_html}
    </div>
    {specialist_html}
    <div style="margin-top:24px;text-align:center;">
      <a href="{report_url}" style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:10px;font-weight:600;font-size:14px;">Open full report</a>
    </div>
    <p style="margin:24px 0 0;color:#64748b;font-size:12px;line-height:1.6;">
      This AI analysis is informational only and is not a substitute for professional medical advice.
      Please consult with a qualified healthcare provider before making any decisions.
    </p>
    """
    return (
        f"Your report is ready: {report_title}",
        _wrap("Report Ready", "Your Medical Report", body),
    )
