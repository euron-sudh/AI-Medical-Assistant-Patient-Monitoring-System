# Contributing to MedAssist AI

Welcome to the MedAssist AI project. This document covers everything you need to follow when contributing code. Read this fully before your first commit.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Branch Naming Convention](#branch-naming-convention)
- [Commit Message Format](#commit-message-format)
- [How to Push Your Code](#how-to-push-your-code)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Rules You Must Never Break](#rules-you-must-never-break)
- [Team Squads & Module Ownership](#team-squads--module-ownership)
- [Development Environment Setup](#development-environment-setup)

---

## Getting Started

1. Get invited to the GitHub repository by PK
2. Clone the repo and set up your local environment (see [Development Environment Setup](#development-environment-setup))
3. Read this entire document
4. Check the Task Tracker spreadsheet for your assigned tasks
5. Never start coding without knowing your branch name and task ID

---

## Branch Naming Convention

**Format:** `<type>/<module>/<short-description>`

- All lowercase, hyphens only, no spaces, no underscores

### Branch Types

| Type        | Use For                  |
| ----------- | ------------------------ |
| `feature/`  | New functionality        |
| `fix/`      | Bug fixes                |
| `refactor/` | Code restructuring       |
| `chore/`    | Config, deps, docs       |

### Module Names (use exactly these)

`auth` | `patient` | `doctor` | `vitals` | `reports` | `medications` | `appointments` | `symptoms` | `triage` | `telemedicine` | `care-plan` | `chat` | `voice` | `agents` | `monitoring` | `notifications` | `admin` | `frontend` | `websocket` | `infra` | `db` | `docs`

### Examples

```
feature/auth/jwt-login-refresh
feature/frontend/patient-dashboard
feature/agents/symptom-analyst
fix/vitals/null-spo2-handling
chore/infra/docker-compose-setup
```

---

## Commit Message Format

**Format:** `<type>(<scope>): <description>`

### Types

`feat` | `fix` | `refactor` | `chore` | `test` | `docs`

### Examples

```
feat(auth): add JWT login and refresh token endpoints
fix(vitals): handle null SpO2 values in batch upload
chore(deps): upgrade openai to v1.35.0
test(reports): add unit tests for lab value extraction
docs(contributing): update PR template section
```

---

## How to Push Your Code

Follow these steps every single time:

1. **Pull latest develop:**
   ```bash
   git checkout develop && git pull origin develop
   ```

2. **Create your feature branch:**
   ```bash
   git checkout -b feature/module/your-description
   ```

3. **Write your code.** Commit often with proper messages.

4. **Push your branch:**
   ```bash
   git push origin feature/module/your-description
   ```

5. **Open a Pull Request** on GitHub targeting the `develop` branch.

6. **Add PK as reviewer** (and your squad lead if applicable).

7. **Wait for approval + CI green**, then **Squash Merge**.

8. **Delete your branch** after merge.

---

## Pull Request Process

- Every PR must target the `develop` branch
- PR title should follow commit message format: `feat(module): description`
- Include in your PR description:
  - **Task ID** from the tracker (e.g., D1-10)
  - **What changed** (brief summary)
  - **How to test** (steps to verify)
  - **Screenshots** (for frontend changes)
- At least 1 approval required before merge (PK or squad lead)
- All CI checks must pass
- Use **Squash Merge** (not regular merge or rebase)
- Delete the branch after merging

---

## Coding Standards

### Backend (Python / Flask)

- Follow PEP 8 style guide
- Use type hints on all function signatures
- Use dataclasses or Pydantic models for request/response schemas
- Service layer pattern: controllers call services, services call models
- All database queries through SQLAlchemy ORM (no raw SQL)
- Use Celery for any operation > 500ms
- Log all errors with `structlog`
- File naming: `snake_case.py`

### Frontend (TypeScript / React / Next.js)

- Use functional components with hooks exclusively
- Use TypeScript strict mode
- Use Tailwind utility classes; avoid custom CSS
- Colocate component tests with components
- Use React Query for all server state
- Use Zustand for client state
- Use Zod schemas for all API response validation
- File naming: `kebab-case.tsx` for components, `camelCase.ts` for utilities

### AI Agents (Python)

- All agents must extend `BaseAgent`
- Each agent must have its own prompt file in `prompts/`
- Use OpenAI function calling for all tool definitions
- Store conversation context in Redis (short-term) and Pinecone (long-term)
- Return structured JSON responses, not free text

---

## Testing Requirements

### Backend

```bash
cd backend
pytest                      # All tests
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest --cov=app            # Coverage report
```

### Frontend

```bash
cd frontend
npm run test                # Jest unit tests
npm run test:e2e            # Cypress E2E tests
npm run lint                # ESLint
npm run type-check          # TypeScript check
```

- Write tests for every new endpoint and service
- Frontend components should have at least basic render tests
- All tests must pass before opening a PR

---

## Rules You Must Never Break

| Rule | Description |
| ---- | ----------- |
| A | **NEVER** push directly to `main` or `develop` |
| B | **NEVER** merge your own PR without approval |
| C | **NEVER** put secrets, passwords, or API keys in code |
| D | **NEVER** combine unrelated changes in one branch |
| E | **ALWAYS** pull latest `develop` before creating a new branch |

---

## Team Squads & Module Ownership

| Name | Squad | Role | Modules Owned |
| ---- | ----- | ---- | ------------- |
| PK | Lead | Project Lead / Architect | Foundation, DB, Docker, Integration, PR Reviews |
| Pallavi Sindkar | Platform | Auth & Security Engineer | Auth, Authorization, HIPAA Audit, Security, Admin |
| Sanjay Kumar | Backend | Patient & Doctor API Developer | Patient APIs, Doctor APIs, Medical History, Search |
| Siddhartha Borpuzari | Frontend | Frontend Lead | All frontend pages, Layouts, Auth UI, Dashboards |
| Abhrajit Pal | Frontend | Reports / Meds / Care Plans | Shared Components, Report UI, Medication UI, Care Plan UI |
| Prodip Sarkar | Frontend | Vitals / Monitoring / Telemedicine | Hooks, Vitals Charts, Monitoring Wall, Telemedicine Video |
| Chidi Henry | AI | AI Agents Lead (Agents 1-3) | Base Agent, Orchestrator, Symptom Analyst, Report Reader, Triage |
| Manish Mishra | AI | AI Agents (Agents 4-7) | Drug Interaction, Voice, Monitoring, Follow-Up Agents |
| G Prabeen Kumar | Backend | Vitals & Monitoring Backend | Vitals APIs, InfluxDB, Device Registry, Monitoring Alerts |
| Vikash Kumar | Backend | Reports & Medications Backend | Report APIs, S3/MinIO, Medication APIs |
| Arjun K | Backend | Appointments / Telemedicine / Care Plans | Appointment, Telemedicine, Care Plan, Chat, Notification APIs |
| Ashish Kumar Singh | Platform | Real-Time / WebSockets / DevOps | WebSocket Server, Celery, CI/CD, Docker, Elasticsearch |

If you need to touch a module outside your ownership, coordinate with the owner first.

---

## Development Environment Setup

### Option 1: Docker (Recommended)

```bash
docker-compose up --build
```

Services available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- Swagger Docs: http://localhost:5000/apidocs
- MinIO Console: http://localhost:9001
- Grafana: http://localhost:3001
- Kibana: http://localhost:5601

### Option 2: Local Development

```bash
# Start infrastructure
docker-compose up -d postgres redis influxdb elasticsearch minio

# Backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
flask db upgrade
python scripts/seed_db.py
python scripts/seed_knowledge_base.py
flask run --port 5000

# Celery worker (separate terminal)
celery -A celery_worker.celery worker --loglevel=info

# Frontend (separate terminal)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

---

## Questions?

Reach out to PK (project lead) on the team channel if anything is unclear.
