"""Local synthetic MCP server; no database, filesystem or network tools."""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AriNova learning tools")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two integers without an LLM."""
    return a + b

@mcp.tool()
def sample_leave_policy() -> str:
    """Return synthetic training policy, not actual company policy."""
    return "Synthetic demo policy: 12 casual leave days per year."

if __name__ == "__main__":
    mcp.run(transport="stdio")
