"""AI agent framework — specialized agents coordinated by an orchestrator.

Agents:
    - SymptomAnalystAgent: Symptom analysis with differential diagnosis
    - SpecialtyAgent: Domain-constrained specialist AI doctors (8 specialties)
    - ReportReaderAgent: Medical report analysis and lab value interpretation
    - TriageAgent: Emergency triage and severity classification
    - AgentOrchestrator: Routes requests to the correct specialist agent

Guardrails:
    - Domain boundary enforcement
    - Controlled substance blocking
    - Mandatory disclaimers
    - Confidence thresholds
    - Emergency detection
"""
