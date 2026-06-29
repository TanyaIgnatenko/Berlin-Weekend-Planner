"""Offline seed scenario — the design's sample weekend, with NO LLM/network.

This is the *only* place hardcoded venues / scripted reasoning live. It exists
so the SPA runs and demos reliably without an API key (and so the signature
"weather swap" beat is guaranteed for a portfolio walkthrough). It is never
mixed with real agent output: the API picks seed XOR real per request.

Mirrors the contract that `serialize.serialize_plan` produces, so the frontend
renders both paths through one code path.
"""
from __future__ import annotations

import copy


def _v(name, type_, area, indoor, hours=None, date=None, cost=0.0):
    return {"name": name, "type": type_, "area": area, "indoor": indoor,
            "hours": hours, "date": date, "cost": cost}


def _slot(time, ts, venue, why, swapped=False, swapNote=None,
          changed=False, changeNote=None):
    return {"time": time, "timestamp": ts, "venue": venue, "why": why,
            "swapped": swapped, "swapNote": swapNote,
            "changed": changed, "changeNote": changeNote}


def seed_plan(request: str = "") -> dict:
    """The default rainy-Saturday / sunny-Sunday plan from the design."""
    sat_slots = [
        _slot("MORNING", "09:30",
              _v("Pergamonmuseum", "museum", "Mitte", True, "10:00–18:00", cost=14),
              "Indoor heavy-hitter for a wet morning — your museum pick, dry and central."),
        _slot("AFTERNOON", "14:00",
              _v("Sea Life Berlin", "aquarium", "Mitte", True, "10:00–19:00", cost=20),
              "Stays indoors while it rains, and an aquarium isn't a repeat of the museum.",
              swapped=True,
              swapNote="Weather swap. Schlachtensee (lake) → Sea Life Berlin. "
                       "Your lake moves to Sunday when it's dry."),
        _slot("EVENING", "19:00",
              _v("Markthalle Neun Street Food", "food", "Kreuzberg", True, "Sat til 22:00",
                 date="2026-07-04", cost=15),
              "Covered street-food hall — dinner that doesn't care about the rain."),
    ]
    sun_slots = [
        _slot("MORNING", "10:00",
              _v("Schlachtensee", "lake", "Zehlendorf", False, "open", cost=0),
              "Your lake, now on the sunny day — best swimming 10:00–16:00."),
        _slot("AFTERNOON", "14:30",
              _v("Tempelhofer Feld", "park", "Tempelhof", False, "open", cost=0),
              "Wide-open park while the sun holds — different type from the lake, no repeat."),
        _slot("EVENING", "20:00",
              _v("Waldbuehne Open-Air Concert", "openair", "Westend", False,
                 date="2026-07-05", cost=55),
              "Open-air concert pinned to its real date, 5 Jul — outdoor finish on the dry day."),
    ]

    days = [
        {"label": "Saturday", "date": "2026-07-04", "wx": "rain",
         "weatherReadout": "70% RAIN · 18°",
         "weather": {"rain_prob": 70, "temp_max": 18, "is_wet": True},
         "slots": sat_slots},
        {"label": "Sunday", "date": "2026-07-05", "wx": "sun",
         "weatherReadout": "SUNNY · 26°",
         "weather": {"rain_prob": 10, "temp_max": 26, "is_wet": False},
         "slots": sun_slots},
    ]

    return _assemble(request or "Plan my weekend 4–5 July 2026. I like museums "
                     "and lakes, max 3 things per day, no repeated types.", days)


def _assemble(request: str, days: list[dict]) -> dict:
    total = sum(s["venue"]["cost"] for d in days for s in d["slots"])
    max_n = max((len(d["slots"]) for d in days), default=0)
    swaps = sum(1 for d in days for s in d["slots"] if s["swapped"])
    return {
        "request": request,
        "spec": {"dates": ["2026-07-04", "2026-07-05"],
                 "liked_types": ["museum", "lake"], "max_per_day": 3,
                 "avoid_repeat_types": True},
        "days": days,
        "constraints": {
            "ok": True, "perDay": f"{max_n} / 3 per day", "perDayMet": True,
            "noRepeat": True, "noRepeatMet": True, "weatherChecked": True,
            "swaps": swaps, "violations": [],
        },
        "costPerPerson": round(total, 2),
        "steps": SEED_STEPS,
        "agentLog": SEED_LOG,
        "final": "",
        "bestEffort": False,
    }


# The design's 7 thinking steps (seed only — real runs derive these live).
SEED_STEPS = [
    {"key": "parse", "title": "Parsing your request",
     "detail": "Sat–Sun 4–5 Jul · museums + lakes · max 3/day · no repeated types · avoid repeats"},
    {"key": "weather", "title": "Checking live weather",
     "detail": "Sat → 70% rain, 18° · Sun → sunny, 26°"},
    {"key": "reason", "title": "Reasoning about conditions",
     "detail": "Saturday is wet → favour indoor, push the lake to sunny Sunday"},
    {"key": "find", "title": "Finding indoor alternatives",
     "detail": "Schlachtensee (lake) → Sea Life Berlin for Sat afternoon"},
    {"key": "plan", "title": "Building the schedule",
     "detail": "6 stops sequenced across morning / afternoon / evening"},
    {"key": "validate", "title": "Validating constraints",
     "detail": "3/3 per day · no repeated types · Waldbühne pinned to 5 Jul"},
    {"key": "fix", "title": "Fixing 1 issue",
     "detail": "Sat evening was a 2nd museum → replaced with a covered market"},
]

SEED_LOG = [
    {"title": "get_weather", "detail": "Sat 70% rain → wet; Sun sunny"},
    {"title": "search_venues", "detail": "indoor museums + aquarium for the wet day"},
    {"title": "search_venues", "detail": "outdoor lakes + parks for the dry day"},
    {"title": "finish", "detail": "enough candidates to build a balanced plan"},
]


# --------------------------------------------------------------------------- #
# Seed refine — the README's intent -> effect map (offline / keyless path).    #
# --------------------------------------------------------------------------- #
def seed_refine(plan: dict, message: str) -> dict:
    """Apply a refine to a seed plan. Returns {reply, plan}.

    Free text is matched case-insensitively against keyword groups, exactly as
    the design specifies. Real mode (api.app) instead re-runs the agent.
    """
    text = (message or "").lower()
    plan = copy.deepcopy(plan)
    days = plan["days"]

    def find_slot(day_idx, pred):
        for s in days[day_idx]["slots"]:
            if pred(s):
                return s
        return None

    if any(k in text for k in ("cheap", "budget", "less", "afford")):
        slot = find_slot(1, lambda s: s["venue"]["name"].startswith("Waldbuehne"))
        if slot:
            slot["venue"] = _v("Freiluftkino Friedrichshain", "openair",
                               "Friedrichshain", False, date="2026-07-05", cost=9.5)
            slot["why"] = "Open-air cinema — same outdoor evening, a fraction of the price."
            slot["changed"] = True
            slot["changeNote"] = "Updated. Swapped the concert for an open-air cinema."
            slot["swapped"] = False
            slot["swapNote"] = None
        plan = _recompute(plan)
        plan["reply"] = (f"Done — swapped the €55 concert for an open-air cinema "
                         f"(€9.50). Weekend total drops to about €{plan['costPerPerson']:.0f}/person.")
        return plan

    if "sunday afternoon" in text or ("swap" in text and "sunday" in text):
        slot = find_slot(1, lambda s: s["time"] == "AFTERNOON")
        if slot:
            slot["venue"] = _v("Badeschiff", "pool", "Kreuzberg", False,
                               "10:00–23:00", cost=7)
            slot["why"] = "River pool — still outdoor, and a pool isn't a repeat of the lake."
            slot["changed"] = True
            slot["changeNote"] = "Updated. Sunday afternoon → Badeschiff."
        plan = _recompute(plan)
        plan["reply"] = ("Swapped Sunday afternoon to Badeschiff — kept it outdoor "
                         "and checked it doesn't repeat the lake.")
        return plan

    if any(k in text for k in ("more outdoor", "outside", "outdoor", "sun ")):
        plan["reply"] = ("Heads up: Saturday is still 70% rain, so forcing it "
                         "outdoors means wet plans. Sunday is already fully "
                         "outdoor. Want me to risk Saturday anyway, or keep it covered?")
        return plan

    plan["reply"] = ("Re-ran the planner with that. Everything still satisfies "
                     "your constraints — nothing needed to change.")
    return plan


def _recompute(plan: dict) -> dict:
    days = plan["days"]
    plan["costPerPerson"] = round(
        sum(s["venue"]["cost"] for d in days for s in d["slots"]), 2)
    plan["constraints"]["swaps"] = sum(
        1 for d in days for s in d["slots"] if s["swapped"])
    return plan
