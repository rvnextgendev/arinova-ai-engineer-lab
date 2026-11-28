"""Read-only MCP policy server over stdio."""
import json
import sys
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
docs=json.loads((Path(sys.argv[1])/"policies.json").read_text(encoding="utf-8"))
server=FastMCP("arinova-policy")
def lookup_policy(policy_id:str)->str:
    """Retrieve an exact policy identifier."""
    return json.dumps([d for d in docs if d["id"]==policy_id])
def list_policies()->str:
    """List policy identifiers and keywords."""
    return json.dumps([{"id":d["id"],"keywords":d["keywords"]} for d in docs])
def search_documents(question:str)->str:
    """Search indexed PDF excerpts for the selected policy department."""
    import psycopg
    from policy_hybrid import retrieve
    domain=json.loads((Path(sys.argv[1])/"manifest.json").read_text())["business_plugin"].split("_")[0]
    with psycopg.connect(os.environ["ARINOVA_POLICY_DSN"]) as conn:
        return json.dumps(retrieve(conn,domain,question))
if os.getenv("ARINOVA_POLICY_PDF_ONLY")=="1":
    server.tool()(search_documents)
else:
    server.tool()(lookup_policy)
    server.tool()(list_policies)
if __name__=="__main__": server.run(transport="stdio")
