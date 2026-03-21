"""SQLAlchemy models for MedAssist AI.

All models are imported here so that Alembic can detect them for migrations.
Team members: import your models here as you create them.

Example:
    from app.models.patient import PatientProfile, MedicalHistory, Allergy  # noqa: F401
"""

from app.models.user import User  # noqa: F401
from app.models.patient import PatientProfile, MedicalHistory, Allergy  # noqa: F401
from app.models.doctor import DoctorProfile  # noqa: F401
from app.models.device import Device  # noqa: F401
from app.models.vitals import VitalsReading  # noqa: F401
from app.models.alert import MonitoringAlert  # noqa: F401
