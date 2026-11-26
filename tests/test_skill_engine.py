import pytest
from backend import skill_engine as s

def test_registry():
    assert len(s.registry()) == 4

def test_unknown_skill():
    with pytest.raises(ValueError):
        s.execute("unknown", "test", "acme", "admin")

def test_hr_delegates(monkeypatch):
    monkeypatch.setattr(s.lab, "authorize", lambda *a: None)
    monkeypatch.setattr(s.lab, "ask", lambda *a: {"answer":"12 days"})
    assert s.execute("hr-policy","How many leaves?","acme","reader")["result"]["answer"] == "12 days"

def test_permission_denied(monkeypatch):
    def deny(*args): raise PermissionError("denied")
    monkeypatch.setattr(s.lab,"authorize",deny)
    with pytest.raises(PermissionError):
        s.execute("database-health","Check database","acme","reader")
