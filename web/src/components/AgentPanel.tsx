import type { AgentLogEntry } from "../api/client";
import type { RefineMessage } from "../hooks/usePlanner";
import { RefinePanel } from "./RefinePanel";

interface Props {
  log: AgentLogEntry[];
  messages: RefineMessage[];
  replanning: boolean;
  onRefine: (text: string) => void;
}

export function AgentPanel({ log, messages, replanning, onRefine }: Props) {
  return (
    <aside className="agent-panel" aria-label="Agent log and refine">
      <div className="agent-log-card">
        <div className="agent-log-head">
          <span className="status-dot green" aria-hidden="true" />
          <span className="meta">AGENT LOG</span>
          <span className="meta agent-log-count">{log.length} steps</span>
        </div>
        <ul className="agent-log-list">
          {log.map((e, i) => (
            <li key={i} className="agent-log-item">
              <span className="log-check mono" aria-hidden="true">
                ✓
              </span>
              <div>
                <div className="mono log-title">{e.title}</div>
                {e.detail && <div className="meta log-detail">{e.detail}</div>}
              </div>
            </li>
          ))}
        </ul>
      </div>

      <RefinePanel messages={messages} replanning={replanning} onSend={onRefine} />
    </aside>
  );
}
