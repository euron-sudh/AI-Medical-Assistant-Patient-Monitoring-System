# Three Interfaces for MedAssist AI

## Overview

MedAssist AI has exactly three web interfaces, all served from a single Next.js 14+ application with role-based routing. There is no separate mobile app or standalone admin/user split. All interfaces share the same Flask API backend.

The three interfaces are:

1. **Patient Portal** -- for patients
2. **Doctor Dashboard** -- for doctors and nurses
3. **Admin Panel** -- for administrators

## Architecture

```
Single Next.js App (frontend/)
├── app/patient/*    → Patient Portal
├── app/doctor/*     → Doctor Dashboard
├── app/admin/*      → Admin Panel
└── middleware.ts    → RBAC route guard

Single Flask API (backend/)
└── /api/v1/*        → Serves all three interfaces
```

- One deployment, one domain, one authentication system.
- Role-based access control (RBAC) enforced at the Next.js middleware level for route protection.
- RBAC additionally enforced at the Flask API level for every endpoint.
- Nurses share the Doctor Dashboard with a reduced permission set (no prescribing).

## Interface 1: Patient Portal

**Route prefix:** `/patient/*`
**Roles:** `patient`

| Route                         | Feature                                    |
| ----------------------------- | ------------------------------------------ |
| `/patient`                    | Home dashboard (upcoming appointments, alerts, quick actions) |
| `/patient/symptoms`           | AI symptom checker (chat + voice input)     |
| `/patient/reports`            | View medical reports and AI-generated summaries |
| `/patient/medications`        | Active medications, refill requests, reminders |
| `/patient/vitals`             | Log and view vitals (manual + device sync)  |
| `/patient/appointments`       | Schedule, view, cancel appointments         |
| `/patient/telemedicine`       | Video consultation via Daily.co WebRTC      |
| `/patient/care-plan`          | AI-generated care plans, goals, progress    |
| `/patient/chat`               | Real-time chat with care team               |
| `/patient/voice`              | Voice-based AI interaction (Whisper + TTS)  |
| `/patient/profile`            | Profile, notification preferences, settings |

### Patient Portal Rules

- All medical data displayed must include disclaimers that AI-generated content is not a substitute for professional medical advice.
- Vitals input must validate ranges before submission (e.g., heart rate 30-250 bpm).
- Reports marked as "AI-generated" must be clearly labeled with confidence scores.
- Voice interface requires explicit user consent before recording.

## Interface 2: Doctor Dashboard

**Route prefix:** `/doctor/*`
**Roles:** `doctor`, `nurse`

| Route                              | Feature                                    |
| ---------------------------------- | ------------------------------------------ |
| `/doctor`                          | Home dashboard (patient queue, alerts, stats) |
| `/doctor/patients`                 | Patient list with search, filters, risk scores |
| `/doctor/patients/:id`            | Individual patient detail (history, vitals, reports) |
| `/doctor/monitoring`              | Real-time vital monitoring (WebSocket-driven) |
| `/doctor/monitoring/:patientId`   | Single patient real-time monitoring view    |
| `/doctor/prescriptions`           | Prescribe medications, review history (doctor only) |
| `/doctor/appointments`            | View and manage appointment schedule        |
| `/doctor/telemedicine`            | Video consultation room (Daily.co WebRTC)   |
| `/doctor/telemedicine/:sessionId` | Active telemedicine session                 |
| `/doctor/analytics`               | Patient outcome analytics, trends           |
| `/doctor/ai-assistant`            | AI-powered clinical decision support        |

### Doctor Dashboard Rules

- Real-time monitoring must use WebSocket connections, not polling.
- Patient list defaults to showing only patients assigned to the logged-in doctor/nurse.
- Prescription routes (`/doctor/prescriptions`) are restricted to `doctor` role only; nurses cannot prescribe.
- AI assistant suggestions must display evidence sources and confidence levels.
- All patient data access is logged to the HIPAA audit trail.
- Monitoring alerts must be visible within 2 seconds of generation.

## Interface 3: Admin Panel

**Route prefix:** `/admin/*`
**Roles:** `admin`

| Route                      | Feature                              |
| -------------------------- | ------------------------------------ |
| `/admin`                   | Admin overview (system stats, alerts) |
| `/admin/users`             | User management (CRUD, role changes) |
| `/admin/users/:id`         | Individual user detail and actions   |
| `/admin/audit-logs`        | HIPAA audit log viewer and export    |
| `/admin/system-health`     | Infrastructure health monitoring     |
| `/admin/ai-config`         | AI agent configuration and thresholds |
| `/admin/ai-analytics`      | AI usage, token costs, model stats   |
| `/admin/platform-metrics`  | Platform usage analytics             |
| `/admin/alerts`            | Monitoring alert summary             |

### Admin Panel Rules

- See `17-admin-dashboard.md` for full admin dashboard specifications.
- Admin sessions timeout after 15 minutes of inactivity.
- All admin actions are double-logged: application log and HIPAA audit log.

## RBAC Middleware

### Next.js Middleware (`middleware.ts`)

```typescript
const ROUTE_ROLES: Record<string, string[]> = {
  '/patient': ['patient'],
  '/doctor': ['doctor', 'nurse'],
  '/admin': ['admin'],
};
```

- Extract role from JWT token in the session cookie.
- Match request path against `ROUTE_ROLES`.
- Redirect unauthorized users to `/unauthorized` (403 page).
- Redirect unauthenticated users to `/login`.

### Flask API Middleware

- Every API endpoint uses a `@require_role(roles)` decorator.
- Role is extracted from the JWT Bearer token.
- Unauthorized requests return `403 Forbidden` with an audit log entry.
- No endpoint is accessible without authentication except `/api/v1/auth/login` and `/api/v1/auth/register`.

## Shared Components

Components used across multiple interfaces live in `frontend/src/components/shared/`:

- `VideoCall` -- Daily.co WebRTC wrapper (used by patient and doctor telemedicine).
- `ChatWindow` -- Real-time chat component (used by patient chat and doctor-patient communication).
- `VitalsChart` -- InfluxDB-backed vitals visualization (used by patient vitals and doctor monitoring).
- `NotificationBell` -- Real-time notification indicator (used by all three interfaces).
- `AIDisclaimer` -- Standard medical AI disclaimer banner.

## Redirects After Login

| Role    | Redirect Target |
| ------- | --------------- |
| patient | `/patient`      |
| doctor  | `/doctor`       |
| nurse   | `/doctor`       |
| admin   | `/admin`        |
