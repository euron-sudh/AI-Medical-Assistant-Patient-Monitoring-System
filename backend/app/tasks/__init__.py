"""Celery background tasks for MedAssist AI.

Import all task modules here so Celery auto-discovers them when the
worker starts via ``celery_worker.py``.
"""

from app.tasks.report_processing import *  # noqa: F401,F403
from app.tasks.notification_tasks import *  # noqa: F401,F403
from app.tasks.monitoring_tasks import *  # noqa: F401,F403
