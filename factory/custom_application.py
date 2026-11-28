"""Custom knowledge assistant starter; arbitrary business workflows require development."""
import json,shutil
from pathlib import Path
from generate import generate
def build_custom(id,output,caps,requirements):
    dest=generate({"project":id,"business_plugin":id.replace("-","_"),"model":"ollama","capabilities":caps},output)
    try:
        root=Path(__file__).parent
        shutil.copyfile(root/"policy_core.py",dest/"arinova_core.py")
        shutil.copyfile(root/"policy_runtime.py",dest/"runtime.py")
        (dest/"policies.json").write_text("[]",encoding="utf-8")
        (dest/"requirements.md").write_text(requirements,encoding="utf-8")
        (dest/"test_app.py").write_text('import unittest\nfrom app import run\nclass CustomTests(unittest.TestCase):\n    def test_unknown(self):\n        self.assertEqual(run("unknown question")["status"],"needs_review")\n    def test_empty(self):\n        with self.assertRaises(ValueError):run("")\n',encoding="utf-8")
        (dest/"agent-task.md").write_text("Implement customer requirements in requirements.md. Add business acceptance tests. Do not invent customer facts or deploy.",encoding="utf-8")
        return dest
    except Exception:
        shutil.rmtree(dest);raise
def package_scaffold(dest):
    root=Path(__file__).parent
    shutil.copyfile(root/"enterprise_auth.py",dest/"enterprise_auth.py")
    shutil.copyfile(root/"standalone_customer.py",dest/"customer_api.py")
    (dest/"requirements.txt").write_text("fastapi>=0.115,<1\nuvicorn>=0.30,<1\nPyJWT[crypto]>=2.10,<3\n",encoding="utf-8")
    (dest/"Dockerfile").write_text("FROM python:3.11-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nUSER 65534:65534\nEXPOSE 8080\nCMD [\"uvicorn\",\"customer_api:app\",\"--host\",\"0.0.0.0\",\"--port\",\"8080\"]\n",encoding="utf-8")
    (dest/".dockerignore").write_text(".env\n.env.*\n.git\n__pycache__\n",encoding="utf-8")
    (dest/"DEPLOYMENT.md").write_text("Build docker build -t customer-app . Run with a trusted OIDC issuer, JWKS URL, audience and ARINOVA_AUTH_MODE=oidc. Bind to loopback behind a TLS proxy. Set ARINOVA_OLLAMA_URL to your trusted model endpoint. POST /ask with Bearer token and JSON question/provider. The token must grant this project ID and viewer or developer role. Offline is default. This starter exposes fixture retrieval only, not central PDF agents. Do not expose legacy web_app.py. No secrets included.\n",encoding="utf-8")
