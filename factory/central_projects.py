"""Local persistent project lifecycle. SQLite is a pilot storage choice."""
import sqlite3,json,re,os
from pathlib import Path
from contextlib import closing
from central_core import VERSION,resolve,CATALOG
from generate import generate
ROOT=Path(__file__).resolve().parent.parent
class Registry:
    def __init__(self,db,output):
        self.db=Path(db);self.output=Path(output);self.db.parent.mkdir(parents=True,exist_ok=True)
        with closing(self.connect()) as c,c:
            c.execute("CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, customer TEXT NOT NULL, requirements TEXT NOT NULL, capabilities TEXT NOT NULL, stage TEXT NOT NULL, plan TEXT, artifact TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS project_templates(project TEXT PRIMARY KEY, template TEXT NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, project TEXT NOT NULL, stage TEXT NOT NULL, detail TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP)")
    def connect(self):
        c=sqlite3.connect(self.db,timeout=10);c.row_factory=sqlite3.Row;return c
    def event(self,c,id,stage,detail):
        c.execute("INSERT INTO events(project,stage,detail) VALUES(?,?,?)",(id,stage,detail))
    def get(self,id):
        with closing(self.connect()) as c:
            row=c.execute("SELECT * FROM projects WHERE id=?",(id,)).fetchone()
            if not row:raise ValueError("Project not found")
            d=dict(row)
            t=c.execute("SELECT template FROM project_templates WHERE project=?",(id,)).fetchone()
            d["template"]=t[0] if t else "generic"
            for k in ("capabilities","plan"):
                if d[k] is not None:d[k]=json.loads(d[k])
            d["events"]=[dict(x) for x in c.execute("SELECT stage,detail,created FROM events WHERE project=? ORDER BY seq",(id,))]
            return d
    def list(self):
        with closing(self.connect()) as c:return [dict(x) for x in c.execute("SELECT id,customer,stage FROM projects ORDER BY id")]
    def create(self,id,customer,requirements,template="generic"):
        if template not in ("generic","hr","it","azure","custom","acquisition","invoice","commerce","enterprise"):raise ValueError("Invalid template")
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}",id):raise ValueError("Invalid project ID")
        if not 1<=len(customer.strip())<=120 or not 1<=len(requirements.strip())<=8000:raise ValueError("Customer and requirements required")
        try:
            with closing(self.connect()) as c,c:
                c.execute("INSERT INTO projects VALUES(?,?,?,?,?,?,?)",(id,customer,requirements,"[]","registered",None,None))
                c.execute("INSERT INTO project_templates VALUES(?,?)",(id,template))
                self.event(c,id,"registered","Customer project and requirements saved; template="+template)
        except sqlite3.IntegrityError:raise ValueError("Project already exists")
        return self.get(id)
    def configure(self,id,selected):
        caps=resolve(selected)
        with closing(self.connect()) as c,c:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT stage FROM projects WHERE id=?",(id,)).fetchone()
            if not row or row[0] not in ("registered","configured","planned"):raise ValueError("Project cannot be configured at this stage")
            c.execute("UPDATE projects SET capabilities=?,stage='configured',plan=NULL WHERE id=?",(json.dumps(caps),id))
            self.event(c,id,"configured","Dependencies resolved: "+", ".join(caps))
        return self.get(id)
    def plan(self,id):
        with closing(self.connect()) as c,c:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT * FROM projects WHERE id=?",(id,)).fetchone()
            if not row or row["stage"]!="configured":raise ValueError("Configure capabilities first")
            caps=json.loads(row["capabilities"])
            t=c.execute("SELECT template FROM project_templates WHERE project=?",(id,)).fetchone()
            template=t[0] if t else "generic"
            plan={"template":template,"core_version":VERSION,"provider":"ollama","components":[{"id":k,"status":CATALOG[k][2],"source":CATALOG[k][3],"integration":"requires customer wiring"} for k in caps],"requirements":row["requirements"],"generation_scope":("Generic DTC fixture starter" if template=="generic" else "Shared policy keyword retrieval and local Ollama adapter")+"; other selected adapters are not automatically activated"}
            from reference_workflows import SPECS
            if template in SPECS:
                plan.update(provider="none",generation_scope=SPECS[template]["architecture"],runtime="Python deterministic reference workflow",components=[])
            c.execute("UPDATE projects SET plan=?,stage='planned' WHERE id=?",(json.dumps(plan),id))
            self.event(c,id,"planned","Architecture inventory and integration gaps recorded")
        return self.get(id)
    def generate(self,id):
        with closing(self.connect()) as c,c:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT * FROM projects WHERE id=?",(id,)).fetchone()
            if not row or row["stage"]!="planned":raise ValueError("Plan project first")
            from generate import CAPABILITIES
            selected=json.loads(row["capabilities"])
            caps={k:True for k in selected if k in CAPABILITIES}
            template=json.loads(row["plan"]).get("template","generic")
            from reference_workflows import SPECS
            if template in SPECS:
                from reference_package import build
                dest=build(id,self.output,template,row["requirements"])
            elif template=="custom":
                from custom_application import build_custom
                dest=build_custom(id,self.output,caps,row["requirements"])
            elif template!="generic":
                from policy_pilot import build
                dest=build(template,self.output,id,caps)
            else: dest=generate({"project":id,"business_plugin":id.replace("-","_"),"model":"ollama","capabilities":caps},self.output)
            try:
                if template not in SPECS and template!="generic":
                    from custom_application import package_scaffold
                    package_scaffold(dest)
                (dest/"architecture-plan.json").write_text(row["plan"],encoding="utf-8")
                (dest/"requirements.md").write_text(row["requirements"],encoding="utf-8")
                c.execute("UPDATE projects SET stage='generated',artifact=? WHERE id=?",(str(dest),id))
                self.event(c,id,"generated","Starter generated; integration and tests pending")
                c.commit()
            except Exception:
                import shutil
                shutil.rmtree(dest)
                raise
        return self.get(id)
def registry():
    return Registry(ROOT/"factory-state"/"projects.sqlite3",ROOT/"generated")
