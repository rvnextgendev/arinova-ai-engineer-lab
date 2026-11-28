"""Local engineering registry and evidence-based reuse planning."""
import ast
import hashlib
import json
import re
from pathlib import Path

ALLOWED={"app.py","business.py","arinova_core.py","runtime.py","web_app.py","test_app.py","README.md","manifest.json","policies.json","reuse-report.json"}
def words(s):
    return set(re.findall(r"[a-z0-9]+",s.lower()))
def index(project):
    root=Path(project)
    if root.is_symlink() or not root.is_dir(): raise ValueError("Invalid project")
    rows=[]
    for p in sorted(root.iterdir()):
        if p.name not in ALLOWED or p.is_symlink() or not p.is_file() or p.stat().st_size>250000: continue
        raw=p.read_bytes()
        content=raw.decode("utf-8")
        symbols=[]
        if p.suffix==".py":
            symbols=[n.name for n in ast.walk(ast.parse(content)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
        rows.append({"file":p.name,"sha256":hashlib.sha256(raw).hexdigest(),"symbols":symbols,"terms":sorted(words(content))})
    return rows
def plan(project, requirement):
    if not requirement.strip(): raise ValueError("Requirement required")
    rows=index(project)
    q=words(requirement)
    ranked=sorted((dict(file=r["file"],sha256=r["sha256"],symbols=r["symbols"],score=len(q & set(r["terms"]))) for r in rows),key=lambda r:(-r["score"],r["file"]))
    return {"requirement":requirement,"candidates":ranked,"reuse":["arinova_core.py","runtime.py","app.py"],"modify":["policies.json","test_app.py"],"limitations":"Heuristic policy-template plan; engineer must verify compatibility."}
