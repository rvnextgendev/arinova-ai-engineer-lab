"""Generate isolated HR and IT policy applications from shared source."""
import argparse
import json
import shutil
from pathlib import Path
from generate import generate

POLICIES={
"hr":[
{"id":"HR-001","keywords":"leave annual vacation carry forward","text":"Demo policy: employees receive 20 annual leave days."},
{"id":"HR-002","keywords":"remote home hybrid work","text":"Demo policy: remote work requires manager agreement."}],
"it":[
{"id":"IT-001","keywords":"vpn remote access","text":"Demo policy: use the approved corporate VPN for remote access."},
{"id":"IT-002","keywords":"password length characters mfa","text":"Demo policy: passwords require at least 14 characters and MFA."},
{"id":"IT-003","keywords":"software install installation unapproved","text":"Demo policy: unapproved software requires IT security authorization."},
{"id":"IT-004","keywords":"device laptop compliance compliant","text":"Demo policy: report non-compliant devices to Technology Support."}]}

def build(domain, output):
    if domain not in POLICIES:
        raise ValueError("Choose hr or it")
    root=Path(__file__).parent
    dest=generate({"project":domain+"-policy-assistant","business_plugin":domain+"_policy","model":"ollama","capabilities":{}},output)
    try:
        shutil.copyfile(root/"policy_core.py",dest/"arinova_core.py")
        (dest/"policies.json").write_text(json.dumps(POLICIES[domain],indent=2),encoding="utf-8")
        # Disable generic live generation until grounded retrieval is integrated.
        (dest/"runtime.py").write_text('from arinova_core import execute\ndef run(question, provider="offline", model="", context=""):\n    if provider != "offline":\n        raise ValueError("Policy pilot is offline only")\n    return execute(question)\n',encoding="utf-8")
        sample="annual leave" if domain=="hr" else "password length"
        code=POLICIES[domain][0 if domain=="hr" else 1]["id"]
        unknown="password length" if domain=="hr" else "annual leave"
        (dest/"test_app.py").write_text(f'import unittest\nfrom app import run\nclass PolicyTests(unittest.TestCase):\n    def test_known(self):\n        self.assertEqual(run({sample!r})["citations"], [{code!r}])\n    def test_other_domain(self):\n        self.assertEqual(run({unknown!r})["status"], "needs_review")\n    def test_empty(self):\n        with self.assertRaises(ValueError): run(" ")\n    def test_approval(self):\n        self.assertEqual(run({"approve "+sample!r})["status"], "needs_review")\n',encoding="utf-8")
        (dest/"README.md").write_text("Fictional policy pilot. Run python -m unittest -v, python app.py or python web_app.py. Select offline mode. Keyword retrieval only; no PDF ingestion, embeddings, authentication or real approval. Do not use real employee data.\n",encoding="utf-8")
        (dest/"reuse-report.json").write_text(json.dumps({"reused":["factory/generate.py","factory/web_template.py","factory/policy_core.py"],"customized":["policies.json","test_app.py"],"disabled":["live model generation"],"reference":"shared policy core"},indent=2),encoding="utf-8")
    except Exception:
        shutil.rmtree(dest)
        raise
    return dest

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("domain",choices=["hr","it"])
    p.add_argument("--output",default="generated")
    a=p.parse_args()
    print(build(a.domain,a.output))
