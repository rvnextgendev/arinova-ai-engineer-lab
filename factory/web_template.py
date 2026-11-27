"""Loopback-only customer application."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from runtime import run

PAGE = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AriNova Customer Studio</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#182b42;font:15px system-ui}header{background:#142b45;color:white;padding:22px 5%}header h1{margin:0;font-size:24px}main{max-width:1200px;margin:24px auto;padding:0 20px;display:grid;grid-template-columns:340px 1fr;gap:20px}section{background:white;border:1px solid #dbe3ed;border-radius:12px;padding:22px;margin-bottom:16px}h2{font-size:18px;margin-top:0}label{display:block;font-weight:600;margin-top:14px}input,select,textarea,button{font:inherit;width:100%;padding:10px;border:1px solid #bdcad9;border-radius:6px;margin-top:6px}button{background:#2057a4;color:white;cursor:pointer;border:0;font-weight:600}button:disabled{opacity:.5}textarea{resize:vertical}small{color:#53677c}pre{white-space:pre-wrap;overflow-wrap:anywhere}li{padding:10px;border-bottom:1px solid #e5ebf2}#answer{white-space:pre-wrap}#status{font-weight:600}nav a{color:white;margin-right:16px}@media(max-width:750px){main{grid-template-columns:1fr}}
</style><header><h1>AriNova Customer Studio</h1><p>Generated application · Local development</p><nav><a href="#configuration">Configuration</a><a href="#execution">Execution</a><a href="#diagnostics">Diagnostics</a></nav></header><main><aside><section id="configuration"><h2>Model configuration</h2><label for="provider">Provider</label><select id="provider"><option>offline</option><option>ollama</option><option>groq</option><option>openai</option></select><div id="live" hidden><label for="model">Model name</label><input id="model" placeholder="llama3.2"><label for="context">Optional context</label><textarea id="context" rows="5"></textarea><small>Cloud providers receive your question and context. API keys are read from environment variables.</small></div><p><small>Offline mode uses sample DTC evidence, not an LLM.</small></p></section><section><h2>Sample questions</h2><button class="sample">Explain P0302</button><button class="sample">Explain P0456</button><button class="sample">Explain P9999</button></section></aside><div><section id="execution"><h2>Execute workflow</h2><label for="question">Question</label><textarea id="question" rows="3">Explain P0302</textarea><button id="go">Execute</button><p id="status" role="status">Ready</p><h2>Answer</h2><div id="answer">No execution yet.</div><p id="citations"></p></section><section><h2>Execution timeline</h2><small>Events are displayed after the response completes.</small><ol id="events"></ol></section><section id="diagnostics"><h2>Diagnostics</h2><p id="duration"></p><details><summary>Raw response</summary><pre id="result"></pre></details></section></div></main><script>
const el=id=>document.getElementById(id);el('provider').onchange=()=>{el('live').hidden=el('provider').value==='offline'};document.querySelectorAll('.sample').forEach(b=>b.onclick=()=>el('question').value=b.textContent);
el('go').onclick=async()=>{el('go').disabled=true;el('status').textContent='Executing...';el('answer').textContent='';el('citations').textContent='';el('events').replaceChildren();el('result').textContent='';const start=performance.now();try{const r=await fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(['provider','model','context','question'].map(k=>[k,el(k).value])))});const d=await r.json();el('status').textContent=d.status||('HTTP '+r.status);el('answer').textContent=d.answer||d.error||'No answer available';el('citations').textContent='Citations: '+(d.citations||[]).join(', ');for(const e of d.events||[]){const li=document.createElement('li');li.textContent=e.stage+' — '+e.status+(e.detail?' — '+JSON.stringify(e.detail):'');el('events').append(li)}el('result').textContent=JSON.stringify(d,null,2)}catch(e){el('status').textContent='Failed';el('answer').textContent=String(e)}finally{el('duration').textContent='Elapsed: '+Math.round(performance.now()-start)+' ms';el('go').disabled=false}};
</script></html>"""
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
