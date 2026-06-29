# Berlin Weekend Planner

An **agentic** weekend planner for Berlin. Given a free-text request, it gathers
venues and events, checks the weather, builds a schedule, and **self-corrects**
when constraints are violated.

This is a portfolio project aimed at an AI (Agentic) Engineer role. The point it
demonstrates: a ReAct agent wrapped around retrieval + a deterministic
constraint-checking loop — not a one-shot RAG pipeline.

## Why this is an agent (and not just RAG)

RAG = retrieve → generate, one pass, no feedback. This task has constraints that
can only be checked *after* a plan exists (no outdoor venues on rainy days,
dated events on the right day, no repeated types, max-per-day). So the system:

1. **gathers** via a ReAct loop where the model chooses which tool to call and
   when to stop (`react_gather` — the genuinely agentic node);
2. **plans** by grounding on what it gathered;
3. **validates** deterministically in Python;
4. **replans** on violations until valid or a cap is hit.

RAG (venue retrieval) lives *inside* the agent as a tool. The agent is the
check-and-fix contour RAG lacks.

## Architecture

```
parse_request → react_gather → plan → validate ─ ok ──→ finalize
                                  ▲                │
                                  └──── replan ←─ not ok
```

| Node            | What it does                                  | LLM? |
|-----------------|-----------------------------------------------|------|
| `parse_request` | free text → `PlanRequest`                     | cheap model |
| `react_gather`  | think→act→observe→repeat→stop (chooses tools) | strong model |
| `plan`          | assemble candidates into a schedule (grounded)| strong model |
| `validate`      | deterministic constraint checks               | none |
| `replan`        | violations → feedback, bump counter           | none |
| `finalize`      | format plan + rationale                       | none |

Tools: `search_venues` (reads `data/venues.json`), `get_weather`
(live Open-Meteo, free, no key).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...          # or set PLANNER_MODEL/EXTRACTOR_MODEL + the matching key
```

Adjust model strings in `src/llm.py` to ones your provider supports.

## Run

```bash
python -m src.run "Plan Saturday 2026-07-04 in Berlin, I like museums and lakes, max 2 things"
python -m src.run --trace "..."       # with Phoenix tracing
python -m eval.evaluate               # constraint-satisfaction rate + metrics
```

Phoenix (optional): `python -m phoenix.server.main serve` → http://localhost:6006

## Web UI & API

The planner also ships a web frontend (React + TypeScript SPA) over a thin
FastAPI layer that wraps the same `build_graph()` — the agent is unchanged; the
API just exposes it. The UI makes the agency legible: a live ReAct thinking
timeline, the day-by-day itinerary with weather swaps and per-item rationale,
and a conversational refine that re-runs the planner.

```bash
# backend (seed mode needs no key; set ANTHROPIC_API_KEY for real planning)
PLANNER_SEED_MODE=1 python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8765
# frontend (separate terminal)
cd web && npm install && npm run dev      # http://localhost:5173
```

See **[FRONTEND.md](FRONTEND.md)** for the full run instructions, the API
contract (`/api/plan` SSE stream, `/api/refine`), seed-vs-real modes, and where
each screen lives.

## What's done vs. what you write

Done and working: graph wiring, both tools, deterministic validator, replan
loop, Phoenix hook, eval harness, seed data, and the web UI + FastAPI layer
(see [FRONTEND.md](FRONTEND.md)).

Your job (marked `TODO` in code):
- `parse_request` — harden the extraction prompt, add few-shot for messy input.
- `react_gather` — this is the project. Tune the ReAct prompt, decide stop
  criteria, optionally upgrade to native tool-calling. Make the agent reason
  about weather *before* committing to outdoor options.
- `plan` — tune grounding / scheduling prompt.
- `data/venues.json` — flesh out to ~30 venues with a spread across
  indoor/outdoor and fixed-hours/dated-event (fill this in by hand).
- `eval/cases.json` — grow to ~10–15 cases.

**Rule:** get the graph running end-to-end once before adding anything below.

## Backlog (v2 — only after the core works)

- Voice input (Whisper / browser STT) before `parse_request` — input layer only.
- Generated dish/venue images — skipped; overlaps MenuMind, no agentic value.
- Ready-made / "buy not cook" as a venue/meal property (`prep_type`).
- Live store / SKU prices (Lidl etc.) — capricious external source, avoid.
- Event-page scraper to auto-fill `venues.json` — replaces hand entry later.
- Review analysis to rank alternatives of the same type.
- LLM-as-judge scoring of plan quality (extend `eval/evaluate.py`).
