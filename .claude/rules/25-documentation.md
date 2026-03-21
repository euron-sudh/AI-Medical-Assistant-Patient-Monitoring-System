# Documentation Standards for MedAssist AI

## API Documentation

### Flasgger (Swagger / OpenAPI 3.0)

All Flask API endpoints must be documented using Flasgger annotations that generate OpenAPI 3.0 compliant specs.

```python
@app.route('/api/v1/patients/<patient_id>/vitals', methods=['GET'])
@require_role(['doctor', 'nurse', 'patient'])
@swag_from({
    'tags': ['Vitals'],
    'summary': 'Get patient vitals history',
    'description': 'Retrieve vital sign readings for a patient within a time range. '
                   'Patients can only access their own vitals. Doctors and nurses can '
                   'access vitals of their assigned patients.',
    'parameters': [
        {
            'name': 'patient_id',
            'in': 'path',
            'type': 'string',
            'format': 'uuid',
            'required': True,
            'description': 'Patient UUID'
        },
        {
            'name': 'start_date',
            'in': 'query',
            'type': 'string',
            'format': 'date-time',
            'description': 'Start of time range (ISO 8601)'
        },
        {
            'name': 'end_date',
            'in': 'query',
            'type': 'string',
            'format': 'date-time',
            'description': 'End of time range (ISO 8601)'
        }
    ],
    'responses': {
        200: {'description': 'List of vital readings'},
        403: {'description': 'Forbidden - insufficient permissions'},
        404: {'description': 'Patient not found'}
    },
    'security': [{'Bearer': []}]
})
def get_patient_vitals(patient_id):
    ...
```

Every endpoint must document:
- Tags (grouping by feature area).
- Summary (one-line description).
- Description (detailed explanation including RBAC rules).
- All parameters (path, query, body) with types and descriptions.
- All response codes with descriptions.
- Security requirements.
- Request/response body schemas (using `definitions` or inline).

Swagger UI is available at `/api/docs` in development and staging environments. Disabled in production.

## Python Docstrings

All Python functions, classes, and methods must have docstrings with type hints.

### Format: Google Style

```python
def analyze_vitals(
    patient_id: str,
    vitals: list[VitalReading],
    threshold_config: ThresholdConfig | None = None,
) -> VitalAnalysisResult:
    """Analyze patient vitals against configured thresholds.

    Evaluates each vital reading against normal ranges and configured
    thresholds. Calculates NEWS2 and MEWS scores. Generates monitoring
    alerts for any threshold breaches.

    Args:
        patient_id: UUID of the patient whose vitals are being analyzed.
        vitals: List of vital readings to analyze.
        threshold_config: Optional custom thresholds. Uses defaults if None.

    Returns:
        VitalAnalysisResult containing:
            - risk_level: Overall risk assessment (low, medium, high, critical).
            - news2_score: Calculated NEWS2 score.
            - alerts: List of generated monitoring alerts.
            - recommendations: AI-generated clinical recommendations.

    Raises:
        PatientNotFoundError: If patient_id does not exist.
        InvalidVitalsError: If any vital reading has invalid values.

    Note:
        This function creates audit log entries for PHI access.
        All generated alerts are persisted to the monitoring_alerts table.
    """
```

### Rules for Docstrings

- All public functions and methods require docstrings.
- Private methods (prefixed with `_`) require docstrings if logic is non-trivial.
- Include `Args`, `Returns`, `Raises` sections when applicable.
- Document side effects (database writes, audit logging, external API calls).
- Use type hints in function signatures AND reference them in docstrings.

## TypeScript / React Documentation

### Component Prop Types

All React components must define props via TypeScript interfaces with JSDoc comments:

```typescript
/**
 * Real-time vitals chart displaying patient vital signs from InfluxDB.
 *
 * Connects to WebSocket for live updates. Falls back to polling if
 * WebSocket connection fails. Supports multiple vital types displayed
 * as overlaid time-series.
 */
interface VitalsChartProps {
  /** UUID of the patient whose vitals to display */
  patientId: string;
  /** Vital types to include in the chart */
  vitalTypes: VitalType[];
  /** Time range for historical data (default: 24 hours) */
  timeRange?: TimeRange;
  /** Callback fired when a vital reading is clicked */
  onReadingClick?: (reading: VitalReading) => void;
  /** Whether to show the AI analysis overlay */
  showAIAnalysis?: boolean;
  /** Refresh interval in seconds for polling fallback (default: 30) */
  refreshInterval?: number;
}

export function VitalsChart({
  patientId,
  vitalTypes,
  timeRange = '24h',
  onReadingClick,
  showAIAnalysis = false,
  refreshInterval = 30,
}: VitalsChartProps): JSX.Element {
  // ...
}
```

### Rules for Frontend Documentation

- Every exported component must have a JSDoc comment explaining its purpose.
- All props must be documented with JSDoc comments in the interface.
- Custom hooks must document their return values and side effects.
- Complex state management logic must have inline comments.

## Agent Tool Descriptions

All AI agent tools (functions available for OpenAI function calling) must have precise descriptions:

```python
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_patient_vitals",
            "description": (
                "Retrieve the most recent vital signs for a patient. "
                "Returns heart rate, blood pressure, SpO2, temperature, "
                "and respiratory rate with timestamps. Use this when you "
                "need to assess a patient's current physiological status "
                "or check for recent changes in vitals."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "The UUID of the patient"
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours of history to retrieve (default: 24, max: 168)",
                        "default": 24
                    }
                },
                "required": ["patient_id"]
            }
        }
    }
]
```

### Rules for Tool Descriptions

- Descriptions must explain WHAT the tool does and WHEN to use it.
- Parameter descriptions must include type, format, constraints, and defaults.
- Tool descriptions must not contain PHI examples.
- Keep descriptions concise but complete (LLM token efficiency matters).

## Medical Terminology Glossary

Maintain a glossary file at `docs/MEDICAL_GLOSSARY.md` containing:

- Medical abbreviations used in the codebase (NEWS2, MEWS, SpO2, HR, BP, etc.).
- Clinical terms referenced in agent prompts and UI labels.
- Standard vital sign ranges and units.
- Severity level definitions as used in the alert system.

This glossary serves both developers and the AI agents (included in system prompts for context).

## HIPAA Compliance Documentation

Maintain at `docs/HIPAA_COMPLIANCE.md`:

- Data classification: what constitutes PHI in the system.
- Access control matrix: which roles can access which data.
- Encryption specifications: at rest (AES-256) and in transit (TLS 1.3).
- Audit trail requirements and retention policy (minimum 6 years).
- Breach notification procedures.
- Business Associate Agreement (BAA) requirements for third-party services.
- Data retention and disposal policies.

## Architecture Decision Records (ADRs)

Store ADRs in `docs/adr/` with sequential numbering:

```
docs/adr/
├── 001-flask-backend.md
├── 002-nextjs-frontend.md
├── 003-openai-gpt4o-model.md
├── 004-influxdb-vitals-storage.md
├── 005-pinecone-vector-store.md
├── 006-dailyco-telemedicine.md
├── 007-celery-task-queue.md
└── ...
```

### ADR Format

```markdown
# ADR-{number}: {Title}

## Status
{Proposed | Accepted | Deprecated | Superseded by ADR-XXX}

## Context
{What is the problem or decision that needs to be made?}

## Decision
{What was decided and why?}

## Consequences
{What are the positive and negative outcomes of this decision?}

## Alternatives Considered
{What other options were evaluated?}
```

## Project Documentation Files

The following documentation files must exist and be maintained:

| File                     | Location               | Content                                              |
| ------------------------ | ---------------------- | ---------------------------------------------------- |
| `README.md`              | Root                   | Project overview, setup instructions, quick start     |
| `CONTRIBUTING.md`        | Root                   | Contribution guidelines, code style, PR process       |
| `docs/PRD.md`            | `docs/`                | Product Requirements Document                         |
| `docs/ARCHITECTURE.md`   | `docs/`                | System architecture, component diagrams, data flow    |
| `docs/DB_SCHEMA.md`      | `docs/`                | Database schema documentation, ER diagrams            |
| `docs/API_SPEC.md`       | `docs/`                | API specification (supplement to Swagger)              |
| `docs/DEPLOYMENT.md`     | `docs/`                | Deployment guide: Docker, K8s, environment setup      |
| `docs/MEDICAL_GLOSSARY.md` | `docs/`              | Medical terminology glossary                          |
| `docs/HIPAA_COMPLIANCE.md` | `docs/`              | HIPAA compliance documentation                        |

## Rules

- Documentation must be updated in the same PR as the code change it describes.
- API documentation (Flasgger) is mandatory for every endpoint before merge.
- Outdated documentation is worse than no documentation. If you change behavior, update the docs.
- Code comments explain "why", not "what". The code itself should explain "what".
- All documentation must be written in American English.
- Use consistent terminology from the medical glossary throughout all documentation.
- Diagrams use Mermaid syntax for version control compatibility.
- Documentation PRs are reviewed by at least one developer and one domain expert (for medical content).
