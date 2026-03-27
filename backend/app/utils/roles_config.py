"""RBAC Configuration — maps endpoints to allowed roles.

Task #20 (Pallavi Sindkar):
Centralized role-based access control configuration.
Each entry maps a route pattern to the roles that can access it.
"""

# Endpoint pattern → allowed roles mapping
# Used by middleware for consistent authorization across all blueprints
ENDPOINT_ROLES = {
    # Auth (open)
    "/api/v1/auth/register": ["*"],  # Public
    "/api/v1/auth/login": ["*"],  # Public
    "/api/v1/auth/refresh": ["*"],  # Any authenticated
    "/api/v1/auth/me": ["patient", "doctor", "nurse", "admin"],
    "/api/v1/auth/change-password": ["patient", "doctor", "nurse", "admin"],

    # Patient data (own data only for patients)
    "/api/v1/patients": ["doctor", "nurse", "admin"],
    "/api/v1/patients/<id>": ["patient", "doctor", "nurse", "admin"],
    "/api/v1/patients/<id>/medical-history": ["doctor", "nurse", "admin"],
    "/api/v1/patients/<id>/allergies": ["doctor", "nurse", "admin"],

    # Vitals (own data for patients, all for doctors)
    "/api/v1/vitals/<id>": ["patient", "doctor", "nurse", "admin"],

    # Appointments
    "/api/v1/appointments": ["patient", "doctor", "nurse", "admin"],

    # Medications
    "/api/v1/medications/<id>": ["patient", "doctor", "nurse", "admin"],

    # Care plans
    "/api/v1/care-plans": ["patient", "doctor", "nurse", "admin"],

    # Reports
    "/api/v1/reports/<id>": ["patient", "doctor", "nurse", "admin"],

    # Symptoms
    "/api/v1/symptoms/session": ["patient", "doctor", "admin"],
    "/api/v1/symptoms/history/<id>": ["patient", "doctor", "admin"],

    # Chat / AI
    "/api/v1/chat/message": ["patient", "doctor", "nurse", "admin"],

    # Notifications
    "/api/v1/notifications": ["patient", "doctor", "nurse", "admin"],

    # Telemedicine
    "/api/v1/telemedicine/session": ["patient", "doctor", "admin"],

    # Doctors
    "/api/v1/doctors": ["patient", "doctor", "nurse", "admin"],

    # Admin (admin only)
    "/api/v1/admin/users": ["admin"],
    "/api/v1/admin/users/<id>": ["admin"],
    "/api/v1/admin/system/health": ["admin"],
    "/api/v1/admin/ai/config": ["admin"],
    "/api/v1/admin/audit-logs": ["admin"],
    "/api/v1/admin/audit-logs/export": ["admin"],
    "/api/v1/admin/analytics/ai-usage": ["admin"],
    "/api/v1/admin/monitoring/alerts": ["admin"],

    # Monitoring
    "/api/v1/monitoring/alerts": ["doctor", "nurse", "admin"],
    "/api/v1/monitoring/patients": ["doctor", "nurse", "admin"],
}

# Resource-level access rules
# These define who can access WHOSE data
RESOURCE_ACCESS_RULES = {
    "patient": {
        "own_data_only": True,  # Patients can only see their own records
        "can_create_own": True,  # Patients can create their own vitals, appointments
    },
    "doctor": {
        "own_data_only": False,
        "can_see_assigned_patients": True,
        "can_see_all_patients": False,  # Only assigned patients
        "can_create_for_patients": True,
    },
    "nurse": {
        "own_data_only": False,
        "can_see_assigned_patients": True,
        "can_see_all_patients": False,
        "can_create_for_patients": True,
    },
    "admin": {
        "own_data_only": False,
        "can_see_all_patients": True,
        "can_create_for_patients": True,
        "can_manage_users": True,
        "can_view_audit_logs": True,
        "can_configure_system": True,
    },
}

# JWT token expiry by role (in minutes)
TOKEN_EXPIRY_BY_ROLE = {
    "admin": 15,      # Short-lived for security
    "doctor": 60,
    "nurse": 60,
    "patient": 60,
}
