from fastapi.testclient import TestClient
from backend import main

def test_ingest_preview_uses_configured_overlap(monkeypatch):
    monkeypatch.setattr(main.lab, "extract_pdf", lambda path: [(1, "Sample policy text")])
    monkeypatch.setattr(main.lab, "ingest", lambda *args: None)
    client = TestClient(main.app)
    response = client.post("/ingest", files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")}, data={"tenant":"acme","actor":"admin"})
    assert response.status_code == 200, response.text
    assert response.json()["chunk_count"] == 1
