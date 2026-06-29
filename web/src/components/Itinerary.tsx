import { useState } from "react";
import type { Plan } from "../api/client";
import type { RefineMessage } from "../hooks/usePlanner";
import { AgentPanel } from "./AgentPanel";
import { BestEffortBanner } from "./BestEffortBanner";
import { ConstraintSummary } from "./ConstraintSummary";
import { DayColumn } from "./DayColumn";

interface Props {
  plan: Plan;
  messages: RefineMessage[];
  replanning: boolean;
  onRefine: (text: string) => void;
}

export function Itinerary({ plan, messages, replanning, onRefine }: Props) {
  const [activeDay, setActiveDay] = useState(0);

  return (
    <section className="itinerary" aria-labelledby="itin-h">
      <div className="itin-header">
        <p className="eyebrow">YOUR WEEKEND · PLANNED & EXPLAINED</p>
        <h1 id="itin-h" className="itin-echo">
          {plan.request}
        </h1>
      </div>

      <ConstraintSummary constraints={plan.constraints} costPerPerson={plan.costPerPerson} />

      {plan.bestEffort && <BestEffortBanner constraints={plan.constraints} />}

      {/* mobile-only day tabs */}
      <div className="day-tabs" role="tablist" aria-label="Choose a day">
        {plan.days.map((d, i) => (
          <button
            key={d.date}
            role="tab"
            aria-selected={activeDay === i}
            className={`day-tab${activeDay === i ? " active" : ""}`}
            onClick={() => setActiveDay(i)}
          >
            {d.label}
          </button>
        ))}
      </div>

      <div className="itin-grid">
        {plan.days.map((d, i) => (
          <div
            key={d.date}
            className={`day-slot${activeDay === i ? " active" : " inactive"}`}
          >
            <DayColumn day={d} />
          </div>
        ))}

        <AgentPanel
          log={plan.agentLog}
          messages={messages}
          replanning={replanning}
          onRefine={onRefine}
        />
      </div>
    </section>
  );
}
