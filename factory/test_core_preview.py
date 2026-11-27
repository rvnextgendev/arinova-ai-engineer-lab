import unittest
from factory.core_preview import execute
class CoreTests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(execute("P0302")["citations"], ["P0302"])
    def test_failure(self):
        self.assertEqual(execute("P0302","failure")["status"],"failed")
    def test_review(self):
        self.assertEqual(execute("unknown")["status"],"needs_review")
    def test_invalid(self):
        with self.assertRaises(ValueError):
            execute("")
