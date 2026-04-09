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
from app.models.monitoring_threshold import MonitoringThreshold  # noqa: F401
from app.models.care_plan import CarePlan, CarePlanGoal, CarePlanActivity  # noqa: F401
from app.models.medication import Medication  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.report import MedicalReport, LabValue  # noqa: F401
from app.models.symptom_session import SymptomSession  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.appointment import Appointment  # noqa: F401
from app.models.telemedicine import TelemedicineSession  # noqa: F401
from app.models.voice_session import VoiceSession  # noqa: F401
