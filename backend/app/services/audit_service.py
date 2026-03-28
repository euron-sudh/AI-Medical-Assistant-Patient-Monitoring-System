"""Audit service — HIPAA-compliant logging of all PHI access.

Audit logs are immutable: they can be created and queried, but NEVER
updated or deleted. This service intentionally has no update or delete methods.
"""

import csv
import io
import uuid
from datetime import datetime

from sqlalchemy import select

from app.extensions import db
from app.models.audit_log import AuditLog
from app.schemas.notification_schema import AuditLogResponse


class AuditService:
    """Handles creation and querying of HIPAA audit log entries.

    This service enforces immutability: there are no update or delete operations.
    Audit logs must be retained for a minimum of 6 years per HIPAA requirements.
    """

    def create_log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        patient_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_method: str | None = None,
        request_path: str | None = None,
        status_code: int | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """Create an immutable audit log entry.

        Args:
            user_id: UUID string of the user performing the action.
            action: Action type (e.g., 'view', 'create', 'update', 'delete', 'export').
            resource_type: Type of resource accessed (e.g., 'patient_record', 'vitals').
            resource_id: UUID string of the specific resource accessed.
            patient_id: UUID string of the patient whose PHI was accessed.
            ip_address: Client IP address.
            user_agent: Client user agent string.
            request_method: HTTP method (GET, POST, etc.).
            request_path: Request URL path.
            status_code: HTTP response status code.
            details: Additional context as a JSON-serializable dict.

        Returns:
            The created AuditLog record.
        """
        log = AuditLog(
            user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            action=action,
            resource_type=resource_type,
            resource_id=uuid.UUID(resource_id) if resource_id else None,
            patient_id=uuid.UUID(patient_id) if patient_id else None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            status_code=status_code,
            details=details,
        )

        db.session.add(log)
        db.session.commit()

        return log

    def query_logs(
        self,
        user_id: str | None = None,
        patient_id: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogResponse]:
        """Query audit logs with filters. Admin-only operation.

        Args:
            user_id: Filter by the user who performed the action.
            patient_id: Filter by the patient whose PHI was accessed.
            action: Filter by action type.
            resource_type: Filter by resource type.
            start_date: Filter logs created on or after this date.
            end_date: Filter logs created on or before this date.
            limit: Maximum number of logs to return.
            offset: Number of logs to skip.

        Returns:
            List of AuditLogResponse matching the filters.
        """
        stmt = select(AuditLog)

        if user_id:
            stmt = stmt.where(AuditLog.user_id == uuid.UUID(user_id))
        if patient_id:
            stmt = stmt.where(AuditLog.patient_id == uuid.UUID(patient_id))
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)

        stmt = (
            stmt.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        logs = db.session.execute(stmt).scalars().all()
        return [self._to_response(log) for log in logs]

    def export_csv(
        self,
        user_id: str | None = None,
        patient_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        """Export audit logs as CSV string for compliance reporting.

        Args:
            user_id: Filter by user.
            patient_id: Filter by patient.
            start_date: Filter start date.
            end_date: Filter end date.

        Returns:
            CSV-formatted string of audit logs.
        """
        logs = self.query_logs(
            user_id=user_id,
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "user_id", "action", "resource_type", "resource_id",
            "patient_id", "ip_address", "request_method", "request_path",
            "status_code", "created_at",
        ])

        for log in logs:
            writer.writerow([
                log.id, log.user_id, log.action, log.resource_type,
                log.resource_id, log.patient_id, log.ip_address,
                log.request_method, log.request_path, log.status_code,
                log.created_at.isoformat() if log.created_at else "",
            ])

        return output.getvalue()

    def _to_response(self, log: AuditLog) -> AuditLogResponse:
        """Convert an AuditLog model to an AuditLogResponse schema."""
        from app.models.user import User

        user_name = None
        user_email = None
        try:
            user = db.session.get(User, log.user_id)
            if user:
                user_name = f"{user.first_name} {user.last_name}"
                user_email = user.email
        except Exception:
            pass

        return AuditLogResponse(
            id=str(log.id),
            user_id=str(log.user_id),
            user_name=user_name,
            user_email=user_email,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=str(log.resource_id) if log.resource_id else None,
            patient_id=str(log.patient_id) if log.patient_id else None,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            request_method=log.request_method,
            request_path=log.request_path,
            status_code=log.status_code,
            details=log.details,
            created_at=log.created_at,
        )


# Module-level instance for use by routes and middleware
audit_service = AuditService()
