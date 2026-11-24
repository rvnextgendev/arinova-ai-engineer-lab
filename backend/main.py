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
        preview = [{"page": p, "chunks": lab.chunks(t, lab.C.chunk_chars, lab.C.overlap)} for p,t in pages]
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
