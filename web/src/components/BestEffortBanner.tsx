import type { Constraints } from "../api/client";

interface Props {
  constraints: Constraints;
}

/** Screen 5 — honest "best effort" reporting when not all constraints hold. */
export function BestEffortBanner({ constraints }: Props) {
  const violations = constraints.violations ?? [];
  const total = 3;
  const met = total - Math.min(violations.length, total);

  return (
    <section className="best-effort" aria-label="Best effort report">
      <div className="be-banner">
        <span className="be-glyph mono" aria-hidden="true">
          !
        </span>
        <div>
          <div className="meta be-kicker">
            BEST EFFORT · {met} OF {total} MET
          </div>
          <p className="be-lead">
            I built the closest plan I could, but couldn't fully satisfy
            everything. Here's what's honest about it:
          </p>
        </div>
      </div>

      <ul className="be-issues">
        {violations.map((v, i) => (
          <li key={i} className="be-issue">
            <span className="be-issue-glyph mono warn" aria-hidden="true">
              ✕
            </span>
            <div>
              <div className="be-issue-title">{titleFor(v.rule)}</div>
              <div className="be-issue-detail meta">{v.detail}</div>
            </div>
          </li>
        ))}
        <li className="be-issue">
          <span className="be-issue-glyph mono ok" aria-hidden="true">
            ✓
          </span>
          <div>
            <div className="be-issue-title">Everything else holds</div>
            <div className="be-issue-detail meta">
              Weather-checked · dated events on the right day.
            </div>
          </div>
        </li>
      </ul>
    </section>
  );
}

function titleFor(rule: string): string {
  switch (rule) {
    case "weather":
      return "Outdoor venue on a wet day";
    case "date":
      return "Dated event on the wrong day";
    case "repeat_type":
      return "Repeated venue type";
    case "max_per_day":
      return "Too many stops in a day";
    case "ungrounded":
      return "Venue not in the catalogue";
    default:
      return "Unmet constraint";
  }
}
