"""Register and generate new PDF-first policy assistants without changing shared code."""
import argparse
import json
import re
from pathlib import Path
from policy_pilot import POLICIES

def create(domain, output):
    if not re.fullmatch(r"[a-z][a-z0-9]{0,39}",domain):
        raise ValueError("Use a lowercase single-word domain, e.g. finance")
    if domain in POLICIES: raise ValueError("Use policy_pilot.py for hr or it")
    # Reuse the existing generator with an empty collection; no fictional facts.
    POLICIES[domain]=[]
    try:
        from generate import generate
        import shutil
        dest=generate({"project":domain+"-policy-assistant","business_plugin":domain+"_policy","model":"ollama","capabilities":{}},output)
        try:
            (dest/"policies.json").write_text("[]",encoding="utf-8")
            shutil.copyfile(Path(__file__).with_name("policy_core.py"),dest/"arinova_core.py")
            (dest/"runtime.py").write_text('def run(**kwargs):\n    return {"status":"needs_review","answer":"Use the PDF agent CLI after indexing documents.","citations":[],"events":[]}\n',encoding="utf-8")
            (dest/"test_app.py").write_text('import unittest\nfrom app import run\nclass EmptyPolicyTests(unittest.TestCase):\n    def test_no_fixture(self):\n        self.assertEqual(run("policy question")["status"],"needs_review")\n',encoding="utf-8")
            (dest/"README.md").write_text(f"PDF-first {domain} assistant. From repository root run python factory/policy_hybrid.py {domain} ingest PATH.pdf, set ARINOVA_POLICY_PDF_ONLY=1, then python factory/policy_agents.py generated/{domain}-policy-assistant langgraph QUESTION. Generic web UI is not connected to PDF retrieval yet.\n",encoding="utf-8")
            (dest/"agent-task.md").write_text(f"Extend the {domain} policy assistant only after reviewing indexed source documents. Preserve shared tools and add domain-specific tests. No deployment.\n",encoding="utf-8")
            (dest/"reuse-report.json").write_text(json.dumps({"domain":domain,"reused":["policy_core.py","generate.py","policy_agents.py","policy_hybrid.py","policy_mcp.py"],"customized":["manifest.json","agent-task.md"],"mode":"pdf-only"},indent=2),encoding="utf-8")
        except Exception:
            shutil.rmtree(dest)
            raise
        return dest
    finally:
        del POLICIES[domain]
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("domain");p.add_argument("--output",default="generated");a=p.parse_args()
    print(create(a.domain,a.output))
