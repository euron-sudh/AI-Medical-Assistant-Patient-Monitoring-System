"""Celery worker entry point for MedAssist AI background tasks.

Start worker:  celery -A celery_worker.celery worker --loglevel=info
Start beat:    celery -A celery_worker.celery beat --loglevel=info
"""

from app import create_app
from app.extensions import make_celery

app = create_app()
celery = make_celery(app)

# Auto-discover tasks
celery.autodiscover_tasks(["app.tasks"])

# Celery Beat schedule
celery.conf.beat_schedule = {
    "check-all-patient-vitals-every-5-min": {
        "task": "app.tasks.monitoring_tasks.check_all_patient_vitals",
        "schedule": 300.0,
    },
    "escalate-unacknowledged-alerts-every-10-min": {
        "task": "app.tasks.monitoring_tasks.escalate_unacknowledged_alerts",
        "schedule": 600.0,
    },
}
