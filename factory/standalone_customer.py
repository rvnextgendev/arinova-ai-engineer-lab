import json,os
from pathlib import Path
from fastapi import FastAPI,Request,HTTPException
from pydantic import BaseModel
from enterprise_auth import authenticate,allowed
app=FastAPI()
PROJECT=json.loads(Path(__file__).with_name("manifest.json").read_text())["project"]
class Question(BaseModel):
    question:str
    provider:str="offline"
@app.post("/ask")
def ask(q:Question,request:Request):
    if os.getenv("ARINOVA_AUTH_MODE")!="oidc":raise HTTPException(503,"OIDC configuration required")
    try:p=authenticate(request.headers.get("authorization",""))
    except Exception:raise HTTPException(401,"Authentication required")
    if not allowed(p,PROJECT,("viewer","developer")):raise HTTPException(403,"Access denied")
    if q.provider not in ("offline","ollama") or not 1<=len(q.question.strip())<=2000:raise HTTPException(400,"Invalid request")
    from runtime import run
    return run(q.question,provider=q.provider)
