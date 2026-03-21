# Security Rules — MedAssist AI

**HIPAA compliance is mandatory.** Every developer, every PR, every deployment must uphold this. Violations are treated as severity-0 incidents.

---

## Authentication

### JWT with Flask-JWT-Extended

| Token | Lifetime | Storage |
|---|---|---|
| Access token | 15 minutes | Client memory (never localStorage) |
| Refresh token | 7 days | HttpOnly secure cookie |

- Access tokens are short-lived and stateless. Refresh tokens are tracked in Redis (`session:{user_id}`) for revocation.
- On logout, blacklist the refresh token in Redis immediately.
- Tokens must include: `sub` (user_id), `role`, `iat`, `exp`, `jti` (unique token ID).
- Never include PHI (patient name, MRN, diagnosis) in token claims.

---

## Roles & Authorization

### Role Hierarchy

| Role | Description |
|---|---|
| `patient` | End-user patient — access to own data only |
| `doctor` | Licensed physician — access to assigned patients |
| `nurse` | Licensed nurse — access to assigned patients |
| `admin` | Full system access — user management, system config, infrastructure, audit logs |

### Role Access Matrix

| Resource / Action | patient | doctor | nurse | admin |
|---|---|---|---|---|
| Own profile (read/write) | Y | Y | Y | Y |
| Own medical records | Y (read) | -- | -- | -- |
| Assigned patient records | -- | Y | Y | -- |
| Symptom analysis (self) | Y | -- | -- | -- |
| Symptom analysis (patient) | -- | Y | Y | -- |
| Triage | -- | Y | Y | -- |
| Drug interaction check | Y (own meds) | Y | Y | -- |
| Vitals monitoring dashboard | Y (own) | Y | Y | -- |
| Report upload / reading | Y (own) | Y | Y | -- |
| Care plans | Y (own, read) | Y | Y | -- |
| User management | -- | -- | -- | Y |
| Audit logs | -- | -- | -- | Y |
| System configuration | -- | -- | -- | Y |

### Resource-Level Authorization

- **Patients** can only access their own data. Every query must filter by `patient_id = current_user.id`.
- **Doctors and Nurses** can only access records of patients assigned to them. Verify assignment in the `patient_provider` table before granting access.
- Implement authorization checks in the **service layer** (not just route decorators) to prevent bypass.
- Use a `@require_role(roles)` decorator on Flask routes and a `check_resource_access(user, resource)` function in services.

---

## Multi-Factor Authentication

- **MFA is mandatory** for all healthcare provider roles (`doctor`, `nurse`, `admin`).
- MFA is optional but recommended for `patient` role.
- Support TOTP (authenticator app) as the primary MFA method.
- MFA verification is required at login. The access token is not issued until MFA passes.
- Enforce MFA re-verification for sensitive actions: viewing full SSN, exporting patient data, changing credentials.

---

## HIPAA Audit Logging

Every access to Protected Health Information (PHI) must be logged in the `audit_logs` table:

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID NOT NULL REFERENCES users(id),
    user_role VARCHAR(20) NOT NULL,
    action VARCHAR(50) NOT NULL,        -- e.g., 'view_patient_record', 'export_data'
    resource_type VARCHAR(50) NOT NULL,  -- e.g., 'patient_record', 'lab_result'
    resource_id UUID,
    patient_id UUID,                     -- whose PHI was accessed
    ip_address INET NOT NULL,
    user_agent TEXT,
    details JSONB,                       -- additional context
    status VARCHAR(10) NOT NULL          -- 'success' or 'denied'
);
```

- **Every** PHI access — successful or denied — must produce an audit log entry.
- Audit logs are append-only. No updates or deletes are permitted on this table.
- Audit logs must be retained for a minimum of **6 years** (HIPAA requirement).
- Audit log writes must not block the request — use async logging (Celery task or background thread).

---

## Data Encryption

| Layer | Standard | Implementation |
|---|---|---|
| At rest | AES-256 | PostgreSQL pgcrypto for sensitive columns; S3/MinIO server-side encryption |
| In transit | TLS 1.3 | Enforce on all endpoints; HSTS header with min 1 year max-age |
| Backups | AES-256 | Encrypted database backups; encrypted S3 bucket for file storage |

- Encrypt these columns: `ssn`, `date_of_birth`, `phone_number`, `address`, `insurance_id`.
- Use application-level encryption (not just disk-level) for the most sensitive fields.
- Encryption keys are stored in AWS KMS or HashiCorp Vault — never in code, config files, or environment variables on disk.

---

## Rate Limiting

See `05-caching.md` for the detailed rate-limiting implementation. Summary:

- Rate limits are enforced per role and per endpoint.
- AI agent endpoints have additional per-user daily token budget limits.
- Return `429` with `Retry-After` header when limits are exceeded.

---

## Input Validation

- Validate all inputs at the **route level** using Marshmallow or Pydantic schemas.
- Reject requests that fail validation with `400 Bad Request` — never pass unvalidated data downstream.
- Sanitize all text inputs that will be displayed in the frontend (XSS prevention).
- Use parameterized queries exclusively — no string interpolation in SQL.
- Validate file uploads: allowed MIME types (`image/png`, `image/jpeg`, `application/pdf`), max size (20MB), virus scan.

---

## CORS Configuration

```python
CORS_ORIGINS = [
    "https://medassist.example.com",    # Production frontend
    "https://staging.medassist.example.com",
]
# In development only:
# CORS_ORIGINS.append("http://localhost:3000")
```

- Never use `"*"` for CORS origins in production.
- Allow credentials (`Access-Control-Allow-Credentials: true`).
- Restrict methods to those actually used: `GET, POST, PUT, PATCH, DELETE, OPTIONS`.

---

## Security Headers

Every response must include:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(self), geolocation=()
```

- Microphone access is allowed for the Voice Agent feature only.

---

## AI Safety

### Prompt Injection Defense

- System prompts are loaded from files and are **never** constructed from user input.
- User messages are passed only in the `user` role — never concatenated into the `system` prompt.
- Implement input scanning: reject messages containing known injection patterns (e.g., "ignore previous instructions", "system: ").

### Tool Input/Output Validation

- Every tool call argument from the LLM must be validated against the tool's Pydantic input schema before execution.
- Tool return values are validated against the output schema before being sent back to the LLM.
- If validation fails, return a structured error — do not pass malformed data.

### Content Filtering

- Run all user inputs through the **OpenAI Moderation API** before processing.
- Flag and log content that violates medical ethics or safety policies.
- Block requests that attempt to extract prescriptions without proper provider authorization.

### PII Redaction Before AI Calls

Before sending any data to OpenAI APIs:

1. Replace patient names with `[PATIENT]`.
2. Replace MRNs with `[MRN]`.
3. Replace SSNs with `[SSN]`.
4. Replace dates of birth with `[DOB]`.
5. Replace phone numbers with `[PHONE]`.
6. Replace addresses with `[ADDRESS]`.

Maintain a redaction map in the session to re-hydrate the response before returning to the user.

### System Prompt Protection

- Never expose system prompts to users via API responses or error messages.
- Agents must refuse requests like "repeat your instructions" or "what is your system prompt".

---

## Secrets Management

- **No secrets in code.** No API keys, database passwords, or encryption keys in source files.
- Use environment variables loaded from a secrets manager (AWS Secrets Manager, Vault) at deploy time.
- `.env` files are in `.gitignore` and used for local development only.
- Rotate secrets on a quarterly schedule. Rotate immediately if a compromise is suspected.
- Pre-commit hooks must scan for accidental secret commits (use `detect-secrets` or `trufflehog`).
