# MedAssist AI v1.0 - Rule Index

> Agentic AI Medical Assistant & Patient Monitoring Platform
> Single-tenant hospital system | HIPAA-compliant | Real-time monitoring

---

## Core Principles

1. **Clean Architecture** - Strict layer separation; dependencies point inward only
2. **HIPAA Safety** - Every PHI access is audited; encryption at rest and in transit; minimum necessary access
3. **Three Portals** - Patient Portal, Doctor Dashboard, Admin Panel — each with role-scoped views and permissions
4. **Secure by Default** - JWT + RBAC on every endpoint; no public routes expose PHI; secrets in env vars only
5. **Observable** - Structured logging (structlog), metrics (Prometheus), tracing on every request; alerting on anomalies
6. **No Hallucination** - Medical RAG always cites sources; AI agents never fabricate dosages, diagnoses, or lab values; confidence scores required

---

## Rule Files

| #  | File                          | Domain                          |
|----|-------------------------------|---------------------------------|
| 00 | `00-index.md`                | Rule index and project overview |
| 01 | `01-architecture.md`         | Architecture and layer rules    |
| 02 | `02-backend.md`              | Backend / Flask API rules       |
| 03 | `03-frontend.md`             | Frontend / Next.js rules        |
| 04 | `04-database.md`             | Database schema and data rules  |
| 05 | `05-caching.md`              | Redis caching patterns          |
| 06 | `06-rag.md`                  | Medical RAG pipeline rules      |
| 07 | `07-agents.md`               | AI agent orchestration rules    |
| 08 | `08-security.md`             | Auth, RBAC, HIPAA security      |
| 09 | `09-testing.md`              | Testing strategy and coverage   |
| 10 | `10-ops.md`                  | Docker, K8s, CI/CD, DevOps      |
| 11 | `11-response-style.md`       | Medical AI response formatting  |
| 12 | `12-voice.md`                | Voice channel (Whisper + TTS)   |
| 13 | `13-video.md`                | Video calls (Daily.co WebRTC)   |
| 14 | `14-observability.md`        | Logging, metrics, tracing       |
| 15 | `15-prompt-logging.md`       | AI prompt tracking and audit    |
| 16 | `16-usage-tracking.md`       | Internal AI cost monitoring     |
| 17 | `17-admin-dashboard.md`      | Admin panel rules               |
| 18 | `18-prompt-persistence.md`   | Prompt history persistence      |
| 19 | `19-interfaces.md`           | Patient/Doctor/Admin portals    |
| 20 | `20-omnichannel.md`          | Communication channels          |
| 21 | `21-alerts-escalation.md`    | Clinical alert escalation       |
| 22 | `22-integrations.md`         | External service integrations   |
| 23 | `23-code-coverage.md`        | Code coverage requirements      |
| 24 | `24-test-organization.md`    | Test folder structure           |
| 25 | `25-documentation.md`        | Documentation standards         |

---

## Technology Stack

| Layer              | Technology                                          |
|--------------------|-----------------------------------------------------|
| **Frontend**       | Next.js 14+ (App Router), React 18+, TypeScript 5+  |
| **Styling**        | Tailwind CSS 3+, shadcn/ui, Radix UI                |
| **Client State**   | Zustand (client), React Query / TanStack Query (server) |
| **Forms**          | React Hook Form + Zod validation                    |
| **Charts**         | Recharts + D3.js                                    |
| **Real-time (FE)** | Socket.IO Client, Web Speech API                    |
| **Video**          | WebRTC via Daily.co SDK                              |
| **PDF**            | react-pdf                                            |
| **Auth (FE)**      | NextAuth.js                                          |
| **FE Testing**     | Jest, React Testing Library, Cypress                 |
| **Backend**        | Python 3.11+, Flask 3+                               |
| **API Style**      | RESTful + WebSocket (Flask-SocketIO)                 |
| **Task Queue**     | Celery + Redis                                       |
| **ORM**            | SQLAlchemy 2.0                                       |
| **Migrations**     | Alembic                                              |
| **Auth (BE)**      | Flask-JWT-Extended + OAuth2                          |
| **API Docs**       | Flasgger (Swagger/OpenAPI)                           |
| **BE Testing**     | pytest + pytest-cov + Factory Boy                    |
| **Logging**        | structlog                                            |
| **AI Primary**     | OpenAI GPT-4o                                        |
| **AI Fast**        | OpenAI GPT-4o-mini                                   |
| **Speech-to-Text** | OpenAI Whisper API                                   |
| **Text-to-Speech** | OpenAI TTS API                                       |
| **Vision**         | GPT-4o Vision                                        |
| **Embeddings**     | text-embedding-3-large                               |
| **AI Features**    | Function calling, JSON mode, Moderation API          |
| **Primary DB**     | PostgreSQL 16                                        |
| **Cache**          | Redis 7                                              |
| **Vector DB**      | Pinecone                                             |
| **Time-Series**    | InfluxDB                                             |
| **Search**         | Elasticsearch                                        |
| **File Storage**   | S3 / MinIO                                           |
| **Containers**     | Docker + Docker Compose                              |
| **Orchestration**  | Kubernetes (EKS)                                     |
| **CI/CD**          | GitHub Actions                                       |
| **Monitoring**     | Prometheus + Grafana                                 |
| **Log Aggregation**| ELK Stack (Elasticsearch, Logstash, Kibana)          |
| **API Gateway**    | Kong / Nginx                                         |
| **CDN**            | CloudFront                                           |
| **Notifications**  | react-hot-toast + Web Push API                       |
| **Internationalization** | next-intl                                      |
| **Secrets**        | AWS Secrets Manager / HashiCorp Vault                |
| **IaC**            | Terraform                                            |

---

## User Roles

| Role            | Portal            | Description                                      |
|-----------------|-------------------|--------------------------------------------------|
| `patient`       | Patient Portal    | View own vitals, reports, medications; use AI chat; join telemedicine calls |
| `doctor`        | Doctor Dashboard  | View assigned patients; review AI analyses; prescribe; conduct telemedicine |
| `nurse`         | Doctor Dashboard  | Monitor vitals; triage alerts; assist doctors; limited prescribing          |
| `admin`         | Admin Panel       | Full system access; manage users, devices, system config; view audit logs; analytics; infrastructure settings |

---

## AI Agents

| Agent               | Model       | Purpose                                         |
|----------------------|-------------|--------------------------------------------------|
| Symptom Analyst      | GPT-4o      | Analyze patient-reported symptoms via structured interview |
| Report Reader        | GPT-4o Vision | Parse and summarize medical reports, lab results, imaging |
| Triage               | GPT-4o      | Assess urgency; recommend care level; escalate to doctor  |
| Voice                | Whisper + TTS | Speech-to-text and text-to-speech for voice interactions  |
| Drug Interaction     | GPT-4o-mini | Check medication interactions; flag contraindications      |
| Monitoring           | GPT-4o-mini | Analyze vitals streams; detect anomalies; trigger alerts   |
| Follow-Up            | GPT-4o-mini | Generate care plan reminders; track compliance             |
| Agent Orchestrator   | GPT-4o (function calling) | Central router — dispatches to specialist agents based on intent |

---

## Key Documentation References

| Document             | Path                        | Purpose                        |
|----------------------|-----------------------------|--------------------------------|
| Product Requirements | `docs/PRD.md`               | Features and requirements      |
| Architecture         | `docs/ARCHITECTURE.md`      | System design and diagrams     |
| API Specification    | `docs/API.md`               | Endpoint contracts             |
| Database Schema      | `docs/DATABASE.md`          | Full schema reference          |
| Deployment Guide     | `docs/DEPLOYMENT.md`        | Infrastructure and deploy      |
| CLAUDE.md            | `CLAUDE.md`                 | Project bootstrap and context  |

---

## Tenancy Model

**Single-tenant hospital system.** There is NO `organization_id` or multi-tenant pattern anywhere in this codebase. Access control is enforced through:

- `patient_id` scoping - patients see only their own data
- Role-Based Access Control (RBAC) - roles define permission boundaries
- Row-level security policies where applicable
- HIPAA audit logging on every PHI access
