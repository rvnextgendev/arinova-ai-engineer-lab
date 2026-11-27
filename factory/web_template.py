"""Loopback-only customer application."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from runtime import run

PAGE = """<!doctype html><meta charset=utf-8><title>AriNova Customer App</title>
<style>body{font:16px system-ui;max-width:800px;margin:40px auto;padding:20px}textarea,input,select,button{font:inherit;margin:8px 0;padding:8px}textarea{width:95%}pre{white-space:pre-wrap}</style>
<h1>AriNova Customer App</h1><p>Offline mode is default. Cloud mode sends your question and context to the selected provider.</p>
<select id="provider"><option>offline</option><option>ollama</option><option>groq</option><option>openai</option></select>
<input id="model" placeholder="Model name for live mode"><br>
<textarea id="context" placeholder="Optional context (live mode only)"></textarea>
<textarea id="question">Explain P0302</textarea><button id="go">Execute</button><pre id="result"></pre>
<script>const el=id=>document.getElementById(id);el('go').onclick=async()=>{el('go').disabled=true;el('result').textContent='Executing...';try{const r=await fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(['provider','model','context','question'].map(k=>[k,el(k).value])))});el('result').textContent=JSON.stringify(await r.json(),null,2)}catch(e){el('result').textContent=String(e)}finally{el('go').disabled=false}};</script>"""
class Handler(BaseHTTPRequestHandler):
    def send(self,status,body,mime):
        self.send_response(status)
        self.send_header("Content-Type",mime)
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        self.send(200,PAGE.encode(),"text/html; charset=utf-8") if self.path=="/" else self.send(404,b"Not found","text/plain")
    def do_POST(self):
        status=200
        try:
            if self.path!="/run" or self.headers.get("Origin")!="http://127.0.0.1:8770":
                raise ValueError("Use the local customer portal")
            n=int(self.headers.get("Content-Length","0"))
            if not 0<n<=128000: raise ValueError("Invalid request size")
            result=run(**json.loads(self.rfile.read(n)))
        except Exception as exc:
            status=400
            result={"status":"failed","error":str(exc)}
        self.send(status,json.dumps(result).encode(),"application/json")
if __name__=="__main__":
    print("Customer app: http://127.0.0.1:8770",flush=True)
    with ThreadingHTTPServer(("127.0.0.1",8770),Handler) as server:
        try: server.serve_forever()
        except KeyboardInterrupt: pass
