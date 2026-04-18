"""Flask extension instances, initialized without app context.

Extensions are bound to the app in the application factory (app/__init__.py).
"""

from celery import Celery
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema  # noqa: F401 — re-exported for convenience

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
socketio = SocketIO()
limiter = Limiter(key_func=get_remote_address)


def make_celery(app: Flask) -> Celery:
    """Create a Celery instance tied to the Flask application context.

    Args:
        app: The Flask application instance.

    Returns:
        Configured Celery instance.
    """
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.update(app.config)
    if app.config.get("CELERY_TASK_ALWAYS_EAGER"):
        celery.conf.task_always_eager = True
        celery.conf.task_eager_propagates = bool(app.config.get("CELERY_TASK_EAGER_PROPAGATES", True))

    class ContextTask(celery.Task):
        """Celery task that runs inside the Flask application context."""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
