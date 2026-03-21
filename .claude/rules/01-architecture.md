# MedAssist AI - Architecture Rules

> Clean Architecture with strict layer separation for a HIPAA-compliant medical platform.

---

## Layer Hierarchy

```
┌─────────────────────────────────────────────────┐
│           Next.js Presentation Layer             │
│   (Patient Portal / Doctor Dashboard / Admin)    │
├─────────────────────────────────────────────────┤
│              Flask API Gateway                   │
│        (REST + WebSocket endpoints)              │
├─────────────────────────────────────────────────┤
│           Application Services                   │
│     (Use cases, orchestration, validation)        │
├─────────────────────────────────────────────────┤
│         Domain / Business Logic                  │
│    (Entities, value objects, domain rules)        │
├─────────────────────────────────────────────────┤
│              Repositories                        │
│      (Data access abstractions)                  │
├─────────────────────────────────────────────────┤
│             Infrastructure                       │
│  PostgreSQL │ Redis │ InfluxDB │ Pinecone │ S3   │
└─────────────────────────────────────────────────┘
```

### Dependency Rule

Dependencies MUST point inward only. Outer layers depend on inner layers, never the reverse.

- Presentation depends on API Gateway
- API Gateway depends on Application Services
- Application Services depend on Domain Logic
- Domain Logic depends on nothing (pure business rules)
- Repositories implement interfaces defined in Domain
- Infrastructure is injected, never imported directly by Domain

---

## 4-Layer System Diagram

```
Client (Browser/Mobile)
    │
    ▼
API Gateway (Kong/Nginx + Flask Routes)
    │
    ▼
Backend Services (Flask App Services + Celery Workers)
    │
    ├──► Agentic AI Layer (7 AI Agents via OpenAI APIs)
    │
    ▼
Data Layer (PostgreSQL + Redis + InfluxDB + Pinecone + S3 + Elasticsearch)
```

---

## Documentation-First Approach

Before writing code, check the relevant documentation:

| Decision Area        | Reference Document           |
|----------------------|------------------------------|
| Feature scope        | `docs/PRD.md`                |
| System design        | `docs/ARCHITECTURE.md`       |
| API contracts        | `docs/API.md`                |
| Database schema      | `docs/DATABASE.md`           |
| Deployment config    | `docs/DEPLOYMENT.md`         |
| Project context      | `CLAUDE.md`                  |

**Rules:**
- Every new feature MUST have a corresponding section in PRD.md before implementation
- API endpoints MUST be documented in API.md before or at the time of implementation
- Schema changes MUST be reflected in DATABASE.md and have an Alembic migration
- Architecture decisions MUST be recorded as ADRs in `docs/adr/`

---

## Directory Structure

### Backend (`backend/`)

```
backend/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Environment-based configuration
│   ├── extensions.py            # Flask extension instances
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py          # Authentication routes
│   │       ├── patients.py      # Patient routes
│   │       ├── vitals.py        # Vitals routes
│   │       ├── reports.py       # Medical reports routes
│   │       ├── symptoms.py      # Symptom analysis routes
│   │       ├── medications.py   # Medication routes
│   │       ├── appointments.py  # Appointment routes
│   │       ├── telemedicine.py  # Telemedicine routes
│   │       ├── care_plans.py    # Care plan routes
│   │       ├── chat.py          # AI chat routes
│   │       ├── voice.py         # Voice interaction routes
│   │       ├── monitoring.py    # Device monitoring routes
│   │       ├── notifications.py # Notification routes
│   │       ├── analytics.py     # Analytics routes
│   │       └── admin.py         # Admin routes
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── patient_service.py
│   │   ├── vitals_service.py
│   │   ├── report_service.py
│   │   ├── medication_service.py
│   │   ├── appointment_service.py
│   │   ├── telemedicine_service.py
│   │   ├── care_plan_service.py
│   │   ├── notification_service.py
│   │   └── analytics_service.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── doctor.py
│   │   ├── vitals.py
│   │   ├── report.py
│   │   ├── medication.py
│   │   ├── appointment.py
│   │   ├── care_plan.py
│   │   ├── device.py
│   │   ├── notification.py
│   │   └── audit_log.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py        # Abstract base agent
│   │   ├── symptom_analyst.py
│   │   ├── report_reader.py
│   │   ├── triage_agent.py
│   │   ├── voice_agent.py
│   │   ├── drug_interaction.py
│   │   ├── monitoring_agent.py
│   │   └── followup_agent.py
│   ├── middleware/
│   │   ├── auth_middleware.py
│   │   ├── hipaa_audit.py
│   │   └── rate_limiter.py
│   ├── schemas/
│   │   ├── auth_schema.py
│   │   ├── patient_schema.py
│   │   ├── vitals_schema.py
│   │   └── ...
│   └── utils/
│       ├── encryption.py
│       ├── validators.py
│       └── helpers.py
├── migrations/                  # Alembic migrations
├── tests/
├── celery_worker.py
├── wsgi.py
└── requirements.txt
```

### Frontend (`frontend/`)

```
frontend/
├── app/
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Landing page
│   ├── (auth)/
│   │   ├── login/
│   │   ├── register/
│   │   └── forgot-password/
│   ├── (patient)/
│   │   ├── dashboard/
│   │   ├── vitals/
│   │   ├── reports/
│   │   ├── medications/
│   │   ├── appointments/
│   │   ├── chat/
│   │   └── telemedicine/
│   ├── (doctor)/
│   │   ├── dashboard/
│   │   ├── patients/
│   │   ├── appointments/
│   │   ├── telemedicine/
│   │   └── analytics/
│   └── (admin)/
│       ├── dashboard/
│       ├── users/
│       ├── devices/
│       ├── audit-logs/
│       └── settings/
├── components/
│   ├── ui/                      # shadcn/ui components
│   ├── charts/                  # Recharts + D3 wrappers
│   ├── forms/                   # Form components
│   ├── layout/                  # Layout components
│   └── shared/                  # Cross-portal components
├── hooks/
│   ├── useAuth.ts
│   ├── useVitals.ts
│   ├── useWebSocket.ts
│   └── useVoice.ts
├── lib/
│   ├── api.ts                   # API client
│   ├── socket.ts                # Socket.IO setup
│   ├── auth.ts                  # NextAuth config
│   └── utils.ts
├── stores/
│   ├── authStore.ts
│   ├── vitalsStore.ts
│   └── notificationStore.ts
├── types/
│   ├── api.ts
│   ├── models.ts
│   └── enums.ts
└── public/
```

---

## Tenancy and Access Control

**This is a single-tenant hospital system. There is NO `organization_id` column or multi-tenant pattern.**

Access control is enforced through:

1. **Patient scoping** - Patients access only their own records via `patient_id` matching their JWT identity
2. **RBAC** - Role-based access control with roles: `patient`, `doctor`, `nurse`, `admin`
3. **Relationship-based access** - Doctors access only their assigned patients
4. **HIPAA audit trail** - Every PHI access logged to `audit_logs` table

```python
# CORRECT - scope by patient and role
@jwt_required()
def get_patient_vitals(patient_id: str):
    current_user = get_jwt_identity()
    if current_user.role == "patient" and current_user.patient_id != patient_id:
        abort(403)
    # ... fetch vitals

# WRONG - never use organization_id
# query.filter_by(organization_id=org_id)  # DO NOT DO THIS
```

---

## Production-Ready Standards

- **No prototype code in main branch** - All code must be production-quality
- **Error handling on every external call** - Database, AI APIs, external services
- **Graceful degradation** - If an AI agent fails, surface a safe fallback, not a stack trace
- **Health checks** - Every service exposes `/health` and `/ready` endpoints
- **Circuit breakers** - On OpenAI API calls and external integrations
- **Retry logic** - Exponential backoff on transient failures (Celery tasks, API calls)

---

## File Size Limits

| File Type          | Max Lines | Action if Exceeded                  |
|--------------------|-----------|-------------------------------------|
| Route file         | 200       | Split into sub-blueprints           |
| Service file       | 300       | Extract sub-services                |
| Model file         | 150       | One model per file                  |
| Component file     | 250       | Extract sub-components              |
| Test file          | 400       | Split by test category              |
| Agent file         | 300       | Extract tools/prompts to separate files |

---

## Type Hints

**Type hints are mandatory everywhere.**

### Python (Backend)

```python
# Every function signature must have type hints
def get_patient_vitals(
    patient_id: uuid.UUID,
    start_date: datetime,
    end_date: datetime,
    limit: int = 100,
) -> list[VitalsReading]:
    ...

# Use modern Python 3.11+ syntax
from typing import Optional  # AVOID - use X | None instead
def find_patient(patient_id: uuid.UUID) -> Patient | None:
    ...
```

### TypeScript (Frontend)

```typescript
// Strict mode enabled - no `any` types
interface VitalsReading {
  id: string;
  patientId: string;
  heartRate: number;
  bloodPressureSystolic: number;
  bloodPressureDiastolic: number;
  temperature: number;
  oxygenSaturation: number;
  timestamp: string;
}

// Props interfaces required for all components
interface VitalsChartProps {
  readings: VitalsReading[];
  timeRange: "1h" | "6h" | "24h" | "7d" | "30d";
  onAnomalyClick?: (reading: VitalsReading) => void;
}
```
