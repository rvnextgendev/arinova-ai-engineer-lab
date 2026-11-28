"""Offline reference workflows. No external network or real payment."""
import csv,io,re,uuid,json
from decimal import Decimal
from contextlib import closing
SPECS={
"acquisition":{"name":"Automotive acquisition","sample":"year,model,dtc\n2022,A3,P0302\n2022,A3,P0302\n2023,A4,P0456\n2022,A3,INVALID","actions":["extract"],"architecture":"CSV acquisition, validation, deduplication and reconciliation"},
"invoice":{"name":"Invoice processing","sample":"Invoice: INV-001\nSubtotal: 100.00\nTax: 18.00\nTotal: 118.00","actions":["extract","approve"],"architecture":"Text extraction, decimal validation, duplicate detection and human approval"},
"commerce":{"name":"E-commerce","sample":"SKU-1","actions":["catalog","add","checkout"],"architecture":"Catalogue, cart and simulated checkout"},
"enterprise":{"name":"Employee management","sample":"EMP-001","actions":["register","request","approve"],"architecture":"Employee records, leave requests and approval"}}
CATALOG={"SKU-1":{"name":"Notebook","price_cents":500},"SKU-2":{"name":"Keyboard","price_cents":2500}}
def execute(kind,state,action,value="",quantity=1):
    if kind not in SPECS or action not in SPECS[kind]["actions"]:raise ValueError("Unsupported action")
    if len(value)>20000:raise ValueError("Input too large")
    events=[]
    def event(s):events.append(s)
    if kind=="acquisition":
        reader=csv.DictReader(io.StringIO(value))
        if reader.fieldnames!=["year","model","dtc"]:raise ValueError("Expected year,model,dtc CSV")
        rows=list(reader);seen=set();accepted=[];invalid=duplicates=0
        event("Parsed CSV source")
        for row in rows:
            y,m,d=(row.get(k) or "" for k in ("year","model","dtc"))
            if not re.fullmatch(r"20[0-9]{2}",y) or not m.strip() or not re.fullmatch(r"[PBCU][0-9A-F]{4}",d):invalid+=1;continue
            key=(y,m,d)
            if key in seen:duplicates+=1;continue
            seen.add(key);accepted.append(row)
        state["report"]={"source":len(rows),"accepted":len(accepted),"duplicates":duplicates,"invalid":invalid,"records":accepted}
        event("Validated, deduplicated and reconciled source rows")
    elif kind=="invoice":
        invoices=state.setdefault("invoices",{})
        if action=="extract":
            fields=dict(re.findall(r"(?m)^(Invoice|Subtotal|Tax|Total):[ \t]*([^\n]+)$",value))
            if set(fields)!={"Invoice","Subtotal","Tax","Total"}:raise ValueError("Four invoice fields required")
            key=fields["Invoice"].strip()
            if not re.fullmatch(r"[A-Za-z0-9-]{1,64}",key):raise ValueError("Invalid invoice ID")
            if key in invoices:raise ValueError("Duplicate invoice")
            for k in ("Subtotal","Tax","Total"):
                if not re.fullmatch(r"[0-9]{1,10}(?:\.[0-9]{1,2})?",fields[k].strip()):raise ValueError("Invalid amount")
            valid=Decimal(fields["Subtotal"])+Decimal(fields["Tax"])==Decimal(fields["Total"])
            invoices[key]={"fields":fields,"valid":valid,"status":"pending_review" if valid else "exception"}
            event("Extracted fields and validated arithmetic")
        else:
            item=invoices.get(value)
            if not item or item["status"]!="pending_review":raise ValueError("No valid pending invoice")
            item["status"]="approved";event("Human approved invoice")
    elif kind=="commerce":
        cart=state.setdefault("cart",{});orders=state.setdefault("orders",[])
        state["catalog"]=CATALOG
        if action=="add":
            if value not in CATALOG or not 1<=quantity<=100 or cart.get(value,0)+quantity>100:raise ValueError("Invalid SKU or quantity")
            cart[value]=cart.get(value,0)+quantity;event("Updated cart")
        elif action=="checkout":
            if not cart:raise ValueError("Cart is empty")
            orders.append({"id":uuid.uuid4().hex,"items":dict(cart),"total_cents":sum(CATALOG[k]["price_cents"]*v for k,v in cart.items()),"payment":"simulated_no_charge"})
            cart.clear();event("Created order; no payment charged")
        else:event("Loaded catalogue")
    else:
        employees=state.setdefault("employees",{});requests=state.setdefault("requests",{})
        if action=="register":
            if not re.fullmatch(r"[A-Za-z0-9-]{1,64}",value) or value in employees:raise ValueError("Invalid or duplicate employee")
            employees[value]={"id":value};event("Registered employee")
        elif action=="request":
            if value not in employees or not 1<=quantity<=30:raise ValueError("Invalid employee or leave days")
            key=uuid.uuid4().hex[:12];requests[key]={"employee":value,"days":quantity,"status":"pending"};event("Created leave request "+key)
        else:
            if value not in requests or requests[value]["status"]!="pending":raise ValueError("No pending request")
            requests[value]["status"]="approved";event("Approved leave request")
    return {"state":state,"events":events}
def run(reg,id,action,value="",quantity=1):
    with closing(reg.connect()) as c,c:
        c.execute("BEGIN IMMEDIATE")
        row=c.execute("SELECT template FROM project_templates WHERE project=?",(id,)).fetchone()
        if not row or row[0] not in SPECS:raise ValueError("Select reference project")
        c.execute("CREATE TABLE IF NOT EXISTS reference_state(project TEXT PRIMARY KEY,data TEXT NOT NULL)")
        old=c.execute("SELECT data FROM reference_state WHERE project=?",(id,)).fetchone()
        state=json.loads(old[0]) if old else {}
        if action=="view":return {"state":state,"events":[]}
        result=execute(row[0],state,action,value,quantity)
        c.execute("INSERT OR REPLACE INTO reference_state VALUES(?,?)",(id,json.dumps(state)))
        stage=c.execute("SELECT stage FROM projects WHERE id=?",(id,)).fetchone()[0]
        reg.event(c,id,stage,"Reference workflow: "+action)
        return result
