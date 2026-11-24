# Local Docker + Ollama learning studio

Windows prerequisites: Docker Desktop running in Linux container mode, Ollama installed and running, VS Code Python and Python Debugger extensions. First build and first embedding/reranker use require internet to download dependencies and models. CPU inference may be slow. Use synthetic PDFs only.

Run from repository root:

    powershell -ExecutionPolicy Bypass -File setup.ps1
    powershell -ExecutionPolicy Bypass -File start.ps1

Open http://localhost:8501 and http://localhost:8000/docs. Check Health first. If Ollama is unavailable, ensure its host service accepts Docker connections; on Windows set user environment OLLAMA_HOST=0.0.0.0:11434 and restart Ollama, only on a trusted network with firewall restrictions. Do not expose the service publicly.

Select admin and upload a text PDF. Switch to reader, retrieve evidence and ask a question. The first model downloads can take minutes. Inspect workflow and audit tables. Use docker compose logs -f api to see actual execution. To enable advisory judge set ARINOVA_ENABLE_LLM_JUDGE=1 in .env and recreate API.

VS Code: open repository, choose Attach to Docker API, F5, set breakpoints in backend/main.py and learning/arinova_architect_master_annotated.py. Submit a UI request. F10 steps over, F11 steps in. Restart API after backend changes: docker compose restart api.

Offline checks:

    docker compose run --rm api python learning/arinova_architect_master_annotated.py --tests
    docker compose run --rm api python learning/arinova_architect_master_annotated.py --advanced-tests
    docker compose run --rm api python learning/arinova_architect_master_annotated.py --pipeline-tests

Stop with docker compose down (volumes retained). Do not use down -v unless intentionally deleting database and model cache.

Limitations: local demo identities, no production authentication, no OCR, no atomic multi-worker claim, no integrated MCP execution or LoRA UI, no full node-level trace UI. Approval is a separate example. Debug port is bound to loopback. No cloud deployment. Docker build and real model integration must be validated on your machine.
