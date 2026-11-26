import pytest
from backend.deep_agent_engine import enabled, execute_deep

def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("DEEP_AGENT_ENABLED", raising=False)
    assert not enabled()
    with pytest.raises(PermissionError):
        execute_deep("test", "acme", "reader")

def test_explicit_enable(monkeypatch):
    monkeypatch.setenv("DEEP_AGENT_ENABLED", "true")
    assert enabled()

@pytest.mark.parametrize("value", ["false", "0", "invalid"])
def test_fail_closed(monkeypatch, value):
    monkeypatch.setenv("DEEP_AGENT_ENABLED", value)
    assert not enabled()


def test_disabled_does_not_import_optional_runtime(monkeypatch):
    import sys
    monkeypatch.setenv("DEEP_AGENT_ENABLED", "false")
    monkeypatch.setitem(sys.modules, "deepagents", None)
    with pytest.raises(PermissionError):
        execute_deep("test", "acme", "reader")
