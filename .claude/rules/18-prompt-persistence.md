# Prompt Persistence Rules

## Purpose

Every user prompt submitted to the AI assistant must be saved for traceability, debugging, and analytics. This applies to all AI-facing prompts across symptom checking, triage, report generation, voice transcription, and general medical Q&A.

## Storage Location

Save all prompts to:

```
prompts/prompt-history.md
```

This file is append-only. Never overwrite, truncate, or delete entries.

## Format

Each entry must follow this exact format:

```markdown
### [YYYY-MM-DD HH:MM:SS UTC]

**Prompt:**

<prompt text here>

---
```

Example:

```markdown
### [2026-03-16 14:32:07 UTC]

**Prompt:**

Analyze the following vitals for patient and determine if any values are outside normal range: heart rate 112 bpm, blood pressure 145/92 mmHg, SpO2 94%, temperature 38.2C.

---
```

## Rules

### Append-Only

- Always append to the end of the file. Never modify or remove existing entries.
- If the file does not exist, create it with a header:

```markdown
# Prompt History

All AI prompts logged here for traceability.

---
```

### Redaction

Before writing any prompt to the file, redact the following:

| Pattern                | Replacement          |
| ---------------------- | -------------------- |
| Passwords              | `[REDACTED_PASSWORD]` |
| API keys / tokens      | `[REDACTED_KEY]`     |
| SSN patterns           | `[REDACTED_SSN]`     |
| Credit card numbers    | `[REDACTED_CC]`      |
| Email addresses        | `[REDACTED_EMAIL]`   |
| Phone numbers          | `[REDACTED_PHONE]`   |
| Patient names (PII)    | `[REDACTED_NAME]`    |
| Date of birth          | `[REDACTED_DOB]`     |
| Medical record numbers | `[REDACTED_MRN]`     |

Use regex-based redaction before appending. PII/PHI redaction is mandatory for HIPAA compliance.

### Keep Generic

- Prompts stored in this file must be generic: stripped of identifying patient information.
- The raw prompt with full context is stored in the database `ai_interactions` table (encrypted at rest).
- `prompt-history.md` serves as a lightweight, human-readable log of prompt patterns and templates.

### Template Extraction

- When a prompt matches a recurring pattern, note the template in `prompts/prompt-templates.md` separately.
- Templates help standardize prompt engineering across the team.

## Implementation

```python
import re
from datetime import datetime, timezone

REDACTION_PATTERNS = {
    r'\b\d{3}-\d{2}-\d{4}\b': '[REDACTED_SSN]',
    r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b': '[REDACTED_CC]',
    r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+': '[REDACTED_PASSWORD]',
    r'(?i)(api[_-]?key|token|secret)\s*[:=]\s*\S+': '[REDACTED_KEY]',
}

def redact_prompt(text: str) -> str:
    for pattern, replacement in REDACTION_PATTERNS.items():
        text = re.sub(pattern, replacement, text)
    return text

def save_prompt(prompt: str, file_path: str = "prompts/prompt-history.md") -> None:
    redacted = redact_prompt(prompt)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"\n### [{timestamp}]\n\n**Prompt:**\n\n{redacted}\n\n---\n"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(entry)
```

## File Maintenance

- Rotate `prompt-history.md` monthly: archive to `prompts/archive/prompt-history-YYYY-MM.md`.
- Archived files are read-only.
- Maximum file size before forced rotation: 10 MB.
- Rotation is handled by a Celery periodic task.
