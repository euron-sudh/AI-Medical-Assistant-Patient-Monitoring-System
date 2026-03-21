# MedAssist AI — Team Development Tracker

> **Purpose:** PK (project lead) is coordinating team development AND simulating additional developers to learn the full corporate workflow — branching, coding, PRs, code review, and merging. This document is the source of truth across all Claude sessions.
>
> **Date Started:** 2026-03-20
> **Lead:** PK (pkpcconnect2026@gmail.com / GitHub: pkpcconnect2026-code)

---

## Repository Collaborators (Real Team)

| GitHub Username | Role | Access Level | Status |
|----------------|------|-------------|--------|
| `euronone` | Org admin | Admin | Active |
| `pkpcconnect2026-code` | Project lead (PK) | Write | Active — pushing code |
| `SKME20417` (Sanjay Kumar) | Backend developer | Write | Active — PR #2 open |
| `euron-tech` | Team member | Write | No commits yet |

---

## Git History (What Has Happened So Far)

| Date | PR # | Branch | Author | Title | Status |
|------|------|--------|--------|-------|--------|
| 2026-03-17 | #1 | `chore/docs/update-learningguide-accuracy` | PK | Project scaffold (Flask, Next.js, Docker, CI, 25 rules, docs) | MERGED |
| 2026-03-20 | #2 | `feature/backend/patient-doctor-api` | **Sanjay Kumar** | Patient & Doctor CRUD API (FastAPI + Supabase) | OPEN — needs review |
| 2026-03-21 | #3 | `chore/docs/team-simulation-plan` | PK | This plan document | MERGED |

### CRITICAL ISSUE WITH PR #2 (Sanjay's Code)

Sanjay's PR has **major problems** that PK must address as lead:

1. **Wrong framework:** He used **FastAPI** instead of **Flask** (project standard is Flask per CLAUDE.md and rules/02-backend.md)
2. **Wrong database:** He used **Supabase** instead of local **PostgreSQL** (project uses Docker Compose PostgreSQL)
3. **Committed __pycache__/ and binary files** — should be in .gitignore
4. **Overwrites existing scaffold files** — his branch diverges significantly from main

**Lead Action Required:**
- Review PR #2, leave comments explaining the issues
- Request changes or close the PR
- Guide Sanjay to redo using Flask (or PK simulates the correct version)

This is a **real-world scenario** — team members sometimes go off-spec. The lead's job is to catch this in code review.

---

## How This Works

1. PK opens separate Claude sessions, each pretending to be a different developer
2. Each "developer" creates a feature branch, writes code, pushes, and opens a PR
3. PK (as lead) reviews and merges each PR in order
4. Everything follows the CONTRIBUTING.md workflow exactly — same as a real team
5. For real team members (Sanjay, euron-tech), PK reviews their actual PRs

---

## Developer Roster (Simulated + Real)

| Developer | Type | Role | Module Focus | Branch | Git Config |
|-----------|------|------|--------------|--------|------------|
| **Dev 1: Arjun** (simulated) | Backend Engineer | Auth system | JWT login, register, RBAC | `feature/auth/jwt-login-register` | `git config user.name "Arjun Mehta"` / `git config user.email "arjun@medassist-team.dev"` |
| **Dev 2: Sanjay Kumar** (REAL) | Backend Engineer | Patient & Doctor API | Patient CRUD, Doctor CRUD | `feature/backend/patient-doctor-api` | His own GitHub account: SKME20417 |
| **Dev 3: Rahul** (simulated) | Frontend Engineer | Auth UI + Layout | Login, register pages, sidebar | `feature/frontend/auth-pages` | `git config user.name "Rahul Sharma"` / `git config user.email "rahul@medassist-team.dev"` |
| **Dev 4: Sneha** (simulated) | AI Engineer | AI Agents | Base agent, Symptom Analyst | `feature/agents/base-and-symptom-analyst` | `git config user.name "Sneha Patel"` / `git config user.email "sneha@medassist-team.dev"` |
| **Dev 5: Vikram** (simulated) | Full-stack | Vitals & Monitoring | Vitals model, API, alerts | `feature/vitals/model-and-api` | `git config user.name "Vikram Reddy"` / `git config user.email "vikram@medassist-team.dev"` |
| **Dev 6: Pallavi** (simulated) | Backend Engineer | Patient & Doctor Models | Patient/Doctor profiles, medical history (Flask — the correct version) | `feature/patient/profile-and-history` | `git config user.name "Pallavi Desai"` / `git config user.email "pallavi@medassist-team.dev"` |

---

## Execution Order (Dependencies)

```
COMPLETED:
  ✅ Dev 1 (Arjun): Auth backend — MERGED as PR #4

BLOCKED:
  🚫 Dev 2 (Sanjay): PR #2 — review feedback given, waiting for fixes (wrong framework)

RUNNING NOW (4 parallel Claude sessions):
  ├── Dev 3 (Rahul): Frontend auth pages     ← no dependencies
  ├── Dev 4 (Sneha): AI agents               ← no dependencies (uses stubs)
  ├── Dev 5 (Vikram): Vitals model + API     ← no dependencies (uses User model)
  └── Dev 6 (Pallavi): Patient/Doctor models  ← no dependencies (builds on User model)

Merge Order:
  1. ✅ Dev 1 (Arjun) — Auth               ← MERGED
  2. Dev 6 (Pallavi) — Patient/Doctor       ← merge first (others may depend on it)
  3. Dev 3 (Rahul) — Frontend auth          ← independent, merge anytime
  4. Dev 5 (Vikram) — Vitals                ← merge after Pallavi
  5. Dev 4 (Sneha) — AI agents              ← merge after Pallavi
  6. Dev 2 (Sanjay) — if he reworks to Flask← merge last
  4. Dev 4 (Sneha) — AI agents           ← after #2 merges
  5. Dev 5 (Vikram) — Vitals             ← after #2 merges
```

---

## Status Tracker

| # | Developer | Type | Branch | Status | PR # | CI | Review | Merged |
|---|-----------|------|--------|--------|------|----|--------|--------|
| 1 | Arjun (Auth) | Simulated | `feature/auth/jwt-login-register` | DONE | #4 | PASS | APPROVED | ✅ MERGED |
| 2 | Sanjay (Patient/Doctor) | REAL | `feature/backend/patient-doctor-api` | CHANGES REQUESTED | #2 | — | FEEDBACK GIVEN | ❌ Waiting |
| 3 | Rahul (Frontend) | Simulated | `feature/frontend/auth-pages` | IN PROGRESS | — | — | — | — |
| 4 | Sneha (Agents) | Simulated | `feature/agents/base-and-symptom-analyst` | IN PROGRESS | — | — | — | — |
| 5 | Vikram (Vitals) | Simulated | `feature/vitals/model-and-api` | IN PROGRESS | — | — | — | — |
| 6 | Pallavi (Patient Models) | Simulated | `feature/patient/profile-and-history` | IN PROGRESS | — | — | — | — |

---

## Instructions for Each Claude Session

When PK opens a new Claude session to simulate a developer, paste this:

### For Dev 1 (Arjun — Auth): ALREADY DONE in session 1
```
Code is written and on branch feature/auth/jwt-login-register.
Just needs: git add, commit, push, and manual PR creation.
Git config: user.name="Arjun Mehta", user.email="arjun@medassist-team.dev"
```

### For Dev 3 (Rahul — Frontend Auth):
```
I'm simulating Developer "Rahul" (frontend engineer) for my team learning exercise.
Read docs/TEAM_SIMULATION_PLAN.md for full context.

FIRST run these git commands:
  git checkout main && git pull origin main
  git config user.name "Rahul Sharma"
  git config user.email "rahul@medassist-team.dev"
  git checkout -b feature/frontend/auth-pages

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
Write the code, commit, push, and open a PR.
```

### For Dev 4 (Sneha — AI Agents):
```
I'm simulating Developer "Sneha" (AI engineer) for my team learning exercise.
Read docs/TEAM_SIMULATION_PLAN.md for full context.

FIRST run these git commands:
  git checkout main && git pull origin main
  git config user.name "Sneha Patel"
  git config user.email "sneha@medassist-team.dev"
  git checkout -b feature/agents/base-and-symptom-analyst

Task: Build base agent + symptom analyst on branch feature/agents/base-and-symptom-analyst
Files to create/modify:
- backend/app/agents/__init__.py
- backend/app/agents/base_agent.py (abstract base class)
- backend/app/agents/orchestrator.py (agent router)
- backend/app/agents/symptom_analyst.py (symptom analysis agent)
- backend/app/agents/tools/__init__.py
- backend/app/agents/tools/medical_kb.py (RAG tool)
- backend/app/agents/tools/patient_history.py (patient data tool)
- backend/app/agents/prompts/system_prompts.py
- backend/app/agents/prompts/symptom_prompts.py
- backend/app/integrations/__init__.py
- backend/app/integrations/openai_client.py (OpenAI wrapper)
- tests/unit/agents/test_symptom_analyst.py
Follow CONTRIBUTING.md and .claude/rules/07-agents.md and 06-rag.md strictly.
Write the code, commit, push, and open a PR.
```

### For Dev 5 (Vikram — Vitals):
```
I'm simulating Developer "Vikram" (full-stack engineer) for my team learning exercise.
Read docs/TEAM_SIMULATION_PLAN.md for full context.

FIRST run these git commands:
  git checkout main && git pull origin main
  git config user.name "Vikram Reddy"
  git config user.email "vikram@medassist-team.dev"
  git checkout -b feature/vitals/model-and-api

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
Write the code, commit, push, and open a PR.
```

---

## What PK Does As Lead (After Each PR)

1. **Review the PR** — check code quality, naming, test coverage, framework compliance
2. **Request changes** if needed (comment on the PR with specific issues)
3. **Approve and merge** when satisfied
4. **Update the status tracker** in this document
5. **Ensure main stays green** — CI passes after each merge
6. **Handle real team PRs** — Sanjay's PR #2 needs review and feedback

---

## Lead's Review Checklist (For Each PR)

- [ ] Correct branch naming? (`feature/module/description`)
- [ ] Conventional commit messages? (`feat(scope): description`)
- [ ] Uses Flask (NOT FastAPI)? Per project rules
- [ ] Uses SQLAlchemy 2.0 style queries?
- [ ] Has Pydantic schemas for validation?
- [ ] Service layer pattern? (routes call services, not raw DB queries)
- [ ] Type hints on all functions?
- [ ] No `__pycache__`, `.env`, `venv/` committed?
- [ ] Tests included?
- [ ] CI passes?

---

## What PK Learns From This Exercise

- How branches isolate work so team members don't conflict
- How PRs enable code review before merging
- How CI catches bugs automatically
- How a lead reviews, approves, and merges work
- How to handle merge conflicts when two devs touch the same file
- How to write good PR descriptions and commit messages
- How to coordinate parallel development across a team
- **How to handle a team member who deviated from tech stack** (Sanjay's FastAPI situation)
- How to give constructive code review feedback

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
