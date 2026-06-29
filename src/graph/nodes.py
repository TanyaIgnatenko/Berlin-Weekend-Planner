"""The six nodes of the planner graph.

Genuinely agentic part = `react_gather`: the model decides which tool to call
and when to stop. Everything else is deterministic plumbing or a single LLM
shaping step. The replan loop is the self-correction contour that makes this an
agent rather than a one-shot RAG pipeline.

Where you write your real logic is marked TODO. The skeleton runs end-to-end
with the naive versions below.
"""
from __future__ import annotations

import json

from src.graph.state import PlannerState
from src.llm import llm, llm_json
from src.schema import PlanRequest, ValidationResult, Violation
from src.tools.venues import all_types, search_venues
from src.tools.weather import get_weather

MAX_REACT_STEPS = 8
MAX_REPLANS = 3


# --------------------------------------------------------------------------- #
# 1. parse_request : free text -> PlanRequest                                  #
# --------------------------------------------------------------------------- #
def parse_request(state: PlannerState) -> PlannerState:
    sys = ("Extract a Berlin weekend plan request. Fields: dates (ISO), "
           f"liked_types and disliked_types (from {all_types()}), "
           "preferred_areas, max_per_day (int), avoid_repeat_types (bool), notes.")
    # TODO: harden the prompt / add few-shot examples for messy inputs.
    data = llm_json(f"User request:\n{state['request']}", system=sys, heavy=False)
    spec = PlanRequest(**{k: v for k, v in data.items()
                          if k in PlanRequest.model_fields})
    return {"spec": spec.model_dump(), "iterations": 0, "weather": {},
            "candidates": [], "react_log": []}


# --------------------------------------------------------------------------- #
# 2. react_gather : the agentic node (think -> act -> observe -> repeat -> stop)#
# --------------------------------------------------------------------------- #
_REACT_SYS = """You are gathering options for a Berlin weekend plan.
You have these tools:
  search_venues(type?, indoor?, area?, date?) -> list of venues
  get_weather(date) -> {rain_prob, temp_max, is_wet}
On each step reply with ONE json object:
  {"thought": "...", "action": "search_venues", "args": {...}}
  {"thought": "...", "action": "get_weather", "args": {"date": "YYYY-MM-DD"}}
  {"thought": "...", "action": "finish"}   when you have enough good candidates.
Reason about weather BEFORE committing to outdoor options. Stop early once you
have a few viable candidates per requested day. Reply with ONLY the json."""

_TOOLS = {"search_venues": search_venues, "get_weather": get_weather}


def react_gather(state: PlannerState) -> PlannerState:
    spec = state["spec"]
    log: list[dict] = []
    candidates: dict[str, dict] = {}
    weather: dict[str, dict] = dict(state.get("weather", {}))

    context = f"Request spec: {json.dumps(spec)}\n"
    for step in range(MAX_REACT_STEPS):
        try:
            decision = llm_json(context + "\nNext step?", system=_REACT_SYS, heavy=True)
        except Exception as e:
            log.append({"step": step, "error": str(e)})
            break

        action = decision.get("action")
        log.append({"step": step, "thought": decision.get("thought"),
                    "action": action, "args": decision.get("args")})

        if action == "finish" or action not in _TOOLS:
            break

        # --- act + observe ---
        args = decision.get("args", {}) or {}
        try:
            result = _TOOLS[action](**args)
        except TypeError as e:
            context += f"\nOBSERVATION: bad args for {action}: {e}"
            continue

        if action == "get_weather":
            weather[args.get("date", "?")] = result
            context += f"\nOBSERVATION weather: {json.dumps(result)}"
        else:  # search_venues
            for v in result:
                candidates[v["name"]] = v
            context += f"\nOBSERVATION venues: {json.dumps(result)[:1500]}"

    # TODO: you may want react_gather to loop back here if it gathered too few.
    return {"candidates": list(candidates.values()),
            "weather": weather, "react_log": log}


# --------------------------------------------------------------------------- #
# 3. plan : assemble gathered candidates into a schedule (grounded)            #
# --------------------------------------------------------------------------- #
def plan(state: PlannerState) -> PlannerState:
    spec, cands = state["spec"], state["candidates"]
    feedback = state.get("feedback", "")
    sys = ("Build a Berlin weekend schedule. Use ONLY venues from the candidate "
           "list (ground every item — never invent a venue). Output json: "
           '{"plan":[{"date","slot","venue","reason"}]}. '
           f"Respect max_per_day={spec.get('max_per_day', 3)} and "
           f"avoid_repeat_types={spec.get('avoid_repeat_types', True)}.")
    prompt = (f"Spec: {json.dumps(spec)}\nCandidates: {json.dumps(cands)}\n"
              f"Weather: {json.dumps(state.get('weather', {}))}\n")
    if feedback:
        prompt += f"\nFix these problems from the last attempt:\n{feedback}"
    # TODO: tune this prompt; this is the shaping step, not the agentic one.
    out = llm_json(prompt, system=sys, heavy=True)
    return {"plan": out.get("plan", [])}


# --------------------------------------------------------------------------- #
# 4. validate : DETERMINISTIC constraint checks (no LLM here on purpose)        #
# --------------------------------------------------------------------------- #
def validate(state: PlannerState) -> PlannerState:
    by_name = {v["name"]: v for v in state["candidates"]}
    weather = state.get("weather", {})
    spec = state["spec"]
    violations: list[Violation] = []

    per_day_types: dict[str, list[str]] = {}
    per_day_count: dict[str, int] = {}

    for item in state["plan"]:
        v = by_name.get(item["venue"])
        if v is None:
            violations.append(Violation(item=item["venue"], rule="ungrounded",
                              detail="venue not in gathered candidates"))
            continue

        d = item["date"]
        per_day_count[d] = per_day_count.get(d, 0) + 1
        per_day_types.setdefault(d, []).append(v["type"])

        # rain vs outdoor
        w = weather.get(d)
        if v["indoor"] is False and w and w.get("is_wet"):
            violations.append(Violation(item=v["name"], rule="weather",
                              detail=f"outdoor on wet day ({w.get('rain_prob')}% rain)"))

        # dated event must match the day
        if v.get("date") and v["date"] != d:
            violations.append(Violation(item=v["name"], rule="date",
                              detail=f"event is on {v['date']}, scheduled on {d}"))

    # max per day
    for d, n in per_day_count.items():
        if n > spec.get("max_per_day", 3):
            violations.append(Violation(item=d, rule="max_per_day",
                              detail=f"{n} > {spec.get('max_per_day', 3)}"))

    # no repeated types within a day
    if spec.get("avoid_repeat_types", True):
        for d, types in per_day_types.items():
            dupes = {t for t in types if types.count(t) > 1}
            for t in dupes:
                violations.append(Violation(item=d, rule="repeat_type",
                                  detail=f"type '{t}' repeated"))

    res = ValidationResult(ok=not violations, violations=violations)
    return {"validation": res.model_dump()}


# --------------------------------------------------------------------------- #
# 5. replan : turn violations into feedback, bump the counter                  #
# --------------------------------------------------------------------------- #
def replan(state: PlannerState) -> PlannerState:
    vs = state["validation"]["violations"]
    fb = "; ".join(f"[{v['rule']}] {v['item']}: {v['detail']}" for v in vs)
    return {"feedback": fb, "iterations": state.get("iterations", 0) + 1}


# --------------------------------------------------------------------------- #
# 6. finalize : format the accepted plan + rationale                          #
# --------------------------------------------------------------------------- #
def finalize(state: PlannerState) -> PlannerState:
    plan, val = state["plan"], state["validation"]
    status = "OK" if val["ok"] else f"BEST EFFORT ({len(val['violations'])} issues left)"
    lines = [f"Berlin weekend plan [{status}]", ""]
    for it in plan:
        lines.append(f"  {it['date']} {it['slot']}: {it['venue']}"
                     + (f" — {it.get('reason','')}" if it.get("reason") else ""))
    return {"final": "\n".join(lines)}


# --------------------------------------------------------------------------- #
# conditional edge after validate                                             #
# --------------------------------------------------------------------------- #
def route_after_validate(state: PlannerState) -> str:
    if state["validation"]["ok"] or state.get("iterations", 0) >= MAX_REPLANS:
        return "finalize"
    return "replan"
