"""Local policy agent adapters. Run from factory directory or via CLI."""
import argparse
import json
import os
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain_core.tools import tool

def model():
    return ChatOllama(model=os.getenv("ARINOVA_AGENT_MODEL","llama3.2:latest"),base_url=os.getenv("ARINOVA_OLLAMA_URL","http://127.0.0.1:11434"),temperature=0)

def policy_tools(project):
    path=Path(project)/"policies.json"
    docs=json.loads(path.read_text(encoding="utf-8"))
    @tool
    def lookup_policy(policy_id: str) -> str:
        """Retrieve a policy by exact identifier from the selected project."""
        return json.dumps([d for d in docs if d["id"]==policy_id])
    @tool
    def list_policies() -> str:
        """List available policy identifiers and search keywords."""
        return json.dumps([{"id":d["id"],"keywords":d["keywords"]} for d in docs])
    return [lookup_policy,list_policies]

async def run(project,question,engine):
    llm=model()
    tools=policy_tools(project)
    instruction="Use policy tools before answering. Cite returned policy IDs. Do not invent policies or approve requests. Escalate approval requests to a human."
    if engine=="deep":
        from deepagents import create_deep_agent
        from deepagents.backends import StateBackend
        agent=create_deep_agent(model=llm,tools=tools,system_prompt=instruction,backend=StateBackend())
    elif engine=="mcp":
        from langchain_mcp_adapters.client import MultiServerMCPClient
        import sys
        client=MultiServerMCPClient({"policy":{"transport":"stdio","command":sys.executable,"args":[str(Path(__file__).with_name("policy_mcp.py")),str(Path(project).resolve())]}})
        tools=await client.get_tools()
        from langchain.agents import create_agent
        agent=create_agent(llm,tools=tools,system_prompt=instruction)
    else:
        from langchain.agents import create_agent
        agent=create_agent(llm,tools=tools,system_prompt=instruction)
    result=await agent.ainvoke({"messages":[{"role":"user","content":question}]},config={"recursion_limit":20})
    return [{"type":m.type,"content":m.content,"tool_calls":getattr(m,"tool_calls",[])} for m in result["messages"]]

if __name__=="__main__":
    import asyncio
    p=argparse.ArgumentParser();p.add_argument("project");p.add_argument("engine",choices=["langgraph","deep","mcp"]);p.add_argument("question");a=p.parse_args()
    print(json.dumps(asyncio.run(run(a.project,a.question,a.engine)),indent=2,default=str))
