# AriNova AI Engineer Lab

Practical, code-first learning in AI engineering and architecture: document ingestion, RAG, LangGraph, security, evaluation, observability, reliability, and deployment patterns.

## Architect learning handbook

The annotated source and 48-page offline PDF handbook are maintained on the `feature/architect-master-learning-guide` branch. They are **learning references and not production-ready deployments**.

- [Complete annotated Python learning source](../../tree/feature/architect-master-learning-guide/learning)
- [Offline PDF AI Architect handbook](../../tree/feature/architect-master-learning-guide/docs)
- [Learning roadmap](../../tree/feature/architect-master-learning-guide)

## Learning approach

**Build It → Break It → Observe It → Fix It → Scale It.**

Learn the reasoning behind each architectural choice, run offline tests before connecting services, and distinguish illustrative components from production-hardened implementations.

## Security

Do not commit credentials, personal documents, API tokens, or production datasets. Use environment variables and secret managers. The included code may use demo identities and development connection defaults; review before use outside a local learning environment.
