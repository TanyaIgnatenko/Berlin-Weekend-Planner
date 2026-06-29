# Frontend — Berlin Weekend Planner

A Vite + React + TypeScript SPA that wires the existing LangGraph planner to the
five screens in `design_handoff_berlin_weekend_planner/`. The **backend owns
planning**; the client only sends the request, streams the agent's real
progress, and renders what comes back.

```
web/                      the SPA
  src/
    api/client.ts         the ONLY module that talks to the backend (typed)
    data/seed.ts          fallback/seed data — isolated from real responses
    hooks/usePlanner.ts    phase state machine (input → thinking → result)
    components/           the screens (see "Where each screen lives")
    styles/tokens.css     design tokens (colours/type/radii) as CSS variables
src/api/                  FastAPI layer that wraps build_graph() — additive only
```

## How to run

Two processes: the FastAPI backend (wraps the agent) and the Vite dev server
(serves the SPA, proxies `/api` to the backend).

```powershell
# 1. backend  (from the repo root, with the venv created per README.md)
#    seed mode needs no API key; omit the env var + set ANTHROPIC_API_KEY for real planning
$env:PLANNER_SEED_MODE = "1"
.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --host 127.0.0.1 --port 8765

# 2. frontend  (separate terminal)
cd web
npm install
npm run dev            # http://localhost:5173
```

Open the Vite URL. The dev server proxies `/api/*` to the backend.

> **Port note (Windows):** the proxy targets `http://127.0.0.1:8765` (IPv4) on
> purpose — using `localhost` can resolve to `::1` and collide with any other
> service bound to that port. Override with `VITE_API_TARGET` if you run the
> backend elsewhere, e.g. `VITE_API_TARGET=http://127.0.0.1:8000`.

### Production-style (single origin)
```powershell
cd web; npm run build         # emits web/dist
.\.venv\Scripts\python.exe -m uvicorn src.api.app:app --port 8000
# open http://localhost:8000  — FastAPI serves web/dist AND /api on one origin
```

## Modes — real vs. seed (no fabricated data)

The app runs in one of two modes, chosen per request by the backend
(`src/api/app.py: seed_mode()`):

| Mode | When | Behaviour |
|---|---|---|
| **seed** | `PLANNER_SEED_MODE` truthy **or** no `ANTHROPIC_API_KEY` | Serves the design's sample weekend (`src/api/seed.py`) with no LLM/network. Guarantees the demo (the rainy-Sat → aquarium swap, €104 total, the three scripted refines). |
| **real** | an `ANTHROPIC_API_KEY` is set and seed is off | Drives the actual LangGraph agent + live Open-Meteo weather. The timeline, plan, weather, and rationales are all derived from real agent output. Exact swaps/copy vary run to run. |

The SPA shows a **SEED MODE** badge in the header when seed mode is active.
Seed/fallback data lives only in `src/api/seed.py` (backend) and
`web/src/data/seed.ts` (offline UI fallback) — it is never merged into a real
response.

## Endpoints the frontend calls

All under `/api`, defined in `src/api/app.py`. **These were added for the
frontend** — the original project was a CLI only; no agent logic changed.

| Method · path | Body | Response |
|---|---|---|
| `GET /api/health` | — | `{ ok }` |
| `GET /api/config` | — | `{ seedMode, hasKey }` — lets the SPA show its mode |
| `POST /api/plan` | `{ request, preferences[] }` | **SSE stream**: `event: step` per real timeline step, then `event: result` with the full plan (see shape below). |
| `POST /api/refine` | `{ request, preferences[], message, plan }` | `{ reply, plan }` — re-runs the agent (real) or applies the README intent-map (seed). |

`preferences[]` is the list of active preference-chip labels; the backend folds
them into the free-text request before parsing.

### Plan shape (`web/src/api/client.ts` mirrors this exactly)
`{ request, spec, days[], constraints, costPerPerson, steps[], agentLog[], bestEffort }`
where `days[].slots[]` carry the venue, `why` rationale, and `swapped`/`changed`
flags that drive the accent borders and callouts.

### Streaming detail
The thinking timeline reflects **real** agent progress: the backend pumps the
LangGraph node stream (`graph.stream(..., stream_mode="updates")`) and emits a
timeline step as each phase completes, then the final plan. In seed mode the
seven design steps are emitted on the ~880 ms design cadence. The client parses
SSE off `fetch` (EventSource can't POST) and tolerates `\n` or `\r\n` framing.

## Backend changes made for the frontend (all additive, isolated)

1. **`src/api/`** — new package: `app.py` (FastAPI), `serialize.py` (PlannerState
   → frontend shape), `seed.py` (offline scenario). No existing module changed.
2. **`Venue.cost`** — added one optional field to `src/schema.py` and seeded
   `data/venues.json` with €-values, so the `€/person` summary and the
   budget-refine are real. Also added `Freiluftkino Friedrichshain` (the
   cheaper-evening alternative).
3. **`requirements.txt`** — added `fastapi`, `uvicorn[standard]`, `sse-starlette`.

The CLI (`python -m src.run`), graph, nodes, tools, and validator are untouched.

## Where each screen lives

| Screen (handoff) | Component(s) |
|---|---|
| 1 · Input / empty state | `RequestInput.tsx`, `PreferenceChips.tsx` |
| 2 · Agent thinking (hero) | `AgentTimeline.tsx` |
| 3 · Itinerary result | `Itinerary.tsx`, `DayColumn.tsx`, `WeatherStrip.tsx`, `VenueCard.tsx`, `SwapCallout.tsx`, `ConstraintSummary.tsx`, `AgentPanel.tsx` |
| 4 · Refine / replan | `RefinePanel.tsx` (inside `AgentPanel`) |
| 5 · Edge / best-effort | `BestEffortBanner.tsx` (renders when `plan.bestEffort`; only reachable in real mode when validation can't be satisfied within the replan cap) |

## Accessibility & responsive
- Semantic landmarks (`header`/`main`/`aside`), labelled inputs, `focus-visible`
  outlines, `aria-live` on the timeline and refine transcript.
- Desktop ≥ 900px: 3-column itinerary with a sticky agent panel. Below 900px:
  day tabs + single column. ≤ 480px: mobile type scale. Hit targets ≥ 44px.
- Light mode only this round (tokens anticipate dark; not built).
- Honors `prefers-reduced-motion`.

## Known limitations / honest notes
- **Weather-swap annotation in real mode:** seed mode shows the full scripted
  "Schlachtensee → Sea Life" swap. Real mode marks an indoor pick on a wet day
  honestly ("Weather-aware: indoor pick for a wet day") rather than fabricating
  a specific prior venue, since the agent doesn't emit an explicit A→B swap.
- **Refine in real mode** re-runs the whole agent with the message folded into
  the request; the reply is a one-line LLM summary of what changed (fails soft
  to a templated diff). The README's exact intent→effect copy is seed-only.
