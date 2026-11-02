# Enterprise AI Support Engineer — Phase 1

A portfolio project developed incrementally toward a production-grade enterprise support platform using LangGraph + LangChain.

**Current state:** deterministic LangGraph workflow; NOT YET AI-powered or production-ready. The current retrieval node uses a tiny static runbook dictionary. No LLM calls, database, user authentication, or real ticket-system integrations exist yet.

## Features implemented
- Ticket intake and validation through FastAPI
- Stateful LangGraph routing: classify → retrieve → recommend → optional human approval
- Development-only in-memory checkpoints and resumable human interrupt
- Read/approval REST endpoints with validation and a duplicate-approval guard
- Unit/API tests and a single-container Dockerfile

## Requirements
Python 3.12 recommended.

## Local start
```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

## Demo
```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H 'Content-Type: application/json' \
  -d '{"description":"Production API returns HTTP 500 during candidate sync"}'
```
Copy `ticket_id` from the response and approve:
```bash
curl -X POST http://127.0.0.1:8000/tickets/YOUR_TICKET_ID/approval \
  -H 'Content-Type: application/json' -d '{"decision":"approved"}'
```
The approval is only a recommendation status change. There are **no automated remediation actions**.

## Test
```bash
pytest -q
```

## Docker
```bash
docker build -t enterprise-ai-support .
docker run --rm -p 8000:8000 enterprise-ai-support
```

## Next milestones
1. LangChain model integration, Pydantic structured triage output, evaluation set and deterministic fallback.
2. Document ingestion, chunking, embeddings, PostgreSQL/pgvector retrieval with source citations.
3. PostgreSQL checkpointer, durable ticket store, idempotent commands and outbox for external side-effects.
4. OAuth/JWT, RBAC, tenant isolation, encryption, audit trails, prompt-injection defense.
5. Observability, timeouts, retries, DLQ, load/security tests, CI and cloud deployment.

**Production warning:** InMemorySaver loses state on restart and is not safe for concurrent replicated services. `GET /health` is liveness only, not a dependency readiness check. The phase-one app has no authentication and should not be exposed to the public internet.
