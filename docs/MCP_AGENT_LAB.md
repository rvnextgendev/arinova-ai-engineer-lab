# MCP agent lab
Two opt-in Studio modules use the same bundled MCP server. LangGraph uses a model node, conditional tool routing and ToolNode loop. Deep Agents uses its planner with the same two typed MCP wrappers and StateBackend. Existing RAG and skill endpoints are unchanged.

Select LangGraph MCP agent or Deep Agent MCP in Advanced Module Console. Set approved true and question "Use MCP to add 12 and 8". Expected answer 20, mcp_used true, completed call with actual MCP result. Try "Read the synthetic leave policy using MCP". Set approved false to expect 403. Deep mode requires DEEP_AGENT_ENABLED=true. Ollama model must support tool calling. A model may choose not to call a tool; mcp_used then remains false. No result is marked verified.

Four MCP calls maximum per request, 30-second timeout per MCP exchange, graph recursion limit 16. Approval is a local request flag, not durable identity-based approval. No arbitrary external MCP servers or commands. Deep Agents built-in capabilities are not production sandboxed.

Run pytest tests/test_mcp_agent_engine.py tests/test_mcp_demo.py -v. These tests cover wrappers and stdio, not live model routing. Live acceptance requires both engines, both tools, denied approval, disabled deep engine, tool failure and telemetry. Tests not executed in remote editing environment.
