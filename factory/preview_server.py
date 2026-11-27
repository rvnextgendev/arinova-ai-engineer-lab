"""Local-only preview. Do not expose to a network."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from core_preview import execute
ROOT=Path(__file__).parent
class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, mime):
        self.send_response(status)
        self.send_header("Content-Type",mime)
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def data(self,status,obj):
        self.send(status,json.dumps(obj).encode(),"application/json")
    def do_GET(self):
        if self.path=="/":
            self.send(200,(ROOT/"architecture.html").read_bytes(),"text/html; charset=utf-8")
        elif self.path=="/catalog":
            self.send(200,(ROOT/"architecture_catalog.json").read_bytes(),"application/json")
        else:
            self.data(404,{"error":"Not found"})
    def do_POST(self):
        if self.path!="/execute":
            return self.data(404,{"error":"Not found"})
        try:
            n=int(self.headers.get("Content-Length","0"))
            if not 0<n<=8192:
                raise ValueError("Invalid request length")
            m=json.loads(self.rfile.read(n))
            self.data(200,execute(m["question"],m.get("scenario","normal")))
        except (ValueError,KeyError,TypeError,AttributeError):
            self.data(400,{"error":"Invalid request"})
if __name__=="__main__":
    HTTPServer(("127.0.0.1",8765),Handler).serve_forever()
