import os,json,base64,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from enterprise_auth import authenticate,password_hash,allowed
from central_projects import Registry
class EnterpriseTests(unittest.TestCase):
    def test_auth(self):
        record={"alice":{"password_hash":password_hash("test-only-password"),"roles":["developer"],"projects":["one"]}}
        with patch.dict(os.environ,{"ARINOVA_AUTH_MODE":"local","ARINOVA_LOCAL_USERS":json.dumps(record)}):
            def header(p):return "Basic "+base64.b64encode(("alice:"+p).encode()).decode()
            p=authenticate(header("test-only-password"))
            self.assertTrue(allowed(p,"one",("developer",)))
            self.assertFalse(allowed(p,"two",("developer",)))
            self.assertFalse(allowed(p,"one",("approver",)))
            with self.assertRaises(ValueError):authenticate(header("wrong"))
    def test_custom(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);r=Registry(p/"state.db",p/"generated")
            r.create("finance-demo","Demo","Finance knowledge assistant","custom")
            r.configure("finance-demo",["local_model"]);r.plan("finance-demo")
            result=r.generate("finance-demo")
            root=Path(result["artifact"])
            for name in ("customer_api.py","enterprise_auth.py","Dockerfile","requirements.txt","DEPLOYMENT.md"):
                self.assertTrue((root/name).is_file())
            self.assertEqual(json.loads((root/"policies.json").read_text()),[])
