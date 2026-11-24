"""Request-scoped local telemetry; never stores prompts or document text."""
from contextvars import ContextVar
from time import perf_counter
from functools import wraps
events = ContextVar("events", default=None)
def emit(name, **fields):
    target = events.get()
    if target is not None:
        target.append({"name":name, **fields})
def measured(name, fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        status = "ok"
        try:
            return fn(*args, **kwargs)
        except Exception:
            status = "error"
            raise
        finally:
            emit(name, status=status, milliseconds=round((perf_counter()-start)*1000,2))
    return wrapper
