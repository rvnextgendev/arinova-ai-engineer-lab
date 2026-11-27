import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from factory.generate import generate, validate

class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(Path(__file__).with_name("example.json").read_text())
    def test_dependencies(self):
        self.m["capabilities"]["rag"] = False
        with self.assertRaises(ValueError):
            validate(self.m)
    def test_traversal(self):
        self.m["project"] = "../escape"
        with self.assertRaises(ValueError):
            validate(self.m)
    def test_unknown(self):
        self.m["capabilities"]["unknown"] = True
        with self.assertRaises(ValueError):
            validate(self.m)
    def test_generate(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = generate(self.m, tmp)
            self.assertTrue((dest / ".github/workflows/test.yml").exists())
            subprocess.run([sys.executable, "-m", "unittest"], cwd=dest, check=True)
            with self.assertRaises(FileExistsError):
                generate(self.m, tmp)
