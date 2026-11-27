"""Offline educational runtime; no external calls or production guarantees."""
import re
from collections import Counter
from uuid import uuid4

DOCS = {"P0302": "P0302 indicates a cylinder 2 misfire detected.", "P0456": "P0456 indicates a very small evaporative emissions system leak."}
def execute(question, scenario="normal"):
    if scenario not in ("normal", "failure", "quality"):
        raise ValueError("Unknown scenario")
    events = []
    def event(stage, status, detail):
        events.append(dict(stage=stage,status=status,detail=detail))
    result = dict(run_id=str(uuid4()), events=events, answer=None, citations=[], dlq=None)
    if not isinstance(question,str) or not question.strip() or len(question)>2000:
        raise ValueError("Question must contain 1-2000 characters")
    event("input_validation","ok","Length validated; not authentication")
    terms=Counter(re.findall(r"\w+",question.upper()))
    hits=[k for k in DOCS if terms[k]]
    event("retrieval","ok",hits)
    if scenario=="failure":
        for attempt in range(1,4):
            event("retry","failed",f"Injected failure {attempt}")
        event("circuit_breaker","simulated","Threshold reached; no persistent breaker")
        result["dlq"]={"question":question,"reason":"injected failure"}
        event("dlq","simulated","In-memory record only")
        result["status"]="failed"
    elif not hits or scenario=="quality":
        event("evaluation","failed","Missing evidence or injected quality failure")
        event("human_approval","pending","Illustrative review state")
        result["status"]="needs_review"
    else:
        result["answer"]=" ".join(DOCS[k] for k in hits)
        result["citations"]=hits
        event("generation","ok","Deterministic extractive answer; no LLM")
        event("evaluation","ok","Exact fixture evidence available")
        result["status"]="completed"
    event("telemetry","ok","Local event list")
    return result
