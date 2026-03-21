"""Medical knowledge base tool — RAG retrieval over medical literature.

Queries Pinecone (vector) and Elasticsearch (BM25) to retrieve relevant
medical knowledge for grounding agent responses. Currently a stub that
returns mock results; will be connected to the real RAG pipeline once
the Pinecone and Elasticsearch integrations are wired.

See .claude/rules/06-rag.md for the full RAG pipeline specification.
"""

import structlog

logger = structlog.get_logger(__name__)


# OpenAI function-calling tool definition
SEARCH_MEDICAL_KB_TOOL = {
    "type": "function",
    "function": {
        "name": "search_medical_kb",
        "description": (
            "Search the medical knowledge base for clinical information relevant "
            "to the query. Returns source-cited medical facts from clinical guidelines, "
            "drug databases, and peer-reviewed literature. Use this when you need "
            "to ground your response in verified medical knowledge."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language medical query to search for",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5, max: 10)",
                    "default": 5,
                },
                "document_type": {
                    "type": "string",
                    "enum": [
                        "clinical_guidelines",
                        "drug_database",
                        "medical_literature",
                        "patient_education",
                        "all",
                    ],
                    "description": "Filter by document type. Use 'all' for broad searches.",
                    "default": "all",
                },
            },
            "required": ["query"],
        },
    },
}

QUERY_PATIENT_HISTORY_TOOL = {
    "type": "function",
    "function": {
        "name": "query_patient_history",
        "description": (
            "Retrieve a patient's medical history including past diagnoses, "
            "active conditions, allergies, and current medications. Use this "
            "to consider the patient's full clinical context when analyzing symptoms."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "UUID of the patient whose history to retrieve",
                },
                "include_allergies": {
                    "type": "boolean",
                    "description": "Whether to include allergy records",
                    "default": True,
                },
                "include_medications": {
                    "type": "boolean",
                    "description": "Whether to include current medications",
                    "default": True,
                },
            },
            "required": ["patient_id"],
        },
    },
}


def search_medical_kb(
    query: str,
    max_results: int = 5,
    document_type: str = "all",
) -> dict:
    """Search the medical knowledge base for relevant clinical information.

    This is a stub implementation returning mock results. The real implementation
    will query Pinecone for semantic search and Elasticsearch for BM25 keyword
    search, then fuse results via Reciprocal Rank Fusion (RRF).

    Args:
        query: Natural language medical query.
        max_results: Maximum results to return.
        document_type: Filter by document category.

    Returns:
        Dict with 'results' list containing source-cited medical knowledge.
    """
    logger.info(
        "search_medical_kb",
        query=query,
        max_results=max_results,
        document_type=document_type,
    )

    # Stub: return mock results for development and testing
    mock_results = [
        {
            "content": (
                "Headaches can be classified as primary (tension-type, migraine, "
                "cluster) or secondary (caused by underlying conditions). Red flags "
                "include sudden severe onset ('thunderclap'), neurological deficits, "
                "fever with neck stiffness, or headache after trauma."
            ),
            "source": "Clinical Guidelines — Headache Classification (IHS)",
            "document_type": "clinical_guidelines",
            "page_number": 12,
            "relevance_score": 0.92,
        },
        {
            "content": (
                "Common causes of chest pain include musculoskeletal strain, "
                "gastroesophageal reflux, anxiety, and cardiac ischemia. Cardiac "
                "causes must be ruled out first. Key differentiators include pain "
                "quality, duration, radiation, and associated symptoms."
            ),
            "source": "Emergency Medicine Guidelines — Chest Pain Evaluation",
            "document_type": "clinical_guidelines",
            "page_number": 45,
            "relevance_score": 0.88,
        },
        {
            "content": (
                "Fever in adults is defined as a body temperature of 100.4F (38C) "
                "or higher. Common causes include infections (viral, bacterial), "
                "inflammatory conditions, and medication reactions. Fever above "
                "103F (39.4C) warrants medical evaluation."
            ),
            "source": "Internal Medicine Reference — Fever Evaluation",
            "document_type": "medical_literature",
            "page_number": 8,
            "relevance_score": 0.85,
        },
    ]

    return {
        "results": mock_results[:max_results],
        "total_found": len(mock_results),
        "query": query,
    }


def query_patient_history(
    patient_id: str,
    include_allergies: bool = True,
    include_medications: bool = True,
) -> dict:
    """Retrieve a patient's medical history.

    This is a stub implementation returning mock data. The real implementation
    will query the patient service layer to fetch from PostgreSQL.

    Args:
        patient_id: UUID of the patient.
        include_allergies: Whether to include allergies.
        include_medications: Whether to include current medications.

    Returns:
        Dict with patient history, allergies, and medications.
    """
    logger.info(
        "query_patient_history",
        patient_id=patient_id,
        include_allergies=include_allergies,
        include_medications=include_medications,
    )

    # Stub: return mock patient history
    result: dict = {
        "patient_id": patient_id,
        "conditions": [
            {
                "name": "Hypertension",
                "status": "active",
                "diagnosed_date": "2023-06-15",
                "icd10": "I10",
            },
        ],
    }

    if include_allergies:
        result["allergies"] = [
            {
                "allergen": "Penicillin",
                "reaction": "Rash",
                "severity": "moderate",
            },
        ]

    if include_medications:
        result["medications"] = [
            {
                "name": "Lisinopril",
                "dosage": "10mg",
                "frequency": "Once daily",
                "status": "active",
            },
        ]

    return result
