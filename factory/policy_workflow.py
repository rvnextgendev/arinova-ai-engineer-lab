"""Local staged policy factory. Explicit approvals; manual OpenHands handoff."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from engineering_registry import plan
from policy_pilot import build

ROOT=Path(__file__).resolve().parent.parent
def main():
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["plan","prepare","review","delivery"])
    p.add_argument("--requirement",default="Add IT security incident policy and tests")
    p.add_argument("--approve",action="store_true")
    p.add_argument("--workspace")
    a=p.parse_args()
    target=ROOT/"generated"/"it-policy-assistant"
    if a.action=="plan":
        if not target.exists(): build("it",ROOT/"generated")
        print(json.dumps(plan(target,a.requirement),indent=2))
    elif a.action=="prepare":
        if not a.approve: p.error("Review plan first; explicit --approve required")
        subprocess.run(["powershell.exe","-ExecutionPolicy","Bypass","-File",str(ROOT/"factory/start-openhands.ps1"),"-Project","it-policy-assistant","-PrepareOnly"],check=True)
        print("Submit agent-task.md manually to OpenHands. No API call was made.")
    else:
        if not a.workspace: p.error("--workspace required")
        base=(ROOT/"agent-workspaces").resolve()
        w=Path(a.workspace).resolve()
        if w.parent!=base or not w.name.startswith("it-policy-assistant-"): p.error("Select isolated IT workspace")
        if a.action=="review":
            # Execute untrusted agent code only inside a restricted disposable container.
            subprocess.run(["docker","run","--rm","--network","none","--cap-drop","ALL","--security-opt","no-new-privileges","--memory","512m","--pids-limit","64","--read-only","--mount",f"type=bind,source={w},target=/app,readonly","-w","/app","python:3.11-slim","python","-B","-m","unittest","-v"],check=True,timeout=180)
        else:
            if not a.approve: p.error("Human review and explicit --approve required")
            print(json.dumps({"workspace":str(w),"status":"manual_delivery_required","instructions":"Review diff and test evidence; copy approved files into a dedicated Git branch and open a PR. No files pushed."},indent=2))
if __name__=="__main__": main()
