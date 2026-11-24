# AriNova AI Engineer Lab

**Build It. Break It. Observe It. Fix It. Scale It.**

A hands-on personal learning reference for AI engineering and AI architecture, grounded in one Python pipeline. This branch holds the complete annotated code and the 48-page offline guide.

## Open the learning materials

- **[Read the PDF handbook in GitHub](docs/AriNova_AI_Architect_Offline_Handbook.pdf)**
- **[Open the complete annotated Python source](learning/arinova_architect_master_annotated.py)**
- **[30-day personal learning roadmap](LEARNING_ROADMAP.md)**
- **[Guide to the PDF edition](docs/README.md)**

### What you will learn

Python and CLI, PDF ingestion, chunking, embeddings, PostgreSQL/pgvector, hybrid search, RRF, reranking, Ollama, grounded answers, LangGraph, JWT/OIDC, RBAC/RLS, prompt-injection guardrails, evaluation, LLM-as-judge, tracing, retries, circuit breakers, idempotency, checkpoints, cancellation, dead-letter queues, MCP, human approval, feedback, fine-tuning, testing, and Azure architecture mapping.

## Run offline test suites

```bash
python learning/arinova_architect_master_annotated.py --tests
python learning/arinova_architect_master_annotated.py --advanced-tests
python learning/arinova_architect_master_annotated.py --pipeline-tests
```

At upload, **19 tests passed** (9 basic, 3 advanced, 7 unified-pipeline); these are offline checks, **not full integration or production acceptance tests**.

## Optional local integration environment

```bash
pip install "psycopg[binary]" pgvector sentence-transformers pypdf langgraph
docker run --name arinova-pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=arinova -p 5432:5432 -d pgvector/pgvector:pg17
ollama pull llama3.2
python learning/arinova_architect_master_annotated.py --init
python learning/arinova_architect_master_annotated.py --ingest policy.pdf --tenant acme --actor admin
python learning/arinova_architect_master_annotated.py --ask "What does the policy say?" --tenant acme --actor reader
```

**Important:** The development database password and demo identities above are for local learning only. Do not use production credentials or confidential documents; production authentication must be independently configured.

## Implementation boundaries

This repository provides a learning/reference pipeline, **not a production-certified AI platform**. Several components are optional demonstrations, not all integrated into the central execution path. Cloud deployment, OCR/layout-aware parsing, robust distributed recovery, atomic multi-worker idempotency, model-cost accounting, real end-to-end integration testing, CI/CD, managed secrets, and operational SLOs still require implementation and verification.

The PDF in this branch is a **searchable, text-reflowed reproduction** of the 48-page original offline handbook. It contains the extracted written material and source code but not all original visual typography/layout. Refer to the separate Python file for exact source.

See [Learning Roadmap](LEARNING_ROADMAP.md) for a day-by-day study plan.

## Local interactive Debug Studio

See [Docker + Ollama setup and VS Code debugging](LOCAL_DEBUG.md). Run `setup.ps1` then `start.ps1` on Windows. UI: http://localhost:8501. Local-only demo; integration testing pending.
