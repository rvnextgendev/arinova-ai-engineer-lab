import tempfile,unittest
from pathlib import Path
from central_projects import Registry
from central_policy_demo import setup,compare,query
class ReferenceDemo(unittest.TestCase):
    def test_pair(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);reg=Registry(p/"state.db",p/"generated")
            hr,it=setup(reg)
            result=compare(reg,hr["id"],it["id"])
            for key in ("shared_core_identical","shared_runtime_identical","policy_data_different"):
                self.assertTrue(result[key])
            self.assertTrue(result["hr"]["passed"])
            self.assertTrue(result["it"]["passed"])
            self.assertEqual(query(reg,hr["id"],"password length")["citations"],[])
            self.assertEqual(query(reg,it["id"],"annual leave")["citations"],[])
            self.assertEqual(len(reg.list()),2)
