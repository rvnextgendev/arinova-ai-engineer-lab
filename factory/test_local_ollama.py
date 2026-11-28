"""Live local integration smoke test. No cloud SDK or key required."""
import json,os
from urllib.request import Request,urlopen

def call(path,payload=None):
    base=os.getenv("ARINOVA_OLLAMA_URL","http://127.0.0.1:11434").rstrip("/")
    req=Request(base+path,data=None if payload is None else json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with urlopen(req,timeout=120) as res: return json.load(res)
def main():
    model=os.getenv("ARINOVA_CHAT_MODEL","llama3.2:latest")
    print("Models:",[m["name"] for m in call("/api/tags")["models"]])
    answer=call("/api/chat",{"model":model,"messages":[{"role":"user","content":"Reply with a short greeting."}],"stream":False})["message"]["content"]
    if not answer.strip(): raise RuntimeError("Empty chat response")
    print("PASS: local chat")
    v=call("/api/embed",{"model":"nomic-embed-text","input":"IT policy"})["embeddings"][0]
    if len(v)!=768: raise RuntimeError("Unexpected embedding dimensions")
    print("PASS: local embeddings (768)")
    answer=call("/v1/chat/completions",{"model":model,"messages":[{"role":"user","content":"Say hello."}],"stream":False})["choices"][0]["message"]["content"]
    if not answer.strip(): raise RuntimeError("Empty compatible response")
    print("PASS: local OpenAI-compatible protocol (Ollama, not OpenAI cloud)")
if __name__=="__main__": main()
