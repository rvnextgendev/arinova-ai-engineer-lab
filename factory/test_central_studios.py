import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from central_projects import Registry
import central_studios as s
import policy_delivery as d
class EndToEnd(unittest.TestCase):
    def test_pipeline_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            r=Registry(p/"state.db",p/"generated")
            r.create("pilot","Demo","Build a starter")
            r.configure("pilot",["local_model"])
            r.plan("pilot")
            r.generate("pilot")
            with patch.object(d,"STATE",p/"workspaces"),patch.object(d,"execute_job",return_value={"exit_code":0,"log":"simulated agent"}):
                job=s.run(r,"pilot","develop")["evidence"]
                with self.assertRaises(ValueError):s.run(r,"pilot","deliver")
                s.run(r,"pilot","execute")
                failed=s.run(r,"pilot","quality",runner=lambda _:{"passed":False,"log":"simulated failure"})
                self.assertEqual(failed["project"]["stage"],"quality_failed")
                with self.assertRaises(ValueError):s.run(r,"pilot","approve")
                passed=s.run(r,"pilot","quality",runner=lambda _:{"passed":True,"log":"simulated pass"})
                token=passed["evidence"]["digest"]
                w=Path(job["workspace"])
                (w/"change.txt").write_text("changed")
                with self.assertRaises(ValueError):s.run(r,"pilot","approve",expected=token)
                passed=s.run(r,"pilot","quality",runner=lambda _:{"passed":True})
                s.run(r,"pilot","approve",expected=passed["evidence"]["digest"])
                result=s.run(r,"pilot","deliver")
                self.assertEqual(result["project"]["stage"],"delivered")
                self.assertTrue(Path(result["evidence"]["package"]).is_file())
                self.assertEqual(Registry(p/"state.db",p/"generated").get("pilot")["stage"],"delivered")
