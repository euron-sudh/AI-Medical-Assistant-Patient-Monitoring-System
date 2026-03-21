# Prompt Logging Rules for MedAssist AI

## Principle

Track **ALL** OpenAI API calls for cost monitoring, quality assurance, and debugging. Prompt logging is essential for understanding AI behavior in a medical context where accuracy is critical.

## HIPAA: De-identification Before Logging

**CRITICAL: All patient data MUST be de-identified before logging prompts sent to OpenAI.**

### PII That Must Be Redacted

| PII Type | Redaction Format | Example |
|----------|-----------------|---------|
| Patient name | `[PATIENT_NAME]` | "John Smith" -> `[PATIENT_NAME]` |
| Date of birth | `[DOB]` | "1985-03-15" -> `[DOB]` |
| SSN | `[SSN]` | "123-45-6789" -> `[SSN]` |
| Phone number | `[PHONE]` | "(555) 123-4567" -> `[PHONE]` |
| Email | `[EMAIL]` | "john@example.com" -> `[EMAIL]` |
| Address | `[ADDRESS]` | "123 Main St" -> `[ADDRESS]` |
| MRN | `[MRN]` | Medical record numbers |

### De-identification Pipeline

```
User/Agent Request
       |
       v
  PII Detection (regex + NER)
       |
       v
  Redact PII from messages
       |
       v
  Log de-identified prompt
       |
       v
  Send ORIGINAL (unredacted) to OpenAI
```

The **original unredacted** prompt goes to OpenAI for accurate medical responses. The **de-identified copy** is what gets stored in `prompt_logs`.

## Database Schema

### `prompt_logs` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `created_at` | TIMESTAMP | When the call was made |
| `model` | VARCHAR(50) | Model used (gpt-4o, gpt-4o-mini) |
| `system_prompt` | TEXT | De-identified system prompt |
| `messages` | JSONB | De-identified conversation messages |
| `tools` | JSONB | Tool definitions provided |
| `tool_calls` | JSONB | Tools the model chose to call |
| `response` | TEXT | De-identified model response |
| `input_tokens` | INTEGER | Prompt token count |
| `output_tokens` | INTEGER | Completion token count |
| `total_tokens` | INTEGER | Total token count |
| `latency_ms` | INTEGER | API response time in milliseconds |
| `finish_reason` | VARCHAR(20) | stop, length, tool_calls, content_filter |
| `patient_id` | UUID | De-identified patient reference (nullable) |
| `agent_name` | VARCHAR(50) | Which agent made the call |
| `session_id` | UUID | Conversation/session identifier |
| `request_id` | UUID | Correlation ID for tracing |
| `error` | TEXT | Error message if call failed (nullable) |
| `status` | VARCHAR(20) | success, error, timeout |

### Index Strategy

```sql
CREATE INDEX idx_prompt_logs_created_at ON prompt_logs (created_at);
CREATE INDEX idx_prompt_logs_model ON prompt_logs (model);
CREATE INDEX idx_prompt_logs_agent ON prompt_logs (agent_name);
CREATE INDEX idx_prompt_logs_patient ON prompt_logs (patient_id);
CREATE INDEX idx_prompt_logs_session ON prompt_logs (session_id);
CREATE INDEX idx_prompt_logs_status ON prompt_logs (status);
```

## Async Logging

**CRITICAL: Prompt logging must NEVER block the response to the user.**

- Log prompts asynchronously via Celery task or background thread.
- If logging fails, the medical response still reaches the user.
- Failed log writes are retried up to 3 times, then dropped with an error metric increment.

```python
# After receiving OpenAI response, fire and forget
log_prompt_async.delay(
    model=model,
    messages=deidentify(messages),
    response=deidentify(response),
    tokens=usage,
    latency_ms=latency,
    agent_name=agent_name,
    patient_id=patient_id,
)
```

## Retention Policy

| Data | Retention | Reason |
|------|-----------|--------|
| Full prompt logs | **90 days** | Debugging, quality monitoring |
| Aggregated usage stats | **2 years** | Cost tracking, trend analysis |
| Error logs | **180 days** | Incident investigation |

After retention period, prompt logs are permanently deleted. Aggregated statistics (token counts, latency averages, error rates) are preserved.

## Usage Analytics

Track and expose via admin dashboard:

- **Token usage per model** -- daily/weekly/monthly breakdown
- **Cost estimation** -- based on current OpenAI pricing
- **Latency trends** -- p50, p95, p99 per model and agent
- **Error rate** -- by model, agent, and error type
- **Finish reason distribution** -- track content_filter hits and length truncations
- **Top agents by usage** -- which agents consume the most tokens

## Quality Monitoring

| Signal | What to Watch | Action |
|--------|--------------|--------|
| `finish_reason: length` | Response was truncated | Increase max_tokens or refine prompts |
| `finish_reason: content_filter` | Content policy triggered | Review prompt for issues |
| High token counts | Prompt bloat | Optimize system prompts and context |
| Rising latency | Model or network degradation | Consider model fallback (4o -> 4o-mini) |
| Error rate spike | API issues | Alert on-call, activate fallback |
