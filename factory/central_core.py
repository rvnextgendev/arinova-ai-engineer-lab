"""Versioned capability inventory. Status describes source availability, not certification."""
VERSION="0.1.0"
CATALOG={
"local_model":("Local Ollama",(),"adapter","runtime_template.py"),
"rag":("PDF hybrid retrieval",("local_model",),"adapter","policy_hybrid.py"),
"langgraph":("LangGraph agent",("rag",),"adapter","policy_agents.py"),
"deep_agents":("Deep Agents",("rag",),"adapter","policy_agents.py"),
"mcp":("MCP tools",("rag",),"adapter","policy_mcp.py"),
"evaluation":("LLM judge",("rag",),"adapter","policy_compare.py"),
"guardrails":("Prompt and masking exercises",(),"demo","architect_labs.py"),
"observability":("Execution callbacks",(),"adapter","policy_agents.py"),
"human_approval":("Snapshot approval",(),"adapter","policy_delivery.py"),
"retry":("Retry and DLQ simulation",(),"demo","core_preview.py"),
"skills":("Skill registry",(),"planned",""),
"rbac":("Enforced authorization",(),"planned",""),
"checkpointing":("Durable checkpointing",(),"planned",""),
"model_gateway":("Central model gateway",(),"planned","")}
def resolve(selected):
    result=[]
    def visit(key):
        if key not in CATALOG:raise ValueError("Unknown capability: "+key)
        if key in result:return
        for dep in CATALOG[key][1]:visit(dep)
        result.append(key)
    for key in selected:visit(key)
    return result
def catalog():
    return [{"id":k,"name":v[0],"dependencies":list(v[1]),"status":v[2],"source":v[3]} for k,v in CATALOG.items()]
