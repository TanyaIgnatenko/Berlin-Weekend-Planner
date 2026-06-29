"""Map the graph's PlannerState into the normalized shape the SPA renders.

The backend owns planning; this module is pure presentation glue. It never
invents venues, weather, or reasoning — every field below is derived from what
the agent actually produced (plan / candidates / weather / validation /
react_log). The one place we add interpretation is turning a free-text `slot`
into a display time, and labelling an indoor-pick-on-a-wet-day honestly.
"""
from __future__ import annotations

from datetime import date as _date
from typing import Optional

# slot keyword -> (display label, default timestamp). The planner emits free
# text like "morning"/"afternoon"/"evening"; dated events may carry a real time.
_SLOTS = {
    "morning": ("MORNING", "09:30"),
    "afternoon": ("AFTERNOON", "14:00"),
    "evening": ("EVENING", "19:00"),
    "night": ("EVENING", "20:00"),
}


def _slot_display(slot: str) -> tuple[str, str]:
    s = (slot or "").strip().lower()
    for key, val in _SLOTS.items():
        if key in s:
            return val
    # already a time like "14:00"? keep it, infer the band.
    if ":" in s:
        hh = int(s.split(":")[0]) if s.split(":")[0].isdigit() else 12
        band = "MORNING" if hh < 12 else "AFTERNOON" if hh < 17 else "EVENING"
        return (band, s)
    return (slot.upper() if slot else "ALL DAY", "")


def _weekday(iso: str) -> str:
    try:
        return _date.fromisoformat(iso).strftime("%A")
    except Exception:
        return iso


def _wx_kind(w: Optional[dict]) -> str:
    if w and w.get("is_wet"):
        return "rain"
    return "sun"


def _wx_readout(w: Optional[dict]) -> str:
    if not w:
        return "UNKNOWN"
    rain, temp = w.get("rain_prob"), w.get("temp_max")
    if rain is None:
        return f"{round(temp)}°" if temp is not None else "UNKNOWN"
    label = "RAIN" if w.get("is_wet") else "SUNNY"
    parts = []
    if w.get("is_wet"):
        parts.append(f"{rain}% RAIN")
    else:
        parts.append("SUNNY")
    if temp is not None:
        parts.append(f"{round(temp)}°")
    return " · ".join(parts)


def serialize_plan(state: dict, *, prev_plan: Optional[list[dict]] = None) -> dict:
    """PlannerState -> PlanResponse dict consumed by the SPA.

    `prev_plan` (a previous list of plan items) lets a refine mark which slots
    actually changed so the UI can show the green "Updated." callout.
    """
    spec = state.get("spec", {}) or {}
    weather = state.get("weather", {}) or {}
    by_name = {v["name"]: v for v in state.get("candidates", [])}
    validation = state.get("validation", {}) or {}
    max_per_day = spec.get("max_per_day", 3)

    prev_by_key = {}
    for it in (prev_plan or []):
        prev_by_key[(it.get("date"), it.get("slot"))] = it.get("venue")

    # group plan items into day columns, preserving plan order within a day
    days_order: list[str] = []
    day_slots: dict[str, list[dict]] = {}
    total_cost = 0.0

    for item in state.get("plan", []):
        d = item.get("date")
        if d not in day_slots:
            day_slots[d] = []
            days_order.append(d)
        v = by_name.get(item.get("venue"), {})
        label, ts = _slot_display(item.get("slot", ""))
        cost = float(v.get("cost", 0) or 0)
        total_cost += cost
        w = weather.get(d)
        indoor = bool(v.get("indoor"))
        # honest weather annotation: an indoor pick on a wet day is the agent's
        # weather-aware behaviour. We do NOT claim a specific A->B swap in real
        # mode (seed mode does that); we surface the truthful note.
        weather_swap = bool(w and w.get("is_wet") and indoor)
        changed = (
            (d, item.get("slot")) in prev_by_key
            and prev_by_key[(d, item.get("slot"))] != item.get("venue")
        )
        day_slots[d].append({
            "time": label,
            "timestamp": ts,
            "venue": {
                "name": v.get("name", item.get("venue")),
                "type": v.get("type", ""),
                "area": v.get("area", ""),
                "indoor": indoor,
                "hours": v.get("hours"),
                "date": v.get("date"),
                "cost": cost,
            },
            "why": item.get("reason", ""),
            "swapped": weather_swap,
            "swapNote": (
                "Weather-aware: indoor pick for a wet day — kept you covered."
                if weather_swap else None
            ),
            "changed": changed,
            "changeNote": "Updated by your refine." if changed else None,
        })

    days = [{
        "label": _weekday(d),
        "date": d,
        "wx": _wx_kind(weather.get(d)),
        "weatherReadout": _wx_readout(weather.get(d)),
        "weather": weather.get(d) or {},
        "slots": day_slots[d],
    } for d in days_order]

    violations = validation.get("violations", []) or []
    repeat_violation = any(v.get("rule") == "repeat_type" for v in violations)
    max_n = max((len(s) for s in day_slots.values()), default=0)
    swaps = sum(1 for d in day_slots.values() for s in d if s["swapped"])

    constraints = {
        "ok": validation.get("ok", False),
        "perDay": f"{max_n} / {max_per_day} per day",
        "perDayMet": max_n <= max_per_day,
        "noRepeat": bool(spec.get("avoid_repeat_types", True)),
        "noRepeatMet": not repeat_violation,
        "weatherChecked": all(d in weather for d in days_order) and bool(days_order),
        "swaps": swaps,
        "violations": violations,
    }

    return {
        "request": state.get("request", ""),
        "spec": spec,
        "days": days,
        "constraints": constraints,
        "costPerPerson": round(total_cost, 2),
        "steps": build_timeline(state),
        "agentLog": build_agent_log(state),
        "final": state.get("final", ""),
        "bestEffort": not validation.get("ok", True),
    }


def build_timeline(state: dict) -> list[dict]:
    """The thinking-timeline steps, derived from REAL agent output.

    Each step's detail is filled from the actual spec / weather / react_log /
    validation, so the timeline reflects what the agent did rather than a
    scripted narrative.
    """
    spec = state.get("spec", {}) or {}
    weather = state.get("weather", {}) or {}
    log = state.get("react_log", []) or []
    validation = state.get("validation", {}) or {}
    iterations = state.get("iterations", 0)

    steps: list[dict] = []

    liked = ", ".join(spec.get("liked_types", []) or []) or "anything"
    steps.append({
        "key": "parse",
        "title": "Parsing your request",
        "detail": (f"{', '.join(spec.get('dates', []) or ['this weekend'])} · "
                   f"{liked} · max {spec.get('max_per_day', 3)}/day · "
                   f"{'no repeated types' if spec.get('avoid_repeat_types', True) else 'repeats ok'}"),
    })

    if weather:
        wx = " · ".join(f"{d} → {_wx_readout(w)}" for d, w in weather.items())
        steps.append({"key": "weather", "title": "Checking live weather",
                      "detail": wx})

    # surface the agent's real reasoning + tool calls from the react trace
    thoughts = [e.get("thought") for e in log if e.get("thought")]
    if thoughts:
        steps.append({"key": "reason", "title": "Reasoning about conditions",
                      "detail": thoughts[-1][:160]})

    searches = [e for e in log if e.get("action") == "search_venues"]
    if searches:
        n = len(state.get("candidates", []) or [])
        steps.append({"key": "gather", "title": "Gathering options",
                      "detail": f"{len(searches)} searches → {n} candidate venues"})

    n_stops = len(state.get("plan", []) or [])
    steps.append({"key": "plan", "title": "Building the schedule",
                  "detail": f"{n_stops} stops sequenced across the weekend"})

    viol = validation.get("violations", []) or []
    if validation:
        steps.append({
            "key": "validate", "title": "Validating constraints",
            "detail": ("all constraints satisfied" if validation.get("ok")
                       else f"{len(viol)} issue(s) found"),
        })

    if iterations:
        steps.append({"key": "fix", "title": f"Fixing {iterations} replan(s)",
                      "detail": "re-planned to resolve violations"})

    return steps


def build_agent_log(state: dict) -> list[dict]:
    """Completed-step list for the sticky Agent panel (from the react trace)."""
    out = []
    for e in state.get("react_log", []) or []:
        action = e.get("action") or "think"
        thought = e.get("thought") or ""
        out.append({"title": action, "detail": thought[:120]})
    return out
