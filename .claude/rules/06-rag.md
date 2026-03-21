# RAG Pipeline Rules — MedAssist AI

MedAssist AI uses a **Retrieval-Augmented Generation** pipeline to ground every clinical response in verified medical knowledge. Hallucination in a medical context is a patient-safety issue — treat it as a severity-1 bug.

---

## Architecture Overview

The pipeline has two phases:

### 1. Ingestion Pipeline

```
Medical Literature / Drug DB / Clinical Guidelines
        │
        ▼
    Parse (PDF, HTML, structured data)
        │
        ▼
    Chunk (deterministic, section-aware)
        │
        ▼
    Embed (OpenAI text-embedding-3-large, 3072 dims)
        │
        ▼
    Index (Pinecone — single namespace, no org scoping)
```

### 2. Retrieval Pipeline

```
User Query / Agent Request
        │
        ▼
    Embed query (text-embedding-3-large)
        │
        ▼
    Hybrid Search (Pinecone vector + Elasticsearch BM25)
        │
        ▼
    Rerank (cross-encoder or reciprocal rank fusion)
        │
        ▼
    Assemble Context (top-k chunks + metadata)
        │
        ▼
    Generate (GPT-4o with grounded system prompt)
```

---

## Embedding Model

- **Model:** `text-embedding-3-large` (3072 dimensions).
- **Do not** switch models without re-indexing the entire corpus — mixed embedding spaces produce garbage results.
- Batch embed during ingestion (max 2048 tokens per chunk input).

---

## Chunking Strategy

Medical documents require **deterministic, section-aware chunking** — not naive fixed-length splits.

| Rule | Detail |
|---|---|
| Chunk size | 512 tokens (target), 768 tokens (hard max) |
| Overlap | 64 tokens between consecutive chunks |
| Boundaries | Prefer section headers, paragraph breaks, list boundaries. Never split mid-sentence. |
| Tables / figures | Keep as a single chunk if under max; otherwise attach a summary chunk. |
| Reproducibility | Given the same input document and version, chunking must produce identical chunks every time. |

### Chunk Metadata (required fields)

Every vector stored in Pinecone must carry this metadata:

```json
{
  "source": "UpToDate — Acute Coronary Syndromes",
  "source_url": "https://...",
  "document_type": "clinical_guidelines",
  "chunk_index": 14,
  "page_number": 7,
  "last_updated": "2025-11-01",
  "icd10_codes": ["I21.0", "I21.9"],
  "loinc_codes": ["2157-6"],
  "content_hash": "sha256:abc123..."
}
```

Valid `document_type` values: `medical_literature`, `drug_database`, `clinical_guidelines`, `patient_education`, `formulary`.

---

## Hybrid Search

Use **both** Pinecone (semantic) and **Elasticsearch** (BM25 keyword) for retrieval, then fuse results.

1. **Pinecone query** — top 20 nearest neighbors by cosine similarity.
2. **Elasticsearch query** — BM25 over the same corpus, top 20.
3. **Reciprocal Rank Fusion (RRF)** — merge the two ranked lists: `score = sum(1 / (k + rank))` with `k = 60`.
4. Take the top 5-8 fused results as context for generation.

- Elasticsearch index mirrors Pinecone metadata and stores the raw chunk text for BM25 scoring.
- For drug-name or ICD-10 code lookups, boost the BM25 path (exact-match matters more than semantic similarity).

---

## Source Attribution

**Every AI-generated clinical response must cite its sources.**

- Include source name, document type, and page/section in the response.
- Format: `[Source: {source}, p.{page_number}]` inline or as footnotes.
- If the retrieval pipeline returns zero relevant chunks above the similarity threshold (0.75), the agent must respond with: _"I don't have enough verified information to answer this question. Please consult a healthcare provider."_
- Never generate a medical claim that is not grounded in a retrieved chunk.

---

## Grounding & Safety

- System prompts for all clinical agents must include: _"Only use information from the provided context. If the context does not contain sufficient information, say so explicitly. Do not speculate."_
- Log every retrieval: query text (de-identified), chunk IDs returned, similarity scores, final response. This enables auditing.
- Set a **confidence threshold** (cosine similarity >= 0.75). Chunks below this are discarded before context assembly.

---

## Patient Data & De-identification

- **Never embed patient-identifiable data** (names, MRNs, SSNs, dates of birth) into Pinecone.
- Patient context (history, vitals) is passed at query time via the prompt — not stored in the vector DB.
- Before sending any patient data to OpenAI for generation, run it through the PII redaction layer (see `08-security.md`).
- This is a single-tenant system — no `organization_id` scoping is needed in Pinecone namespaces or Elasticsearch indices.

---

## Medical Code Support

The pipeline must handle structured medical codes:

| Code System | Usage |
|---|---|
| **ICD-10** | Diagnosis codes — stored as chunk metadata, searchable via Elasticsearch |
| **LOINC** | Lab/observation codes — attached to lab-report chunks |
| **RxNorm / NDC** | Drug identifiers — used by Drug Interaction Agent |
| **SNOMED CT** | Clinical terms — used for semantic normalization during chunking |

When a user query contains a code (e.g., "ICD-10 I21.0"), prefer exact-match Elasticsearch lookup over semantic search.

---

## Ingestion Pipeline Operations

- Ingestion runs as a **Celery task** (not in the request path).
- De-duplicate by `content_hash` before upserting to Pinecone.
- Track ingestion runs in PostgreSQL (`ingestion_logs` table) with: document source, chunk count, timestamp, status.
- Schedule periodic re-ingestion for sources that update (e.g., drug databases quarterly).
