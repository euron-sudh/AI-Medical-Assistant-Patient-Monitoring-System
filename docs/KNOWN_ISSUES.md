# MedAssist AI — Known Issues

Tested on: 2026-03-26
Environment: GCP Production (http://medassist-ai.136.119.221.67.nip.io)

## CRITICAL (4)

### 1. CORS allows any origin with credentials
- **Where:** Backend CORS configuration
- **Impact:** Any malicious website can make authenticated requests and steal tokens
- **Fix:** Restrict `Access-Control-Allow-Origin` to the app's domain only

### 2. Stored XSS — no input sanitization on user names
- **Where:** POST /api/v1/auth/register
- **Impact:** `<script>alert(1)</script>` accepted as `first_name`, returned unsanitized in API responses. If frontend renders via `dangerouslySetInnerHTML`, enables XSS attacks.
- **Fix:** Sanitize/escape HTML in user input fields at the API layer

### 3. Admin pages accessible without authentication
- **Where:** Frontend — all 9 `/admin/*` pages
- **Impact:** Unauthenticated users can access admin dashboard, user management, system health, AI config, audit logs, analytics, alerts, platform metrics, and settings. Leaks real user counts and DB config.
- **Fix:** Add auth middleware to protect `/admin/*` routes in Next.js middleware.ts

### 4. Medications, Reports, Telemedicine, Symptom sessions APIs missing
- **Where:** Backend routes
- **Endpoints returning 404:**
  - `GET/POST /api/v1/medications` — Medications/Prescriptions
  - `GET/POST /api/v1/reports` — Medical Reports
  - `GET/POST /api/v1/telemedicine/sessions` — Telemedicine
  - `GET /api/v1/symptoms/sessions` — Symptom session listing
- **Impact:** Frontend pages exist but have no working backend. Doctor prescriptions workflow completely broken.
- **Fix:** Implement the missing API route handlers and register blueprints

## HIGH (4)

### 5. Vitals anomaly detection not working
- **Where:** POST /api/v1/vitals/{user_id}
- **Impact:** Abnormal vitals (HR=110, BP=145/95, temp=101.5, O2=94%, RR=22) all flagged as `is_anomalous: false`. No alerts generated for dangerous readings.
- **Fix:** Review anomaly detection thresholds in vitals_service.py

### 6. Doctor cannot access patient data
- **Where:** GET /api/v1/patients (returns empty), GET /api/v1/patients/{id} (returns 403)
- **Impact:** Doctors cannot view patient profiles, medical history, or allergies. Core doctor workflow completely blocked.
- **Note:** Access control inconsistency — doctors CAN view patient vitals and create appointments/care plans, but CANNOT view patient profiles.
- **Fix:** Establish doctor-patient relationship when appointment is created; update access control to allow doctors to view their patients

### 7. 500 Internal Server Error on appointment creation with doctor profile ID
- **Where:** POST /api/v1/appointments
- **Impact:** Using the `id` from GET /api/v1/doctors (profile ID) as `doctor_id` causes a 500 error. Must use `user_id` instead. No clear error message.
- **Fix:** Validate `doctor_id` and return a 400 with a clear message, or accept both profile ID and user ID

### 8. No admin user creation path
- **Where:** POST /api/v1/auth/register
- **Impact:** API schema blocks admin role registration. No endpoint to promote users. Admin can only be created via seed script or direct DB access.
- **Fix:** Add a seed command or admin promotion endpoint (protected by existing admin auth)

## MEDIUM (4)

### 9. Patients cannot add own medical history or allergies
- **Where:** POST /api/v1/patients/{id}/medical-history, POST /api/v1/patients/{id}/allergies
- **Impact:** Returns 403 for patient role. Patients should be able to self-report.
- **Fix:** Add `patient` to allowed roles for these endpoints (own data only)

### 10. No rate limiting on authenticated endpoints
- **Where:** All API endpoints
- **Impact:** 10+ rapid requests all succeed with 200. Vulnerable to brute-force and API abuse.
- **Fix:** Verify Flask-Limiter is actually active with Redis backend in production

### 11. Appointment creation requires patient_id when authenticated as patient
- **Where:** POST /api/v1/appointments
- **Impact:** Should auto-fill patient_id from JWT token.
- **Fix:** Default `patient_id` to current user if role is patient

### 12. cancelled_by not populated when cancelling appointment
- **Where:** PUT /api/v1/appointments/{id}
- **Impact:** No audit trail of who cancelled.
- **Fix:** Set `cancelled_by` to current user ID when status changes to "cancelled"

## LOW (4)

### 13. Inconsistent 404 vs empty array for no-data responses
- **Where:** medications, reports, telemedicine return 404; appointments, care-plans, notifications return []
- **Fix:** Standardize to return `[]` with 200 for list endpoints with no data

### 14. Invalid token returns 422 instead of 401
- **Where:** JWT error handling
- **Impact:** Leaks JWT library info ("Not enough segments", "Signature verification failed")
- **Fix:** Override Flask-JWT-Extended error handlers to return 401

### 15. Field naming inconsistency in API
- **Where:** Multiple endpoints
- **Examples:** `current_password` vs documented `old_password`; `chief_complaint` vs documented `initial_symptoms`
- **Fix:** Update API docs or standardize field names

### 16. doctor_id ambiguity in appointments
- **Where:** POST /api/v1/appointments
- **Impact:** Field `doctor_id` expects user UUID, not doctor profile UUID. Confusing API design.
- **Fix:** Accept either ID or document clearly which one to use

---

## Test Credentials
- Patient: `testpatient@medassist.ai` / `TestPass123!`
- Doctor: `testdoctor@medassist.ai` / `TestPass123!`
- Admin: No admin exists — must be created via seed script
