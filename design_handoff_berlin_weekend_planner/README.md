# Handoff: Berlin Weekend Planner

> Agentic AI itinerary planner for a Berlin weekend. Turns one free-text request into a day-by-day plan, checks live weather, self-corrects outdoor→indoor when it rains, validates constraints, and **shows its reasoning** the whole way.

---

## How to use this package (read first)

The files in this bundle are **design references authored in HTML** — interactive prototypes that show the intended look, motion, and behavior. **They are not production code to copy.** Your job is to **recreate these designs in this project's environment** using its established patterns, components, and libraries.

- If the repo already has a frontend stack (React/Next, Vue, Svelte, SwiftUI, etc.), build the screens with **that** stack and its design-system/component primitives. Match the visuals in this doc pixel-for-pixel; don't import the HTML.
- If there is **no** frontend yet, choose the most appropriate modern stack for the project (a React + TypeScript + Vite SPA is a sensible default for this app) and implement there.
- The `.dc.html` files use a custom runtime (`support.js`) just so they render standalone — **ignore that runtime**. What matters is the markup structure, the inline styles (exact colors/spacing/type), and the agent state machine logic, all of which are documented below and visible in the source.

**Fidelity: High-fidelity (hifi).** Final colors, typography, spacing, and interactions are intentional. Recreate them precisely.

### Recommended file/component structure (suggestion)
```
src/
  App.tsx                 // owns plannerPhase state machine
  data/venues.ts          // venue catalog (table below)
  data/weather.ts         // per-day weather (mock/real API)
  agent/planner.ts        // buildPlan(), validate(), applyRefine() — the "agent"
  components/
    RequestInput.tsx      // screen 1
    PreferenceChips.tsx
    AgentTimeline.tsx     // screen 2 (the hero)
    Itinerary.tsx         // screen 3
    DayColumn.tsx
    WeatherStrip.tsx
    VenueCard.tsx
    SwapCallout.tsx
    ConstraintSummary.tsx
    RefinePanel.tsx       // screen 4 (chat)
    AgentLog.tsx
    BestEffortBanner.tsx  // screen 5 (edge)
```

---

## Overview

A single-page app with four primary phases plus one edge state. The differentiator is **legible agency**: the planner doesn't just list places — it reasons out loud (a ReAct-style loop), reacts to live weather, and self-corrects, explaining every choice. The UI must make that thinking *central*, never hidden behind a spinner.

Sample scenario (use as seed data): a **rainy Saturday 4 Jul 2026 / sunny Sunday 5 Jul 2026** weekend. Request: *"Plan my weekend 4–5 July 2026. I like museums and lakes, max 3 things per day, no repeated types, avoid repeats."* The agent detects 70% rain Saturday, moves the lake to Sunday, and swaps it for an indoor aquarium on Saturday.

---

## Design Tokens

### Color
| Token | Hex | Use |
|---|---|---|
| `bg/page` | `#f3efe8` | App background (warm paper) |
| `bg/surface` | `#ffffff` | Cards |
| `bg/surfaceWarm` | `#faf7f1` | Inset panels, echoed request, refine footer |
| `bg/dayPanel` | `#f8f4ed` | Day-column body behind cards |
| `ink/900` | `#1b1714` | Primary text, dark buttons |
| `ink/700` | `#544c42` | "Why" rationale text |
| `ink/500` | `#6f665b` | Secondary text |
| `ink/400` | `#9a9081` | Meta / mono labels |
| `ink/300` | `#b3a999` | Placeholder text |
| `line` | `#e6dfd3` | Default borders |
| `line/soft` | `#f0eadf` · `#efe8dc` | Inner dividers |
| **`accent` (ochre)** | **`#cf8400`** | AI reasoning + all agent actions, primary CTA |
| `accent/ink` | `#9a6200` · `#7a5408` · `#5e3f06` | Ochre text on light |
| `accent/bg` | `#f7ead0` | Ochre chip/callout fill |
| `accent/border` | `#ecd29a` | Ochre chip/callout border |
| `indoor/fg` | `#3a5680` | Indoor label text (cool blue) |
| `indoor/bg` | `#e8edf5` | Indoor label fill |
| `outdoor/fg` | `#2f6b45` | Outdoor label text (warm green) |
| `outdoor/bg` | `#e6efe7` | Outdoor label fill |
| `success/bg` | `#eef2ea` | Constraint-met pill fill |
| `success/border` | `#cdd9c8` | |
| `wx/rain` dot/fg/bg/border | `#5b7a99` / `#3f5a73` / `#eaeef2` / `#d4dde4` | Rainy day strip |
| `wx/sun` dot/fg/bg/border | `#cf8400` / `#9a6200` / `#fbf2dc` / `#eedfb8` | Sunny day strip |
| `warn/fg` (edge) | `#b5561f` | Unmet-constraint marker |
| `warn/bg` · `border` | `#fbeee6` · `#e9c4ad` | Best-effort banner |

> **Color semantics are load-bearing:** ochre = AI/agent action, cool blue = indoor, warm green = outdoor. Keep these consistent everywhere.

Dark mode was out of scope for this round (light only) but the token structure anticipates it.

### Typography
- **Body / UI:** `Helvetica Neue, Helvetica, Arial, sans-serif`. Tight, Swiss/utilitarian.
- **Mono (the "agent voice"):** `IBM Plex Mono` (weights 400/500/600). Used for ALL labels, meta lines, timestamps, weather readouts, kicker eyebrows, and the agent log. This mono/sans split is the core type idea — mono signals "machine/data", sans is human-facing copy.
- Scale (px): hero `46` (mobile `30`) / day title `18–19` / venue name `16–17` / body `15` / secondary `13–14` / rationale `13` / meta-mono `11–12` / eyebrow-mono `10–11`.
- Headlines: `font-weight:600`, `letter-spacing:-0.3px` to `-1.4px` (tighter as larger), `line-height:1.04–1.05`. Use `text-wrap:balance` on the hero.
- Mono labels: `letter-spacing:0.10–0.18em`, often `text-transform:uppercase`.

### Spacing / Radius / Elevation
- Radii: cards `6px`, panels/inputs `8–10px`, pills `15–20px`, primary button `8–10px`, phone screen `38px`/bezel `48px`.
- **Flat surfaces** — no heavy gradients or drop shadows in the UI itself. Cards use 1px borders, not shadows. The only shadows are subtle frame elevation on the canvas board (`0 4px 24px rgba(0,0,0,.08)`) — not part of the product UI.
- Venue cards carry a **3px left accent border**: `#e6dfd3` default, **`#cf8400` when weather-swapped**, `#2f6b45` when edited by a refine.
- Generous whitespace; content max-widths: input `780px`, thinking `680px`, result `1340px`.

---

## Screens / Views

### 1 · Input / empty state
**Purpose:** low-friction "smart search bar" to capture a free-text request + optional preference chips.

**Layout (desktop):** centered column, `max-width:780px`, padding `72px 32px 96px`.
- Eyebrow (mono, ochre, uppercase, `.18em`): "A PLANNER THAT SHOWS ITS THINKING".
- H1 `46px/600/-1.4px`: *"Tell me your weekend. I'll plan it — and show every decision."*
- Sub `17px` `#6f665b`, max-width `560px`.
- **Request card** (`#fff`, 1px `#e6dfd3`, radius `10px`, padding `8px`): a borderless `<textarea>` (min-height `96px`, `17px`) with placeholder *"Plan my Saturday 4 July 2026 — I like museums and lakes, max 3 things, avoid repeats…"*. Below it, a chip row prefixed by a mono "PREFERENCES" label; footer row split between mono hint "Live weather · self-correcting" and the primary CTA.
- **Primary CTA:** ochre `#cf8400`, white text, `13px 24px`, radius `8px`, label "Plan my weekend →".
- **Example prompts** under the card: mono "Try:" + 2 ghost chips that fill the textarea.

**Preference chips** (toggle, default on = ochre): `Sat–Sun 4–5 Jul`, `Mitte`, `Kreuzberg`, `Treptow`, `Indoor-friendly`, `Max 3 / day`, `No repeats`. Each chip = pill with a 6px leading dot (ochre `#cf8400` when on, `#cdc3b3` off); on-state fill `#f7ead0` / border `#ecd29a` / text `#9a6200`; off-state `#fff` / `#e0d6c5` / `#6f665b`.

**Mobile (390):** same content stacked; CTA is full-width; textarea placeholder shown as muted text.

---

### 2 · Agent working / thinking — **the hero screen**
**Purpose:** visualize the ReAct + self-correction loop as a live, elegant vertical timeline. Must feel intelligent and trustworthy, NOT a generic spinner.

**Layout:** centered `max-width:680px`, padding `64px 32px 96px`.
- Status row: pulsing 7px ochre dot + mono eyebrow "AGENT WORKING · ReAct LOOP".
- Echoed request in a mono inset card (`#faf7f1`, 1px border, radius `8px`).
- **Timeline**: 2-col grid per step `[28px | 1fr]`, gap `16px`. Left rail = an 18px node circle + a 2px connector line growing down to the next node. Right = step title (`16px/600`) + mono detail line.

**The 7 steps (drive these in sequence ~880ms apart):**
1. **Parsing your request** — `Sat–Sun 4–5 Jul · museums + lakes · max 3/day · no repeated types · avoid repeats`
2. **Checking live weather** — `Sat → 70% rain, 18° · Sun → sunny, 26°`
3. **Reasoning about conditions** — `Saturday is wet → favour indoor, push the lake to sunny Sunday`
4. **Finding indoor alternatives** — `Schlachtensee (lake) → Sea Life Berlin for Sat afternoon`
5. **Building the schedule** — `6 stops sequenced across morning / afternoon / evening`
6. **Validating constraints** — `3/3 per day · no repeated types · Waldbühne pinned to 5 Jul`
7. **Fixing 1 issue** — `Sat evening was a 2nd museum → replaced with a covered market`

**Node states:**
- *Done*: fill `#2f6b45`, white `✓`, connector `#cdd9c8`, title `#1b1714`, row opacity `1`.
- *Active*: fill+ring `#cf8400`, no glyph, `animation: pulse 1.1s ease-in-out infinite`, connector `#e6dfd3`.
- *Pending*: hollow, 2px ring `#d8cfc0`, title `#9a9081`, row opacity `0.32`.
- Row opacity transitions `0.4s ease` as steps activate.

After step 7, wait ~700ms then transition to the itinerary.

> **Variation B (optional, in Overview Board):** the same trace rendered as a dark "agent.plan() — live trace" terminal in mono, with colored glyphs (`✓` green, `→`/`!` ochre) and a blinking cursor block. Offered as an alternate treatment — pick one.

---

### 3 · Itinerary result — the payoff
**Purpose:** the day-by-day plan with full reasoning legible.

**Layout (desktop):** `max-width:1340px`. Header eyebrow + echoed request, then the **constraint summary** pill row, then a 3-col grid `[1fr | 1fr | 340px]`, gap `22px`, `align-items:start`:
- **Col 1 = Saturday**, **Col 2 = Sunday**, **Col 3 = sticky Agent panel** (`position:sticky; top:92px`).

**Constraint summary pills** (mono): `✓ 3 / 3 per day`, `✓ No repeated types`, `✓ All weather-checked` (all green: bg `#eef2ea`/border `#cdd9c8`/fg `#356043`); `↺ 1 weather swap` (ochre pill); `€ ≈ €104 / person` (neutral). The € total is computed from venue costs — keep it live/derived.

**Each day = weather strip (header) + card stack (body):**
- **Weather strip:** rounded top, day name (`19px/600`) + mono date; right side = colored dot + mono readout. Saturday uses the rain palette (`70% RAIN · 18°`), Sunday the sun palette (`SUNNY · 26°`). The card stack below shares the strip's border color and a `#f8f4ed` fill.

**Venue card** (the key component):
- White, 1px `#ece5d8`, radius `6px`, **3px left accent border** (color encodes swap/edit state), padding `~13px 15px`.
- Top row: mono `TIME · timestamp` (e.g. `AFTERNOON · 14:00`) on the left; **indoor/outdoor label** chip on the right (blue/green per tokens, mono `9.5px`, `.10em`, uppercase, radius `4px`).
- Name `17px/600/-0.3px`.
- Mono meta line: `Type · Area · hours-or-event-date` (e.g. `Aquarium · Mitte · 10:00–19:00`, or `Concert · Westend · 5 Jul 20:00` for dated events).
- Divider, then a **"WHY" rationale row**: mono ochre `WHY` tag + a one-line reason in `#544c42`.

**Swap callout** (sits *above* the swapped card): ochre box (`#f7ead0`/`#ecd29a`), mono `↺`, text *"**Weather swap.** Schlachtensee (lake) → Sea Life Berlin. Your lake moves to Sunday when it's dry."* — this is the single most important "the agent is intelligent" moment; make it obvious. (An analogous green "**Updated.** ✎" callout appears above any card changed by a refine.)

**Agent panel (col 3):** white card. Header (green dot + mono "AGENT LOG" + "7 steps"). Scrollable list of completed steps (green `✓` + title + mono sub-detail), `max-height:230px`. Below it the **Refine** section (see screen 4).

**Mobile (390):** day tabs (Saturday/Sunday segmented control) instead of side-by-side columns; weather strip + constraint pills below the tabs; single card stack; the Refine input becomes a **sticky bottom bar** (blurred), and full refine is a bottom-sheet.

---

### 4 · Refine / replan (conversational)
**Purpose:** adjust the plan in natural language; re-runs the planner and updates the itinerary in place.

**Desktop:** lives in the sticky agent panel footer (`#faf7f1`). Mono "REFINE" header → chat transcript → quick-action chips → text input + dark send button (`#1b1714`, mono `→`).
- **Chat bubbles:** user = right-aligned, `#1b1714`/white, radius `12px`; agent = left-aligned, `#fff` + 1px border, `#1b1714`.
- **Quick chips:** `Make it cheaper`, `Swap Sunday afternoon`, `More outdoor`.
- **Re-planning indicator:** ochre pulsing dot + mono "Re-planning…" while it works (~1.1s), then the agent reply bubble appears AND the affected venue card updates (green left-border + "Updated." callout).

**Intent → effect mapping (implement these):**
- *cheaper / budget / less* → Sunday evening **Waldbühne (€55) → Freiluftkino Friedrichshain (€9.50)**. Reply: *"Done — swapped the €55 concert for an open-air cinema (€9.50). Weekend total drops to about €56/person."*
- *swap Sunday afternoon* → **Tempelhofer Feld → Badeschiff** (still outdoor, river-pool ≠ lake so no repeat). Reply: *"Swapped Sunday afternoon to Badeschiff — kept it outdoor and checked it doesn't repeat the lake."*
- *more outdoor / outside / sun* → no destructive change; agent **pushes back honestly**: *"Heads up: Saturday is still 70% rain, so forcing it outdoors means wet plans. Sunday is already fully outdoor. Want me to risk Saturday anyway, or keep it covered?"*
- *anything else* → generic: *"Re-ran the planner with that. Everything still satisfies your constraints — nothing needed to change."*

Free-text is matched case-insensitively against those keyword groups. Enter key submits.

---

### 5 · Edge state — graceful "best effort"
**Purpose:** when not all constraints can be met, be honest, not silently wrong.

- **Banner** (`#fbeee6`/`#e9c4ad`): mono `!` + "BEST EFFORT · 2 OF 3 MET", then *"I built the closest plan I could, but couldn't fully satisfy everything. Here's what's honest about it:"*
- **Issue rows** (white cards, leading mono glyph):
  - `✕` (warn `#b5561f`) **No budget dinner found** — *"No indoor dinner under €15 in Treptow on Sat. Showing nearest: Freischwimmer (€18)."*
  - `↺` (ochre) **Waldbühne sold out** — *"Suggested Freiluftkino instead — same evening, outdoor, €9.50."*
  - `✓` (green) **Everything else holds** — *"Weather-checked · no repeated types · dated events on the right day."*
- **Actions:** dark "Relax budget" + ghost "Keep best effort".

---

## Interactions & Behavior
- **Phase machine:** `input → thinking → result` (with `edge` as an alternate terminal of `thinking`). A persistent "↺ Start over" in the header returns to `input` and rebuilds the default plan.
- **Thinking sequence:** advance one step every ~880ms; each step flips pending→active→done; 700ms hold after the last step before showing the result.
- **Refine:** push user bubble → show "Re-planning…" ~1.1s → push agent bubble + mutate the relevant slot (mark `changed`/`swapped` so the card shows its colored border + callout).
- **Animations:** `pulse` (opacity 1↔.3) on the active node; `dot` (scale/opacity) on status dots; row opacity fade `0.4s`; connector lines can grow with a height transition. Keep motion subtle and quick.
- **Responsive:** desktop is the 3-col itinerary; at mobile width collapse to tabbed single-column with a sticky refine bar / bottom-sheet. Hit targets ≥ 44px on mobile.
- **Hover:** chips/buttons lighten or border-darken slightly; primary CTA can deepen ochre on hover.

## State Management
- `phase`: `'input' | 'thinking' | 'result'` (+ `'edge'`).
- `step`: index of current thinking step (−1 idle).
- `request` / `requestEcho`: the free-text prompt.
- `chips[]`: preference toggles `{id,label,on}`.
- `days[]`: `{ label, date, wx:'rain'|'sun', slots:[{ time, t, venue, swapped?, swapNote?, changed?, changeNote? }] }`.
- `messages[]`: refine chat `{role:'user'|'agent', text}`.
- `replanning`: boolean.
- Derived: constraint summary + `€/person` total computed from `days`.

## Agent logic (recreate as plain functions)
- `parseRequest(text, chips)` → constraints `{dates, interests, maxPerDay, noRepeatTypes}`.
- `getWeather(date)` → `{rain, tempC}` (mock the 4 Jul rain / 5 Jul sun scenario; swappable for a real API later).
- `buildPlan(constraints, weather, catalog)` → picks venues, **prefers indoor on rainy days**, defers outdoor faves to clear days, places dated events on their real date.
- `validate(plan)` → checks per-day count, no repeated `type`, dated-event placement; returns issues.
- `selfCorrect(plan, issues)` → resolves issues (e.g. 2nd museum → market) and records what changed.
- `applyRefine(plan, intent)` → see intent map in screen 4.

## Sample data — Venue catalog
| key | name | type | area | env | hours / event | cost € |
|---|---|---|---|---|---|---|
| pergamon | Pergamonmuseum | Museum | Mitte | indoor | 10:00–18:00 | 14 |
| sealife | Sea Life Berlin | Aquarium | Mitte | indoor | 10:00–19:00 | 20 |
| markthalle | Markthalle Neun | Food market | Kreuzberg | indoor | Sat til 22:00 | 15 |
| schlachtensee | Schlachtensee | Lake | Zehlendorf | outdoor | best 10:00–16:00 | 0 |
| tempelhof | Tempelhofer Feld | Park | Tempelhof | outdoor | sunrise–sunset | 0 |
| waldbuhne | Waldbühne Open-Air | Concert | Westend | outdoor | event · 5 Jul 20:00 | 55 |
| badeschiff | Badeschiff | River pool | Kreuzberg | outdoor | 10:00–23:00 | 7 |
| freiluft | Freiluftkino Friedrichshain | Open-air cinema | Friedrichshain | outdoor | event · 5 Jul 21:30 | 9.5 |

**Default plan:** Sat — Pergamonmuseum (09:30) / *swap:* Sea Life Berlin (14:00) / Markthalle Neun (19:00). Sun — Schlachtensee (10:00) / Tempelhofer Feld (14:30) / Waldbühne (20:00). Each venue carries a one-line `why` (see source for exact copy).

## Assets
- **Font:** IBM Plex Mono via Google Fonts (`https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600`). Helvetica Neue is system.
- **No image assets.** Venue photos are placeholders in the design — wire to real imagery (e.g. a CMS/venue API) or keep a tasteful flat placeholder. Card variant B shows an image-led treatment if you want photos.
- **Icons:** all glyphs are plain text (`✓ ↺ ✎ ✕ ! → €`). Swap for your icon set if preferred, but the meanings must stay (✓ met, ↺ weather swap, ✎ edited, ✕ unmet).
- **Logo:** simple ochre rounded square with mono "B" + wordmark "Berlin Weekend Planner".

## Files in this bundle
- `Berlin Weekend Planner.dc.html` — the full **interactive prototype** (input → thinking → itinerary → refine). Best reference for behavior, copy, and the agent state machine — read its embedded logic class.
- `Overview Board.dc.html` — a **gallery board**: all 5 mobile screens (iPhone frames), desktop itinerary + thinking, plus the timeline and venue-card **variations** and a visual-language legend. Best reference for layout/spacing across breakpoints.
- `support.js` — the prototype runtime only; **not relevant** to your implementation, do not port it.

To view: open either `.dc.html` in a browser (they're self-contained). Ignore the `support.js` machinery; read the markup + inline styles + the logic class for ground truth.
