# Dual engine source review
Base commit dd3083db2997367435c8ba1d86198329d1449fe4.
Existing adapter, UI comparison and feature flag were present before this review.

## Source map
- backend/deep_agent_engine.py: optional Deep Agents adapter, role-filtered skill allowlist, six business calls, recursion limit 25, state backend, timing and telemetry.
- backend/skill_engine.py: shared registry, routing, permission checks, RAG and DTC handlers.
- backend/main.py: API and persisted request telemetry.
- backend/studio.html: engine selection and sequential comparison.
- tests/test_deep_agent.py: disabled-default and fail-closed checks.

## Run
Set DEEP_AGENT_ENABLED=true and DEEP_AGENT_MODEL to an installed tool-capable Ollama model in .env. Rebuild with docker compose up -d --build. Open http://localhost:8000/studio. Run python -m pytest tests/test_deep_agent.py tests/test_skill_v2.py inside API container.

## Boundaries
Static review only; dependency compatibility and runtime not verified. StateBackend is not a production sandbox. Built-in agent tools and subagents require independent policy review. Six business calls and recursion limit are not a hard wall-clock deadline or token budget. Deep outputs remain unverified and require review. Comparison is sequential latency, not a controlled accuracy benchmark. Demo identities are not production authentication. Full DTC boundaries, HDS business rules, cancellation and durable deep-agent recovery remain pending.
