# Testing Rules — MedAssist AI

All code in MedAssist AI must be tested. Medical software demands a higher standard — untested code paths are potential patient-safety risks.

---

## Technology Stack

| Layer | Tools |
|---|---|
| Backend unit & integration | pytest, pytest-cov, Factory Boy |
| Frontend unit | Jest, React Testing Library |
| End-to-end | Cypress |
| CI | GitHub Actions |

---

## Test Directory Structure

```
tests/
├── unit/
│   ├── agents/              # Agent logic, tool functions
│   ├── services/            # Service layer business logic
│   ├── repositories/        # Database queries (with test DB)
│   ├── auth/                # Authentication, authorization
│   └── utils/               # Utility functions
├── integration/
│   ├── api/                 # Full API endpoint tests
│   ├── agents/              # Agent → tool → service → DB flows
│   ├── rag/                 # Ingestion and retrieval pipeline
│   └── celery/              # Async task execution
├── e2e/
│   └── cypress/
│       ├── fixtures/
│       ├── e2e/             # User journey specs
│       └── support/
├── factories/               # Factory Boy factories
├── fixtures/                # Shared pytest fixtures
└── conftest.py              # Root conftest
```

- Mirror the `app/` module structure under `tests/unit/`.
- One test file per source module (e.g., `app/services/patient_service.py` → `tests/unit/services/test_patient_service.py`).

---

## Test Pyramid

```
        ▲  E2E (Cypress)         — few, critical user journeys
       ▲ ▲  Integration          — API endpoints, agent flows, DB
      ▲ ▲ ▲  Unit                — bulk of tests, fast, isolated
```

- **Unit tests** are the foundation. They run in milliseconds, mock all external dependencies.
- **Integration tests** verify that components work together. They use a real test PostgreSQL database (via Docker) and mock only external APIs (OpenAI, Pinecone).
- **E2E tests** exercise full user journeys through the browser. Run against a full Docker Compose stack.

---

## Factory Pattern (Factory Boy)

Use Factory Boy for all test data creation. Never use raw SQL inserts or manual object construction in tests.

```python
class PatientFactory(factory.Factory):
    class Meta:
        model = Patient

    id = factory.LazyFunction(uuid4)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    date_of_birth = factory.Faker("date_of_birth", minimum_age=18)
    role = "patient"
    email = factory.Faker("email")

class DoctorFactory(factory.Factory):
    class Meta:
        model = User

    role = "doctor"
    # ...

class VitalsFactory(factory.Factory):
    class Meta:
        model = Vitals

    heart_rate = factory.Faker("random_int", min=60, max=100)
    systolic_bp = factory.Faker("random_int", min=90, max=140)
    diastolic_bp = factory.Faker("random_int", min=60, max=90)
    spo2 = factory.Faker("random_int", min=95, max=100)
    temperature = factory.Faker("pyfloat", min_value=36.0, max_value=37.5)
    respiratory_rate = factory.Faker("random_int", min=12, max=20)
```

- Create factories for every model: `UserFactory`, `PatientFactory`, `DoctorFactory`, `AppointmentFactory`, `VitalsFactory`, `LabResultFactory`, `AuditLogFactory`.
- Use factory traits for edge cases (e.g., `PatientFactory(critical=True)` sets abnormal vitals).

---

## Mocking External Services

### OpenAI API

```python
@pytest.fixture
def mock_openai(mocker):
    mock = mocker.patch("app.agents.base.openai.ChatCompletion.acreate")
    mock.return_value = MockChatCompletion(
        content="Based on the symptoms described...",
        tool_calls=[...],
        usage={"prompt_tokens": 500, "completion_tokens": 200}
    )
    return mock
```

- Mock at the `openai` client level — not inside agent methods.
- Provide realistic mock responses that match the expected structured output schemas.
- Test that agents handle OpenAI errors gracefully: timeout, rate limit (429), invalid response.

### Pinecone

```python
@pytest.fixture
def mock_pinecone(mocker):
    mock_index = mocker.patch("app.rag.retriever.pinecone_index")
    mock_index.query.return_value = MockQueryResponse(
        matches=[
            {"id": "chunk_1", "score": 0.92, "metadata": {...}},
            {"id": "chunk_2", "score": 0.87, "metadata": {...}},
        ]
    )
    return mock_index
```

### InfluxDB

```python
@pytest.fixture
def mock_influxdb(mocker):
    mock = mocker.patch("app.services.vitals_service.influx_client")
    mock.query.return_value = [
        {"time": "2026-03-16T10:00:00Z", "heart_rate": 72, "spo2": 98}
    ]
    return mock
```

- Mock all external services in unit tests.
- In integration tests, use real PostgreSQL and Redis (via Docker) but still mock OpenAI, Pinecone, and InfluxDB.

---

## HIPAA Compliance Tests

These tests are **mandatory** and must pass on every PR.

### Audit Log Tests

```python
def test_viewing_patient_record_creates_audit_log(client, doctor_token, patient):
    response = client.get(
        f"/api/v1/patients/{patient.id}/records",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert response.status_code == 200
    audit = AuditLog.query.filter_by(
        user_id=doctor.id, resource_type="patient_record", patient_id=patient.id
    ).first()
    assert audit is not None
    assert audit.action == "view_patient_record"
    assert audit.status == "success"

def test_denied_access_creates_audit_log(client, patient_token, other_patient):
    response = client.get(
        f"/api/v1/patients/{other_patient.id}/records",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert response.status_code == 403
    audit = AuditLog.query.filter_by(
        patient_id=other_patient.id, status="denied"
    ).first()
    assert audit is not None
```

### PHI Access Control Tests

```python
def test_patient_cannot_access_other_patient_data(client, patient_token, other_patient):
    response = client.get(f"/api/v1/patients/{other_patient.id}/records",
                          headers=auth_header(patient_token))
    assert response.status_code == 403

def test_doctor_cannot_access_unassigned_patient(client, doctor_token, unassigned_patient):
    response = client.get(f"/api/v1/patients/{unassigned_patient.id}/records",
                          headers=auth_header(doctor_token))
    assert response.status_code == 403
```

---

## RBAC Tests

Test every role against every protected endpoint:

```python
@pytest.mark.parametrize("role,endpoint,method,expected_status", [
    ("patient", "/api/v1/admin/users", "GET", 403),
    ("patient", "/api/v1/patients/{own_id}/records", "GET", 200),
    ("doctor", "/api/v1/patients/{assigned_id}/records", "GET", 200),
    ("doctor", "/api/v1/admin/users", "GET", 403),
    ("nurse", "/api/v1/patients/{assigned_id}/vitals", "GET", 200),
    ("admin", "/api/v1/admin/users", "GET", 200),
    ("admin", "/api/v1/audit-logs", "GET", 200),
])
def test_role_access(client, role, endpoint, method, expected_status, ...):
    ...
```

---

## Agent Response Tests

```python
def test_symptom_analyst_returns_structured_output(mock_openai, symptom_input):
    agent = SymptomAnalystAgent()
    result = await agent.run(symptom_input)
    assert isinstance(result, SymptomAnalysisResult)
    assert len(result.differential_diagnoses) > 0
    assert 1 <= result.urgency_score <= 10
    assert result.sources  # Source attribution present

def test_agent_timeout_handling(mock_openai_slow):
    agent = SymptomAnalystAgent()
    with pytest.raises(AgentTimeoutError):
        await agent.run(symptom_input)

def test_agent_deidentifies_phi_before_openai_call(mock_openai, patient_with_phi):
    agent = SymptomAnalystAgent()
    await agent.run(input_with_phi)
    call_args = mock_openai.call_args
    messages_str = str(call_args)
    assert patient_with_phi.ssn not in messages_str
    assert patient_with_phi.full_name not in messages_str
```

---

## Coverage Requirements

| Scope | Minimum Coverage |
|---|---|
| `app/auth/` | **100%** |
| `app/security/` | **100%** |
| `app/services/audit_service.py` | **100%** |
| `app/agents/` | **90%** |
| `app/services/` | **85%** |
| Overall project | **80%** |

- Coverage is enforced in CI. A PR that drops coverage below thresholds is blocked.
- Use `pytest-cov` with `--cov-fail-under=80`.

---

## Integration Test Flows

Test complete user journeys through the API:

```python
class TestPatientSymptomCheckFlow:
    """Full flow: register → login → submit symptoms → get diagnosis."""

    def test_full_flow(self, client, mock_openai, mock_pinecone):
        # 1. Register
        reg = client.post("/api/v1/auth/register", json={...})
        assert reg.status_code == 201

        # 2. Login
        login = client.post("/api/v1/auth/login", json={...})
        assert login.status_code == 200
        token = login.json["access_token"]

        # 3. Submit symptoms
        symptoms = client.post("/api/v1/agents/symptom-analysis",
                               json={"symptoms": "persistent headache, blurred vision"},
                               headers=auth_header(token))
        assert symptoms.status_code == 202  # Accepted (async)
        task_id = symptoms.json["task_id"]

        # 4. Poll for result
        result = client.get(f"/api/v1/tasks/{task_id}",
                            headers=auth_header(token))
        assert result.status_code == 200
        assert "differential_diagnoses" in result.json
        assert result.json["sources"]  # Citations present
```

---

## CI Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: medassist_test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements-test.txt
      - run: pytest tests/ --cov=app --cov-report=xml --cov-fail-under=80
      - uses: codecov/codecov-action@v4

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd frontend && npm ci && npm test -- --coverage

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f docker-compose.test.yml up -d
      - run: cd frontend && npx cypress run
```

- All three test stages must pass for a PR to be mergeable.
- Backend and frontend tests run in parallel; E2E runs after both pass.
- Test results and coverage reports are uploaded as artifacts.
