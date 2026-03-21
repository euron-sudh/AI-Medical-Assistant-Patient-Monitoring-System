# MedAssist AI — Project Build Journal

> How this project was built, issues faced, and lessons learned.
> Author: PK (Project Lead) | Date: 2026-03-20 to 2026-03-21

---

## Overview

MedAssist AI is a full-stack HIPAA-compliant medical platform built by a team of 10 developers (3 real, 7 simulated). The project was used as a learning exercise to understand corporate software development workflows: branching, PRs, CI/CD, code review, merge conflicts, and team coordination.

---

## Phase 1: Foundation (PRs #1–#8)

### PR #1 — Project Scaffold (PK)
**What:** Set up the entire project foundation — Flask backend, Next.js frontend, Docker Compose, CI pipeline, 25 coding rules, documentation.
**Issues:** None — clean first commit.

### PR #2 — Sanjay's Patient/Doctor API (REAL team member) — CLOSED
**What:** Sanjay Kumar built Patient & Doctor CRUD endpoints.
**Issue:** He used **FastAPI instead of Flask** and **Supabase instead of local PostgreSQL**.
**Resolution:** As lead, PK left a detailed code review explaining:
- Wrong framework (project standard is Flask per CLAUDE.md)
- Wrong database (project uses Docker Compose PostgreSQL)
- Committed `__pycache__/` binary files
- PR was closed after Pallavi built the correct Flask version in PR #8.
**Lesson:** Always read the project standards before coding. Code review catches framework mismatches early.

### PR #4 — Auth System (Arjun Mehta) — 3 CI failures fixed
**What:** JWT authentication, login, register, RBAC middleware.
**CI Failure 1:** `ModuleNotFoundError: email_validator` — Pydantic's `EmailStr` requires `pydantic[email]` extra. Fixed by updating `requirements.txt`.
**CI Failure 2:** `FATAL: password authentication failed` — TestingConfig used `TEST_DATABASE_URL` but CI set `DATABASE_URL`. Fixed by making config check both.
**CI Failure 3:** `PatientProfile failed to locate a name` — User model had `relationship("PatientProfile")` but that model didn't exist yet. Fixed by commenting out until Dev 2 creates it.
**Lesson:** CI catches dependency issues, environment mismatches, and cross-dependency problems that work locally but fail on clean machines.

### PR #8 — Patient & Doctor Profiles (Pallavi Desai) — 1 CI failure
**What:** Patient/Doctor models, medical history, allergies, CRUD API.
**CI Failure:** `RuntimeError: Working outside of application context` — Tests that query "not found" cases didn't include the `db` fixture, so no Flask app context was created.
**Fix:** Added `db` parameter to 3 test methods.

### PR #5 — Frontend Auth Pages (Rahul Sharma)
**What:** Login, register pages, header, sidebar, API client.
**Issues:** None — CI passed on first try.

### PR #6 — Vitals & Monitoring (Vikram Reddy) — Merge conflict
**What:** VitalsReading, Device, MonitoringAlert models + API.
**Conflict:** PR #6 and #8 both modified `__init__.py`, `api/__init__.py`, and `models/__init__.py` (blueprint and model registrations).
**Fix:** Merged main into branch, kept both sets of imports.
**Lesson:** When two developers add code to the same registration files, Git can't auto-merge. The lead must combine both.

### PR #7 — AI Agents (Sneha Patel)
**What:** BaseAgent, AgentOrchestrator, SymptomAnalystAgent, OpenAI client.
**Issues:** None — CI passed.

### Git Author Issue (All Phase 1 PRs)
**Problem:** All 4 Claude instances shared the same `.git/config` on disk. Whichever instance set `git config user.name` last overwrote the others. All PRs showed "Pallavi Desai" as author.
**Fix:** Used `git commit --amend --author="Correct Name <email>"` + `git push --force` on each branch.
**Lesson:** In real companies, each developer has their own machine. In simulation, use worktrees or separate directories.

---

## Phase 2: Full Feature Set (PRs #9–#12)

### PR #9 — HIPAA Audit Logging (Meera Iyer) — CI failure + conflict
**CI Failure:** `ModuleNotFoundError: app.models.care_plan` — Meera's branch didn't have Rohan's care plan models (PR #10 merged after her branch was created).
**Fix:** Merged main into her branch after PR #10 was merged.
**Conflict:** Same 3 registration files — combined imports.

### PR #10 — Care Plans & Medications (Rohan Verma)
**What:** CarePlan, CarePlanGoal, CarePlanActivity, Medication models + API.
**Issues:** None — CI passed. Merged first in Phase 2.

### PR #11 — Medical Reports & Conversations (Ananya Gupta) — 6 conflicts
**What:** MedicalReport, LabValue, SymptomSession, Conversation models + API.
**6 Conflicts:** 3 registration files (usual) + 3 add/add conflicts where both Ananya and Meera created the same files (hipaa_audit.py, test_audit_service.py, test_notification_service.py).
**Fix:** Kept main's version for add/add conflicts (Meera's code was already merged), combined imports for registration files.
**Lesson:** When branches overlap in scope, add/add conflicts are harder than content conflicts.

### PR #12 — Appointments & Telemedicine (Karthik Nair) — Datetime bugs + conflicts
**What:** Appointment, TelemedicineSession models + API.
**Bug:** `TypeError: can't compare offset-naive and offset-aware datetimes` — Tests used `datetime.utcnow()` (naive) but services used `datetime.now(timezone.utc)` (aware).
**Fix:** Changed both services and tests to use `datetime.now(timezone.utc)` consistently.
**Conflict:** Same 3 registration files — combined imports.
**Lesson:** Always use timezone-aware datetimes in Python. `datetime.utcnow()` is deprecated for this reason.

---

## Phase 3: Integration & Testing

### Frontend Login Issue
**Problem:** Login returned "Login failed" error.
**Root Cause 1:** API client default URL was `localhost:5000` but backend ran on port `5055`.
**Root Cause 2:** Backend returned `access_token` (snake_case) but frontend expected `accessToken` (camelCase).
**Root Cause 3:** Login redirected to `/patient` but actual route was `/patient/dashboard`.
**Root Cause 4:** Database tables didn't exist (fresh Docker container).
**Fix:** Updated API client URL, fixed field mapping, created dashboard pages, seeded database.

### EURI API Integration
**What:** Configured EURI (Euron's OpenAI-compatible gateway) as the AI backend.
**Base URL:** `https://api.euron.one/api/v1/euri`
**Key:** Stored in `.env` as both `EURI_API_KEY` and `OPENAI_API_KEY`.
**How:** OpenAI Python SDK with custom `base_url` parameter — drop-in replacement.

### Port Conflicts
**Problem:** Standard ports (5432, 6379, 3000, 5000) were already in use by existing services.
**Fix:** Changed all ports to non-standard ones:
| Service | Standard | Our Port |
|---|---|---|
| PostgreSQL | 5432 | 5499 |
| Redis | 6379 | 6399 |
| Backend | 5000 | 5055 |
| Frontend | 3000 | 3055 |
| InfluxDB | 8086 | 8099 |
| Elasticsearch | 9200 | 9299 |
| MinIO | 9000/9001 | 9099/9098 |

---

## Final Test Report

### Infrastructure
| Service | Port | Status |
|---|---|---|
| PostgreSQL | 5499 | PASS |
| Redis | 6399 | PASS |
| Backend API | 5055 | PASS |
| Frontend | 3055 | PASS |
| EURI AI API | api.euron.one | PASS |

### Authentication (3 roles)
| User | Role | Login | Status |
|---|---|---|---|
| patient@demo.dev | patient | Demo1234! | PASS |
| doctor@demo.dev | doctor | Demo1234! | PASS |
| admin@demo.dev | admin | Demo1234! | PASS |

### Frontend Pages (28 total)
| Section | Pages | Status |
|---|---|---|
| Public | /, /login, /register | 3/3 PASS |
| Patient Portal | dashboard, symptoms, vitals, reports, medications, appointments, chat, care-plan, profile | 9/9 PASS |
| Doctor Dashboard | dashboard, patients, monitoring, appointments, prescriptions, telemedicine, analytics, ai-assistant | 8/8 PASS |
| Admin Panel | dashboard, users, system-health, ai-config, audit-logs, ai-analytics, alerts, settings | 8/8 PASS |

### Database (572 records across 20 tables)
| Table | Records |
|---|---|
| users | 40 |
| patient_profiles | 20 |
| doctor_profiles | 10 |
| medical_history | 40 |
| allergies | 24 |
| vitals_readings | 100 |
| monitoring_alerts | 10 |
| medical_reports | 50 |
| lab_values | 32 |
| medications | 20 |
| appointments | 30 |
| care_plans | 15 |
| care_plan_goals | 37 |
| care_plan_activities | 54 |
| symptom_sessions | 10 |
| conversations | 10 |
| audit_logs | 50 |
| notifications | 20 |

### Backend Tests
- **230 tests passed** (0 failures)

---

## PR Summary

| PR | Author | Title | Status | Issues Fixed |
|---|---|---|---|---|
| #1 | PK (Lead) | Project scaffold | MERGED | — |
| #2 | Sanjay Kumar | Patient/Doctor (FastAPI) | CLOSED | Wrong framework |
| #3 | PK (Lead) | Team simulation plan | MERGED | — |
| #4 | Arjun Mehta | Auth + RBAC | MERGED | 3 CI failures |
| #5 | Rahul Sharma | Frontend auth pages | MERGED | — |
| #6 | Vikram Reddy | Vitals + alerts | MERGED | Merge conflict |
| #7 | Sneha Patel | AI agents | MERGED | — |
| #8 | Pallavi Desai | Patient/Doctor profiles | MERGED | 1 CI failure |
| #9 | Meera Iyer | HIPAA audit + notifications | MERGED | CI failure + conflict |
| #10 | Rohan Verma | Care plans + medications | MERGED | — |
| #11 | Ananya Gupta | Reports + conversations | MERGED | 6 conflicts |
| #12 | Karthik Nair | Appointments + telemedicine | MERGED | Datetime bugs + conflict |

---

## Key Lessons Learned

1. **CI catches what "works on my machine" misses** — dependency issues, environment mismatches, cross-model references
2. **Code review prevents framework drift** — Sanjay's FastAPI PR was caught before merge
3. **Merge conflicts are normal** — every PR that touches registration files will conflict; resolve by combining both
4. **Timezone-aware datetimes always** — never use `datetime.utcnow()`, always `datetime.now(timezone.utc)`
5. **Branch naming conventions matter** — `feature/module/description` makes it easy to see who's working on what
6. **Squash merge keeps history clean** — each feature is one commit on main
7. **Test users and seed data are essential** — can't test the UI without data in the database
8. **Port conflicts happen** — use non-standard ports in development to avoid clashing with existing services
9. **API field naming must be consistent** — snake_case vs camelCase mismatch between backend and frontend is a common bug
10. **OpenAI-compatible gateways work as drop-in replacements** — EURI just needs a different `base_url`
