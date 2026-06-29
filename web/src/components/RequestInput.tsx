import { useState } from "react";
import { PreferenceChips } from "./PreferenceChips";
import { EXAMPLE_PROMPTS, PLACEHOLDER, type Chip } from "../data/seed";

interface Props {
  request: string;
  setRequest: (v: string) => void;
  chips: Chip[];
  onToggle: (id: string) => void;
  onSubmit: (text?: string) => void;
}

export function RequestInput({ request, setRequest, chips, onToggle, onSubmit }: Props) {
  const [focused, setFocused] = useState(false);

  return (
    <section className="input-screen" aria-labelledby="input-h1">
      <p className="eyebrow">A PLANNER THAT SHOWS ITS THINKING</p>
      <h1 id="input-h1" className="hero-h1">
        Tell me your weekend. I'll plan it — and show every decision.
      </h1>
      <p className="hero-sub">
        One free-text request becomes a day-by-day Berlin plan. It checks live
        weather, self-corrects outdoor → indoor when it rains, and explains
        every choice as it reasons.
      </p>

      <div className={`request-card${focused ? " focused" : ""}`}>
        <label htmlFor="request" className="sr-only">
          Describe your weekend
        </label>
        <textarea
          id="request"
          className="request-textarea"
          placeholder={PLACEHOLDER}
          value={request}
          onChange={(e) => setRequest(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSubmit();
          }}
          rows={3}
        />
        <PreferenceChips chips={chips} onToggle={onToggle} />
        <div className="request-footer">
          <span className="meta">Live weather · self-correcting</span>
          <button className="cta-btn" onClick={() => onSubmit()}>
            Plan my weekend →
          </button>
        </div>
      </div>

      <div className="examples">
        <span className="meta">Try:</span>
        {EXAMPLE_PROMPTS.map((p) => (
          <button
            key={p}
            className="ghost-chip"
            onClick={() => {
              setRequest(p);
            }}
          >
            {p.length > 54 ? p.slice(0, 54) + "…" : p}
          </button>
        ))}
      </div>
    </section>
  );
}
