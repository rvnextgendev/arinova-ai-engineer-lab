"""Real stdio protocol integration tests; no Ollama or database required."""
import pytest
from backend import mcp_demo_client as client

def test_discovery():
    tools = client.discover()
    assert {t["name"] for t in tools} == {"add_numbers", "sample_leave_policy"}
    assert all("inputSchema" in t for t in tools)

def test_call():
    result = client.call("add_numbers", {"a": 12, "b": 8}, True)
    assert not result.get("isError")
    assert any(c.get("text") == "20" for c in result["content"])

@pytest.mark.parametrize("name,approved", [("add_numbers", False), ("unknown", True)])
def test_denied(name, approved):
    with pytest.raises(PermissionError):
        client.call(name, {}, approved)
