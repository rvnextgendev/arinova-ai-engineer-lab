# Architect Labs
Run from repository root after installing factory/requirements-studio.txt.
Set ARINOVA_ENABLE_ARCHITECT_LABS=1, configure ARINOVA_POLICY_DSN and ARINOVA_OLLAMA_URL, then run python factory/policy_studio.py. Open http://127.0.0.1:8790/architect.
Run python -m unittest discover -s factory -p test_architect_labs.py -v.
Exercises: actual service health, local token/latency benchmark, illustrative regex security, two-node LangGraph context selection, Ollama embedding similarity, temporary SQLite backup/restore.
These are introductory exercises, not the full 44-capability roadmap. No Keycloak, LiteLLM, Langfuse, Temporal, Neo4j or Kubernetes integration is added by this change. Use fictional inputs. No production certification or authenticated security boundary. Local integration tests remain required.
