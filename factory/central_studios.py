"""Local pilot studios. Production authentication and worker isolation remain required."""
import hashlib,json,subprocess,tempfile,zipfile,uuid
from pathlib import Path
from contextlib import closing
from dataclasses import dataclass
from typing import Callable

def snapshot(root):
    root=Path(root)
    if root.is_symlink() or not root.is_dir():raise ValueError("Invalid workspace")
    files={}
    for p in root.rglob("*"):
        if p.is_symlink():raise ValueError("Symlinks not allowed")
        if any(x in (".git","__pycache__") for x in p.relative_to(root).parts):continue
        if p.is_file():
            if p.name==".env" or p.name.startswith(".env.") or p.suffix.lower() in (".pem",".key",".pfx"):raise ValueError("Potential secret file rejected")
            if p.stat().st_size>2_000_000 or len(files)>=300:raise ValueError("Artifact limit exceeded")
            files[p.relative_to(root).as_posix()]=p.read_bytes()
    return files

def digest(files):
    return hashlib.sha256(json.dumps({k:hashlib.sha256(v).hexdigest() for k,v in files.items()},sort_keys=True).encode()).hexdigest()

def docker_tests(root):
    name="arinova-quality-"+uuid.uuid4().hex
    cmd=["docker","run","--rm","--name",name,"--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges","--memory","512m","--pids-limit","64","--user","65534:65534","--mount",f"type=bind,source={root.resolve()},target=/app,readonly","-w","/app","python:3.11-slim","python","-B","-m","unittest","discover","-v"]
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
        log=(p.stdout+p.stderr)[-24000:]
        import re
        m=re.search(r"Ran (\d+) tests?",log)
        return {"passed":p.returncode==0 and bool(m and int(m[1])>0),"log":log,"exit_code":p.returncode}
    except subprocess.TimeoutExpired:
        subprocess.run(["docker","rm","-f",name],capture_output=True,timeout=30)
        return {"passed":False,"log":"Quality execution timed out"}

@dataclass(frozen=True)
class Studio:
    id:str
    allowed:tuple
    handler:Callable

def develop(ctx):
    import policy_delivery as d
    job=d.prepare(ctx["id"],ctx["root"],ctx["requirement"] or ctx["requirements"])
    # Copy deployment scaffolding before testing and approval, not after.
    import shutil
    for name in ("requirements.md","architecture-plan.json","enterprise_auth.py","customer_api.py","requirements.txt","Dockerfile",".dockerignore","DEPLOYMENT.md"):
        source=ctx["root"]/name
        if source.is_file():shutil.copyfile(source,Path(job["workspace"])/name)
    return "development_prepared",job

def execute(ctx):
    import policy_delivery as d
    result=d.execute_job(ctx["evidence"]["develop"]["job"])
    return ("developed" if result["exit_code"]==0 else "development_prepared"),result

def quality(ctx):
    files=snapshot(ctx["workspace"])
    # Test a frozen copy, never the mutable agent workspace.
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        for name,data in files.items():
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        result=ctx["runner"](root)
    result["digest"]=digest(files)
    result["scope"]="Unit tests only; not enterprise certification"
    return ("quality_passed" if result["passed"] else "quality_failed"),result

def approve(ctx):
    current=digest(snapshot(ctx["workspace"]))
    if current!=ctx["evidence"]["quality"]["digest"] or current!=ctx["expected"]:raise ValueError("Snapshot changed or digest not confirmed; rerun quality")
    return "approved",{"digest":current,"reviewer":ctx["reviewer"]}

def deliver(ctx):
    files=snapshot(ctx["workspace"]);current=digest(files)
    if current!=ctx["evidence"]["approve"]["digest"]:raise ValueError("Approved snapshot changed")
    out=ctx["root"].parent.parent/"factory-state"/"releases";out.mkdir(parents=True,exist_ok=True)
    target=out/(ctx["id"]+"-"+current[:12]+".zip")
    with zipfile.ZipFile(target,"x",zipfile.ZIP_DEFLATED) as z:
        for name,data in files.items():z.writestr("source/"+name,data)
        z.writestr("evidence.json",json.dumps(ctx["evidence"],indent=2))
        z.writestr("requirements.md",ctx["requirements"])
        z.writestr("architecture.json",json.dumps(ctx["plan"],indent=2))
    return "delivered",{"package":str(target),"digest":current,"remote_push":False}

STUDIOS={s.id:s for s in (
    Studio("develop",("generated",),develop),
    Studio("execute",("development_prepared","quality_failed"),execute),
    Studio("quality",("developed","quality_failed","quality_passed","approved"),quality),
    Studio("approve",("quality_passed",),approve),
    Studio("deliver",("approved",),deliver))}
def run(reg,id,action,requirement="",expected="",runner=docker_tests,reviewer="local operator"):
    if action not in STUDIOS:raise ValueError("Unknown studio")
    plugin=STUDIOS[action]
    # Serialize transitions; local pilot only. Long jobs hold a DB write lock.
    with closing(reg.connect()) as c,c:
        c.execute("BEGIN IMMEDIATE")
        c.execute("CREATE TABLE IF NOT EXISTS studio_evidence(project TEXT, action TEXT, data TEXT, PRIMARY KEY(project,action))")
        row=c.execute("SELECT * FROM projects WHERE id=?",(id,)).fetchone()
        if not row or row["stage"] not in plugin.allowed:raise ValueError("Stage prerequisites not met")
        evidence={x[0]:json.loads(x[1]) for x in c.execute("SELECT action,data FROM studio_evidence WHERE project=?",(id,))}
        root=Path(row["artifact"])
        if root.resolve()!= (reg.output/id).resolve():raise ValueError("Invalid project artifact")
        ctx=dict(row);ctx.update(root=root,plan=json.loads(row["plan"]),evidence=evidence,requirement=requirement,expected=expected,runner=runner,reviewer=reviewer)
        if "develop" in evidence:ctx["workspace"]=Path(evidence["develop"]["workspace"])
        stage,result=plugin.handler(ctx)
        if action in ("execute","quality"):c.execute("DELETE FROM studio_evidence WHERE project=? AND action IN ('approve','deliver')",(id,))
        c.execute("INSERT OR REPLACE INTO studio_evidence VALUES(?,?,?)",(id,action,json.dumps(result)))
        c.execute("UPDATE projects SET stage=? WHERE id=?",(stage,id))
        reg.event(c,id,stage,action+" completed")
    return {"project":reg.get(id),"evidence":result}
def evidence(reg,id):
    with closing(reg.connect()) as c:
        c.execute("CREATE TABLE IF NOT EXISTS studio_evidence(project TEXT, action TEXT, data TEXT, PRIMARY KEY(project,action))")
        return {x[0]:json.loads(x[1]) for x in c.execute("SELECT action,data FROM studio_evidence WHERE project=?",(id,))}
