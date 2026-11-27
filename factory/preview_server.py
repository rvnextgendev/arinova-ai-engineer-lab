"""Local-only preview. Do not expose to a network."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from core_preview import execute
from generate import generate, CAPABILITIES
import webbrowser
import sys
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
        elif self.path=="/capabilities":
            self.data(200,CAPABILITIES)
        elif self.path=="/catalog":
            self.send(200,(ROOT/"architecture_catalog.json").read_bytes(),"application/json")
        else:
            self.data(404,{"error":"Not found"})
    def do_POST(self):
        if self.path not in ("/execute","/generate"):
            return self.data(404,{"error":"Not found"})
        try:
            n=int(self.headers.get("Content-Length","0"))
            if not 0<n<=8192:
                raise ValueError("Invalid request length")
            m=json.loads(self.rfile.read(n))
            if self.path=="/generate":
                if self.headers.get("Origin") != "http://127.0.0.1:8765":
                    return self.data(403,{"error":"Local portal origin required"})
                dest=generate(m,ROOT.parent/"generated")
                return self.data(201,{"project":dest.name,"path":str(dest)})
            self.data(200,execute(m["question"],m.get("scenario","normal")))
        except FileExistsError:
            self.data(409,{"error":"Project already exists"})
        except (ValueError,KeyError,TypeError,AttributeError):
            self.data(400,{"error":"Invalid request"})
if __name__=="__main__":
    with HTTPServer(("127.0.0.1",8765),Handler) as server:
        print("AriNova Studio: http://127.0.0.1:8765",flush=True)
        if "--no-browser" not in sys.argv:
            webbrowser.open("http://127.0.0.1:8765")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")
