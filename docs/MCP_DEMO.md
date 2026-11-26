# Local MCP demo

The Studio MCP discovery endpoint now starts a bundled FastMCP server over stdio using the current Python interpreter. No ARINOVA_MCP_COMMAND or external credentials are required. Select MCP discovery to see tool names and input schemas. Select MCP call (approved demo), review the arguments and change approved to true, then execute. add_numbers with 12 and 8 returns 20. sample_leave_policy returns synthetic training data, not Evolutyz policy.

The fixed server exposes only two read-only synthetic tools. Calls require an explicit approval flag and allowlist; this is a local demo, not authenticated human approval or production sandboxing. Existing external MCP helpers in learning remain unchanged and require explicit environment configuration. The new endpoints do not automatically give MCP tools to either agent engine.

Run: docker compose exec -T api python -m pytest tests/test_mcp_demo.py -v

Validation status: integration tests added, not executed in the remote editing environment.
