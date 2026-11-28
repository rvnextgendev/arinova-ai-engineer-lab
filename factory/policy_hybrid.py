"""Optional local PDF ingestion and pgvector hybrid retrieval. Fictional data only."""
import json
from urllib.request import Request,urlopen
from pathlib import Path

def embed(text):
    req=Request("http://127.0.0.1:11434/api/embed",data=json.dumps({"model":"nomic-embed-text","input":text}).encode(),headers={"Content-Type":"application/json"})
    with urlopen(req,timeout=60) as res: v=json.load(res)["embeddings"][0]
    if len(v)!=768: raise ValueError("Expected 768 dimensions")
    return "["+",".join(map(str,v))+"]"

def ingest(conn,domain,pdf):
    from pypdf import PdfReader
    if domain not in ("hr","it"): raise ValueError("Invalid domain")
    path=Path(pdf)
    if path.stat().st_size>20*1024*1024: raise ValueError("PDF too large")
    reader=PdfReader(path)
    if len(reader.pages)>200: raise ValueError("Too many pages")
    rows=[]
    for i,page in enumerate(reader.pages,1):
        t=page.extract_text() or ""
        for j in range(0,len(t),1000):
            chunk=t[j:j+1200].strip()
            if chunk: rows.append((domain,path.name,i,j,chunk,embed(chunk)))
    if not rows: raise ValueError("No extractable text")
    with conn.transaction():
        conn.execute("DELETE FROM factory_policy_chunks WHERE domain=%s AND source=%s",(domain,path.name))
        with conn.cursor() as cur:
            cur.executemany("INSERT INTO factory_policy_chunks(domain,source,page,offset_id,body,embedding) VALUES (%s,%s,%s,%s,%s,%s::vector)",rows)
    return len(rows)

def initialize(conn):
    with conn.transaction():
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute("CREATE TABLE IF NOT EXISTS factory_policy_chunks(id bigserial PRIMARY KEY, domain text NOT NULL, source text NOT NULL,page int NOT NULL,offset_id int NOT NULL,body text NOT NULL,embedding vector(768) NOT NULL)")

def retrieve(conn,domain,question):
    if domain not in ("hr","it") or not question.strip(): raise ValueError("Invalid query")
    v=embed(question)
    rows=conn.execute("""WITH v AS (SELECT id,row_number() OVER (ORDER BY embedding <=> %s::vector,id) r FROM factory_policy_chunks WHERE domain=%s ORDER BY embedding <=> %s::vector,id LIMIT 20),
    k AS (SELECT id,row_number() OVER (ORDER BY ts_rank(to_tsvector('english',body),plainto_tsquery('english',%s)) DESC,id) r FROM factory_policy_chunks WHERE domain=%s AND to_tsvector('english',body) @@ plainto_tsquery('english',%s) ORDER BY r LIMIT 20),
    fused AS (SELECT id,sum(score) score FROM (SELECT id,1.0/(60+r) score FROM v UNION ALL SELECT id,1.0/(60+r) FROM k) s GROUP BY id)
    SELECT source,page,body,score FROM fused JOIN factory_policy_chunks USING(id) WHERE domain=%s ORDER BY score DESC,id LIMIT 5""",(v,domain,v,question,domain,question,domain)).fetchall()
    return [{"source":r[0],"page":r[1],"excerpt":r[2],"rrf":float(r[3])} for r in rows]

if __name__=="__main__":
    import argparse,os,psycopg
    p=argparse.ArgumentParser();p.add_argument("domain",choices=["hr","it"]);p.add_argument("action",choices=["ingest","search"]);p.add_argument("value");a=p.parse_args()
    with psycopg.connect(os.environ["ARINOVA_POLICY_DSN"],autocommit=True) as conn:
        initialize(conn)
        print(json.dumps(ingest(conn,a.domain,a.value) if a.action=="ingest" else retrieve(conn,a.domain,a.value),indent=2))
