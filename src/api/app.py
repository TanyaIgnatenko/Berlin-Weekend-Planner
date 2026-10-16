"""FastAPI surface over the LangGraph planner.

This is the ONLY web layer in the project and it is purely additive — it wraps
the existing `build_graph()` and does not change agent behaviour. Endpoints:

    GET  /api/health           liveness
    GET  /api/config           {seedMode, hasKey} so the SPA can show its mode
    POST /api/plan             SSE stream: real graph progress -> final plan
    POST /api/refine           re-run the agent with the refine message, JSON

Mode selection (seed XOR real), decided per process at request time:
  * seed mode  -> no LLM/network; serves src/api/seed.py (the design scenario).
                  Active when PLANNER_SEED_MODE is truthy OR no ANTHROPIC_API_KEY.
  * real mode  -> drives the actual LangGraph agent + live Open-Meteo weather.

Run:  uvicorn src.api.app:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.api import seed as seedmod
from src.api.serialize import build_timeline, serialize_plan

app = FastAPI(title="Berlin Weekend Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"


def seed_mode() -> bool:
    if os.getenv("PLANNER_SEED_MODE", "").lower() in ("1", "true", "yes", "on"):
        return True
    return not os.getenv("ANTHROPIC_API_KEY")


# --------------------------------------------------------------------------- #
# cost guard — simple in-memory rate limit on the paid (real-mode) endpoints. #
# Real mode spends tokens per request on a public endpoint, so cap abuse:      #
# per-IP sliding window + a global daily ceiling. Seed mode is free -> skip.   #
# Single-instance in-memory state is fine for this deploy; swap for Redis if   #
# you ever run multiple replicas. All limits are env-tunable.                  #
# --------------------------------------------------------------------------- #
_RATE_MAX = int(os.getenv("RATE_LIMIT_MAX", "10"))             # requests / window / IP
_RATE_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "3600"))  # 1 hour
_GLOBAL_DAILY_MAX = int(os.getenv("RATE_LIMIT_GLOBAL_DAILY", "50"))  # whole service / day
_hits: dict[str, list[float]] = {}
_global_hits: list[float] = []


def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")  # set by Railway/Vercel proxy
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request) -> None:
    """Raise 429 when a caller (or the whole service) is over budget."""
    if seed_mode():
        return  # seed mode makes no paid calls
    now = time.time()

    global _global_hits
    _global_hits = [t for t in _global_hits if now - t < 86400]
    if len(_global_hits) >= _GLOBAL_DAILY_MAX:
        raise HTTPException(429, "Daily demo limit reached — try again tomorrow.")

    ip = _client_ip(request)
    hits = [t for t in _hits.get(ip, []) if now - t < _RATE_WINDOW]
    if len(hits) >= _RATE_MAX:
        raise HTTPException(429, "Too many requests — please wait a minute and retry.")

    hits.append(now)
    _hits[ip] = hits
    _global_hits.append(now)


# --------------------------------------------------------------------------- #
# request models                                                              #
# --------------------------------------------------------------------------- #
class PlanBody(BaseModel):
    request: str = ""
    preferences: list[str] = []


class RefineBody(BaseModel):
    request: str = ""
    preferences: list[str] = []
    message: str = ""
    plan: dict | None = None


def _augment(request: str, preferences: list[str]) -> str:
    req = (request or "").strip()
    if preferences:
        req += "\nPreferences: " + ", ".join(preferences)
    return req or ("Plan my coming weekend in Berlin. I like museums and lakes, "
                   "max 3 things per day, no repeated types.")


# --------------------------------------------------------------------------- #
# routes                                                                      #
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/config")
def config() -> dict:
    return {"seedMode": seed_mode(), "hasKey": bool(os.getenv("ANTHROPIC_API_KEY"))}


@app.post("/api/plan")
async def plan(body: PlanBody, _: None = Depends(rate_limit)):
    """Stream timeline steps as the agent works, then the final itinerary."""
    request_text = _augment(body.request, body.preferences)

    if seed_mode():
        async def seed_gen():
            for step in seedmod.SEED_STEPS:
                yield {"event": "step", "data": json.dumps({**step, "status": "done"})}
                await asyncio.sleep(0.88)  # design cadence
            await asyncio.sleep(0.7)
            result = seedmod.seed_plan(body.request)
            yield {"event": "result", "data": json.dumps(result)}
        return EventSourceResponse(seed_gen())

    # real mode: pump the LangGraph stream from a worker thread onto a queue
    async def real_gen():
        from src.graph.build import build_graph
        q: asyncio.Queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def worker():
            acc: dict = {"request": request_text}
            emitted: set[str] = set()
            try:
                graph = build_graph()
                for update in graph.stream({"request": request_text},
                                           stream_mode="updates"):
                    for _node, delta in update.items():
                        if delta:
                            acc.update(delta)
                    for step in build_timeline(acc):
                        if step["key"] not in emitted:
                            emitted.add(step["key"])
                            loop.call_soon_threadsafe(
                                q.put_nowait,
                                ("step", {**step, "status": "done"}))
                # echo the user's original request, not the augmented prompt
                acc["request"] = body.request.strip() or request_text
                loop.call_soon_threadsafe(
                    q.put_nowait, ("result", serialize_plan(acc)))
            except Exception as e:  # surface, don't hang the stream
                loop.call_soon_threadsafe(
                    q.put_nowait, ("error", {"message": str(e)}))
            finally:
                loop.call_soon_threadsafe(q.put_nowait, None)

        threading.Thread(target=worker, daemon=True).start()
        while True:
            item = await q.get()
            if item is None:
                break
            event, data = item
            yield {"event": event, "data": json.dumps(data)}

    return EventSourceResponse(real_gen())


@app.post("/api/refine")
async def refine(body: RefineBody, _: None = Depends(rate_limit)) -> dict:
    """Apply a natural-language refine and return {reply, plan}."""
    if seed_mode():
        base = body.plan or seedmod.seed_plan()
        out = seedmod.seed_refine(base, body.message)
        return {"reply": out.pop("reply", ""), "plan": out}

    # real mode: re-run the agent with the refine folded into the request.
    from src.graph.build import build_graph
    request_text = (_augment(body.request, body.preferences)
                    + f"\nRefinement from the user: {body.message}")

    prev_plan = _plan_items_from_response(body.plan)
    state = await asyncio.to_thread(
        lambda: build_graph().invoke({"request": request_text}))
    result = serialize_plan(state, prev_plan=prev_plan)
    result["reply"] = _refine_reply(body.message, prev_plan, result)
    return {"reply": result.pop("reply"), "plan": result}


def _plan_items_from_response(plan: dict | None) -> list[dict]:
    """Rebuild [{date, slot, venue}] from a serialized plan for diffing."""
    if not plan:
        return []
    items = []
    for day in plan.get("days", []):
        for s in day.get("slots", []):
            items.append({"date": day.get("date"),
                          "slot": (s.get("time") or "").lower(),
                          "venue": s.get("venue", {}).get("name")})
    return items


def _refine_reply(message: str, prev: list[dict], result: dict) -> str:
    """One-line summary of what the refine changed (cheap LLM, fail-soft)."""
    new = _plan_items_from_response(result)
    old_names = {i["venue"] for i in prev}
    new_names = {i["venue"] for i in new}
    added = new_names - old_names
    removed = old_names - new_names
    try:
        from src.llm import llm
        prompt = (f"The user asked to refine a Berlin weekend plan: '{message}'.\n"
                  f"Removed venues: {sorted(removed) or 'none'}.\n"
                  f"Added venues: {sorted(added) or 'none'}.\n"
                  f"Constraints still satisfied: {result['constraints']['ok']}.\n"
                  "Reply in ONE friendly sentence telling the user what changed.")
        return llm(prompt, heavy=False).strip()
    except Exception:
        if added or removed:
            return (f"Re-ran the planner — swapped in {', '.join(sorted(added)) or 'updates'}"
                    f"{' and dropped ' + ', '.join(sorted(removed)) if removed else ''}.")
        return ("Re-ran the planner with that. Everything still satisfies your "
                "constraints — nothing needed to change.")


# --------------------------------------------------------------------------- #
# serve the built SPA (after API routes so they take precedence)              #
# --------------------------------------------------------------------------- #
if _DIST.exists():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="spa")
