# Observability Rules for MedAssist AI

## Three Pillars

| Pillar | Tool | Purpose |
|--------|------|---------|
| **Logs** | ELK Stack (Elasticsearch, Logstash, Kibana) | Structured event logging |
| **Metrics** | Prometheus + Grafana | Numeric time-series monitoring |
| **Traces** | Distributed tracing (OpenTelemetry) | Request flow across services |

## Structured Logging

Use **structlog** for all Python logging. Output format: JSON.

### Required Fields on Every Log Entry

| Field | Description | Example |
|-------|-------------|---------|
| `timestamp` | ISO 8601 | `2026-03-16T14:30:00Z` |
| `level` | Log level | `info` |
| `service` | Service name | `flask-backend` |
| `request_id` | Unique per request | `req_abc123` |
| `user_id` | Authenticated user | `usr_def456` |
| `patient_id` | When applicable | `pat_ghi789` |
| `event` | What happened | `vitals_alert_triggered` |

### HIPAA CRITICAL: No PII in Logs

**NEVER log the following:**

- Patient names
- Dates of birth
- Social Security numbers
- Phone numbers or email addresses
- Medical record numbers (use opaque IDs only)
- Addresses
- Any of the 18 HIPAA identifiers

Use de-identified patient IDs (`patient_id`) only. If you need to debug a specific patient's data, use the secure admin interface with audit logging.

### Log Levels

| Level | Usage | Environments |
|-------|-------|-------------|
| `DEBUG` | Detailed diagnostic info | **dev only** -- never in staging/prod |
| `INFO` | Normal operations (request handled, task completed) | All |
| `WARNING` | Recoverable issues (retry succeeded, cache miss) | All |
| `ERROR` | Failures requiring attention (API error, DB timeout) | All |
| `CRITICAL` | System-level failures (service down, data corruption) | All |

### Example

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "vitals_processed",
    patient_id=patient.id,
    vital_type="heart_rate",
    value=92,
    alert_triggered=False,
    request_id=g.request_id,
)
```

## Prometheus Metrics

### Standard Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | Counter | method, endpoint, status | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | method, endpoint | Request latency |
| `ai_response_latency_seconds` | Histogram | model, agent | AI inference time |
| `ai_tokens_used_total` | Counter | model, direction (input/output) | Token consumption |
| `vitals_processed_total` | Counter | vital_type, alert_triggered | Vitals data points processed |
| `monitoring_alerts_total` | Counter | severity, type | Patient monitoring alerts |
| `agent_runs_total` | Counter | agent_name, status | Agent executions |

### Medical-Specific Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `esi_triage_time_seconds` | Histogram | Time to complete ESI triage |
| `report_analysis_time_seconds` | Histogram | Time to analyze a medical report |
| `symptom_session_duration_seconds` | Histogram | Duration of symptom checker sessions |
| `emergency_detections_total` | Counter | Emergency symptoms flagged |
| `physician_handoff_total` | Counter | Handoffs to human physician |

### Instrumentation

```python
from prometheus_client import Counter, Histogram

ai_latency = Histogram(
    "ai_response_latency_seconds",
    "AI model response latency",
    labelnames=["model", "agent"],
    buckets=[0.5, 1, 2, 3, 5, 10, 30],
)

ai_tokens = Counter(
    "ai_tokens_used_total",
    "Total tokens consumed",
    labelnames=["model", "direction"],
)
```

## Alerting Rules

### Critical Alerts (PagerDuty / immediate)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| High error rate | > 5% of requests returning 5xx over 5 min | Page on-call engineer |
| AI latency | > 5 seconds p95 over 5 min | Page on-call engineer |
| Monitoring alert escalation failure | Any escalation not acknowledged in 5 min | Page on-call + backup |
| Database connection pool exhausted | 0 available connections | Page on-call engineer |
| Celery queue backlog | > 1000 tasks pending for 10 min | Page on-call engineer |

### Warning Alerts (Slack notification)

| Condition | Threshold |
|-----------|-----------|
| Elevated error rate | > 1% of requests returning 5xx over 15 min |
| AI latency rising | > 3 seconds p95 over 15 min |
| Disk usage | > 80% on any volume |
| Certificate expiry | < 14 days until expiration |

## Grafana Dashboards

### Required Dashboard Panels

1. **System Overview** -- request rate, error rate, latency p50/p95/p99
2. **AI Performance** -- model latency, token usage, agent run counts
3. **Patient Monitoring** -- vitals processed, alerts triggered, escalations
4. **Telemedicine** -- active video sessions, voice sessions, quality metrics
5. **Infrastructure** -- CPU, memory, disk, network per service
6. **Business Metrics** -- active users by role, sessions per day, triage counts

## Distributed Tracing

- Use OpenTelemetry SDK for trace instrumentation.
- Propagate `trace_id` and `span_id` across all service boundaries.
- Key spans to instrument:
  - HTTP request handling
  - Database queries
  - Redis operations
  - OpenAI API calls
  - Celery task execution
  - External API calls (Daily.co, Pinecone)
