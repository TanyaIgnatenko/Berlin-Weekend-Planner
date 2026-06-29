"""The graph's shared state. Every node reads/writes this dict."""
from __future__ import annotations

from typing import Optional, TypedDict


class PlannerState(TypedDict, total=False):
    request: str                 # raw user text
    spec: dict                   # PlanRequest.model_dump()
    weather: dict                # {date: weather_dict}
    candidates: list[dict]       # venues gathered by the ReAct node
    react_log: list[dict]        # think/act/observe trace (also useful for Phoenix)
    plan: list[dict]             # list of PlanItem.model_dump()
    validation: dict             # ValidationResult.model_dump()
    feedback: str                # what replan tells plan to fix
    iterations: int              # replan counter
    final: str                   # formatted output
