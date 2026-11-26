"""Local learning skill registry. No dynamic code execution or arbitrary SQL."""
from pathlib import Path
from learning import arinova_architect_master_annotated as lab
from learning.telemetry import emit

ROOT = Path(__file__).parent / "skills"
CATALOG = {
    "hr-policy": ("HR Policy", "Grounded policy answers", "How many casual leaves are allowed?", "ask"),
    "automotive-dtc": ("Automotive DTC", "Retrieve diagnostic evidence for review", "Find P0456 diagnostic procedures", "ask"),
    "database-health": ("Database Health", "Read-only tenant-scoped chunk statistics", "Check PostgreSQL", "eval"),
    "retrieval-inspector": ("Retrieval Inspector", "Inspect hybrid search evidence", "How many casual leaves are allowed?", "ask"),
}

def registry():
    return [{"id": key, "name": v[0], "description": v[1], "example": v[2],
             "version": "1.0.0", "instructions": (ROOT / key / "SKILL.md").read_text(encoding="utf-8")}
            for key, v in CATALOG.items()]

def execute(skill_id, question, tenant, actor, request_id=None):
    if skill_id not in CATALOG:
        raise ValueError("Unknown skill")
    lab.authorize(actor, CATALOG[skill_id][3], tenant)
    question = lab.validate_question(question)
    emit("skill_selected", skill=skill_id, version="1.0.0")
    if skill_id == "hr-policy":
        result = lab.ask(question, tenant, actor, request_id)
    elif skill_id == "database-health":
        with lab.db() as conn:
            row = conn.execute("SELECT count(*), count(DISTINCT document_id), min(vector_dims(embedding)) FROM chunks WHERE tenant=%s", (tenant,)).fetchone()
        result = {"chunks": row[0], "documents": row[1], "dimensions": row[2]}
    else:
        result = {"evidence": lab.hybrid_search(question, tenant),
                  "review_required": skill_id == "automotive-dtc"}
    emit("skill_completed", skill=skill_id)
    return {"skill": skill_id, "version": "1.0.0", "result": result}
