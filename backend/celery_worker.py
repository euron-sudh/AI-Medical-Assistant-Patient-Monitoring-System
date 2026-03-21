"""Celery worker entry point for MedAssist AI background tasks."""

from app import create_app
from app.extensions import make_celery

app = create_app()
celery = make_celery(app)
