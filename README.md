# MedAssist AI

**Real-time Agentic AI Medical Assistant and Patient Monitoring System**

MedAssist AI is a full-stack, HIPAA-compliant medical assistant platform powered by specialized AI agents. Built for hospitals, telemedicine providers, and health startups, it combines symptom analysis, medical report interpretation, continuous patient monitoring, voice interaction, and intelligent alerting into a unified system.

---

## Live Demo

**URL:** http://medassist-ai.136.119.221.67.nip.io

### Login Credentials

All accounts use password: `Demo1234!`

| Role | Email | Name |
|------|-------|------|
| **Admin** | admin@medassist.ai | System Admin |
| **Doctor** | priya.sharma@medassist.ai | Dr. Priya Sharma (Internal Medicine) |
| **Doctor** | thomas.mitchell@medassist.ai | Dr. Thomas Mitchell (Cardiology) |
| **Doctor** | lisa.wong@medassist.ai | Dr. Lisa Wong (Endocrinology) |
| **Doctor** | ahmed.hassan@medassist.ai | Dr. Ahmed Hassan (Pulmonology) |
| **Doctor** | rachel.green@medassist.ai | Dr. Rachel Green (Neurology) |
| **Patient** | sarah.johnson@medassist.ai | Sarah Johnson |
| **Patient** | james.williams@medassist.ai | James Williams |
| **Patient** | maria.garcia@medassist.ai | Maria Garcia |
| **Patient** | robert.chen@medassist.ai | Robert Chen |
| **Patient** | emily.davis@medassist.ai | Emily Davis |
| **Patient** | michael.brown@medassist.ai | Michael Brown |
| **Patient** | aisha.patel@medassist.ai | Aisha Patel |
| **Patient** | david.kim@medassist.ai | David Kim |
| **Patient** | jennifer.taylor@medassist.ai | Jennifer Taylor |
| **Patient** | william.anderson@medassist.ai | William Anderson |

Each patient has pre-loaded: vitals history, medical conditions, allergies, medications, appointments, care plans, medical reports with lab values, AI chat conversations, and symptom analysis sessions.

---

## Key Features

### Symptom Analysis and Triage
- AI-guided multi-turn symptom interviews via chat, voice, or interactive body map
- Ranked differential diagnosis with confidence scores
- Emergency Severity Index (ESI) assignment with automatic escalation
- Specialist recommendations and urgency scoring
- Full session history for audit and physician review
- Conservative triage bias for patient safety
- Body map with anatomical region mapping, pain type, and severity

### Medical Report Reading
- Upload and analyze PDF, image, or structured data reports
- Vision model extraction with OCR for scanned documents
- Structured data tables with test name, value, unit, reference range, status
- Color-coded abnormality highlighting by severity
- Plain-language explanations for patients and clinical summaries for doctors
- Trend analysis across historical reports
- Supports CBC, metabolic panels, lipid panels, thyroid, liver, imaging, pathology, ECG

### Real-Time Patient Monitoring
- IoT device and wearable integration via MQTT gateway
- Continuous monitoring of HR, BP, SpO2, temperature, respiratory rate, blood glucose
- Per-patient adaptive baselines with statistical and AI anomaly detection
- Predictive deterioration alerts 30-60 minutes in advance (NEWS2, MEWS)
- 4-level alert escalation chain (info, warning, critical, emergency)
- Real-time monitoring wall with sparklines and drill-down views
- Automated shift handoff report generation

### Voice-Based AI Assistant
- Hands-free symptom reporting and voice-controlled navigation
- Real-time streaming transcription in 50+ languages (Whisper)
- Ambient clinical note generation (SOAP format, ICD-10 suggestions)
- Medical terminology-aware transcription
- Configurable voice output (6 voices, adjustable speed)
- Voice sessions with bidirectional audio streaming via WebSocket
- Doctor-patient consultation recording with consent

### Drug Interaction Checking
- Automatic checking on new prescriptions and medication changes
- Drug-drug, drug-allergy, and drug-condition analysis
- Dosage verification for age, weight, renal/hepatic function
- Duplicate therapy and food-drug interaction detection
- Severity classification with evidence-based citations
- Alternative medication suggestions and optimized dosing schedules
- Real-time alerts to prescribing physicians

### Telemedicine Video Consultations
- HD video calls via WebRTC (Daily.co)
- Screen sharing for collaborative report review
- In-call AI assistant sidebar
- Real-time transcription overlay (optional)
- Waiting room with queue position display
- Post-call AI-generated clinical notes
- Multi-participant support (patient, doctor, specialist, interpreter)

### Care Plans and Analytics
- AI-generated personalized care plans based on diagnosis and patient profile
- Measurable goal setting with progress tracking and adaptive adjustments
- Medication adherence logging with automated multi-channel reminders
- Patient health analytics (vitals trends, symptom frequency, adherence rates)
- Doctor analytics (consultation stats, AI accuracy feedback, workload)
- Admin analytics (platform usage, AI agent performance, HIPAA compliance)
- Gamification elements (streaks, milestones)

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | Next.js 14+, React 18+, Tailwind CSS 3+, shadcn/ui, Zustand, React Query, Recharts, D3.js, Socket.IO Client, Daily.co SDK |
| Backend | Python 3.11+, Flask 3+, SQLAlchemy 2.0, Alembic, Celery, Flask-SocketIO, Flask-JWT-Extended |
| AI/LLM | OpenAI GPT-4o, GPT-4o-mini, Whisper API, TTS API, GPT-4o Vision, text-embedding-3-large |
| Databases | PostgreSQL 16, Redis 7, InfluxDB, Pinecone, Elasticsearch |
| Storage | AWS S3 / MinIO |
| Infrastructure | Docker, Kubernetes (EKS), GitHub Actions, Terraform, Kong/Nginx, CloudFront |
| Monitoring | Prometheus + Grafana, ELK Stack |

---

## Quick Start

### Docker (Recommended)

```bash
git clone <repo-url> medassist-ai
cd medassist-ai
docker-compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Swagger Docs: http://localhost:5000/apidocs
- Grafana: http://localhost:3001

### Manual Setup

```bash
# Infrastructure
docker-compose up -d postgres redis influxdb elasticsearch minio

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
flask db upgrade && python scripts/seed_db.py
flask run --port 5000

# Celery worker (separate terminal)
celery -A celery_worker.celery worker --loglevel=info

# Frontend (separate terminal)
cd frontend
npm install && cp .env.local.example .env.local
npm run dev
```

---

## Project Structure

```
medassist-ai/
  CLAUDE.md                  # Master PRD (do not modify)
  docker-compose.yml         # Local development services
  frontend/                  # Next.js 14+ application
    src/app/                 # App Router pages (patient, doctor, admin)
    src/components/          # React components (UI, chat, voice, vitals, etc.)
    src/hooks/               # Custom hooks (auth, socket, vitals stream)
    src/stores/              # Zustand state stores
  backend/                   # Flask 3+ API server
    app/models/              # SQLAlchemy models
    app/api/v1/              # REST API endpoints
    app/api/websocket/       # WebSocket event handlers
    app/services/            # Business logic services
    app/agents/              # AI agents (orchestrator + 7 specialists)
    app/middleware/           # Auth, HIPAA audit, rate limiting
    app/tasks/               # Celery async tasks
    migrations/              # Alembic database migrations
  infrastructure/            # Terraform, Kubernetes, Nginx configs
  docs/                      # Architecture, API spec, deployment guide
  data/                      # Medical knowledge base and seed data
```

---

## Documentation

- [Product Requirements](docs/PRD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database Schema](docs/DB_SCHEMA.md)
- [API Specification](docs/API_SPEC.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, coding conventions, branch naming, and PR requirements.

---

## License

This project is proprietary. All rights reserved.
