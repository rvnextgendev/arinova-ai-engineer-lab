"""Shared, deterministic policy retrieval for the HR-to-IT reuse pilot."""
import re
import json
from pathlib import Path

def tokens(text):
    return set(re.findall(r"[a-z0-9]+", text.lower()))

def execute(question, scenario="normal"):
    if not isinstance(question, str) or not question.strip() or len(question)>2000:
        raise ValueError("Question must contain 1-2000 characters")
    if scenario != "normal":
        raise ValueError("Policy pilot supports normal scenario only")
    docs=json.loads(Path(__file__).with_name("policies.json").read_text(encoding="utf-8"))
    return evaluate(question,docs)

def evaluate(question,docs):
    if not isinstance(question,str) or not question.strip() or len(question)>2000:raise ValueError("Question must contain 1-2000 characters")
    events=[{"stage":"input_validation","status":"ok"}]
    q=tokens(question)
    ranked=sorted(((len(q & tokens(d["keywords"])),d["id"],d) for d in docs),key=lambda x:(-x[0],x[1]))
    events.append({"stage":"policy_retrieval","status":"ok"})
    if not ranked or ranked[0][0]==0 or (len(ranked)>1 and ranked[0][0]==ranked[1][0]):
        return {"status":"needs_review","answer":"No unambiguous matching policy found.","citations":[],"events":events,"evaluation":"not matched"}
    d=ranked[0][2]
    events.append({"stage":"source_selection","status":"ok"})
    approval=bool(q & {"approve","authorize","exception","bypass"})
    if approval:
        events.append({"stage":"human_review","status":"pending"})
    return {"status":"needs_review" if approval else "completed","answer":d["text"]+(" Human authorization is required; no action was taken." if approval else ""),"citations":[d["id"]],"events":events,"evaluation":"source excerpt only"}
