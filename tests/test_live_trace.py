from backend import live_trace
from learning import telemetry
from uuid import uuid4
import pytest

def test_live_events_and_privacy():
    key = str(uuid4())
    assert live_trace.start(key)
    assert not live_trace.start(key)
    token = telemetry.live_sink.set(lambda name, **kw: live_trace.publish(key,name,**kw))
    try:
        def work():
            telemetry.emit("retrieval_ranks", vector=["private-id"], prompt="private text")
            assert not live_trace.snapshot(key)["done"]
            return 42
        assert telemetry.measured("retrieve",work)() == 42
    finally:
        telemetry.live_sink.reset(token)
        live_trace.finish(key,200)
    result = live_trace.snapshot(key)
    assert result["done"]
    assert [e["name"] for e in result["events"]] == ["retrieve","retrieval_ranks","retrieve","request_finished"]
    assert result["events"][1]["vector_count"] == 1
    assert "private" not in str(result)

def test_failed_node():
    key = str(uuid4())
    assert live_trace.start(key)
    token = telemetry.live_sink.set(lambda name, **kw: live_trace.publish(key,name,**kw))
    try:
        def fail():
            raise ValueError("failure")
        with pytest.raises(ValueError):
            telemetry.measured("generate",fail)()
        assert live_trace.snapshot(key)["events"][-1]["status"] == "error"
    finally:
        telemetry.live_sink.reset(token)
        live_trace.finish(key,500)
