import tempfile
import unittest
from pathlib import Path
from central_core import resolve
from central_projects import Registry
class CentralTests(unittest.TestCase):
    def test_dependencies(self):
        self.assertEqual(resolve(["mcp","rag"]),["local_model","rag","mcp"])
    def test_unknown(self):
        with self.assertRaises(ValueError):resolve(["unknown"])
    def test_lifecycle(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);r=Registry(p/"state.db",p/"generated")
            r.create("pilot","Demo","Build a policy assistant")
            with self.assertRaises(ValueError):r.generate("pilot")
            r.configure("pilot",["mcp"])
            r.plan("pilot")
            result=r.generate("pilot")
            self.assertEqual(result["stage"],"generated")
            self.assertTrue((p/"generated"/"pilot"/"architecture-plan.json").is_file())
            self.assertEqual(len(Registry(p/"state.db",p/"generated").get("pilot")["events"]),4)
            with self.assertRaises(ValueError):r.configure("pilot",[])
    def test_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);r=Registry(p/"state.db",p/"generated")
            r.create("pilot","Demo","Requirement")
            with self.assertRaises(ValueError):r.create("pilot","Demo","Requirement")
