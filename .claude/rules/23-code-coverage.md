# Code Coverage Rules for MedAssist AI

## Tools

| Component | Tool                    | Command                                         |
| --------- | ----------------------- | ----------------------------------------------- |
| Backend   | pytest-cov              | `pytest --cov=backend --cov-report=html`        |
| Frontend  | Jest (built-in coverage)| `npx jest --coverage`                           |
| E2E       | Cypress (Istanbul)      | `npx cypress run` (with @cypress/code-coverage) |

## Coverage Tiers

### Backend (Python / Flask)

| Category                              | Minimum Coverage | Examples                                              |
| ------------------------------------- | ---------------- | ----------------------------------------------------- |
| Security-critical (auth, HIPAA audit) | 100%             | `auth/`, `audit/`, `middleware/auth.py`, `rbac.py`    |
| Business logic (services, agents)     | 95%              | `services/`, `agents/`, `ai/`                         |
| API endpoints                         | 90%              | `routes/`, `api/`                                     |
| Data access                           | 90%              | `models/`, `repositories/`, `db/`                     |
| Utilities                             | 85%              | `utils/`, `helpers/`, `validators/`                   |

### Frontend (TypeScript / Next.js)

| Category                              | Minimum Coverage | Examples                                              |
| ------------------------------------- | ---------------- | ----------------------------------------------------- |
| Auth components and hooks             | 100%             | `AuthProvider`, `useAuth`, `RoleGuard`                |
| Business logic hooks and services     | 95%              | `useVitals`, `useAlerts`, `apiClient`                 |
| Page components                       | 85%              | `app/patient/`, `app/doctor/`, `app/admin/`           |
| Shared UI components                  | 80%              | `components/shared/`                                  |
| Utility functions                     | 90%              | `lib/`, `utils/`                                      |

## Mandatory Test Scenarios

The following scenarios must have dedicated tests regardless of coverage numbers:

### Authentication and Authorization

- Login flow (valid credentials, invalid credentials, locked account).
- JWT token generation, validation, expiry, and refresh.
- RBAC: each role (patient, doctor, nurse, admin) accessing each route category.
- Unauthorized access attempts return 403 and create audit log entries.

### HIPAA Audit Logging

- Every PHI access event produces an audit log entry.
- Audit logs are immutable (cannot be updated or deleted via API).
- Audit log entries contain: user ID, action, resource, timestamp, IP address.
- Audit log export produces valid CSV with all required fields.

### AI Agent Tool Calls

- Agent invokes correct tools for given prompts.
- Tool call parameters are validated before execution.
- Agent handles tool call failures gracefully.
- Agent respects configured thresholds and confidence levels.
- Token usage is tracked and recorded per interaction.

### Vital Anomaly Detection

- Normal vitals produce no alerts.
- Vitals exceeding warning thresholds produce warning alerts.
- Vitals exceeding critical thresholds produce critical alerts.
- Vitals exceeding emergency thresholds produce emergency alerts.
- NEWS2 and MEWS scores are calculated correctly.
- Duplicate alert suppression works within the 5-minute window.

### PHI Access Audit

- Accessing patient records creates an audit log entry.
- Accessing patient vitals creates an audit log entry.
- Accessing medical reports creates an audit log entry.
- Cross-patient access (doctor accessing unassigned patient) is logged with elevated severity.

## CI Enforcement

### Backend

```yaml
# In CI pipeline (GitHub Actions / GitLab CI)
- name: Run backend tests with coverage
  run: |
    cd backend
    pytest --cov=. --cov-report=xml --cov-report=html --cov-fail-under=80
```

- `--cov-fail-under=80` is the global minimum. The CI pipeline fails if overall coverage drops below 80%.
- Per-module coverage checks are enforced via a custom script that parses the coverage XML report against the tier thresholds.

### Frontend

```yaml
- name: Run frontend tests with coverage
  run: |
    cd frontend
    npx jest --coverage --coverageThreshold='{"global":{"branches":75,"functions":80,"lines":80,"statements":80}}'
```

### Coverage Report Artifacts

- Coverage HTML reports are uploaded as CI artifacts on every pipeline run.
- Coverage trends are tracked over time (comment on PRs with coverage diff).
- Coverage badge displayed in repository README.

## Coverage Configuration

### Backend (`pyproject.toml`)

```toml
[tool.coverage.run]
source = ["backend"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/__pycache__/*",
    "*/conftest.py",
]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
]
```

### Frontend (`jest.config.ts`)

```typescript
collectCoverageFrom: [
  'src/**/*.{ts,tsx}',
  '!src/**/*.d.ts',
  '!src/**/index.ts',
  '!src/**/*.stories.{ts,tsx}',
  '!src/types/**',
],
coverageThreshold: {
  global: {
    branches: 75,
    functions: 80,
    lines: 80,
    statements: 80,
  },
},
```

## Rules

- Never use `# pragma: no cover` without a code review comment explaining why.
- Coverage must not decrease on any PR (enforced by CI coverage diff check).
- New files must include corresponding test files before merging.
- Mock external services (OpenAI, Pinecone, InfluxDB, Twilio, SendGrid) in unit tests; use real services only in integration tests with test credentials.
- Test data must never contain real patient information, even in test environments.
