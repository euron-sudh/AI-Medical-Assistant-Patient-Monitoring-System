# Agent Orchestration Rules — MedAssist AI

MedAssist AI runs **7 specialized AI agents** coordinated by an **Agent Orchestrator**. Every agent extends `BaseAgent`, uses OpenAI function calling, and accesses data exclusively through a tool layer — never via direct database queries.

---

## Architecture

```
User Request
      │
      ▼
Agent Orchestrator
      │
      ├─→ Symptom Analyst Agent
      ├─→ Report Reader Agent
      ├─→ Triage Agent
      ├─→ Voice Agent
      ├─→ Drug Interaction Agent
      ├─→ Monitoring Agent
      └─→ Follow-Up Agent
```

The Orchestrator inspects the user intent, selects one or more specialist agents, fans out work, and assembles the final response.

---

## Agent Specifications

### 1. Symptom Analyst Agent

| Property | Value |
|---|---|
| Model | GPT-4o |
| Purpose | Analyze patient symptoms, generate differential diagnoses, recommend specialists |

**Tools:**

| Tool | Description |
|---|---|
| `search_medical_kb` | Query RAG pipeline (Pinecone + Elasticsearch) for medical knowledge |
| `query_patient_history` | Retrieve patient medical history from PostgreSQL via service layer |
| `calculate_urgency_score` | Compute urgency score (1-10) based on symptom severity |
| `generate_differential_diagnosis` | Produce ranked list of possible diagnoses with confidence scores |
| `recommend_specialist` | Suggest specialist type based on differential diagnosis |

---

### 2. Report Reader Agent

| Property | Value |
|---|---|
| Model | GPT-4o (Vision) |
| Purpose | Parse medical reports/images, extract lab values, identify abnormalities |

**Tools:**

| Tool | Description |
|---|---|
| `extract_text_from_image` | OCR extraction from uploaded report images (S3/MinIO) |
| `parse_lab_values` | Extract structured lab values with units and reference ranges |
| `identify_abnormalities` | Flag out-of-range values and clinically significant findings |
| `explain_report` | Generate patient-friendly explanation of report findings |
| `correlate_with_history` | Compare current results against patient's historical data |

---

### 3. Triage Agent

| Property | Value |
|---|---|
| Model | GPT-4o-mini |
| Purpose | Emergency triage, priority assignment, wait-time estimation |

**Tools:**

| Tool | Description |
|---|---|
| `calculate_esi_score` | Compute Emergency Severity Index (ESI) level 1-5 |
| `check_emergency_symptoms` | Match against emergency symptom red-flag checklist |
| `get_wait_times` | Retrieve current facility wait times |
| `assign_priority` | Assign and persist triage priority to the encounter |

---

### 4. Voice Agent

| Property | Value |
|---|---|
| Model | Whisper (STT) + TTS |
| Purpose | Voice-based interaction, clinical note generation |

**Tools:**

| Tool | Description |
|---|---|
| `transcribe_audio` | Convert audio input to text via Whisper API |
| `synthesize_speech` | Convert text response to audio via TTS API |
| `generate_clinical_notes` | Produce SOAP-format clinical notes from conversation |

---

### 5. Drug Interaction Agent

| Property | Value |
|---|---|
| Model | GPT-4o-mini |
| Purpose | Check drug interactions, verify dosages, suggest alternatives |

**Tools:**

| Tool | Description |
|---|---|
| `check_interactions` | Query drug interaction database for conflicts |
| `verify_dosage` | Validate prescribed dosage against guidelines (weight, age, renal function) |
| `suggest_alternatives` | Recommend alternative medications when interactions are found |
| `check_allergies` | Cross-reference medication against patient allergy records |

---

### 6. Monitoring Agent

| Property | Value |
|---|---|
| Model | GPT-4o-mini |
| Purpose | Real-time vitals monitoring, anomaly detection, alerting |

**Tools:**

| Tool | Description |
|---|---|
| `read_vitals` | Query InfluxDB for patient vitals (HR, BP, SpO2, temp, RR) |
| `calculate_news2_score` | Compute National Early Warning Score 2 from current vitals |
| `detect_anomalies` | Run anomaly detection on vitals time series |
| `trigger_alert` | Send alert via Redis Pub/Sub + persist to PostgreSQL |

---

### 7. Follow-Up Agent

| Property | Value |
|---|---|
| Model | GPT-4o |
| Purpose | Care plan generation, adherence tracking, follow-up scheduling |

**Tools:**

| Tool | Description |
|---|---|
| `generate_care_plan` | Create personalized post-visit care plan |
| `track_adherence` | Monitor patient compliance with care plan |
| `adjust_care_plan` | Modify care plan based on progress and feedback |
| `schedule_followup` | Schedule follow-up appointments and reminders |

---

## BaseAgent Contract

Every agent must extend `BaseAgent` and implement:

```python
class BaseAgent(ABC):
    agent_name: str
    model: str
    tools: list[dict]           # OpenAI function-calling tool definitions
    system_prompt: str          # Loaded from prompts/ directory
    max_tokens: int
    timeout: int = 300          # 5 minutes

    @abstractmethod
    async def run(self, input: AgentInput) -> AgentOutput: ...

    def _build_messages(self, input: AgentInput) -> list[dict]: ...
    def _execute_tool(self, tool_call: ToolCall) -> ToolResult: ...
    def _log_usage(self, tokens_used: TokenUsage) -> None: ...
```

---

## Tool Layer

**Agents never access the database directly.** All data access goes through the tool layer:

```
Agent  →  Tool Function  →  Service Layer  →  Repository  →  Database
```

- Each tool function validates its inputs, calls the appropriate service, and returns a structured result.
- Tool functions are defined in `app/agents/tools/` with one module per agent.
- Tool input and output schemas are defined as Pydantic models.

---

## Prompt Management

- All system prompts live in `prompts/` directory as `.txt` or `.jinja2` files.
- Prompts are version-controlled — changes to prompts are reviewed in PRs like code.
- Use Jinja2 templating for dynamic context injection (patient name, vitals, etc.).
- Never hardcode prompts inside agent classes.

---

## Structured Output

All agents return structured output conforming to Pydantic schemas:

- `SymptomAnalysisResult`, `ReportAnalysisResult`, `TriageResult`, etc.
- Use OpenAI's `response_format` (JSON mode) or parse function-call outputs into these schemas.
- Validate output before returning to the user.

---

## Execution Model

- All agent runs execute as **Celery tasks** (async, non-blocking).
- **Timeout:** 5 minutes per agent run. If an agent exceeds this, the task is terminated and the user receives a timeout error.
- The Orchestrator may run multiple agents **in parallel** (e.g., Symptom Analyst + Drug Interaction) using Celery group/chord.
- Track **token usage** per agent run in PostgreSQL (`agent_usage_logs` table): `agent_name`, `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `cost_usd`, `duration_ms`.

---

## Shared Memory

| Layer | Store | TTL | Purpose |
|---|---|---|---|
| Short-term | Redis (`agent_ctx:{session_id}`) | 30 min | Current conversation context, intermediate results |
| Long-term | Pinecone | Persistent | Patient context embeddings (de-identified) for continuity across sessions |

- When a session starts, load relevant long-term context from Pinecone into the agent's system prompt.
- On session end, summarize and embed key findings back to Pinecone.
- Short-term context is evicted automatically by Redis TTL.

---

## HIPAA & Safety

- **De-identify all patient data** before sending to OpenAI APIs. Use the PII redaction layer (see `08-security.md`).
- Agents must not store PHI in logs, error messages, or Celery task results.
- All agent interactions are logged to `audit_logs` for HIPAA compliance.
- The Orchestrator validates that the requesting user has the required role to invoke the agent (e.g., patients cannot invoke the Monitoring Agent directly — only via their own dashboard).
