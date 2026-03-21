# MedAssist AI — Team Simulation Plan

> **Purpose:** PK (project lead) is simulating all 5 team developers to learn the full corporate workflow — branching, coding, PRs, code review, and merging. This document is the source of truth across all Claude sessions.
>
> **Date Started:** 2026-03-20
> **Lead:** PK (pkpcconnect2026@gmail.com / GitHub: pkpcconnect2026-code)

---

## How This Works

1. PK opens separate Claude sessions, each pretending to be a different developer
2. Each "developer" creates a feature branch, writes code, pushes, and opens a PR
3. PK (as lead) reviews and merges each PR in order
4. Everything follows the CONTRIBUTING.md workflow exactly — same as a real team

---

## The Team (Simulated)

| Developer | Role | Squad | Module Focus | Branch They'll Create |
|-----------|------|-------|--------------|----------------------|
| **Dev 1: Arjun** | Backend Engineer | Backend Core | Auth system (JWT login, register, RBAC) | `feature/auth/jwt-login-register` |
| **Dev 2: Priya** | Backend Engineer | Backend Core | Patient & Doctor models + API endpoints | `feature/patient/profile-and-history` |
| **Dev 3: Rahul** | Frontend Engineer | Frontend | Auth pages (login, register) + layout | `feature/frontend/auth-pages` |
| **Dev 4: Sneha** | AI Engineer | AI/Agents | Base agent + Symptom Analyst Agent | `feature/agents/base-and-symptom-analyst` |
| **Dev 5: Vikram** | Full-stack | Real-time | Vitals model + API + basic monitoring | `feature/vitals/model-and-api` |

---

## Execution Order (Dependencies)

```
Phase A (can run in parallel — no dependencies):
  ├── Dev 1 (Arjun): Auth backend     ← MUST go first or parallel
  ├── Dev 2 (Priya): Patient models   ← depends on User model (already exists)
  └── Dev 3 (Rahul): Frontend auth    ← depends on nothing (can mock API)

Phase B (after Phase A merges):
  ├── Dev 4 (Sneha): AI agents        ← depends on patient models from Dev 2
  └── Dev 5 (Vikram): Vitals          ← depends on patient models from Dev 2

Merge Order:
  1. Dev 1 (Arjun) — Auth
  2. Dev 2 (Priya) — Patient models
  3. Dev 3 (Rahul) — Frontend auth pages
  4. Dev 4 (Sneha) — AI agents
  5. Dev 5 (Vikram) — Vitals
```

---

## Status Tracker

| # | Developer | Branch | Status | PR # | CI | Review | Merged |
|---|-----------|--------|--------|------|----|--------|--------|
| 1 | Arjun (Auth) | `feature/auth/jwt-login-register` | NOT STARTED | — | — | — | — |
| 2 | Priya (Patient) | `feature/patient/profile-and-history` | NOT STARTED | — | — | — | — |
| 3 | Rahul (Frontend) | `feature/frontend/auth-pages` | NOT STARTED | — | — | — | — |
| 4 | Sneha (Agents) | `feature/agents/base-and-symptom-analyst` | NOT STARTED | — | — | — | — |
| 5 | Vikram (Vitals) | `feature/vitals/model-and-api` | NOT STARTED | — | — | — | — |

---

## Instructions for Each Claude Session

When PK opens a new Claude session to simulate a developer, paste this:

### For Dev 1 (Arjun — Auth):
```
I'm simulating Developer "Arjun" (backend engineer) for my team learning exercise.
Read docs/TEAM_SIMULATION_PLAN.md for full context.
Task: Build the auth system on branch feature/auth/jwt-login-register
Files to create/modify:
- backend/app/api/v1/auth.py (register, login, refresh, logout endpoints)
- backend/app/services/auth_service.py (business logic)
- backend/app/middleware/auth_middleware.py (JWT decorators, role checks)
- backend/app/schemas/auth_schema.py (Pydantic request/response models)
- tests/unit/services/test_auth_service.py (unit tests)
Follow CONTRIBUTING.md and .claude/rules/02-backend.md and 08-security.md strictly.
Create the branch, write the code, commit, push, and open a PR.
```

### For Dev 2 (Priya — Patient Models):
```
I'm simulating Developer "Priya" (backend engineer) for my team learning exercise.
Read docs/TEAM_SIMULATION_PLAN.md for full context.
Task: Build patient & doctor profile models + API on branch feature/patient/profile-and-history
Files to create/modify:
- backend/app/models/patient.py (PatientProfile, MedicalHistory, Allergy models)
- backend/app/models/doctor.py (DoctorProfile model)
- backend/app/api/v1/patients.py (CRUD endpoints)
- backend/app/api/v1/doctors.py (CRUD endpoints)
- backend/app/services/patient_service.py
- backend/app/services/doctor_service.py
- backend/app/schemas/patient_schema.py
- backend/app/schemas/doctor_schema.py
Follow CONTRIBUTING.md and .claude/rules/02-backend.md and 04-database.md strictly.
Create the branch, write the code, commit, push, and open a PR.
```

### For Dev 3 (Rahul — Frontend Auth):
```
I'm simulating Developer "Rahul" (frontend engineer) for my team learning exercise.
Read docs/TEAM_SIMULATION_PLAN.md for full context.
Task: Build auth pages + app layout on branch feature/frontend/auth-pages
Files to create/modify:
- frontend/src/app/(auth)/login/page.tsx
- frontend/src/app/(auth)/register/page.tsx
- frontend/src/app/(auth)/layout.tsx
- frontend/src/components/auth/login-form.tsx
- frontend/src/components/auth/register-form.tsx
- frontend/src/components/layout/header.tsx
- frontend/src/components/layout/sidebar.tsx
- frontend/src/lib/api-client.ts (Axios instance)
- frontend/src/lib/validators.ts (Zod schemas)
Follow CONTRIBUTING.md and .claude/rules/03-frontend.md strictly.
Create the branch, write the code, commit, push, and open a PR.
```

### For Dev 4 (Sneha — AI Agents):
```
I'm simulating Developer "Sneha" (AI engineer) for my team learning exercise.
Read docs/TEAM_SIMULATION_PLAN.md for full context.
Task: Build base agent + symptom analyst on branch feature/agents/base-and-symptom-analyst
Files to create/modify:
- backend/app/agents/base_agent.py (abstract base class)
- backend/app/agents/orchestrator.py (agent router)
- backend/app/agents/symptom_analyst.py (symptom analysis agent)
- backend/app/agents/tools/medical_kb.py (RAG tool)
- backend/app/agents/tools/patient_history.py (patient data tool)
- backend/app/agents/prompts/system_prompts.py
- backend/app/agents/prompts/symptom_prompts.py
- backend/app/integrations/openai_client.py (OpenAI wrapper)
- tests/unit/agents/test_symptom_analyst.py
Follow CONTRIBUTING.md and .claude/rules/07-agents.md and 06-rag.md strictly.
Create the branch, write the code, commit, push, and open a PR.
```

### For Dev 5 (Vikram — Vitals):
```
I'm simulating Developer "Vikram" (full-stack engineer) for my team learning exercise.
Read docs/TEAM_SIMULATION_PLAN.md for full context.
Task: Build vitals model + API + basic monitoring on branch feature/vitals/model-and-api
Files to create/modify:
- backend/app/models/vitals.py (VitalsReading model)
- backend/app/models/device.py (Device model)
- backend/app/models/alert.py (MonitoringAlert model)
- backend/app/api/v1/vitals.py (CRUD + history + trends endpoints)
- backend/app/services/vitals_service.py
- backend/app/schemas/vitals_schema.py
- tests/unit/services/test_vitals_service.py
Follow CONTRIBUTING.md and .claude/rules/02-backend.md and 04-database.md strictly.
Create the branch, write the code, commit, push, and open a PR.
```

---

## What PK Does As Lead (After Each PR)

1. **Review the PR** — check code quality, naming, test coverage
2. **Request changes** if needed (comment on the PR)
3. **Approve and merge** when satisfied
4. **Update the status tracker** in this document
5. **Ensure main stays green** — CI passes after each merge

---

## What PK Learns From This Exercise

- How branches isolate work so team members don't conflict
- How PRs enable code review before merging
- How CI catches bugs automatically
- How a lead reviews, approves, and merges work
- How to handle merge conflicts when two devs touch the same file
- How to write good PR descriptions and commit messages
- How to coordinate parallel development across a team

---

## Key Files Each Developer Must Follow

| File | Purpose |
|------|---------|
| `CONTRIBUTING.md` | Branch naming, commit format, PR process |
| `CLAUDE.md` | Full PRD — what to build |
| `.claude/rules/02-backend.md` | Flask patterns, service layer, SQLAlchemy 2.0 |
| `.claude/rules/03-frontend.md` | Next.js, TypeScript, Tailwind, shadcn/ui |
| `.claude/rules/04-database.md` | Full schema reference |
| `.claude/rules/08-security.md` | HIPAA, JWT, RBAC, encryption |
| `docs/API_SPEC.md` | API endpoint contracts |
| `docs/DB_SCHEMA.md` | Database schema details |
