# MedAssist AI - Database Rules

> Multi-database architecture for a HIPAA-compliant medical platform.

---

## Database Architecture

| Database         | Purpose                          | Technology       |
|------------------|----------------------------------|------------------|
| **Primary**      | Relational data (users, records) | PostgreSQL 16    |
| **Time-Series**  | Vitals readings, device metrics  | InfluxDB         |
| **Vector**       | Medical knowledge embeddings     | Pinecone         |
| **Cache**        | Session cache, rate limiting     | Redis 7          |
| **Search**       | Full-text search on records      | Elasticsearch    |
| **File Storage** | Reports, images, documents       | S3 / MinIO       |

---

## Tenancy Model

**Single-tenant hospital system. There is NO `organization_id` column anywhere.**

Access control uses:
- `patient_id` scoping - patients only see their own data
- RBAC via `users.role` - determines API access boundaries
- `doctor_id` / `assigned_doctor_id` - relationship-based access for care providers
- `audit_logs` - every PHI access is recorded

```sql
-- CORRECT: scope by patient
SELECT * FROM vitals_readings WHERE patient_id = :patient_id;

-- WRONG: never filter by organization
-- SELECT * FROM vitals_readings WHERE organization_id = :org_id;
```

---

## Mandatory Columns

Every PostgreSQL table MUST include:

```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

Tables containing PHI or mutable records MUST also include:

```sql
created_by      UUID REFERENCES users(id),
updated_by      UUID REFERENCES users(id)
```

Soft deletes where applicable:

```sql
deleted_at      TIMESTAMPTZ,
deleted_by      UUID REFERENCES users(id)
```

---

## SQLAlchemy Base Model

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

class BaseModel(db.Model):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

---

## Full Schema

### users

Core identity table for all roles.

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('patient', 'doctor', 'nurse', 'admin')),
    phone           VARCHAR(20),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### patient_profiles

Extended profile for users with role `patient`.

```sql
CREATE TABLE patient_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE REFERENCES users(id),
    date_of_birth       DATE NOT NULL,
    gender              VARCHAR(20),
    blood_type          VARCHAR(5),
    height_cm           DECIMAL(5,1),
    weight_kg           DECIMAL(5,1),
    emergency_contact   JSONB,
    insurance_info      JSONB,
    assigned_doctor_id  UUID REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_patient_profiles_user_id ON patient_profiles(user_id);
CREATE INDEX idx_patient_profiles_assigned_doctor ON patient_profiles(assigned_doctor_id);
```

### doctor_profiles

Extended profile for users with role `doctor`.

```sql
CREATE TABLE doctor_profiles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE REFERENCES users(id),
    specialization      VARCHAR(100) NOT NULL,
    license_number      VARCHAR(50) NOT NULL,
    license_state       VARCHAR(5),
    years_of_experience INTEGER,
    department          VARCHAR(100),
    bio                 TEXT,
    availability        JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_doctor_profiles_user_id ON doctor_profiles(user_id);
CREATE INDEX idx_doctor_profiles_specialization ON doctor_profiles(specialization);
```

### medical_history

```sql
CREATE TABLE medical_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    condition_name  VARCHAR(255) NOT NULL,
    diagnosis_date  DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'chronic', 'managed')),
    icd_10_code     VARCHAR(10),
    notes           TEXT,
    diagnosed_by    UUID REFERENCES users(id),
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_medical_history_patient ON medical_history(patient_id);
CREATE INDEX idx_medical_history_status ON medical_history(patient_id, status);
```

### allergies

```sql
CREATE TABLE allergies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    allergen        VARCHAR(255) NOT NULL,
    reaction        TEXT,
    severity        VARCHAR(20) NOT NULL CHECK (severity IN ('mild', 'moderate', 'severe', 'life_threatening')),
    diagnosed_date  DATE,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_allergies_patient ON allergies(patient_id);
```

### medications

```sql
CREATE TABLE medications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    name            VARCHAR(255) NOT NULL,
    dosage          VARCHAR(100) NOT NULL,
    frequency       VARCHAR(100) NOT NULL,
    route           VARCHAR(50),
    prescribed_by   UUID REFERENCES users(id),
    start_date      DATE NOT NULL,
    end_date        DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'discontinued', 'on_hold')),
    reason          TEXT,
    side_effects    TEXT,
    refills_remaining INTEGER DEFAULT 0,
    pharmacy_notes  TEXT,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_medications_patient ON medications(patient_id);
CREATE INDEX idx_medications_patient_status ON medications(patient_id, status);
CREATE INDEX idx_medications_prescribed_by ON medications(prescribed_by);
```

### medical_reports

```sql
CREATE TABLE medical_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    report_type     VARCHAR(50) NOT NULL CHECK (report_type IN ('lab', 'imaging', 'pathology', 'radiology', 'discharge', 'consultation', 'progress', 'other')),
    title           VARCHAR(255) NOT NULL,
    content         TEXT,
    file_url        VARCHAR(500),
    file_type       VARCHAR(20),
    ai_summary      TEXT,
    ai_analysis     JSONB,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'reviewed')),
    reviewed_by     UUID REFERENCES users(id),
    reviewed_at     TIMESTAMPTZ,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_medical_reports_patient ON medical_reports(patient_id);
CREATE INDEX idx_medical_reports_type ON medical_reports(patient_id, report_type);
CREATE INDEX idx_medical_reports_status ON medical_reports(status);
```

### lab_values

```sql
CREATE TABLE lab_values (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID NOT NULL REFERENCES medical_reports(id),
    patient_id      UUID NOT NULL REFERENCES users(id),
    test_name       VARCHAR(255) NOT NULL,
    value           DECIMAL(10,4),
    unit            VARCHAR(50),
    reference_min   DECIMAL(10,4),
    reference_max   DECIMAL(10,4),
    is_abnormal     BOOLEAN NOT NULL DEFAULT FALSE,
    loinc_code      VARCHAR(20),
    collected_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lab_values_patient ON lab_values(patient_id);
CREATE INDEX idx_lab_values_report ON lab_values(report_id);
CREATE INDEX idx_lab_values_test ON lab_values(patient_id, test_name);
```

### vitals_readings

Primary storage in PostgreSQL; also mirrored to InfluxDB for time-series queries.

```sql
CREATE TABLE vitals_readings (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id                  UUID NOT NULL REFERENCES users(id),
    heart_rate                  INTEGER,
    blood_pressure_systolic     INTEGER,
    blood_pressure_diastolic    INTEGER,
    temperature                 DECIMAL(5,2),
    oxygen_saturation           DECIMAL(5,2),
    respiratory_rate            INTEGER,
    blood_glucose               DECIMAL(6,2),
    weight_kg                   DECIMAL(5,1),
    pain_level                  INTEGER CHECK (pain_level BETWEEN 0 AND 10),
    device_id                   UUID REFERENCES devices(id),
    is_manual_entry             BOOLEAN NOT NULL DEFAULT FALSE,
    is_anomalous                BOOLEAN NOT NULL DEFAULT FALSE,
    notes                       TEXT,
    recorded_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by                  UUID NOT NULL REFERENCES users(id),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vitals_patient ON vitals_readings(patient_id);
CREATE INDEX idx_vitals_patient_time ON vitals_readings(patient_id, recorded_at DESC);
CREATE INDEX idx_vitals_anomalous ON vitals_readings(patient_id, is_anomalous) WHERE is_anomalous = TRUE;
CREATE INDEX idx_vitals_device ON vitals_readings(device_id);
```

### devices

```sql
CREATE TABLE devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    device_type     VARCHAR(50) NOT NULL,
    device_name     VARCHAR(100) NOT NULL,
    manufacturer    VARCHAR(100),
    model           VARCHAR(100),
    serial_number   VARCHAR(100),
    firmware_version VARCHAR(50),
    status          VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'retired')),
    last_sync_at    TIMESTAMPTZ,
    battery_level   INTEGER,
    configuration   JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_devices_patient ON devices(patient_id);
CREATE INDEX idx_devices_status ON devices(status);
```

### monitoring_alerts

```sql
CREATE TABLE monitoring_alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    vitals_reading_id UUID REFERENCES vitals_readings(id),
    alert_type      VARCHAR(50) NOT NULL,
    severity        VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title           VARCHAR(255) NOT NULL,
    description     TEXT NOT NULL,
    ai_analysis     JSONB,
    status          VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved', 'dismissed')),
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    resolved_by     UUID REFERENCES users(id),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_patient ON monitoring_alerts(patient_id);
CREATE INDEX idx_alerts_severity ON monitoring_alerts(severity, status);
CREATE INDEX idx_alerts_active ON monitoring_alerts(status) WHERE status = 'active';
```

### symptom_sessions

```sql
CREATE TABLE symptom_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'cancelled')),
    chief_complaint TEXT,
    symptoms        JSONB,
    ai_analysis     JSONB,
    triage_level    VARCHAR(20) CHECK (triage_level IN ('non_urgent', 'semi_urgent', 'urgent', 'emergency')),
    recommended_action TEXT,
    escalated_to    UUID REFERENCES users(id),
    conversation_log JSONB,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_symptom_sessions_patient ON symptom_sessions(patient_id);
CREATE INDEX idx_symptom_sessions_triage ON symptom_sessions(triage_level);
```

### appointments

```sql
CREATE TABLE appointments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    doctor_id       UUID NOT NULL REFERENCES users(id),
    appointment_type VARCHAR(30) NOT NULL CHECK (appointment_type IN ('in_person', 'telemedicine', 'follow_up', 'emergency')),
    status          VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')),
    scheduled_at    TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    reason          TEXT,
    notes           TEXT,
    cancelled_by    UUID REFERENCES users(id),
    cancelled_reason TEXT,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX idx_appointments_scheduled ON appointments(scheduled_at);
CREATE INDEX idx_appointments_status ON appointments(status, scheduled_at);
```

### telemedicine_sessions

```sql
CREATE TABLE telemedicine_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id  UUID NOT NULL REFERENCES appointments(id),
    patient_id      UUID NOT NULL REFERENCES users(id),
    doctor_id       UUID NOT NULL REFERENCES users(id),
    room_url        VARCHAR(500) NOT NULL,
    room_token      TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'in_progress', 'completed', 'failed')),
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    duration_seconds INTEGER,
    recording_url   VARCHAR(500),
    ai_transcript   TEXT,
    ai_summary      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_telemedicine_appointment ON telemedicine_sessions(appointment_id);
CREATE INDEX idx_telemedicine_patient ON telemedicine_sessions(patient_id);
CREATE INDEX idx_telemedicine_doctor ON telemedicine_sessions(doctor_id);
```

### care_plans

```sql
CREATE TABLE care_plans (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    doctor_id       UUID NOT NULL REFERENCES users(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('draft', 'active', 'completed', 'cancelled')),
    start_date      DATE NOT NULL,
    end_date        DATE,
    ai_recommendations JSONB,
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_care_plans_patient ON care_plans(patient_id);
CREATE INDEX idx_care_plans_doctor ON care_plans(doctor_id);
CREATE INDEX idx_care_plans_status ON care_plans(status);
```

### care_plan_goals

```sql
CREATE TABLE care_plan_goals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    care_plan_id    UUID NOT NULL REFERENCES care_plans(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    target_value    VARCHAR(100),
    current_value   VARCHAR(100),
    unit            VARCHAR(50),
    status          VARCHAR(20) NOT NULL DEFAULT 'in_progress' CHECK (status IN ('not_started', 'in_progress', 'achieved', 'missed')),
    target_date     DATE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_care_plan_goals_plan ON care_plan_goals(care_plan_id);
```

### care_plan_activities

```sql
CREATE TABLE care_plan_activities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    care_plan_id    UUID NOT NULL REFERENCES care_plans(id) ON DELETE CASCADE,
    goal_id         UUID REFERENCES care_plan_goals(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    activity_type   VARCHAR(30) NOT NULL CHECK (activity_type IN ('medication', 'exercise', 'diet', 'monitoring', 'appointment', 'other')),
    frequency       VARCHAR(100),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped')),
    due_date        TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_care_plan_activities_plan ON care_plan_activities(care_plan_id);
CREATE INDEX idx_care_plan_activities_goal ON care_plan_activities(goal_id);
CREATE INDEX idx_care_plan_activities_due ON care_plan_activities(due_date) WHERE status = 'pending';
```

### conversations

AI chat conversation history.

```sql
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id      UUID NOT NULL REFERENCES users(id),
    agent_type      VARCHAR(30) NOT NULL CHECK (agent_type IN ('symptom_analyst', 'report_reader', 'triage', 'voice', 'drug_interaction', 'monitoring', 'follow_up', 'general')),
    title           VARCHAR(255),
    messages        JSONB NOT NULL DEFAULT '[]',
    status          VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'closed', 'escalated')),
    escalated_to    UUID REFERENCES users(id),
    metadata        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_patient ON conversations(patient_id);
CREATE INDEX idx_conversations_agent ON conversations(agent_type);
```

### audit_logs

**HIPAA-critical table.** Records every PHI access.

```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    action          VARCHAR(50) NOT NULL,
    resource_type   VARCHAR(50) NOT NULL,
    resource_id     UUID,
    patient_id      UUID,
    ip_address      INET,
    user_agent      TEXT,
    request_method  VARCHAR(10),
    request_path    VARCHAR(500),
    status_code     INTEGER,
    details         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- audit_logs has NO updated_at — logs are immutable
-- audit_logs has NO deleted_at — logs are never deleted

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_patient ON audit_logs(patient_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);
```

### notifications

```sql
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    type            VARCHAR(50) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    message         TEXT NOT NULL,
    data            JSONB,
    read            BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    channel         VARCHAR(20) NOT NULL DEFAULT 'in_app' CHECK (channel IN ('in_app', 'email', 'sms', 'push')),
    sent_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, read) WHERE read = FALSE;
```

---

## InfluxDB (Time-Series Vitals)

High-frequency vitals data (from continuous monitoring devices) is stored in InfluxDB for time-series queries.

```
Measurement: vitals
Tags: patient_id, device_id, device_type
Fields: heart_rate, bp_systolic, bp_diastolic, temperature, oxygen_saturation, respiratory_rate, blood_glucose
Timestamp: recorded_at

Retention Policies:
- raw: 30 days (1-second resolution)
- downsampled_5m: 1 year (5-minute averages)
- downsampled_1h: 5 years (1-hour averages)
```

---

## Pinecone (Vector Embeddings)

Medical knowledge base and patient record embeddings for RAG.

```
Index: medassist-medical-knowledge
Dimension: 3072 (text-embedding-3-large)
Metric: cosine
Namespaces:
  - medical-guidelines: Clinical guidelines and protocols
  - drug-database: Medication information and interactions
  - patient-records: De-identified patient record summaries (for context in AI responses)
```

---

## Redis 7 (Cache)

```
Key Patterns:
  session:{user_id}           -> JWT session data (TTL: 24h)
  vitals:latest:{patient_id}  -> Latest vitals snapshot (TTL: 5m)
  rate_limit:{user_id}:{endpoint} -> Rate limit counter (TTL: 1m)
  cache:patient:{patient_id}  -> Patient profile cache (TTL: 15m)
  lock:vitals:{patient_id}    -> Distributed lock for vitals processing
  queue:notifications         -> Notification dispatch queue
```

---

## Elasticsearch (Search)

```
Indices:
  - patients: Searchable patient records (name, MRN, conditions)
  - medications: Drug names, generics, interactions
  - medical-reports: Full-text search on report content
  - audit-logs: Searchable audit trail for compliance
```

---

## Alembic Migration Rules

1. Every schema change requires an Alembic migration
2. Never hand-edit the database schema in production
3. Migration filenames: `{revision}_description.py`
4. Messages must be descriptive: `alembic revision -m "add_respiratory_rate_to_vitals_readings"`
5. Every `upgrade()` must have a corresponding `downgrade()`
6. Test migrations on a fresh database before applying to staging/production
7. Data migrations must be idempotent

```bash
# Generate migration
cd backend && alembic revision --autogenerate -m "add_respiratory_rate_to_vitals_readings"

# Apply migration
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## HIPAA: Audit Logging Requirements

The `audit_logs` table is the HIPAA compliance backbone:

1. **Every PHI read** is logged (viewing patient records, vitals, reports)
2. **Every PHI write** is logged (creating, updating, deleting medical data)
3. **Every PHI export** is logged (downloading reports, printing)
4. **Audit logs are immutable** - no UPDATE or DELETE on audit_logs
5. **Retention: 6 years minimum** per HIPAA requirements
6. **Access to audit_logs** is restricted to `admin` role
7. **Audit log access is itself audited** (meta-auditing)

```python
# backend/app/middleware/hipaa_audit.py
PHI_TABLES = {
    "patient_profiles", "medical_history", "allergies", "medications",
    "medical_reports", "lab_values", "vitals_readings", "symptom_sessions",
    "care_plans", "care_plan_goals", "care_plan_activities",
    "conversations", "telemedicine_sessions",
}
```
