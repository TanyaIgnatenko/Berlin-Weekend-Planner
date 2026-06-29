import type { Day } from "../api/client";

export function WeatherStrip({ day }: { day: Day }) {
  return (
    <div className={`wx-strip ${day.wx}`}>
      <div className="wx-left">
        <span className="wx-day">{day.label}</span>
        <span className="meta wx-date">{formatDate(day.date)}</span>
      </div>
      <div className="wx-right">
        <span className={`wx-dot ${day.wx}`} aria-hidden="true" />
        <span className="mono wx-readout">{day.weatherReadout}</span>
      </div>
    </div>
  );
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso + "T00:00:00");
    return d
      .toLocaleDateString("en-GB", { day: "numeric", month: "short" })
      .toUpperCase();
  } catch {
    return iso;
  }
}
