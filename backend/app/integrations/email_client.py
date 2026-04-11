"""Email client for transactional emails.

Prefers SendGrid when ``SENDGRID_API_KEY`` is configured, falls back to SMTP
when ``SMTP_HOST`` is set, and becomes a no-op logger otherwise so local/dev
environments without mail credentials don't crash on import or on send.

All send paths return ``True`` on success and ``False`` on failure. Callers
should treat email as best-effort: a failed send is logged but does not raise.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable

from flask import current_app

logger = logging.getLogger(__name__)


class EmailClient:
    """Unified email sender with SendGrid + SMTP fallback."""

    def _config(self, key: str, default: str = "") -> str:
        try:
            return current_app.config.get(key, default) or default
        except RuntimeError:
            # No Flask app context (e.g. direct Celery worker invocation).
            import os

            return os.getenv(key, default) or default

    def _from_address(self) -> tuple[str, str]:
        name = self._config("SMTP_FROM_NAME", "MedAssist AI")
        sender = (
            self._config("SMTP_FROM_EMAIL")
            or self._config("SENDGRID_FROM_EMAIL")
            or self._config("SMTP_USERNAME")
            or "noreply@medassist.ai"
        )
        return name, sender

    def send(
        self,
        to: str | Iterable[str],
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        """Send an email to one or more recipients."""
        if isinstance(to, str):
            recipients = [to]
        else:
            recipients = [addr for addr in to if addr]

        if not recipients:
            logger.warning("email_send_skipped_no_recipients subject=%s", subject)
            return False

        # Prefer SendGrid if configured
        if self._config("SENDGRID_API_KEY"):
            return self._send_via_sendgrid(recipients, subject, html_body, text_body)

        # Fall back to SMTP
        if self._config("SMTP_HOST"):
            return self._send_via_smtp(recipients, subject, html_body, text_body)

        # No provider configured — log and move on (dev mode)
        logger.info(
            "email_send_noop provider=none to=%s subject=%s",
            ",".join(recipients),
            subject,
        )
        return False

    def _send_via_sendgrid(
        self,
        recipients: list[str],
        subject: str,
        html_body: str,
        text_body: str | None,
    ) -> bool:
        try:
            import sendgrid  # type: ignore
            from sendgrid.helpers.mail import Content, Email, Mail, To  # type: ignore
        except ImportError:
            logger.warning("sendgrid_not_installed_falling_back_to_smtp")
            if self._config("SMTP_HOST"):
                return self._send_via_smtp(recipients, subject, html_body, text_body)
            return False

        try:
            from_name, from_addr = self._from_address()
            sg = sendgrid.SendGridAPIClient(api_key=self._config("SENDGRID_API_KEY"))
            mail = Mail(
                from_email=Email(from_addr, from_name),
                to_emails=[To(addr) for addr in recipients],
                subject=subject,
                html_content=Content("text/html", html_body),
            )
            if text_body:
                mail.add_content(Content("text/plain", text_body))
            response = sg.send(mail)
            logger.info(
                "email_sent_via_sendgrid to=%s subject=%s status=%s",
                ",".join(recipients),
                subject,
                getattr(response, "status_code", "?"),
            )
            return True
        except Exception:
            logger.exception("sendgrid_send_failed to=%s", recipients)
            return False

    def _send_via_smtp(
        self,
        recipients: list[str],
        subject: str,
        html_body: str,
        text_body: str | None,
    ) -> bool:
        host = self._config("SMTP_HOST")
        port = int(self._config("SMTP_PORT", "587") or 587)
        username = self._config("SMTP_USERNAME")
        password = self._config("SMTP_PASSWORD")
        use_tls = str(self._config("SMTP_USE_TLS", "true")).lower() == "true"

        from_name, from_addr = self._from_address()

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_addr}>"
        msg["To"] = ", ".join(recipients)
        msg.set_content(text_body or _html_to_text(html_body))
        msg.add_alternative(html_body, subtype="html")

        try:
            with smtplib.SMTP(host, port, timeout=15) as server:
                if use_tls:
                    server.starttls()
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
            logger.info(
                "email_sent_via_smtp to=%s subject=%s host=%s",
                ",".join(recipients),
                subject,
                host,
            )
            return True
        except Exception:
            logger.exception("smtp_send_failed host=%s to=%s", host, recipients)
            return False


def _html_to_text(html: str) -> str:
    """Minimal HTML stripping for plain-text fallback."""
    import re

    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</(p|div|li|h[1-6])>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


# Singleton instance
email_client = EmailClient()
