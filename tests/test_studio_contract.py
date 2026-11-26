"""Static regression checks for Studio UI contracts; not browser tests."""
from pathlib import Path

STUDIO = (Path(__file__).resolve().parents[1] / "backend" / "studio.html").read_text(encoding="utf-8")

def test_request_timeout_cleanup():
    assert "new AbortController()" in STUDIO
    assert "finally{clearTimeout(timer)}" in STUDIO

def test_comparison_reports_errors():
    assert "partialFailure:!!(results.standard.error||results.deep.error)" in STUDIO
    assert "Comparison finished with errors" in STUDIO
    assert "standard:results.standard,deep:results.deep" in STUDIO

def test_auto_clears_selection():
    assert "document.querySelectorAll('.skill').forEach(x=>x.classList.remove('active'));selected={id:'auto'}" in STUDIO

def test_input_and_busy_feedback():
    assert "Enter a request and tenant before executing." in STUDIO
    assert "Another request is running. Please wait." in STUDIO

def test_availability_error_is_distinct():
    assert "Unable to check Deep Agent availability:" in STUDIO
