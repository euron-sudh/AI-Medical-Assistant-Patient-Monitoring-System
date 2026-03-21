# Caching Rules — MedAssist AI

This project uses **Redis 7** as the primary caching layer, Celery broker, and real-time pub/sub transport.

---

## Key Naming Convention

All Redis keys follow the pattern:

```
{namespace}:{resource}:{identifier}
```

This is a **single-tenant** deployment. Never include `organization_id` in any key.

### Registered Key Patterns

| Pattern | Purpose | TTL |
|---|---|---|
| `session:{user_id}` | JWT session token / refresh token metadata | 7 days (matches refresh token lifetime) |
| `ratelimit:{role}:{endpoint}` | Per-role rate-limit counters | Window-based (see Rate Limiting) |
| `agent_ctx:{session_id}` | Short-term agent conversation context | 30 min (sliding) |
| `vitals:{patient_id}:latest` | Most recent vitals snapshot from InfluxDB | 15 sec |
| `patient_summary:{patient_id}` | Cached patient summary for agent consumption | 5 min |

### Rules

- **Always set a TTL.** Every `SET`, `HSET`, or pipeline write must include an expiry. Unbounded keys are a production incident waiting to happen.
- If a key does not appear in the table above, propose it in a PR description before adding it.
- Use `:` as the delimiter — never `/` or `.`.

---

## Cache-Aside Pattern

All read paths follow **cache-aside** (lazy population):

```
1. Check Redis for the key.
2. On HIT  → return cached value, done.
3. On MISS → query the authoritative store (PostgreSQL / InfluxDB).
4. Write the result to Redis with the correct TTL.
5. Return the value.
```

- Never pre-warm caches at application startup unless there is a documented performance reason.
- On any **write** to the underlying data, **invalidate** the corresponding cache key immediately (delete, do not overwrite).
- Use `WATCH` / optimistic locking or Lua scripts when the read-modify-write cycle must be atomic.

---

## Rate Limiting

Rate limits are enforced per **role** and **endpoint** using the sliding-window algorithm (`ratelimit:{role}:{endpoint}`).

| Role | Default Limit | Window |
|---|---|---|
| `patient` | 60 req | 1 min |
| `doctor` | 120 req | 1 min |
| `nurse` | 120 req | 1 min |
| `admin` | 200 req | 1 min |

- Implement via `MULTI`/`EXEC` with `ZADD` + `ZREMRANGEBYSCORE` (sorted-set sliding window).
- Return `429 Too Many Requests` with `Retry-After` header when the limit is exceeded.
- AI agent endpoints (e.g., `/api/v1/agents/symptom-analysis`) may have separate, tighter limits to control OpenAI token spend.

---

## Pub/Sub Channels

Redis Pub/Sub powers real-time event delivery to WebSocket consumers.

| Channel Pattern | Payload | Consumers |
|---|---|---|
| `vitals:{patient_id}` | Latest vitals JSON from Monitoring Agent | Frontend dashboard, Monitoring Agent |
| `alerts:{patient_id}` | Threshold-breach or anomaly alerts | Doctor/Nurse dashboards, Triage Agent |
| `chat:{session_id}` | Agent ↔ user streaming messages | Frontend chat UI |

- Publishers must JSON-serialize payloads — no raw strings.
- Subscribers must handle missed messages gracefully (Pub/Sub is fire-and-forget); fall back to polling the REST API for consistency.
- For durable event delivery (e.g., critical alerts), publish to both Redis Pub/Sub **and** a Celery task that persists the event to PostgreSQL.

---

## Celery Broker & Result Backend

Redis also serves as the **Celery broker** and **result backend**.

```python
# config.py
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/1"
```

- Use **DB 0** for the broker, **DB 1** for results, and **DB 2** for application caching. Keep them isolated.
- Set `result_expires` to 1 hour — never leave task results in Redis indefinitely.
- All agent execution tasks (symptom analysis, report reading, etc.) run through Celery. See `07-agents.md` for timeout rules.

---

## Implementation Checklist

- [ ] Use `flask-caching` with the Redis backend or a thin custom wrapper — not raw `redis-py` calls scattered across route handlers.
- [ ] Serialize all cached values as JSON (not pickle) for debuggability and interop.
- [ ] Log cache HITs and MISSes at `DEBUG` level for performance tuning.
- [ ] Monitor Redis memory usage and eviction policy (`allkeys-lru` recommended).
- [ ] Write integration tests that assert correct TTL, invalidation, and pub/sub behavior (see `09-testing.md`).
