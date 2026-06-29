"""Phoenix tracing setup (the Mercanis 'observability / evaluation' bullet).

Call init_tracing() once at startup. It auto-instruments LiteLLM so every model
call becomes a span; node-level timing comes from the graph. Designed to fail
open — if Phoenix isn't installed/running, the planner still works untraced.

Run Phoenix locally first:   python -m phoenix.server.main serve
Then open http://localhost:6006 to inspect traces.
"""
from __future__ import annotations


def init_tracing(project_name: str = "berlin-weekend-planner") -> bool:
    try:
        from phoenix.otel import register
        from openinference.instrumentation.litellm import LiteLLMInstrumentor

        tracer_provider = register(project_name=project_name, auto_instrument=True)
        LiteLLMInstrumentor().instrument(tracer_provider=tracer_provider)
        print(f"[phoenix] tracing on -> project '{project_name}'")
        return True
    except Exception as e:  # not installed / server down — keep running
        print(f"[phoenix] tracing off ({e})")
        return False
