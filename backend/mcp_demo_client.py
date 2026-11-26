"""Bounded local MCP client using a fixed, trusted stdio server."""
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ALLOWED = frozenset({"add_numbers", "sample_leave_policy"})

async def _exchange(name=None, arguments=None):
    async with asyncio.timeout(30):
        params = StdioServerParameters(command=sys.executable, args=["-m", "backend.mcp_demo_server"])
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                if name is None:
                    result = await session.list_tools()
                    return [{"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
                            for t in result.tools if t.name in ALLOWED]
                result = await session.call_tool(name, arguments=arguments)
                if result.isError:
                    raise ValueError("MCP tool rejected the arguments")
                return result.model_dump(mode="json")

def discover():
    return asyncio.run(_exchange())

def call(name, arguments, approved):
    if not approved or name not in ALLOWED:
        raise PermissionError("MCP tool execution requires approval and an allowlisted tool")
    return asyncio.run(_exchange(name, arguments))
