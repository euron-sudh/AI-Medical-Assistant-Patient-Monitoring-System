# MedAssist AI - Backend Rules

> Python 3.11+ / Flask 3+ backend for a HIPAA-compliant medical platform.
> **This project uses Flask, NOT FastAPI.**

---

## Framework: Flask 3+

Flask is the backend framework. Do NOT use FastAPI, Django, or any other framework.

### Flask App Factory

```python
# backend/app/__init__.py
def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins=app.config["CORS_ORIGINS"])
    celery_init_app(app)

    # Register blueprints
    from app.api.v1 import api_v1_bp
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")

    # Register middleware
    register_hipaa_audit(app)
    register_error_handlers(app)

    return app
```

---

## Blueprints for Route Organization

Every API domain gets its own Blueprint. All blueprints are registered under `/api/v1/`.

```python
# backend/app/api/v1/__init__.py
from flask import Blueprint

api_v1_bp = Blueprint("api_v1", __name__)

from app.api.v1 import (
    auth, patients, vitals, reports, symptoms,
    medications, appointments, telemedicine,
    care_plans, chat, voice, monitoring,
    devices, notifications, analytics, admin,
)
```

```python
# backend/app/api/v1/vitals.py
from flask import Blueprint

vitals_bp = Blueprint("vitals", __name__, url_prefix="/vitals")

@vitals_bp.route("/", methods=["POST"])
@jwt_required()
@audit_phi_access("vitals", "create")
def create_vitals_reading():
    ...
```

---

## SQLAlchemy 2.0 ORM

Use SQLAlchemy 2.0 style queries (select statements, not legacy Query API).

```python
# CORRECT - SQLAlchemy 2.0 style
from sqlalchemy import select

stmt = select(VitalsReading).where(
    VitalsReading.patient_id == patient_id,
    VitalsReading.recorded_at >= start_date,
).order_by(VitalsReading.recorded_at.desc()).limit(limit)
result = db.session.execute(stmt).scalars().all()

# WRONG - Legacy Query API
# db.session.query(VitalsReading).filter_by(patient_id=patient_id).all()
```

---

## Alembic for Migrations

- Every schema change MUST have an Alembic migration
- Never modify the database schema directly
- Migration messages must be descriptive: `alembic revision -m "add_oxygen_saturation_to_vitals_readings"`
- Always review auto-generated migrations before applying
- Down migrations are mandatory for every up migration

---

## Flask-JWT-Extended for Authentication

```python
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt,
    create_access_token, create_refresh_token,
)

@vitals_bp.route("/<uuid:patient_id>", methods=["GET"])
@jwt_required()
def get_patient_vitals(patient_id: uuid.UUID):
    current_user = get_jwt_identity()
    claims = get_jwt()

    # RBAC enforcement
    if claims["role"] == "patient" and str(current_user) != str(patient_id):
        return jsonify({"error": "Forbidden"}), 403

    vitals = vitals_service.get_patient_vitals(patient_id)
    return jsonify(vitals_schema.dump(vitals, many=True)), 200
```

---

## Request/Response Schemas

Use Pydantic models or dataclasses for validation. Every endpoint has explicit input validation and output serialization.

```python
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class CreateVitalsRequest(BaseModel):
    patient_id: uuid.UUID
    heart_rate: int = Field(ge=20, le=300)
    blood_pressure_systolic: int = Field(ge=50, le=300)
    blood_pressure_diastolic: int = Field(ge=20, le=200)
    temperature: float = Field(ge=90.0, le=115.0)
    oxygen_saturation: float = Field(ge=0, le=100)
    respiratory_rate: int | None = Field(default=None, ge=4, le=60)
    device_id: uuid.UUID | None = None

class VitalsResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    heart_rate: int
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    temperature: float
    oxygen_saturation: float
    recorded_at: datetime
    is_anomalous: bool
```

---

## Service Layer Pattern

Routes MUST NOT contain business logic. The flow is: **Routes -> Services -> Models**

```python
# Route (thin) - only handles HTTP concerns
@vitals_bp.route("/", methods=["POST"])
@jwt_required()
@audit_phi_access("vitals", "create")
def create_vitals_reading():
    data = CreateVitalsRequest.model_validate(request.get_json())
    reading = vitals_service.create_reading(data, created_by=get_jwt_identity())
    return jsonify(VitalsResponse.model_validate(reading).model_dump()), 201

# Service (business logic)
class VitalsService:
    def __init__(self, db_session, monitoring_agent, notification_service):
        self.db = db_session
        self.monitoring = monitoring_agent
        self.notifications = notification_service

    def create_reading(self, data: CreateVitalsRequest, created_by: uuid.UUID) -> VitalsReading:
        reading = VitalsReading(**data.model_dump(), created_by=created_by)
        self.db.add(reading)
        self.db.commit()

        # Trigger async anomaly detection
        check_vitals_anomaly.delay(str(reading.id))

        return reading
```

---

## All Routes Under /api/v1/

Every API endpoint MUST be prefixed with `/api/v1/`.

### API Endpoints

| Prefix                    | Blueprint        | Description                     |
|---------------------------|------------------|---------------------------------|
| `/api/v1/auth`            | `auth`           | Login, register, refresh, logout |
| `/api/v1/patients`        | `patients`       | Patient CRUD, profiles, search   |
| `/api/v1/vitals`          | `vitals`         | Vitals readings CRUD, history    |
| `/api/v1/reports`         | `reports`        | Medical reports, lab results     |
| `/api/v1/symptoms`        | `symptoms`       | Symptom sessions, AI analysis    |
| `/api/v1/medications`     | `medications`    | Prescriptions, drug interactions |
| `/api/v1/appointments`    | `appointments`   | Scheduling, availability         |
| `/api/v1/telemedicine`    | `telemedicine`   | Video sessions, room management  |
| `/api/v1/care-plans`      | `care_plans`     | Care plans, goals, activities    |
| `/api/v1/chat`            | `chat`           | AI chat conversations            |
| `/api/v1/voice`           | `voice`          | Voice interaction endpoints      |
| `/api/v1/monitoring`      | `monitoring`     | Device monitoring, alerts        |
| `/api/v1/devices`         | `devices`        | Device registration, management  |
| `/api/v1/notifications`   | `notifications`  | Notification CRUD, preferences   |
| `/api/v1/analytics`       | `analytics`      | Dashboards, metrics, trends      |
| `/api/v1/admin`           | `admin`          | User management, system config   |

---

## Dependency Injection Pattern for Flask

Use Flask's application context and a simple DI container — not global imports of service instances.

```python
# backend/app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from celery import Celery

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()
celery = Celery()

# backend/app/services/__init__.py
def get_vitals_service() -> VitalsService:
    """Factory function for VitalsService with dependencies."""
    from app.agents.monitoring_agent import MonitoringAgent
    from app.services.notification_service import NotificationService
    return VitalsService(
        db_session=db.session,
        monitoring_agent=MonitoringAgent(),
        notification_service=NotificationService(),
    )
```

---

## Error Handling

All errors return consistent JSON responses. Never expose stack traces in production.

```python
# Standard error response format
{
    "error": "validation_error",
    "message": "Heart rate must be between 20 and 300",
    "details": {...},  # Optional field-level errors
    "request_id": "uuid"
}

# HTTP status code usage
# 200 - Success
# 201 - Created
# 204 - No Content (successful delete)
# 400 - Validation error / bad request
# 401 - Unauthenticated
# 403 - Forbidden (authenticated but not authorized)
# 404 - Resource not found
# 409 - Conflict (duplicate resource)
# 422 - Unprocessable entity
# 429 - Rate limited
# 500 - Internal server error (generic, never expose details)
```

```python
# backend/app/middleware/error_handlers.py
def register_error_handlers(app: Flask):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({
            "error": "bad_request",
            "message": str(e.description),
            "request_id": g.get("request_id"),
        }), 400

    @app.errorhandler(500)
    def internal_error(e):
        logger.error("internal_error", error=str(e), request_id=g.get("request_id"))
        return jsonify({
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "request_id": g.get("request_id"),
        }), 500
```

---

## Background Tasks with Celery + Redis

Long-running tasks MUST be offloaded to Celery workers. Never block Flask request threads.

```python
# Tasks that MUST be async:
# - AI agent invocations (symptom analysis, report reading, triage)
# - Vitals anomaly detection
# - Report PDF generation
# - Notification dispatch (email, SMS, push)
# - Drug interaction checks
# - Care plan compliance checks

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def check_vitals_anomaly(self, reading_id: str):
    try:
        reading = VitalsReading.query.get(reading_id)
        result = monitoring_agent.analyze(reading)
        if result.is_anomalous:
            create_monitoring_alert.delay(reading_id, result.severity)
    except OpenAIError as exc:
        self.retry(exc=exc)
```

---

## Flask-SocketIO for WebSockets

Real-time features use Flask-SocketIO, NOT raw WebSockets.

```python
# Real-time events:
# - vitals_update: New vitals reading for monitored patient
# - alert_triggered: Monitoring alert fired
# - chat_message: AI chat response streaming
# - notification: New notification for user
# - telemedicine_signal: WebRTC signaling for video calls

@socketio.on("subscribe_vitals")
@jwt_required_socket()
def handle_subscribe_vitals(data):
    patient_id = data["patient_id"]
    # Verify access rights before joining room
    if not can_access_patient(current_user, patient_id):
        emit("error", {"message": "Forbidden"})
        return
    join_room(f"patient:{patient_id}:vitals")
```

---

## API Documentation with Flasgger

Every endpoint MUST have Flasgger/Swagger documentation.

```python
@vitals_bp.route("/", methods=["POST"])
@jwt_required()
@swag_from({
    "tags": ["Vitals"],
    "summary": "Create a vitals reading",
    "security": [{"Bearer": []}],
    "parameters": [...],
    "responses": {
        "201": {"description": "Vitals reading created"},
        "400": {"description": "Validation error"},
        "401": {"description": "Unauthenticated"},
        "403": {"description": "Forbidden"},
    },
})
def create_vitals_reading():
    ...
```

---

## Logging with structlog

Use structlog for all logging. Never use `print()` statements.

```python
import structlog

logger = structlog.get_logger(__name__)

# Structured log entries
logger.info("vitals_reading_created",
    patient_id=str(patient_id),
    reading_id=str(reading.id),
    heart_rate=reading.heart_rate,
    is_anomalous=result.is_anomalous,
)

logger.warning("rate_limit_exceeded",
    user_id=str(current_user.id),
    endpoint=request.path,
    ip_address=request.remote_addr,
)
```

---

## HIPAA Audit Middleware

Every endpoint that accesses PHI MUST be decorated with the audit middleware.

```python
def audit_phi_access(resource_type: str, action: str):
    """Decorator that logs PHI access to audit_logs table."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            result = f(*args, **kwargs)

            audit_log = AuditLog(
                user_id=user_id,
                resource_type=resource_type,
                action=action,
                resource_id=kwargs.get("patient_id") or kwargs.get("id"),
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                status_code=result[1] if isinstance(result, tuple) else 200,
            )
            db.session.add(audit_log)
            db.session.commit()

            return result
        return wrapper
    return decorator
```

---

## Testing with pytest + Factory Boy

```python
# Every service must have unit tests
# Every endpoint must have integration tests
# Minimum 80% code coverage

# Factory pattern for test data
class VitalsReadingFactory(factory.Factory):
    class Meta:
        model = VitalsReading

    id = factory.LazyFunction(uuid.uuid4)
    patient_id = factory.LazyFunction(uuid.uuid4)
    heart_rate = factory.Faker("random_int", min=60, max=100)
    blood_pressure_systolic = factory.Faker("random_int", min=90, max=140)
    blood_pressure_diastolic = factory.Faker("random_int", min=60, max=90)
    temperature = factory.Faker("pyfloat", min_value=97.0, max_value=99.5)
    oxygen_saturation = factory.Faker("pyfloat", min_value=95.0, max_value=100.0)

# Test example
def test_create_vitals_reading(client, auth_headers, sample_patient):
    response = client.post(
        "/api/v1/vitals/",
        json={
            "patient_id": str(sample_patient.id),
            "heart_rate": 75,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "temperature": 98.6,
            "oxygen_saturation": 98.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json["heart_rate"] == 75
```
