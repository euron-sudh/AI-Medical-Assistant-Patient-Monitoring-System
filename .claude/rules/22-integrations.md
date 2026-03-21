# External Integrations for MedAssist AI

## Overview

MedAssist AI integrates with multiple external services. Each integration follows the adapter pattern, stores credentials in environment variables, handles rate limits gracefully, and logs all actions to the HIPAA audit trail.

## Integration Registry

| Service         | Purpose                        | SDK / Client              | Auth Method           |
| --------------- | ------------------------------ | ------------------------- | --------------------- |
| OpenAI          | LLM, speech, vision, embeddings| `openai` Python SDK       | API key (Bearer)      |
| Pinecone        | Vector similarity search       | `pinecone-client`         | API key               |
| InfluxDB        | Time-series vitals storage     | `influxdb-client`         | Token                 |
| Elasticsearch   | Medical records full-text search| `elasticsearch`           | API key / basic auth  |
| S3 / MinIO      | File and document storage      | `boto3`                   | Access key + secret   |
| Daily.co        | WebRTC video consultations     | REST API + `daily-python` | API key (Bearer)      |
| Twilio          | SMS notifications              | `twilio`                  | Account SID + auth token |
| SendGrid        | Email notifications            | `sendgrid`                | API key (Bearer)      |

## 1. OpenAI API

### Models and Capabilities

| Capability     | Model / Endpoint         | Use Case                                           |
| -------------- | ------------------------ | -------------------------------------------------- |
| Chat Completion| GPT-4o                   | Symptom analysis, triage, clinical decision support |
| Embeddings     | text-embedding-3-large   | Medical record vectorization for RAG               |
| Whisper        | whisper-1                | Voice-to-text for patient voice input              |
| TTS            | tts-1 / tts-1-hd        | Text-to-speech for accessibility                   |
| Vision         | GPT-4o (vision)          | Medical image analysis (skin lesions, wound photos)|
| Moderation     | omni-moderation-latest   | Content safety check on user inputs                |

### Configuration (Environment Variables)

```bash
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_WHISPER_MODEL=whisper-1
OPENAI_TTS_MODEL=tts-1
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.3
OPENAI_TIMEOUT=30
```

### Rate Limit Handling

- Track token usage per minute via Redis counter.
- Implement exponential backoff on 429 responses (retry after `Retry-After` header value).
- Maximum 3 retries per request.
- Queue non-urgent requests (report generation) during rate limit periods.
- Log rate limit events for capacity planning.

### Audit Requirements

- Log every API call: model, token count (prompt + completion), latency, user ID, purpose.
- Store in `ai_interactions` table with encrypted prompt/response for PHI-containing requests.
- Never log raw patient data to external monitoring services.

## 2. Pinecone (Vector Store)

### Purpose

Store and query medical knowledge embeddings for Retrieval-Augmented Generation (RAG).

### Configuration

```bash
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=medassist-medical-knowledge
PINECONE_NAMESPACE=production
```

### Usage Patterns

- **Upsert**: When new medical documents or guidelines are added.
- **Query**: During symptom analysis to retrieve relevant medical context.
- **Delete**: When outdated medical information is removed.

### Implementation Rules

- Dimension must match embedding model output (text-embedding-3-large: 3072).
- Metadata stored with each vector: `source`, `category`, `last_updated`, `document_id`.
- Never store PHI in Pinecone metadata or vectors. Only medical knowledge base content.
- Batch upserts in groups of 100 vectors maximum.

## 3. InfluxDB (Time-Series)

### Purpose

Store and query patient vital signs as time-series data for real-time monitoring and historical analysis.

### Configuration

```bash
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=...
INFLUXDB_ORG=medassist
INFLUXDB_BUCKET=patient_vitals
INFLUXDB_RETENTION=365d
```

### Data Structure

```
measurement: vitals
tags: patient_id, vital_type, device_id, unit
fields: value (float), quality (string)
timestamp: nanosecond precision
```

### Implementation Rules

- Write vitals with nanosecond timestamps.
- Use Flux queries for aggregation (mean, min, max over time windows).
- Retention policy: 365 days for raw data, 5 years for downsampled (hourly averages).
- Continuous queries downsample raw data to hourly and daily aggregates.
- Patient ID is a tag for efficient per-patient queries.

## 4. Elasticsearch (Medical Records Search)

### Purpose

Full-text search across medical records, reports, notes, and care plans.

### Configuration

```bash
ELASTICSEARCH_URL=http://elasticsearch:9200
ELASTICSEARCH_API_KEY=...
ELASTICSEARCH_INDEX_PREFIX=medassist
```

### Indices

| Index                          | Content                       |
| ------------------------------ | ----------------------------- |
| `medassist-medical-records`    | Patient medical history       |
| `medassist-reports`            | AI-generated reports          |
| `medassist-prescriptions`      | Prescription records          |
| `medassist-care-plans`         | Care plans and notes          |

### Implementation Rules

- All indices use HIPAA-compliant encryption at rest.
- Access control: queries must include `patient_id` filter; no cross-patient search for non-admin roles.
- Bulk index operations during off-peak hours.
- Synonym dictionary for medical terminology.

## 5. S3 / MinIO (File Storage)

### Purpose

Store medical documents, images, voice recordings, and report PDFs.

### Configuration

```bash
S3_ENDPOINT_URL=http://minio:9000    # MinIO for dev, S3 URL for prod
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
S3_BUCKET_NAME=medassist-files
S3_REGION=us-east-1
```

### Bucket Structure

```
medassist-files/
├── medical-images/{patient_id}/{uuid}.{ext}
├── voice-recordings/{patient_id}/{uuid}.webm
├── reports/{patient_id}/{uuid}.pdf
├── documents/{patient_id}/{uuid}.{ext}
└── exports/{admin_id}/{uuid}.csv
```

### Implementation Rules

- All objects encrypted at rest (SSE-S3 or SSE-KMS).
- Pre-signed URLs for secure, time-limited access (15 minute expiry).
- File type validation: only allow whitelisted MIME types.
- Maximum file size: 50 MB for images, 100 MB for voice recordings, 25 MB for documents.
- Lifecycle policy: move to infrequent access after 90 days, Glacier after 1 year.
- All uploads and downloads are audit logged.

## 6. Daily.co (WebRTC Video)

### Purpose

Telemedicine video consultations between patients and doctors.

### Configuration

```bash
DAILY_API_KEY=...
DAILY_API_URL=https://api.daily.co/v1
DAILY_DOMAIN=medassist.daily.co
```

### API Usage

| Endpoint                  | Purpose                              |
| ------------------------- | ------------------------------------ |
| `POST /rooms`             | Create a telemedicine room           |
| `DELETE /rooms/:name`     | End and clean up a session           |
| `POST /meeting-tokens`    | Generate participant access tokens   |
| `GET /rooms/:name`        | Check room status                    |

### Webhook Events

Handle via `POST /api/v1/webhooks/dailyco/events`:

| Event                  | Action                                             |
| ---------------------- | -------------------------------------------------- |
| `meeting.started`      | Update appointment status to "in_progress"         |
| `meeting.ended`        | Update appointment status, trigger summary gen      |
| `participant.joined`   | Log participant join time                          |
| `participant.left`     | Log participant leave time, check if session ended |

### Implementation Rules

- Rooms are created on-demand when a telemedicine appointment starts.
- Meeting tokens include: `user_name`, `user_id`, `is_owner` (doctor = owner).
- Token expiry: 1 hour from creation.
- Recording disabled by default (requires explicit consent from both parties).
- Room auto-deletes 5 minutes after `meeting.ended`.

## 7. Twilio (SMS)

### Configuration

```bash
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1...
TWILIO_STATUS_CALLBACK_URL=https://api.medassist.ai/api/v1/webhooks/twilio/status
```

### Implementation Rules

- Validate Twilio request signatures on all webhooks.
- Never include PHI in SMS body. Use generic notifications with portal links.
- Rate limit: max 10 SMS per user per day.
- Opt-out handling: process STOP/START keywords automatically.
- Phone numbers stored with AES-256 encryption in the database.

## 8. SendGrid (Email)

### Configuration

```bash
SENDGRID_API_KEY=SG...
SENDGRID_FROM_EMAIL=notifications@medassist.ai
SENDGRID_FROM_NAME=MedAssist AI
SENDGRID_WEBHOOK_VERIFICATION_KEY=...
```

### Implementation Rules

- Use dynamic templates stored in SendGrid for consistent branding.
- Never include PHI in email subject or preview text.
- Include unsubscribe link in every email (CAN-SPAM compliance).
- Validate SendGrid webhook signatures.
- Track bounce rates; disable email for hard-bounced addresses.
- Rate limit: max 20 emails per user per day.

## Adapter Pattern

All integrations implement a common adapter interface:

```python
from abc import ABC, abstractmethod
from typing import Any

class IntegrationAdapter(ABC):
    """Base adapter for external service integrations."""

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the external service is reachable and healthy."""
        pass

    @abstractmethod
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute an operation against the external service."""
        pass

    def _handle_rate_limit(self, retry_after: int) -> None:
        """Handle rate limit with exponential backoff."""
        pass

    def _audit_log(self, operation: str, status: str, details: dict) -> None:
        """Log the integration action to the HIPAA audit trail."""
        pass
```

Each adapter is registered in the application's dependency injection container and can be swapped with mock implementations for testing.

## Credential Management

- All credentials stored as environment variables, never in code or config files.
- In production: credentials loaded from Kubernetes Secrets.
- In development: credentials loaded from `.env` file (which is in `.gitignore`).
- Rotate API keys quarterly or immediately if compromised.
- Audit log records which credentials are used but never logs the credential values.

## Error Handling

All integrations must implement:

1. **Retry with backoff**: exponential backoff (1s, 2s, 4s) with max 3 retries.
2. **Circuit breaker**: after 5 consecutive failures, open circuit for 60 seconds.
3. **Fallback**: graceful degradation when a service is unavailable (e.g., queue for later, show cached data).
4. **Alerting**: notify admin dashboard when an integration enters degraded state.
5. **Timeout**: all external calls have a maximum timeout (default 30s, configurable per service).
