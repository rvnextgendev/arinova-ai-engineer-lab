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


def test_enabled_agent_uses_backend_instance(monkeypatch):
    from types import SimpleNamespace
    import deepagents
    from deepagents.backends import StateBackend
    import langchain_ollama
    from learning import arinova_architect_master_annotated as lab
    monkeypatch.setenv("DEEP_AGENT_ENABLED", "true")
    monkeypatch.setattr(lab, "authorize", lambda *args: None)
    monkeypatch.setattr(lab, "validate_question", lambda q: q)
    monkeypatch.setattr(langchain_ollama, "ChatOllama", lambda **kwargs: object())
    def create(**kwargs):
        assert isinstance(kwargs["backend"], StateBackend)
        return SimpleNamespace(invoke=lambda *args, **kw: {"messages": [SimpleNamespace(content="test answer")]})
    monkeypatch.setattr(deepagents, "create_deep_agent", create)
    result = execute_deep("How many casual leaves?", "acme", "reader", "hr-policy")
    assert result["answer"] == "test answer"
    assert result["verified"] is False
