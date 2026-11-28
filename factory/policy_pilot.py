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
        web=(root/"web_template.py").read_text(encoding="utf-8")
        title=domain.upper()+" Policy Assistant"
        web=web.replace("AriNova Customer Studio",title).replace("Generated application · Local development","Fictional policy demo · Local Ollama")
        web=web.replace("<option>offline</option><option selected>ollama</option><option>groq</option><option>openai</option>","<option>ollama</option><option>offline</option>").replace("Offline mode uses sample DTC evidence, not an LLM.","Ollama runs locally. Offline mode is a deterministic test fallback.")
        web=web.replace('id="live" hidden','id="live"').replace("Optional context","Unused context (policy evidence is retrieved automatically)").replace("Cloud calls are disabled unless ARINOVA_ALLOW_CLOUD=1. Ollama uses the local endpoint.","Only local Ollama is supported; leave model blank for the configured default.")
        samples=["What is annual leave?","What is remote work policy?","What is password length?"] if domain=="hr" else ["Do I need VPN?","What is password length?","Approve software installation"]
        for old,new in zip(["Explain P0302","Explain P0456","Explain P9999"],samples): web=web.replace(old,new)
        (dest/"web_app.py").write_text(web,encoding="utf-8")
        (dest/"agent-task.md").write_text("Inspect existing code and reuse-report.json. Preserve the shared retrieval core. "+("Add IT-005: suspected security incidents must be reported to Technology Support. Add keywords and tests for incident retrieval and exception review." if domain=="it" else "Add a fictional HR training policy and tests.")+" Run all tests. Do not deploy or modify the original project. Report changes.\n",encoding="utf-8")
        shutil.copyfile(root/"policy_runtime.py",dest/"runtime.py")
        sample="annual leave" if domain=="hr" else "password length"
        code=POLICIES[domain][0 if domain=="hr" else 1]["id"]
        unknown="password length" if domain=="hr" else "annual leave"
        (dest/"test_app.py").write_text(f'import unittest\nfrom app import run\nclass PolicyTests(unittest.TestCase):\n    def test_known(self):\n        self.assertEqual(run({sample!r})["citations"], [{code!r}])\n    def test_other_domain(self):\n        self.assertEqual(run({unknown!r})["status"], "needs_review")\n    def test_empty(self):\n        with self.assertRaises(ValueError): run(" ")\n    def test_approval(self):\n        self.assertEqual(run({"approve "+sample!r})["status"], "needs_review")\n',encoding="utf-8")
        (dest/"README.md").write_text("Fictional policy pilot. Run python -m unittest -v, python app.py or python web_app.py. Ollama is the default UI provider; offline CLI tests remain deterministic. Keyword retrieval only; no PDF ingestion, embeddings, authentication or real approval. Do not use real employee data.\n",encoding="utf-8")
        (dest/"reuse-report.json").write_text(json.dumps({"reused":["factory/generate.py","factory/web_template.py","factory/policy_core.py"],"customized":["policies.json","test_app.py","web_app.py","agent-task.md"],"disabled":["cloud model generation"],"reference":"shared policy core"},indent=2),encoding="utf-8")
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
