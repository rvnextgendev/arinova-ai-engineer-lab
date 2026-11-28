"""Local delivery review: prepare workspace, inspect diff, approve exact snapshot."""
import hashlib,json,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
STATE=ROOT/"agent-workspaces"
FILES=("app.py","business.py","arinova_core.py","runtime.py","web_app.py","test_app.py","policies.json","README.md","agent-task.md","manifest.json","reuse-report.json")
def snapshot(path):
    out={}
    for name in FILES:
        p=path/name
        if p.is_symlink(): raise ValueError("Symlink rejected")
        if p.is_file():
            if p.stat().st_size>250000: raise ValueError("File too large")
            out[name]=p.read_text(encoding="utf-8")
    return out
def digest(data): return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def prepare(domain,project,requirement):
    import shutil
    STATE.mkdir(exist_ok=True)
    job=uuid.uuid4().hex
    w=STATE/job;w.mkdir()
    baseline=snapshot(project)
    for name,content in baseline.items(): (w/name).write_text(content,encoding="utf-8")
    (w/"agent-task.md").write_text(requirement,encoding="utf-8")
    meta={"domain":domain,"baseline":snapshot(w),"approved":None}
    (STATE/(job+".json")).write_text(json.dumps(meta),encoding="utf-8")
    return {"job":job,"workspace":str(w),"task":requirement}
def load(job):
    if len(job)!=32 or any(c not in "0123456789abcdef" for c in job): raise ValueError("Invalid job")
    w=STATE/job
    if w.is_symlink(): raise ValueError("Invalid workspace")
    p=STATE/(job+".json")
    return w,p,json.loads(p.read_text(encoding="utf-8"))
def review(job):
    import difflib
    w,p,m=load(job);current=snapshot(w)
    diff="".join("".join(difflib.unified_diff(m["baseline"].get(n,"").splitlines(True),current.get(n,"").splitlines(True),fromfile="before/"+n,tofile="after/"+n)) for n in FILES)
    return {"diff":diff,"digest":digest(current),"workspace":str(w)}
def approve(job,expected):
    w,p,m=load(job)
    if digest(snapshot(w))!=expected: raise ValueError("Workspace changed; review again")
    m["approved"]=expected;p.write_text(json.dumps(m),encoding="utf-8")
    return {"approved":expected}
def deliver(job):
    w,p,m=load(job);current=snapshot(w)
    if not m["approved"] or digest(current)!=m["approved"]: raise ValueError("Review and approve current snapshot first")
    # Local Git artifact repository; never push or modify the factory branch.
    target=STATE/(job+"-delivery")
    target.mkdir()
    def git(*args): return subprocess.run(["git","-C",str(target),*args],check=True,capture_output=True,text=True).stdout.strip()
    git("init","-b","delivery/"+m["domain"]+"-"+job[:8])
    for name,content in current.items(): (target/name).write_text(content,encoding="utf-8")
    git("add","--",*current.keys())
    git("commit","-m","Approved policy assistant delivery")
    return {"branch":git("branch","--show-current"),"commit":git("rev-parse","HEAD"),"repository":str(target),"pushed":False}

def execute_job(job):
    import os
    w,p,m=load(job)
    m["approved"]=None
    p.write_text(json.dumps(m),encoding="utf-8")
    name="arinova-agent-"+job
    cmd=["docker","run","--rm","--name",name,"--cap-drop","ALL","--security-opt","no-new-privileges","--memory","2g","--pids-limit","128","--mount",f"type=bind,source={w.resolve()},target=/workspace","-e","ARINOVA_OPENHANDS_MODEL="+os.getenv("ARINOVA_OPENHANDS_MODEL","ollama_chat/qwen2.5-coder:7b"),"-e","ARINOVA_OPENHANDS_URL="+os.getenv("ARINOVA_OPENHANDS_URL","http://host.docker.internal:11434"),"arinova-openhands-worker"]
    try:
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=900)
        return {"exit_code":result.returncode,"log":(result.stdout+result.stderr)[-24000:],"review":review(job)}
    except subprocess.TimeoutExpired:
        subprocess.run(["docker","rm","-f",name],capture_output=True,timeout=30)
        raise ValueError("OpenHands task timed out")
