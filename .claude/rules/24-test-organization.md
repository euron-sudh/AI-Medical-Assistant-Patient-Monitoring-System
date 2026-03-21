# Test Organization for MedAssist AI

## Backend Test Structure

```
backend/
└── tests/
    ├── conftest.py                      # Shared fixtures, app factory, test DB setup
    ├── factories/                       # Factory Boy model factories
    │   ├── __init__.py
    │   ├── user_factory.py              # PatientFactory, DoctorFactory, NurseFactory, AdminFactory
    │   ├── vitals_factory.py            # VitalsFactory, VitalsReadingFactory
    │   ├── appointment_factory.py       # AppointmentFactory
    │   ├── report_factory.py            # MedicalReportFactory, AIReportFactory
    │   ├── prescription_factory.py      # PrescriptionFactory
    │   ├── alert_factory.py             # MonitoringAlertFactory
    │   └── notification_factory.py      # NotificationFactory
    ├── fixtures/                        # Static test data (JSON, CSV)
    │   ├── patient_data.json            # Sample patient profiles
    │   ├── doctor_data.json             # Sample doctor profiles
    │   ├── vitals_data.json             # Sample vital readings (normal, warning, critical, emergency)
    │   ├── reports_data.json            # Sample medical reports
    │   ├── openai_responses.json        # Mocked OpenAI API responses
    │   └── pinecone_responses.json      # Mocked Pinecone query results
    ├── unit/
    │   ├── services/
    │   │   ├── test_auth_service.py
    │   │   ├── test_patient_service.py
    │   │   ├── test_vitals_service.py
    │   │   ├── test_appointment_service.py
    │   │   ├── test_prescription_service.py
    │   │   ├── test_notification_service.py
    │   │   ├── test_report_service.py
    │   │   ├── test_alert_service.py
    │   │   └── test_audit_service.py
    │   ├── agents/
    │   │   ├── test_symptom_agent.py
    │   │   ├── test_triage_agent.py
    │   │   ├── test_report_agent.py
    │   │   ├── test_monitoring_agent.py
    │   │   └── test_care_plan_agent.py
    │   ├── models/
    │   │   ├── test_user_model.py
    │   │   ├── test_vitals_model.py
    │   │   └── test_alert_model.py
    │   └── utils/
    │       ├── test_validators.py
    │       ├── test_encryption.py
    │       ├── test_news2_calculator.py
    │       └── test_phi_redaction.py
    ├── integration/
    │   ├── api/
    │   │   ├── test_auth_endpoints.py
    │   │   ├── test_patient_endpoints.py
    │   │   ├── test_doctor_endpoints.py
    │   │   ├── test_admin_endpoints.py
    │   │   ├── test_vitals_endpoints.py
    │   │   ├── test_appointment_endpoints.py
    │   │   ├── test_telemedicine_endpoints.py
    │   │   ├── test_report_endpoints.py
    │   │   ├── test_alert_endpoints.py
    │   │   └── test_webhook_endpoints.py
    │   ├── agents/
    │   │   ├── test_symptom_agent_integration.py
    │   │   ├── test_triage_agent_integration.py
    │   │   └── test_monitoring_agent_integration.py
    │   └── integrations/
    │       ├── test_openai_adapter.py
    │       ├── test_pinecone_adapter.py
    │       ├── test_influxdb_adapter.py
    │       ├── test_twilio_adapter.py
    │       └── test_sendgrid_adapter.py
    └── e2e/
        ├── test_patient_symptom_flow.py     # Patient submits symptoms → AI analysis → report
        ├── test_vital_alert_flow.py         # Vital logged → alert generated → nurse notified → escalation
        ├── test_appointment_flow.py         # Book → confirm → reminder → telemedicine → summary
        ├── test_prescription_flow.py        # Doctor prescribes → patient notified → reminder set
        └── test_admin_user_management.py    # Admin creates user → assigns role → verifies access
```

## Frontend Test Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── shared/
│   │   │   ├── VideoCall/
│   │   │   │   ├── VideoCall.tsx
│   │   │   │   └── __tests__/
│   │   │   │       └── VideoCall.test.tsx
│   │   │   ├── ChatWindow/
│   │   │   │   ├── ChatWindow.tsx
│   │   │   │   └── __tests__/
│   │   │   │       └── ChatWindow.test.tsx
│   │   │   └── VitalsChart/
│   │   │       ├── VitalsChart.tsx
│   │   │       └── __tests__/
│   │   │           └── VitalsChart.test.tsx
│   │   ├── patient/
│   │   │   └── __tests__/               # Tests colocated with patient components
│   │   ├── doctor/
│   │   │   └── __tests__/               # Tests colocated with doctor components
│   │   └── admin/
│   │       └── __tests__/               # Tests colocated with admin components
│   ├── hooks/
│   │   ├── __tests__/
│   │   │   ├── useAuth.test.ts
│   │   │   ├── useVitals.test.ts
│   │   │   ├── useAlerts.test.ts
│   │   │   ├── useWebSocket.test.ts
│   │   │   └── useNotifications.test.ts
│   │   └── ...
│   └── lib/
│       ├── __tests__/
│       │   ├── apiClient.test.ts
│       │   ├── validators.test.ts
│       │   └── formatters.test.ts
│       └── ...
├── cypress/
│   ├── e2e/
│   │   ├── patient/
│   │   │   ├── symptom-checker.cy.ts
│   │   │   ├── vitals-logging.cy.ts
│   │   │   ├── appointments.cy.ts
│   │   │   └── profile.cy.ts
│   │   ├── doctor/
│   │   │   ├── patient-monitoring.cy.ts
│   │   │   ├── prescriptions.cy.ts
│   │   │   └── telemedicine.cy.ts
│   │   ├── admin/
│   │   │   ├── user-management.cy.ts
│   │   │   ├── audit-logs.cy.ts
│   │   │   └── system-health.cy.ts
│   │   └── auth/
│   │       ├── login.cy.ts
│   │       ├── registration.cy.ts
│   │       └── rbac.cy.ts
│   ├── fixtures/
│   │   ├── patient.json
│   │   ├── doctor.json
│   │   ├── vitals.json
│   │   └── appointments.json
│   └── support/
│       ├── commands.ts                  # Custom Cypress commands (login, seed data)
│       └── e2e.ts
└── jest.config.ts
```

## Fixtures

### Patient Data (`tests/fixtures/patient_data.json`)

```json
{
  "valid_patient": {
    "email": "patient.test@example.com",
    "name": "Test Patient",
    "role": "patient",
    "date_of_birth": "1990-01-15",
    "blood_type": "A+",
    "allergies": ["penicillin"],
    "emergency_contact": "+15551234567"
  }
}
```

### Vitals Data (`tests/fixtures/vitals_data.json`)

Include samples for each severity level:

```json
{
  "normal": {
    "heart_rate": 72, "blood_pressure_systolic": 120, "blood_pressure_diastolic": 80,
    "spo2": 98, "temperature": 36.8, "respiratory_rate": 16
  },
  "warning": {
    "heart_rate": 105, "blood_pressure_systolic": 145, "blood_pressure_diastolic": 92,
    "spo2": 94, "temperature": 37.8, "respiratory_rate": 22
  },
  "critical": {
    "heart_rate": 135, "blood_pressure_systolic": 170, "blood_pressure_diastolic": 105,
    "spo2": 90, "temperature": 39.2, "respiratory_rate": 28
  },
  "emergency": {
    "heart_rate": 160, "blood_pressure_systolic": 200, "blood_pressure_diastolic": 120,
    "spo2": 83, "temperature": 40.5, "respiratory_rate": 35
  }
}
```

## Factory Boy Factories (Backend)

All factories inherit from `factory.alchemy.SQLAlchemyModelFactory` and use the test database session.

```python
# tests/factories/user_factory.py
import factory
from backend.models import User

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    id = factory.Faker("uuid4")
    email = factory.Faker("email")
    name = factory.Faker("name")
    role = "patient"
    is_active = True

class PatientFactory(UserFactory):
    role = "patient"

class DoctorFactory(UserFactory):
    role = "doctor"

class NurseFactory(UserFactory):
    role = "nurse"

class AdminFactory(UserFactory):
    role = "admin"
```

## Test Configuration

### Separate Test Databases and Services

| Service       | Test Configuration                                        |
| ------------- | --------------------------------------------------------- |
| PostgreSQL    | Separate test database (`medassist_test`), reset per test suite |
| Redis         | Separate test instance (DB 1) or mock, flush between tests |
| OpenAI        | Mock via `unittest.mock` or `responses` library           |
| Pinecone      | Mock adapter returning fixture data                       |
| InfluxDB      | Mock adapter or test bucket (`patient_vitals_test`)       |
| Twilio        | Mock via `unittest.mock`, never send real SMS in tests    |
| SendGrid      | Mock via `unittest.mock`, never send real emails in tests |
| S3 / MinIO    | Test bucket (`medassist-files-test`) or mock via `moto`   |
| Daily.co      | Mock REST API responses                                   |

### Backend Test Config (`tests/conftest.py`)

```python
import pytest
from backend import create_app
from backend.extensions import db as _db

@pytest.fixture(scope="session")
def app():
    app = create_app(config="testing")
    return app

@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    """Return JWT auth headers for each role."""
    def _headers(role="patient"):
        # Login and get token for the given role
        ...
        return {"Authorization": f"Bearer {token}"}
    return _headers

@pytest.fixture
def mock_openai(mocker):
    """Mock OpenAI API calls."""
    return mocker.patch("backend.integrations.openai_adapter.client")

@pytest.fixture
def mock_pinecone(mocker):
    """Mock Pinecone queries."""
    return mocker.patch("backend.integrations.pinecone_adapter.index")
```

## CI Pipeline Order

Tests run in this order. Each stage must pass before the next begins:

```
1. Unit Tests        (fast, no external dependencies, mocked services)
   ├── Backend:  pytest tests/unit/ --cov
   └── Frontend: npx jest --testPathPattern="__tests__"

2. Integration Tests (test databases, mocked external APIs)
   ├── Backend:  pytest tests/integration/ --cov
   └── Frontend: (API integration tests if applicable)

3. E2E Tests         (full stack, Cypress for frontend, pytest for backend flows)
   ├── Backend:  pytest tests/e2e/
   └── Frontend: npx cypress run
```

### Parallelization

- Unit tests run in parallel (pytest-xdist: `pytest -n auto`).
- Integration tests run sequentially (shared test database).
- E2E tests run sequentially (full application state).

## Naming Conventions

| Convention            | Pattern                          | Example                              |
| --------------------- | -------------------------------- | ------------------------------------ |
| Test file (backend)   | `test_{module}.py`               | `test_auth_service.py`               |
| Test file (frontend)  | `{Component}.test.tsx`           | `VideoCall.test.tsx`                 |
| Test function         | `test_{action}_{scenario}`       | `test_login_with_invalid_password`   |
| Test class            | `Test{Module}{Feature}`          | `TestAuthServiceLogin`               |
| Fixture               | Descriptive noun                 | `patient_with_vitals`                |
| Factory               | `{Model}Factory`                 | `PatientFactory`                     |
| Cypress spec          | `{feature}.cy.ts`                | `symptom-checker.cy.ts`             |

## Rules

- Every new feature branch must include tests before merge.
- Test files mirror the source file structure.
- No test should depend on another test's state (tests must be independent and idempotent).
- Use factories and fixtures, never hardcode test data inline.
- All test data must be synthetic. Never use real patient data, even anonymized.
- Tests that require external network calls must be marked with `@pytest.mark.integration` or `@pytest.mark.e2e`.
- Flaky tests must be fixed immediately or quarantined with `@pytest.mark.skip(reason="flaky: <ticket>")`.
