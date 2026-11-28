"""Opt-in, bounded architect learning exercises; no deployment or external writes."""
import os,json,time,math,hashlib,sqlite3
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import URLError
ROOT=Path(__file__).resolve().parent.parent
def ollama(path,payload=None):
    base=os.getenv("ARINOVA_OLLAMA_URL","http://127.0.0.1:11434").rstrip("/")
    req=Request(base+path,data=None if payload is None else json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with urlopen(req,timeout=120 if payload else 5) as res:return json.load(res)
def health():
    checks={}
    try: checks["ollama"]={"ok":True,"models":[m["name"] for m in ollama("/api/tags")["models"]]}
    except Exception as e: checks["ollama"]={"ok":False,"error":type(e).__name__}
    try:
        import psycopg
        with psycopg.connect(os.environ["ARINOVA_POLICY_DSN"],connect_timeout=5) as c:
            checks["postgres"]={"ok":True,"pgvector":bool(c.execute("SELECT 1 FROM pg_extension WHERE extname='vector'").fetchone())}
    except Exception as e: checks["postgres"]={"ok":False,"error":type(e).__name__}
    return checks
def benchmark(text):
    start=time.monotonic()
    result=ollama("/api/chat",{"model":os.getenv("ARINOVA_AGENT_MODEL","llama3.2:latest"),"messages":[{"role":"user","content":text}],"stream":False,"options":{"num_predict":128}})
    return {"answer":result["message"]["content"],"seconds":round(time.monotonic()-start,3),"input_tokens":result.get("prompt_eval_count"),"output_tokens":result.get("eval_count")}
def security(text):
    import re
    masked=re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}","[EMAIL]",text)
    masked=re.sub(r"\b\d{10}\b","[PHONE]",masked)
    flags=[p for p in ("ignore previous","system prompt","reveal secret","bypass") if p in text.lower()]
    return {"masked":masked,"heuristic_flags":flags,"tool_policy":{"reader_can_search":True,"reader_can_deliver":False},"warning":"Illustrative regex and policy rules, not an enforced security boundary."}
def context(text):
    from langgraph.graph import StateGraph,START,END
    from typing import TypedDict
    class State(TypedDict):
        question:str
        context:list
        trace:list
    def select(s):
        words=set(s["question"].lower().split())
        candidates=["VPN access requires approval","Annual leave requires manager approval","Security incidents must be reported"]
        return {"context":sorted(candidates,key=lambda c:len(words&set(c.lower().split())),reverse=True)[:2],"trace":["select_context"]}
    def review(s):return {"trace":s["trace"]+["review_context"]}
    g=StateGraph(State);g.add_node("select",select);g.add_node("review",review);g.add_edge(START,"select");g.add_edge("select","review");g.add_edge("review",END)
    return g.compile().invoke({"question":text,"context":[],"trace":[]})
def knowledge(text):
    start=time.monotonic()
    result=ollama("/api/embed",{"model":"nomic-embed-text","input":[text,"Corporate policy and employee requirements","Weather forecast and rainfall"]})
    vectors=result["embeddings"]
    def cosine(a,b):return sum(x*y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)))
    return {"dimensions":len(vectors[0]),"seconds":round(time.monotonic()-start,3),"similarity":{"policy":cosine(vectors[0],vectors[1]),"weather":cosine(vectors[0],vectors[2])}}
def recovery():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        a=sqlite3.connect(str(Path(d)/"original.db"));a.execute("create table sample(value text)");a.execute("insert into sample values ('fictional policy')");a.commit()
        b=sqlite3.connect(str(Path(d)/"backup.db"));a.backup(b);a.close();b.close()
        c=sqlite3.connect(str(Path(d)/"backup.db"));value=c.execute("select value from sample").fetchone()[0];c.close()
        return {"backup_restored":value=="fictional policy","scope":"Temporary SQLite exercise; not PostgreSQL disaster recovery"}
MODULES={"validation":("Testing & Validation",lambda t:health()),"llmops":("LLMOps",benchmark),"security":("Security & Governance",security),"agents":("Advanced Agents",context),"knowledge":("Knowledge & Models",knowledge),"deployment":("Deployment & Recovery",lambda t:recovery())}
def execute(module,text):
    if module not in MODULES:raise ValueError("Unknown module")
    if len(text)>2000:raise ValueError("Input too long")
    start=time.monotonic()
    return {"module":module,"result":MODULES[module][1](text),"elapsed_seconds":round(time.monotonic()-start,3)}
