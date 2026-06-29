import type { ReactNode } from "react";
import type { Constraints } from "../api/client";

interface Props {
  constraints: Constraints;
  costPerPerson: number;
}

export function ConstraintSummary({ constraints, costPerPerson }: Props) {
  const c = constraints;
  return (
    <div className="constraint-row mono" role="list" aria-label="Constraint summary">
      <Pill ok={c.perDayMet}>
        {c.perDayMet ? "✓" : "✕"} {c.perDay}
      </Pill>
      {c.noRepeat && (
        <Pill ok={c.noRepeatMet}>{c.noRepeatMet ? "✓" : "✕"} No repeated types</Pill>
      )}
      <Pill ok={c.weatherChecked}>
        {c.weatherChecked ? "✓" : "·"} All weather-checked
      </Pill>
      {c.swaps > 0 && (
        <span className="pill ochre">
          ↺ {c.swaps} weather swap{c.swaps > 1 ? "s" : ""}
        </span>
      )}
      <span className="pill neutral">€ ≈ €{formatCost(costPerPerson)} / person</span>
    </div>
  );
}

function Pill({ ok, children }: { ok: boolean; children: ReactNode }) {
  return <span className={`pill ${ok ? "success" : "warn"}`} role="listitem">{children}</span>;
}

function formatCost(c: number): string {
  return Number.isInteger(c) ? String(c) : c.toFixed(2).replace(/\.00$/, "");
}
