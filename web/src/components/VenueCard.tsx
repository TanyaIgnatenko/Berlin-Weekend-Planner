import type { Slot } from "../api/client";

export function VenueCard({ slot }: { slot: Slot }) {
  const { venue } = slot;
  // left accent border: ochre when weather-swapped, green when refine-edited
  const variant = slot.swapped ? "swapped" : slot.changed ? "changed" : "";

  const eventOrHours = venue.date
    ? `${formatEventDate(venue.date)}`
    : venue.hours ?? "";
  const meta = [cap(venue.type), venue.area, eventOrHours].filter(Boolean).join(" · ");

  return (
    <article className={`venue-card ${variant}`}>
      <div className="vc-top">
        <span className="mono vc-time">
          {slot.time}
          {slot.timestamp && <> · {slot.timestamp}</>}
        </span>
        <span className={`env-label mono ${venue.indoor ? "indoor" : "outdoor"}`}>
          {venue.indoor ? "INDOOR" : "OUTDOOR"}
        </span>
      </div>
      <h3 className="vc-name">{venue.name}</h3>
      <div className="mono vc-meta">{meta}</div>
      {venue.cost > 0 && <div className="mono vc-cost">€{formatCost(venue.cost)}</div>}
      <div className="vc-divider" />
      <div className="vc-why">
        <span className="mono why-tag">WHY</span>
        <span className="why-text">{slot.why}</span>
      </div>
    </article>
  );
}

function cap(s: string): string {
  return s ? s[0].toUpperCase() + s.slice(1) : s;
}
function formatCost(c: number): string {
  return Number.isInteger(c) ? String(c) : c.toFixed(2).replace(/\.00$/, "");
}
function formatEventDate(iso: string): string {
  try {
    const d = new Date(iso + "T00:00:00");
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  } catch {
    return iso;
  }
}
