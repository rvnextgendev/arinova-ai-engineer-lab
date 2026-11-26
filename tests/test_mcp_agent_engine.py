import pytest
from backend import mcp_agent_engine as engine

def test_approval_required():
    with pytest.raises(PermissionError):
        engine.build_tools(False)

def test_tool_calls_mcp_and_enforces_budget(monkeypatch):
    seen = []
    def fake(name, args, approved):
        seen.append((name, args, approved))
        return {"content": [{"text": "20"}]}
    monkeypatch.setattr(engine.mcp_demo_client, "call", fake)
    tools, calls = engine.build_tools(True)
    add = next(t for t in tools if t.name == "add_numbers")
    for _ in range(4):
        assert "20" in add.invoke({"a": 12, "b": 8})
    assert len(seen) == 4
    assert all(c["status"] == "completed" for c in calls)
    with pytest.raises(ValueError, match="budget"):
        add.invoke({"a": 12, "b": 8})

def test_failed_call_recorded(monkeypatch):
    def fail(*args):
        raise RuntimeError("test failure")
    monkeypatch.setattr(engine.mcp_demo_client, "call", fail)
    tools, calls = engine.build_tools(True)
    with pytest.raises(RuntimeError):
        tools[0].invoke({"a": 1, "b": 2})
    assert calls[0]["status"] == "failed"
