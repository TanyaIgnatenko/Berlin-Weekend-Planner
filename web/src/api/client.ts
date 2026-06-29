/**
 * Typed API client / adapter — the ONLY module that talks to the backend.
 * Endpoints, shapes, and transport live here. Types mirror the backend's
 * `src/api/serialize.py` output exactly.
 *
 * The backend owns planning; the client only sends the request + preferences,
 * streams the agent's real progress, and renders what comes back.
 */

const BASE = "/api";

/* ----------------------------- types ----------------------------- */
export interface Venue {
  name: string;
  type: string;
  area: string;
  indoor: boolean;
  hours: string | null;
  date: string | null;
  cost: number;
}

export interface Slot {
  time: string; // "AFTERNOON"
  timestamp: string; // "14:00"
  venue: Venue;
  why: string;
  swapped: boolean;
  swapNote: string | null;
  changed: boolean;
  changeNote: string | null;
}

export interface Day {
  label: string; // "Saturday"
  date: string; // "2026-07-04"
  wx: "rain" | "sun";
  weatherReadout: string; // "70% RAIN · 18°"
  weather: { rain_prob?: number; temp_max?: number; is_wet?: boolean };
  slots: Slot[];
}

export interface Constraints {
  ok: boolean;
  perDay: string;
  perDayMet: boolean;
  noRepeat: boolean;
  noRepeatMet: boolean;
  weatherChecked: boolean;
  swaps: number;
  violations: { item: string; rule: string; detail: string }[];
}

export interface TimelineStep {
  key: string;
  title: string;
  detail: string;
  status?: "done" | "active" | "pending";
}

export interface AgentLogEntry {
  title: string;
  detail: string;
}

export interface Plan {
  request: string;
  spec: Record<string, unknown>;
  days: Day[];
  constraints: Constraints;
  costPerPerson: number;
  steps: TimelineStep[];
  agentLog: AgentLogEntry[];
  final: string;
  bestEffort: boolean;
}

export interface AppConfig {
  seedMode: boolean;
  hasKey: boolean;
}

export interface PlanInput {
  request: string;
  preferences: string[];
}

/* --------------------------- requests ---------------------------- */
export async function getConfig(): Promise<AppConfig> {
  const r = await fetch(`${BASE}/config`);
  if (!r.ok) throw new Error(`config ${r.status}`);
  return r.json();
}

export interface PlanStreamHandlers {
  onStep: (step: TimelineStep) => void;
  onResult: (plan: Plan) => void;
  onError?: (message: string) => void;
}

/**
 * POST /api/plan as an SSE stream parsed off fetch (EventSource can't POST).
 * Emits each real timeline step, then the final plan.
 */
export async function streamPlan(
  input: PlanInput,
  handlers: PlanStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE}/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(input),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`plan ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line. sse-starlette uses CRLF, so
    // split on \r\n\r\n OR \n\n; keep the trailing partial frame in the buffer.
    const frames = buf.split(/\r?\n\r?\n/);
    buf = frames.pop() ?? "";
    for (const frame of frames) {
      const ev = parseFrame(frame);
      if (!ev) continue;
      if (ev.event === "step") handlers.onStep(JSON.parse(ev.data));
      else if (ev.event === "result") handlers.onResult(JSON.parse(ev.data));
      else if (ev.event === "error")
        handlers.onError?.(JSON.parse(ev.data).message ?? "unknown error");
    }
  }
}

function parseFrame(frame: string): { event: string; data: string } | null {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of frame.split(/\r?\n/)) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (!dataLines.length) return null;
  return { event, data: dataLines.join("\n") };
}

export interface RefineResponse {
  reply: string;
  plan: Plan;
}

export async function refine(
  input: PlanInput & { message: string; plan: Plan },
): Promise<RefineResponse> {
  const r = await fetch(`${BASE}/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!r.ok) throw new Error(`refine ${r.status}`);
  return r.json();
}
