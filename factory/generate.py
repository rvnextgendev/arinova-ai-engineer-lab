"""Local, opt-in factory CLI. No external dependencies for generation."""
import argparse
import json
import re
import shutil
from pathlib import Path

CAPABILITIES = {
    "rag": (), "hybrid_search": ("rag",), "langgraph": (),
    "deep_agents": (), "mcp": (), "skills": (), "evaluation": (),
    "guardrails": (), "retry": (), "circuit_breaker": (),
    "dlq": ("retry",), "checkpointing": (), "human_approval": (),
    "observability": (), "rbac": (), "ci_cd": (),
}
# Registry describes requested features, not verified runtime availability.
def validate(m):
    if not isinstance(m, dict):
        raise ValueError("Expected object")
    for key, pattern in [("project", r"[a-z][a-z0-9-]{0,63}"), ("business_plugin", r"[a-z][a-z0-9_]{0,63}")]:
        if not isinstance(m.get(key), str) or not re.fullmatch(pattern, m[key]):
            raise ValueError("Invalid " + key)
    if m.get("model") not in ("ollama", "groq", "openai"):
        raise ValueError("Unknown model provider")
    caps = m.get("capabilities")
    if not isinstance(caps, dict) or any(k not in CAPABILITIES or type(v) is not bool for k,v in caps.items()):
        raise ValueError("Invalid capabilities")
    for k, deps in CAPABILITIES.items():
        if caps.get(k) and any(not caps.get(d) for d in deps):
            raise ValueError(k + " requires " + ", ".join(deps))
    return {k:m[k] for k in ("project","business_plugin","model","capabilities")}

def generate(manifest, output):
    m = validate(manifest)
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    dest = root / m["project"]
    dest.mkdir(exist_ok=False)
    try:
        (dest / "manifest.json").write_text(json.dumps(m, indent=2), encoding="utf-8")
        shutil.copyfile(Path(__file__).with_name("core_preview.py"), dest / "arinova_core.py")
        shutil.copyfile(Path(__file__).with_name("runtime_template.py"), dest / "runtime.py")
        shutil.copyfile(Path(__file__).with_name("web_template.py"), dest / "web_app.py")
        (dest / "business.py").write_text('from arinova_core import execute\ndef process(question):\n    return execute(question)\n', encoding="utf-8")
        (dest / "app.py").write_text('import json\nfrom business import process\ndef run(question):\n    return process(question)\nif __name__ == "__main__":\n    print(json.dumps(run(input("Question: ")), indent=2))\n', encoding="utf-8")
        (dest / "test_app.py").write_text('import unittest\nfrom app import run\nclass PilotTests(unittest.TestCase):\n    def test_process(self):\n        self.assertEqual(run("P0302")["status"], "completed")\n    def test_empty(self):\n        with self.assertRaises(ValueError):\n            run(" ")\n', encoding="utf-8")
        (dest / "README.md").write_text("Run python app.py or python web_app.py (http://127.0.0.1:8770), and python -m unittest. Live models require explicit selection and model name; cloud keys are environment variables. Offline fixture-based Core runtime included. Manifest AI selections are requirements, not activated external integrations. No production deployment.\n", encoding="utf-8")
        if m["capabilities"].get("ci_cd"):
            p = dest / ".github/workflows"
            p.mkdir(parents=True)
            (p / "test.yml").write_text("name: Pilot tests\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n      - run: python -m unittest\n", encoding="utf-8")
    except Exception:
        shutil.rmtree(dest)
        raise
    return dest

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path)
    p.add_argument("--output", type=Path, default=Path("generated"))
    args = p.parse_args()
    print(generate(json.loads(args.manifest.read_text(encoding="utf-8")), args.output))
