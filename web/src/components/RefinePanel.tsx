import { useState } from "react";
import type { RefineMessage } from "../hooks/usePlanner";

interface Props {
  messages: RefineMessage[];
  replanning: boolean;
  onSend: (text: string) => void;
}

const QUICK = ["Make it cheaper", "Swap Sunday afternoon", "More outdoor"];

export function RefinePanel({ messages, replanning, onSend }: Props) {
  const [text, setText] = useState("");

  const send = (v: string) => {
    const t = v.trim();
    if (!t || replanning) return;
    onSend(t);
    setText("");
  };

  return (
    <div className="refine">
      <div className="refine-head meta">REFINE</div>

      {messages.length > 0 && (
        <div className="chat" aria-live="polite" aria-label="Refine conversation">
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role}`}>
              {m.text}
            </div>
          ))}
          {replanning && (
            <div className="replanning mono">
              <span className="pulse-dot small" aria-hidden="true" />
              Re-planning…
            </div>
          )}
        </div>
      )}

      <div className="quick-chips">
        {QUICK.map((q) => (
          <button key={q} className="ghost-chip small" onClick={() => send(q)} disabled={replanning}>
            {q}
          </button>
        ))}
      </div>

      <div className="refine-input-row">
        <label htmlFor="refine-input" className="sr-only">
          Refine the plan
        </label>
        <input
          id="refine-input"
          className="refine-input"
          placeholder="Adjust the plan…"
          value={text}
          disabled={replanning}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") send(text);
          }}
        />
        <button
          className="send-btn mono"
          aria-label="Send refine"
          onClick={() => send(text)}
          disabled={replanning}
        >
          →
        </button>
      </div>
    </div>
  );
}
