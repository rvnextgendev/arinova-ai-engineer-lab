import json,shutil
from pathlib import Path
def build(id,output,kind,requirements):
    dest=Path(output)/id
    dest.mkdir(parents=True,exist_ok=False)
    try:
        shutil.copyfile(Path(__file__).with_name("reference_workflows.py"),dest/"arinova_core.py")
        (dest/"manifest.json").write_text(json.dumps({"project":id,"template":kind,"business_plugin":kind,"capabilities":{}},indent=2))
        (dest/"business.py").write_text("from arinova_core import execute\nKIND="+repr(kind)+"\n")
        (dest/"app.py").write_text('import json,sys\nfrom business import execute,KIND\nif __name__=="__main__":\n    request=json.load(sys.stdin)\n    print(json.dumps(execute(KIND,request.get("state",{}),request["action"],request.get("value",""),request.get("quantity",1)),indent=2))\n')
        (dest/"test_app.py").write_text('import unittest\nfrom business import execute,KIND\nclass Tests(unittest.TestCase):\n    def test_invalid(self):\n        with self.assertRaises(ValueError):execute(KIND,{},"invalid")\n')
        (dest/"README.md").write_text("Offline reference workflow. Run python app.py with JSON on stdin containing action, value, quantity and state. Returned state can be supplied to the next call. No external services.\n")
        (dest/"Dockerfile").write_text('FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nUSER 65534:65534\nENTRYPOINT ["python","app.py"]\n')
        return dest
    except Exception:
        shutil.rmtree(dest);raise
