# Alert & Escalation Rules

## Important

MedAssist AI is NOT a support platform. There is no ticketing system. This document defines the clinical alert and escalation system for patient monitoring.

## Alert System Overview

Monitoring alerts are generated when patient vitals breach configured thresholds or when AI anomaly detection identifies concerning patterns. Alerts flow through an escalation chain with defined SLAs to ensure timely clinical response.

## Alert Schema

Alerts are stored in the `monitoring_alerts` table:

```sql
CREATE TABLE monitoring_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES users(id),
    vital_type VARCHAR(50) NOT NULL,
    value DECIMAL NOT NULL,
    threshold_breached VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,       -- 'info', 'warning', 'critical', 'emergency'
    category VARCHAR(50) NOT NULL,       -- auto-categorized by vital type
    message TEXT NOT NULL,
    news2_score INTEGER,                 -- NEWS2 early warning score at time of alert
    mews_score INTEGER,                  -- MEWS score at time of alert
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'acknowledged', 'resolved', 'escalated', 'suppressed'
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    escalation_level INTEGER DEFAULT 0,  -- 0=initial, 1=nurse, 2=physician, 3=on-call
    escalated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Severity Levels

| Severity    | Description                                      | Examples                                           |
| ----------- | ------------------------------------------------ | -------------------------------------------------- |
| `info`      | Informational, no action required                | Vitals logged, minor fluctuation within normal range |
| `warning`   | Attention needed, not urgent                     | Slightly elevated BP, mild tachycardia              |
| `critical`  | Requires prompt clinical attention               | SpO2 < 92%, HR > 130, significant BP deviation     |
| `emergency` | Immediate life-threatening situation              | SpO2 < 85%, cardiac arrest indicators, NEWS2 >= 7  |

## Auto-Categorization by Vital Type

| Vital Type        | Category               | Normal Range              |
| ----------------- | ---------------------- | ------------------------- |
| `heart_rate`      | Cardiac                | 60-100 bpm                |
| `blood_pressure`  | Cardiovascular         | 90/60-140/90 mmHg         |
| `spo2`            | Respiratory            | 95-100%                   |
| `temperature`     | Thermoregulation       | 36.1-37.2 C               |
| `respiratory_rate`| Respiratory            | 12-20 breaths/min         |
| `blood_glucose`   | Metabolic              | 70-140 mg/dL              |
| `weight`          | General                | Patient-specific baseline  |

Severity is automatically assigned based on how far the value deviates from the normal range:

- Within range: no alert.
- Mildly outside range (< 10% deviation): `warning`.
- Significantly outside range (10-20% deviation): `critical`.
- Dangerously outside range (> 20% deviation or known danger thresholds): `emergency`.

## Early Warning Scores

### NEWS2 (National Early Warning Score 2)

Calculate NEWS2 score from aggregate vitals. Used for severity assessment:

| NEWS2 Score | Clinical Risk | Alert Severity |
| ----------- | ------------- | -------------- |
| 0-4         | Low           | `info`         |
| 5-6         | Medium        | `warning`      |
| 7+          | High          | `critical`     |
| 7+ with any single parameter scoring 3 | High | `emergency` |

### MEWS (Modified Early Warning Score)

Alternative scoring used alongside NEWS2 for cross-validation. Both scores are recorded on every alert for clinical reference.

## Escalation Chain

```
Alert Generated
    │
    ▼
Level 0: Assigned Nurse (via WebSocket + Push)
    │
    │ ── If not acknowledged within SLA ──►
    │
    ▼
Level 1: Charge Nurse / Nurse Supervisor (via WebSocket + Push + SMS)
    │
    │ ── If not acknowledged within SLA ──►
    │
    ▼
Level 2: Assigned Physician (via WebSocket + Push + SMS)
    │
    │ ── If not acknowledged within SLA ──►
    │
    ▼
Level 3: On-Call Physician (via SMS + Phone Call via Twilio)
```

## SLA Response Times

| Severity    | Initial Response SLA | Escalation Trigger | Max Time to Acknowledge |
| ----------- | -------------------- | ------------------ | ----------------------- |
| `emergency` | < 2 minutes          | After 2 min        | 5 minutes               |
| `critical`  | < 5 minutes          | After 5 min        | 15 minutes              |
| `warning`   | < 15 minutes         | After 15 min       | 60 minutes              |
| `info`      | No SLA               | No escalation      | N/A                     |

- SLA timers start at `created_at` for initial, `escalated_at` for each escalation level.
- Celery Beat periodic task checks for unacknowledged alerts every 30 seconds.
- Each escalation increments `escalation_level` and updates `escalated_at`.

## Auto-Escalation Logic

```python
# Celery periodic task: check_alert_escalation (runs every 30s)

def check_alert_escalation():
    sla_map = {
        'emergency': timedelta(minutes=2),
        'critical': timedelta(minutes=5),
        'warning': timedelta(minutes=15),
    }

    for severity, sla in sla_map.items():
        unacknowledged = MonitoringAlert.query.filter(
            MonitoringAlert.severity == severity,
            MonitoringAlert.status == 'active',
            MonitoringAlert.created_at < datetime.utcnow() - sla,
            MonitoringAlert.escalation_level < 3,
        ).all()

        for alert in unacknowledged:
            escalate_alert(alert)
```

## Duplicate Alert Suppression

To prevent alert fatigue, duplicate alerts are suppressed:

- **Same patient + same vital type + same severity** within a **5-minute window**: suppress the duplicate.
- Suppressed alerts are stored with `status = 'suppressed'` and a reference to the original alert.
- Suppression resets if:
  - The original alert is acknowledged or resolved.
  - The severity increases (e.g., warning escalates to critical).
  - A different vital type triggers.

```python
def is_duplicate_alert(patient_id: str, vital_type: str, severity: str) -> bool:
    window = datetime.utcnow() - timedelta(minutes=5)
    existing = MonitoringAlert.query.filter(
        MonitoringAlert.patient_id == patient_id,
        MonitoringAlert.vital_type == vital_type,
        MonitoringAlert.severity == severity,
        MonitoringAlert.status.in_(['active', 'acknowledged']),
        MonitoringAlert.created_at > window,
    ).first()
    return existing is not None
```

## Alert Actions

### Acknowledge

- Sets `status = 'acknowledged'`, records `acknowledged_by` and `acknowledged_at`.
- Stops escalation timer.
- Only nurses, doctors, and admins can acknowledge.
- Acknowledgment is audit logged.

### Resolve

- Sets `status = 'resolved'`, records `resolved_by`, `resolved_at`, and `resolution_notes`.
- Resolution notes are mandatory for `critical` and `emergency` alerts.
- Only doctors can resolve `emergency` alerts.
- Resolution is audit logged.

### Snooze (Warning Only)

- `warning` alerts can be snoozed for 30, 60, or 120 minutes.
- Snoozed alerts re-activate after the snooze period.
- `critical` and `emergency` alerts cannot be snoozed.

## Smart Routing

Alerts are routed based on:

1. **Patient assignment**: to the nurse/doctor assigned to the patient.
2. **Shift schedule**: only to staff currently on shift.
3. **Specialization**: cardiac alerts preferentially route to cardiology team if available.
4. **Load balancing**: if primary assignee has > 5 unacknowledged alerts, route to backup.

## Notification Channels for Alerts

| Severity    | WebSocket | Push | SMS | Email |
| ----------- | --------- | ---- | --- | ----- |
| `info`      | Yes       | No   | No  | No    |
| `warning`   | Yes       | Yes  | No  | No    |
| `critical`  | Yes       | Yes  | Yes | No    |
| `emergency` | Yes       | Yes  | Yes | Yes   |

## Metrics and Reporting

Track and display in the admin dashboard:
- Mean time to acknowledge (MTTA) by severity.
- Mean time to resolve (MTTR) by severity.
- Alert volume trends (daily, weekly, monthly).
- Escalation rate (percentage of alerts that escalate beyond level 0).
- False positive rate (alerts resolved as "not clinically significant").
- SLA compliance percentage per severity level.
