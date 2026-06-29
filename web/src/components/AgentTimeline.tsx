import type { TimelineStep } from "../api/client";

/** Display skeleton: the canonical step order. Real steps fill these in as the
 *  agent streams progress; keys map a couple of backend aliases onto one row. */
const SKELETON: { key: string; aliases: string[]; title: string }[] = [
  { key: "parse", aliases: [], title: "Parsing your request" },
  { key: "weather", aliases: [], title: "Checking live weather" },
  { key: "reason", aliases: [], title: "Reasoning about conditions" },
  { key: "find", aliases: ["gather"], title: "Finding indoor alternatives" },
  { key: "plan", aliases: [], title: "Building the schedule" },
  { key: "validate", aliases: [], title: "Validating constraints" },
  { key: "fix", aliases: [], title: "Fixing issues" },
];

type State = "done" | "active" | "pending";

interface Props {
  requestEcho: string;
  steps: TimelineStep[];
}

export function AgentTimeline({ requestEcho, steps }: Props) {
  const arrived = new Map<string, TimelineStep>();
  for (const s of steps) arrived.set(s.key, s);

  const matched = (row: (typeof SKELETON)[number]) =>
    arrived.get(row.key) ?? row.aliases.map((a) => arrived.get(a)).find(Boolean);

  // first not-yet-arrived row is "active"
  const firstPendingIdx = SKELETON.findIndex((r) => !matched(r));

  const rows = SKELETON.map((row, i) => {
    const hit = matched(row);
    const state: State = hit ? "done" : i === firstPendingIdx ? "active" : "pending";
    return {
      title: hit?.title ?? row.title,
      detail: hit?.detail ?? "",
      state,
    };
  });

  return (
    <section className="thinking-screen" aria-labelledby="thinking-h">
      <div className="thinking-status">
        <span className="pulse-dot" aria-hidden="true" />
        <span className="eyebrow" id="thinking-h">
          AGENT WORKING · ReAct LOOP
        </span>
      </div>

      <div className="echo-card mono">{requestEcho}</div>

      <ol className="timeline" aria-live="polite" aria-label="Agent reasoning steps">
        {rows.map((r, i) => (
          <li key={i} className={`tl-row ${r.state}`}>
            <div className="tl-rail">
              <span className={`tl-node ${r.state}`} aria-hidden="true">
                {r.state === "done" ? "✓" : ""}
              </span>
              {i < rows.length - 1 && <span className={`tl-connector ${r.state}`} />}
            </div>
            <div className="tl-body">
              <div className="tl-title">{r.title}</div>
              {r.detail && <div className="tl-detail mono">{r.detail}</div>}
              <span className="sr-only">{r.state}</span>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
