"""Bounded, process-local live traces for the loopback learning studio."""
from collections import OrderedDict
from threading import Lock
from time import monotonic
from uuid import UUID

_lock = Lock()
_runs = OrderedDict()
MAX_RUNS = 64
MAX_EVENTS = 256

def valid_id(value):
    try:
        return str(UUID(value, version=None)) == value
    except (ValueError, TypeError, AttributeError):
        return False

def start(key):
    with _lock:
        if key in _runs:
            return False
        if len(_runs) >= MAX_RUNS:
            finished = next((k for k,v in _runs.items() if v["done"]), None)
            if finished is None:
                return False
            del _runs[finished]
        _runs[key] = {"start": monotonic(), "events": [], "done": False}
        return True

def publish(key, name, **fields):
    # No prompts, document content, tool arguments or chunk identifiers.
    safe = {k:v for k,v in fields.items() if k in {
        "status","milliseconds","attempt","model","input_tokens","output_tokens",
        "count","dimensions","tool_name","skill","tool_calls"} and
        isinstance(v,(str,int,float,bool,type(None)))}
    for k in ("vector","keyword","fused"):
        if isinstance(fields.get(k),list):
            safe[k+"_count"] = len(fields[k])
    with _lock:
        run = _runs.get(key)
        if run is not None and not run["done"] and len(run["events"]) < MAX_EVENTS:
            run["events"].append({"name":name,"elapsed_ms":round((monotonic()-run["start"])*1000),**safe})

def finish(key, status):
    publish(key,"request_finished",status=status)
    with _lock:
        if key in _runs:
            _runs[key]["done"] = True
            _runs[key]["http_status"] = status

def snapshot(key):
    with _lock:
        run = _runs.get(key)
        if run is None:
            return None
        return {"done":run["done"],"http_status":run.get("http_status"),
                "events":[dict(e) for e in run["events"]]}
