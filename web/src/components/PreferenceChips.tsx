import type { Chip } from "../data/seed";

interface Props {
  chips: Chip[];
  onToggle: (id: string) => void;
}

export function PreferenceChips({ chips, onToggle }: Props) {
  return (
    <div className="chip-row" role="group" aria-label="Preferences">
      <span className="meta chip-label">PREFERENCES</span>
      {chips.map((c) => (
        <button
          key={c.id}
          type="button"
          className={`pref-chip${c.on ? " on" : ""}`}
          aria-pressed={c.on}
          onClick={() => onToggle(c.id)}
        >
          <span className="chip-dot" aria-hidden="true" />
          {c.label}
        </button>
      ))}
    </div>
  );
}
