# Settings README — MedAssist AI Claude Configuration

This document describes the `.claude/rules/` directory structure and how it maps to the MedAssist AI project. It is intended for developers onboarding to the project or modifying the AI assistant configuration.

---

## 1. Overview

The `.claude/rules/` directory contains rule files that configure Claude's behavior when working on MedAssist AI. Each file focuses on a specific domain and provides context, conventions, and constraints that Claude follows during code generation, review, and assistance.

The `CLAUDE.md` at the project root is the **master PRD** and must not be modified directly. These rule files extract and operationalize specific aspects of that PRD.

---

## 2. Rule Files

| File | Domain | MedAssist-Specific? |
|------|--------|---------------------|
| `00-index.md` | Master index of all rules, project overview, and cross-references | Yes |
| `01-architecture.md` | System architecture, layer hierarchy, agent definitions, component boundaries | Yes |
| `05-caching.md` | Redis caching strategy, cache keys, TTLs, invalidation patterns | Mostly generic, some MedAssist-specific cache patterns |
| `06-rag.md` | RAG pipeline, Pinecone configuration, embedding strategy, medical knowledge base | Yes |
| `10-ops.md` | DevOps, Docker, Kubernetes, CI/CD, monitoring, deployment procedures | Mixed (generic patterns, MedAssist-specific service list) |
| `11-response-style.md` | Claude response formatting, coding conventions, output style | Generic |
| `12-voice.md` | Voice agent, Whisper/TTS integration, audio streaming, ambient notes | Yes |
| `17-admin-dashboard.md` | Admin panel features, user management, audit logs, system health | Yes |
| `18-prompt-persistence.md` | Prompt history tracking, session context management | Generic |

---

## 3. MedAssist-Specific vs Generic Rules

### MedAssist-Specific
These rules contain domain knowledge, schema references, agent definitions, or medical-specific logic that would not apply to other projects:
- `00-index.md` -- Project overview and cross-references
- `01-architecture.md` -- 7 AI agents, orchestrator, 4-layer architecture
- `06-rag.md` -- Medical knowledge base, Pinecone namespaces, clinical embeddings
- `12-voice.md` -- Medical voice assistant, ambient clinical notes, SOAP format
- `17-admin-dashboard.md` -- HIPAA audit, AI agent config, medical platform admin

### Generic / Reusable
These rules contain patterns that could transfer to other projects with minor adjustments:
- `05-caching.md` -- Redis caching patterns (adjust cache keys and TTLs)
- `10-ops.md` -- Docker/K8s/CI-CD patterns (adjust service names)
- `11-response-style.md` -- Coding conventions and response formatting
- `18-prompt-persistence.md` -- Prompt history management

---

## 4. How to Modify Rules When Tech Changes

### If the LLM provider changes (e.g., OpenAI to Anthropic)
- Update `01-architecture.md`: Agent model references
- Update `06-rag.md`: Embedding model and dimension
- Update `12-voice.md`: STT/TTS API references

### If a database changes (e.g., Pinecone to pgvector)
- Update `06-rag.md`: Vector store configuration, query patterns
- Update `01-architecture.md`: Data layer description

### If the frontend framework changes
- Update `01-architecture.md`: Client layer description
- Update `11-response-style.md`: Frontend coding conventions

### If new AI agents are added
- Update `01-architecture.md`: Add agent definition
- Update `00-index.md`: Update agent count and cross-references
- Consider creating a new rule file if the agent has complex domain-specific logic

### If infrastructure changes (e.g., EKS to GKE)
- Update `10-ops.md`: Deployment targets, cloud service references

---

## 5. Onboarding Checklist for New Developers

- [ ] Read `CLAUDE.md` (project root) -- this is the master PRD and the single source of truth
- [ ] Read `00-index.md` in `.claude/rules/` -- understand the rule structure and cross-references
- [ ] Read `01-architecture.md` -- understand the 4-layer architecture, 7 AI agents, and orchestrator pattern
- [ ] Review `docs/PRD.md` -- product requirements, features, user roles
- [ ] Review `docs/ARCHITECTURE.md` -- detailed architecture with data flow diagrams
- [ ] Review `docs/DB_SCHEMA.md` -- database tables, relationships, index strategy
- [ ] Review `docs/API_SPEC.md` -- all API endpoints, WebSocket events, auth patterns
- [ ] Review `docs/DEPLOYMENT.md` -- local setup, Docker, CI/CD, environment variables
- [ ] Set up local development environment (see `docs/DEPLOYMENT.md` section 1)
- [ ] Verify you have API keys for: OpenAI, Pinecone, Daily.co (request from project lead if needed)
- [ ] Run the test suite: `pytest` (backend) and `npm run test` (frontend)
- [ ] Review `CONTRIBUTING.md` for branch naming, commit conventions, and PR requirements

---

## 6. File Naming Convention

Rule files use a numeric prefix for ordering:
- `00-09`: Core project context (index, architecture)
- `05-09`: Data layer rules (caching, RAG, databases)
- `10-19`: Operations and style (ops, response style, voice, admin)
- `17-19`: Feature-specific rules

When adding new rules, choose a number that places the file near related topics. Update `00-index.md` to reference the new file.
