"""Local-only learning API. Demo identities are not authentication."""
import os
import tempfile
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from learning import arinova_architect_master_annotated as lab
from urllib.request import urlopen

@asynccontextmanager
async def lifespan(app):
    lab.initialize()
    if os.getenv("ARINOVA_LANGGRAPH_POSTGRES") == "1":
        lab.initialize_langgraph_checkpointer()
    with lab.db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS local_telemetry (id BIGSERIAL PRIMARY KEY, payload JSONB NOT NULL)")
    yield

app = FastAPI(title="AriNova Local Debug Studio", lifespan=lifespan)

class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1200)
    tenant: str = "acme"
    actor: str = "reader"
    request_id: str | None = None

class Feedback(Question):
    answer: str
    rating: int = Field(ge=1, le=5)

def run(fn, *args):
    try:
        return fn(*args)
    except lab.CircuitOpen as exc:
        raise HTTPException(503, 'Model circuit open; wait for recovery before retrying') from exc
    except TimeoutError as exc:
        logging.exception('Local model timed out')
        raise HTTPException(504, 'Local model timed out; check Ollama and ARINOVA_LLM_TIMEOUT_SECONDS') from exc
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        logging.exception("Local lab operation failed")
        raise HTTPException(500, type(exc).__name__ + ": " + str(exc)) from exc

@app.get("/health")
def health():
    status = {"api": "ok", "database": "unknown", "ollama": "unknown"}
    try:
        with lab.db() as conn:
            conn.execute("SELECT 1")
        status["database"] = "ok"
    except Exception:
        status["database"] = "unavailable"
    try:
        with urlopen(lab.C.ollama_url.rsplit("/api/", 1)[0] + "/api/tags", timeout=3) as response:
            import json
            status["models"] = [m["name"] for m in json.load(response)["models"]]
        status["ollama"] = "ok"
    except Exception:
        status["ollama"] = "unavailable"
    return status

@app.post("/ingest")
def ingest(file: UploadFile = File(...), tenant: str = Form("acme"), actor: str = Form("admin")):
    run(lab.authorize, actor, "ingest", tenant)
    data = file.file.read(15_000_001)
    if len(data) > 15_000_000 or not data.startswith(b"%PDF-"):
        raise HTTPException(400, "Valid PDF up to 15 MB required")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "upload.pdf"
        path.write_bytes(data)
        pages = run(lambda: list(lab.extract_pdf(str(path))))
        preview = [{"page": p, "chunks": lab.chunks(t, lab.C.chunk_chars, lab.C.overlap_chars)} for p,t in pages]
        started = time.perf_counter()
        run(lab.ingest, str(path), tenant, actor)
        return {"pages": len(pages), "chunk_count": sum(len(p["chunks"]) for p in preview),
                "preview": preview[:5], "seconds": time.perf_counter()-started}

@app.post("/ask")
def ask(q: Question):
    return run(lab.ask, q.question, q.tenant, q.actor, q.request_id)

@app.post("/retrieve")
def retrieve(q: Question):
    run(lab.authorize, q.actor, "ask", q.tenant)
    return run(lab.hybrid_search, run(lab.validate_question, q.question), q.tenant)

@app.post("/embedding")
def embedding(q: Question):
    run(lab.authorize, q.actor, "ask", q.tenant)
    vector = run(lab.embed, [q.question])[0]
    return {"dimensions": len(vector), "vector": vector}

@app.post("/security")
def security(q: Question):
    run(lab.authorize, q.actor, "ask", q.tenant)
    return {"suspicious": lab.suspicious(q.question), "redacted": lab.redact(q.question)}

@app.post("/evaluate")
def evaluate(q: Question):
    return run(lab.evaluate, q.tenant, q.actor)

@app.post("/feedback")
def feedback(q: Feedback):
    run(lab.record_feedback, q.tenant, q.actor, q.question, q.answer, q.rating)
    return {"saved": True}

@app.get("/inspect/{table}")
def inspect(table: str, tenant: str = "acme"):
    run(lab.authorize, "admin", "eval", tenant)
    queries = {
        "workflows": "SELECT id,status,state,updated_at FROM workflows WHERE tenant=%s ORDER BY updated_at DESC LIMIT 30",
        "audit": "SELECT action,detail,created_at FROM audit WHERE tenant=%s ORDER BY id DESC LIMIT 30",
        "dlq": "SELECT id,reason,status,attempts FROM dlq WHERE tenant=%s LIMIT 30",
        "chunks": "SELECT document_id,page,content FROM chunks WHERE tenant=%s LIMIT 30"
    }
    if table not in queries:
        raise HTTPException(404, "Unknown table")
    with lab.db() as conn:
        from psycopg.rows import dict_row
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(queries[table], (tenant,))
            return cursor.fetchall()

@app.post("/workflow/{action}/{item_id}")
def workflow(action: str, item_id: str, tenant: str = "acme"):
    functions = {"cancel": lab.cancel_workflow, "replay": lab.replay_dlq,
                 "request_approval": lab.request_approval, "approve": lab.approve}
    if action not in functions:
        raise HTTPException(404, "Unknown action")
    return run(functions[action], item_id, tenant, "admin")


# Additional learning endpoints. Local demo only.
from learning import telemetry
from fastapi import Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import threading
from collections import deque
import uuid
history = deque(maxlen=200)
history_lock = threading.Lock()
requests_total = Counter("arinova_requests_total","HTTP requests",["route","status"])
latency = Histogram("arinova_request_seconds","HTTP latency",["route"])

@app.middleware("http")
async def monitor(request: Request, call_next):
    start = time.perf_counter()
    events = []
    token = telemetry.events.set(events)
    trace = uuid.uuid4().hex
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Trace-ID"] = trace
        return response
    finally:
        telemetry.events.reset(token)
        route = getattr(request.scope.get("route"),"path","unknown")
        elapsed = time.perf_counter()-start
        requests_total.labels(route,str(status)).inc()
        latency.labels(route).observe(elapsed)
        if route in ("/ask","/retrieve","/ingest","/judge","/embedding","/evaluate","/skills/{skill_id}/execute","/deep-agent/{skill_id}/execute","/skills/{skill_id}/evaluate"):
            with history_lock:
                record = {"trace_id":trace,"route":route,"status":status,
                          "milliseconds":round(elapsed*1000,2),"events":events}
                history.append(record)
            try:
                from starlette.concurrency import run_in_threadpool
                def persist():
                    from psycopg.types.json import Jsonb
                    with lab.db() as conn:
                        conn.execute("INSERT INTO local_telemetry(payload) VALUES (%s)", (Jsonb(record),))
                await run_in_threadpool(persist)
            except Exception:
                logging.exception("Telemetry persistence failed")

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/telemetry")
def traces():
    with lab.db() as conn:
        return [r[0] for r in reversed(conn.execute("SELECT payload FROM local_telemetry ORDER BY id DESC LIMIT 200").fetchall())]

class Judge(Question):
    evidence: str = Field(max_length=12000)
    answer: str = Field(max_length=4000)

@app.post("/judge")
def judge(q: Judge):
    run(lab.authorize,q.actor,"ask",q.tenant)
    return run(lab.llm_judge,q.question,q.evidence,q.answer)

@app.post("/prompt")
def prompt(q: Question):
    run(lab.authorize,q.actor,"ask",q.tenant)
    docs = run(lab.hybrid_search,q.question,q.tenant)
    return {"prompt":lab.make_prompt(q.question,docs),"evidence":docs}

class ChunkInput(BaseModel):
    text: str = Field(max_length=20000)
    size: int = Field(default=1100,ge=50,le=3000)
    overlap: int = Field(default=180,ge=0,le=2999)

@app.post("/chunk")
def chunk(q: ChunkInput):
    return run(lab.chunks,q.text,q.size,q.overlap)

@app.get("/circuit")
def circuit():
    return {"failures":lab.BREAKER.failures,"opened_at_monotonic":lab.BREAKER.opened_at,
            "reset_seconds":lab.BREAKER.reset_seconds}

@app.get("/mcp/tools")
def mcp_tools():
    return run(lab.mcp_list_tools)

@app.get("/training/candidates")
def candidates(tenant: str="acme"):
    return run(lab.export_finetune_candidates,tenant,"admin")

# Local skill studio: reviewed, explicitly registered handlers only.
from backend.skill_engine import registry, execute
from fastapi.responses import FileResponse

@app.get("/studio")
def studio():
    return FileResponse(Path(__file__).parent / "studio.html")

@app.get("/skills")
def skills():
    return registry()

@app.post("/skills/{skill_id}/execute")
def execute_skill(skill_id: str, q: Question):
    return run(execute, skill_id, q.question, q.tenant, q.actor, q.request_id)

from backend.skill_engine import route, evaluate_skill

@app.post("/skills/route")
def route_skill(q: Question):
    run(lab.authorize,q.actor,"ask",q.tenant)
    return {"skill":run(route,q.question)}

@app.post("/skills/{skill_id}/evaluate")
def skill_evaluation(skill_id: str, q: Judge):
    return run(evaluate_skill,skill_id,q.question,q.evidence,q.answer,q.tenant,q.actor)

from backend.deep_agent_engine import enabled, execute_deep

@app.get("/deep-agent/status")
def deep_agent_status():
    return {"enabled": enabled()}

@app.post("/deep-agent/{skill_id}/execute")
def deep_agent_execute(skill_id: str, q: Question):
    return run(execute_deep, q.question, q.tenant, q.actor, skill_id)
