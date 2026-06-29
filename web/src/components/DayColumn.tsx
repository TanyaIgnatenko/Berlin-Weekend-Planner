import type { Day } from "../api/client";
import { SwapCallout } from "./SwapCallout";
import { VenueCard } from "./VenueCard";
import { WeatherStrip } from "./WeatherStrip";

export function DayColumn({ day }: { day: Day }) {
  return (
    <div className={`day-column ${day.wx}`}>
      <WeatherStrip day={day} />
      <div className="day-stack">
        {day.slots.map((slot, i) => (
          <div key={i} className="slot-wrap">
            {slot.swapped && slot.swapNote && (
              <SwapCallout kind="swap" text={slot.swapNote} />
            )}
            {slot.changed && slot.changeNote && (
              <SwapCallout kind="edit" text={slot.changeNote} />
            )}
            <VenueCard slot={slot} />
          </div>
        ))}
      </div>
    </div>
  );
}
