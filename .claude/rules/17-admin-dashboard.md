# Admin Dashboard Rules

## Access Control

- Admin role only. All `/admin/*` routes and corresponding API endpoints require `role = admin`.
- Middleware must verify admin role before rendering any admin component or processing any admin API request.
- Failed access attempts must be logged to the HIPAA audit trail.

## Dashboard Modules

### 1. User Management

- List all users with filters: role (patient, doctor, nurse, admin), status (active, inactive), search by name/email.
- Change user roles with confirmation dialog and audit log entry.
- Activate/deactivate user accounts (soft delete only, never hard delete for HIPAA compliance).
- View user activity history and last login timestamp.
- Bulk operations are prohibited. One user change at a time with explicit confirmation.

### 2. System Health

Monitor the health of all infrastructure components:

| Component    | Health Check                          | Interval |
| ------------ | ------------------------------------- | -------- |
| PostgreSQL   | Connection pool status, query latency | 30s      |
| Redis        | Ping, memory usage, connected clients | 30s      |
| InfluxDB     | Write/query health, retention status  | 60s      |
| OpenAI API   | Model availability, rate limit status | 60s      |
| Pinecone     | Index stats, query latency            | 60s      |
| Celery       | Worker count, queue depth             | 30s      |
| MinIO/S3     | Bucket accessibility, storage usage   | 120s     |

- Display status as green/yellow/red indicators.
- Show historical uptime percentages.
- Alert when any component degrades.

### 3. AI Agent Configuration

- Model settings: select GPT-4o model version, set temperature, max tokens, top_p.
- Agent thresholds: configure confidence thresholds for symptom analysis, triage recommendations, anomaly detection.
- Prompt template management: view and edit system prompts for each agent (symptom checker, triage, report generator).
- Feature flags for enabling/disabling specific AI capabilities.
- All configuration changes require confirmation and are audit logged.

### 4. HIPAA Audit Log Viewer

- Read-only access to `audit_logs` table.
- Filters: date range, user, action type, resource type, PHI access events.
- Export as CSV for compliance reporting (export action itself is audit logged).
- Retention: audit logs are immutable and retained for minimum 6 years per HIPAA requirements.
- Search by patient ID to trace all access to a specific patient's records.

### 5. AI Usage Analytics

- Token consumption: daily, weekly, monthly breakdowns by model and agent type.
- Cost tracking: estimated costs per API call category (chat completion, embeddings, whisper, TTS, vision).
- Usage by feature: symptom checker, report generation, triage, voice interactions.
- Rate limit utilization percentage.
- Anomaly detection on usage spikes.

### 6. Platform Usage Metrics

- Active users: DAU, WAU, MAU by role.
- Feature adoption: usage counts per feature (appointments, telemedicine, vitals logging, AI chat).
- Session duration and frequency.
- API endpoint hit counts and response times.
- Error rates by endpoint and category.

### 7. Monitoring Alert Summary

- Aggregate view of all `monitoring_alerts` from the alert system.
- Breakdown by severity: emergency, critical, warning, info.
- Response time metrics: time to acknowledge, time to resolve.
- Escalation counts and patterns.
- Unacknowledged alert queue with age tracking.

## Frontend Routes

| Route                       | Component              | Description                  |
| --------------------------- | ---------------------- | ---------------------------- |
| `/admin`                    | AdminDashboard         | Overview with key metrics    |
| `/admin/users`              | UserManagement         | User list and management     |
| `/admin/users/:id`          | UserDetail             | Individual user detail       |
| `/admin/system-health`      | SystemHealth           | Infrastructure monitoring    |
| `/admin/ai-config`          | AIConfiguration        | Agent and model settings     |
| `/admin/audit-logs`         | AuditLogViewer         | HIPAA audit log browser      |
| `/admin/ai-analytics`       | AIUsageAnalytics       | Token and cost tracking      |
| `/admin/platform-metrics`   | PlatformMetrics        | Usage statistics             |
| `/admin/alerts`             | AlertSummary           | Monitoring alert overview    |

## API Endpoints (Section 6.15)

All endpoints prefixed with `/api/v1/admin/`. Require admin JWT with `role: admin` claim.

```
GET    /api/v1/admin/users                  — List users (paginated, filterable)
GET    /api/v1/admin/users/:id              — Get user detail
PATCH  /api/v1/admin/users/:id              — Update user role/status
GET    /api/v1/admin/system/health           — System health snapshot
GET    /api/v1/admin/system/health/history   — Health check history
GET    /api/v1/admin/ai/config               — Get AI configuration
PUT    /api/v1/admin/ai/config               — Update AI configuration
GET    /api/v1/admin/audit-logs              — Query audit logs (paginated)
GET    /api/v1/admin/audit-logs/export       — Export audit logs as CSV
GET    /api/v1/admin/analytics/ai-usage      — AI usage statistics
GET    /api/v1/admin/analytics/platform      — Platform usage metrics
GET    /api/v1/admin/alerts/summary          — Alert summary and counts
```

## Implementation Rules

- Never expose raw database queries or internal error details in admin API responses.
- All admin actions that modify state must create an audit log entry with: admin user ID, action, target resource, timestamp, IP address.
- Admin dashboard data should use dedicated read replicas or cached aggregations to avoid impacting production query performance.
- Rate limit admin endpoints to 100 requests/minute per admin user.
- Session timeout for admin sessions: 15 minutes of inactivity.
