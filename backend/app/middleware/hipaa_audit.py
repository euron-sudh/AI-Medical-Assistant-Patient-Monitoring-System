"""HIPAA audit middleware — logs every PHI access to the audit_logs table.

Every endpoint that accesses Protected Health Information MUST use the
@audit_phi_access decorator to ensure HIPAA compliance.
"""

from functools import wraps
from typing import Callable

from flask import request
from flask_jwt_extended import get_jwt_identity, get_jwt


def audit_phi_access(resource_type: str, action: str) -> Callable:
    """Decorator that logs PHI access to the audit_logs table.

    Must be applied AFTER @jwt_required() so that JWT identity is available.

    Usage:
        @bp.route("/patients/<patient_id>/records")
        @jwt_required()
        @audit_phi_access("patient_record", "view")
        def get_patient_records(patient_id):
            ...

    Args:
        resource_type: The type of PHI resource being accessed (e.g., 'patient_record',
                       'vitals', 'medical_report', 'lab_values').
        action: The action being performed (e.g., 'view', 'create', 'update', 'delete',
                'export').

    Returns:
        Decorated function that creates an audit log entry after execution.
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            claims = get_jwt()

            # Execute the wrapped function
            result = fn(*args, **kwargs)

            # Determine status code from response
            if isinstance(result, tuple):
                status_code = result[1]
            else:
                status_code = 200

            # Extract patient_id from route kwargs or request body
            patient_id = kwargs.get("patient_id")
            resource_id = kwargs.get("id") or kwargs.get("report_id") or kwargs.get("alert_id")

            # Create audit log entry (import here to avoid circular imports)
            from app.services.audit_service import audit_service

            audit_service.create_log(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                patient_id=patient_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
                request_method=request.method,
                request_path=request.path,
                status_code=status_code,
                details={
                    "role": claims.get("role"),
                },
            )

            return result

        return wrapper

    return decorator
