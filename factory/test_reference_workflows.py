import unittest,tempfile
from pathlib import Path
from reference_workflows import execute,SPECS,run
from central_projects import Registry
class ReferenceTests(unittest.TestCase):
    def test_acquisition(self):
        r=execute("acquisition",{},"extract",SPECS["acquisition"]["sample"])["state"]["report"]
        self.assertEqual((r["source"],r["accepted"],r["duplicates"],r["invalid"]),(4,2,1,1))
    def test_invoice(self):
        s={}
        execute("invoice",s,"extract",SPECS["invoice"]["sample"])
        with self.assertRaises(ValueError):execute("invoice",s,"extract",SPECS["invoice"]["sample"])
        execute("invoice",s,"approve","INV-001")
        self.assertEqual(s["invoices"]["INV-001"]["status"],"approved")
    def test_commerce(self):
        s={}
        execute("commerce",s,"add","SKU-1",2)
        execute("commerce",s,"checkout")
        self.assertEqual(s["orders"][0]["total_cents"],1000)
        self.assertEqual(s["cart"],{})
    def test_enterprise(self):
        s={}
        execute("enterprise",s,"register","EMP-001")
        execute("enterprise",s,"request","EMP-001",2)
        k=next(iter(s["requests"]))
        execute("enterprise",s,"approve",k)
        self.assertEqual(s["requests"][k]["status"],"approved")
    def test_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);r=Registry(p/"state.db",p/"generated")
            for kind in SPECS:
                r.create(kind,"Demo","Reference",kind);r.configure(kind,[]);r.plan(kind)
                self.assertTrue((Path(r.generate(kind)["artifact"])/"app.py").is_file())
            run(r,"commerce","add","SKU-1",2)
            self.assertEqual(run(r,"enterprise","view")["state"],{})
            self.assertEqual(run(r,"commerce","view")["state"]["cart"],{"SKU-1":2})
