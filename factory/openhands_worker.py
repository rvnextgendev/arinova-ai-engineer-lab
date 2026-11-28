"""OpenHands SDK worker, executed inside a dedicated Docker container."""
import os
from pathlib import Path
from openhands.sdk import LLM, Agent, Conversation, Tool
from openhands.tools.terminal import TerminalTool
from openhands.tools.file_editor import FileEditorTool

def main():
    llm=LLM(model=os.environ["ARINOVA_OPENHANDS_MODEL"],base_url=os.environ["ARINOVA_OPENHANDS_URL"],api_key="local-ollama")
    agent=Agent(llm=llm,tools=[Tool(name=TerminalTool.name),Tool(name=FileEditorTool.name)])
    conversation=Conversation(agent=agent,workspace="/workspace")
    task=Path("/workspace/agent-task.md").read_text(encoding="utf-8")
    conversation.send_message("Work only in /workspace. Do not deploy or push. Implement and test this requirement:\n"+task)
    conversation.run()
if __name__=="__main__": main()
