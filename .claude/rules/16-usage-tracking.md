# Usage Tracking Rules for MedAssist AI

## Purpose

Track AI and infrastructure usage for **internal cost monitoring and optimization**. No external billing or Stripe integration -- this is purely for understanding and controlling operational costs.

## Tracked Usage Categories

| Category | Unit | Description |
|----------|------|-------------|
| `ai_tokens` | tokens | OpenAI API token consumption (input + output) |
| `report_analyses` | count | Medical report/imaging analyses performed |
| `voice_minutes` | minutes | Voice session duration (STT + TTS) |
| `video_minutes` | minutes | Telemedicine video session duration |
| `agent_runs` | count | AI agent invocations |

## Database Schema

### `usage_events` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `created_at` | TIMESTAMP | Event timestamp |
| `category` | VARCHAR(30) | ai_tokens, report_analyses, voice_minutes, video_minutes, agent_runs |
| `subcategory` | VARCHAR(50) | Model name, agent name, or session type |
| `quantity` | DECIMAL | Amount consumed |
| `unit` | VARCHAR(20) | tokens, count, minutes |
| `user_id` | UUID | User who triggered the usage |
| `patient_id` | UUID | Associated patient (nullable) |
| `session_id` | UUID | Session identifier (nullable) |
| `metadata` | JSONB | Additional context (model, agent, endpoint) |

### Index Strategy

```sql
CREATE INDEX idx_usage_events_created ON usage_events (created_at);
CREATE INDEX idx_usage_events_category ON usage_events (category);
CREATE INDEX idx_usage_events_user ON usage_events (user_id);
CREATE INDEX idx_usage_events_date_cat ON usage_events (created_at, category);
```

### `usage_aggregates` Table (Materialized)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `period` | DATE | Aggregation date |
| `period_type` | VARCHAR(10) | daily, monthly |
| `category` | VARCHAR(30) | Usage category |
| `subcategory` | VARCHAR(50) | Detailed breakdown |
| `total_quantity` | DECIMAL | Sum of quantity |
| `event_count` | INTEGER | Number of events |
| `estimated_cost_usd` | DECIMAL(10,4) | Estimated dollar cost |

## Cost Estimation per Model

Maintain a cost configuration (updated when OpenAI pricing changes):

```python
COST_PER_UNIT = {
    "gpt-4o": {
        "input_token": 2.50 / 1_000_000,   # $2.50 per 1M input tokens
        "output_token": 10.00 / 1_000_000,  # $10.00 per 1M output tokens
    },
    "gpt-4o-mini": {
        "input_token": 0.15 / 1_000_000,    # $0.15 per 1M input tokens
        "output_token": 0.60 / 1_000_000,   # $0.60 per 1M output tokens
    },
    "whisper": {
        "minute": 0.006,                     # $0.006 per minute
    },
    "tts-1": {
        "character": 15.00 / 1_000_000,     # $15.00 per 1M characters
    },
    "tts-1-hd": {
        "character": 30.00 / 1_000_000,     # $30.00 per 1M characters
    },
}
```

Update these values when pricing changes. Store in config, not hardcoded in business logic.

## Recording Usage Events

Log usage events asynchronously (same pattern as prompt logging -- never block the user):

```python
def record_usage(category, subcategory, quantity, unit, user_id, **kwargs):
    """Fire-and-forget usage recording via Celery."""
    record_usage_event.delay(
        category=category,
        subcategory=subcategory,
        quantity=quantity,
        unit=unit,
        user_id=user_id,
        patient_id=kwargs.get("patient_id"),
        session_id=kwargs.get("session_id"),
        metadata=kwargs.get("metadata", {}),
    )
```

## Aggregation

### Daily Aggregation

Run a Celery Beat scheduled task **every night at 02:00 UTC**:

1. Aggregate all `usage_events` from the previous day.
2. Group by `category` and `subcategory`.
3. Calculate `total_quantity`, `event_count`, and `estimated_cost_usd`.
4. Insert into `usage_aggregates` with `period_type = 'daily'`.

### Monthly Aggregation

Run on the **1st of each month at 03:00 UTC**:

1. Sum daily aggregates for the previous month.
2. Insert into `usage_aggregates` with `period_type = 'monthly'`.

## Admin Dashboard

The admin dashboard (`/admin/usage`) provides:

### Overview Panel
- Total estimated cost (current month)
- Cost trend (last 6 months line chart)
- Top cost drivers (pie chart by category)

### Breakdown Views
- **By Model**: GPT-4o vs GPT-4o-mini token usage and cost comparison
- **By Agent**: Which agents consume the most resources
- **By Category**: Tokens vs voice vs video vs reports
- **By Time**: Daily/weekly/monthly trends

### Optimization Insights
- Identify agents that could use GPT-4o-mini instead of GPT-4o
- Flag unusually high token consumption sessions
- Track cost-per-interaction trends
- Compare voice vs text interaction costs

## Retention

| Data | Retention |
|------|-----------|
| Raw `usage_events` | 90 days |
| Daily `usage_aggregates` | 2 years |
| Monthly `usage_aggregates` | Indefinite |

## Access Control

- **Admin role**: Full access to all usage data and dashboards.
- **Doctor/Nurse**: Can view their own usage summary (not cost data).
- **Patient**: No access to usage tracking data.
