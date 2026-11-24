# AriNova — 30-Day Personal AI Architect Learning Roadmap

Use the code beside the PDF every day. For each topic answer: **What / Why / How / Failure mode / How to verify?** Run tests when changing the code.

| Day | Topic | Practical exercise |
|---|---|---|
| 1 | Python project and CLI | Trace `main()` and each flag |
| 2 | Configuration and environment | Override model and database settings |
| 3 | Database schema | Sketch chunks, workflows, audit, DLQ tables |
| 4 | Indexes and transactions | Explain tenant, GIN and HNSW indexes |
| 5 | PDF extraction | Inspect page and text handling |
| 6 | Chunking and ingestion | Vary chunk size and overlap |
| 7 | Embeddings | Trace vector generation |
| 8 | Semantic similarity | Compare two query vectors conceptually |
| 9 | Hybrid retrieval | Contrast keyword and vector results |
| 10 | RRF and reranking | Calculate a sample RRF score |
| 11 | Ollama API | Read LLM request/response flow |
| 12 | Grounded prompts | Verify citations vs evidence |
| 13 | LangGraph state | Draw state transitions |
| 14 | LangGraph failures | Trace validate/evaluate path |
| 15 | JWT, OIDC and RBAC | Identify identity and role checks |
| 16 | Tenant isolation/RLS | Explain cross-tenant protection |
| 17 | Input/answer guardrails | Execute injection and redaction tests |
| 18 | Retrieval evaluation | Calculate hit rate / precision / recall |
| 19 | Judge and quality gates | Contrast deterministic vs LLM judgement |
| 20 | OpenTelemetry | Trace a request ID across components |
| 21 | Retry and backoff | Design transient-failure recovery |
| 22 | Circuit breaker | Trigger circuit-open example |
| 23 | Idempotency/checkpoints | Explain safe re-execution |
| 24 | Cancellation, DLQ and replay | Describe operational recovery |
| 25 | MCP | Identify allowed/disallowed tool actions |
| 26 | Human approval and feedback | Trace a review decision |
| 27 | LoRA and fine-tuning | Identify candidate data requirements |
| 28 | Azure architecture | Map components to Azure services |
| 29 | Unified pipeline | Debug request from start to end |
| 30 | Architecture review | Explain gaps, trade-offs and next steps |

## Self-assessment after each module

1. Explain the concept in plain English.
2. Identify the exact source function.
3. Sketch the data/control flow.
4. Describe a realistic failure and control.
5. Execute a focused test or give a verifiable test plan.

## Interview-ready mnemonic

**Chunking divides; embeddings represent meaning; hybrid retrieval combines signals; LangGraph orchestrates; security authorizes; evaluation measures; observability explains; reliability recovers.**
