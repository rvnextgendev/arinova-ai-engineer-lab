"""Read-only MCP policy server over stdio."""
import json
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP
docs=json.loads((Path(sys.argv[1])/"policies.json").read_text(encoding="utf-8"))
server=FastMCP("arinova-policy")
@server.tool()
def lookup_policy(policy_id:str)->str:
    """Retrieve an exact policy identifier."""
    return json.dumps([d for d in docs if d["id"]==policy_id])
@server.tool()
def list_policies()->str:
    """List policy identifiers and keywords."""
    return json.dumps([{"id":d["id"],"keywords":d["keywords"]} for d in docs])
if __name__=="__main__": server.run(transport="stdio")
