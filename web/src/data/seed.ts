/**
 * Fallback / seed data — ISOLATED from real API responses.
 *
 * Used only for: the default chips/example prompts, and a graceful offline
 * fallback plan if the backend is unreachable. Real plans always come from the
 * API (which has its own authoritative seed mode in src/api/seed.py). Never
 * merge this with a live response.
 */
import type { Plan } from "../api/client";

export interface Chip {
  id: string;
  label: string;
  on: boolean;
}

export const DEFAULT_CHIPS: Chip[] = [
  { id: "dates", label: "Sat–Sun 4–5 Jul", on: true },
  { id: "mitte", label: "Mitte", on: true },
  { id: "kreuzberg", label: "Kreuzberg", on: false },
  { id: "treptow", label: "Treptow", on: false },
  { id: "indoor", label: "Indoor-friendly", on: true },
  { id: "max3", label: "Max 3 / day", on: true },
  { id: "norepeat", label: "No repeats", on: true },
];

export const EXAMPLE_PROMPTS = [
  "Plan my Saturday 4 July 2026 — I like museums and lakes, max 3 things, avoid repeats",
  "A rainy-day Berlin weekend, mostly indoor, with one open-air evening",
];

export const PLACEHOLDER =
  "Plan my Saturday 4 July 2026 — I like museums and lakes, max 3 things, avoid repeats…";

/** Mirror of the backend seed scenario, for offline fallback only. */
export const FALLBACK_PLAN: Plan = {
  request:
    "Plan my weekend 4–5 July 2026. I like museums and lakes, max 3 things per day, no repeated types.",
  spec: {},
  costPerPerson: 104,
  bestEffort: false,
  final: "",
  steps: [],
  agentLog: [
    { title: "get_weather", detail: "Sat 70% rain → wet; Sun sunny" },
    { title: "search_venues", detail: "indoor museums + aquarium for the wet day" },
    { title: "search_venues", detail: "outdoor lakes + parks for the dry day" },
    { title: "finish", detail: "enough candidates to build a balanced plan" },
  ],
  constraints: {
    ok: true,
    perDay: "3 / 3 per day",
    perDayMet: true,
    noRepeat: true,
    noRepeatMet: true,
    weatherChecked: true,
    swaps: 1,
    violations: [],
  },
  days: [
    {
      label: "Saturday",
      date: "2026-07-04",
      wx: "rain",
      weatherReadout: "70% RAIN · 18°",
      weather: { rain_prob: 70, temp_max: 18, is_wet: true },
      slots: [
        {
          time: "MORNING",
          timestamp: "09:30",
          venue: { name: "Pergamonmuseum", type: "museum", area: "Mitte", indoor: true, hours: "10:00–18:00", date: null, cost: 14 },
          why: "Indoor heavy-hitter for a wet morning — dry and central.",
          swapped: false, swapNote: null, changed: false, changeNote: null,
        },
        {
          time: "AFTERNOON",
          timestamp: "14:00",
          venue: { name: "Sea Life Berlin", type: "aquarium", area: "Mitte", indoor: true, hours: "10:00–19:00", date: null, cost: 20 },
          why: "Stays indoors while it rains, and isn't a repeat of the museum.",
          swapped: true,
          swapNote: "Weather swap. Schlachtensee (lake) → Sea Life Berlin. Your lake moves to Sunday when it's dry.",
          changed: false, changeNote: null,
        },
        {
          time: "EVENING",
          timestamp: "19:00",
          venue: { name: "Markthalle Neun Street Food", type: "food", area: "Kreuzberg", indoor: true, hours: "Sat til 22:00", date: "2026-07-04", cost: 15 },
          why: "Covered street-food hall — dinner that doesn't care about the rain.",
          swapped: false, swapNote: null, changed: false, changeNote: null,
        },
      ],
    },
    {
      label: "Sunday",
      date: "2026-07-05",
      wx: "sun",
      weatherReadout: "SUNNY · 26°",
      weather: { rain_prob: 10, temp_max: 26, is_wet: false },
      slots: [
        {
          time: "MORNING",
          timestamp: "10:00",
          venue: { name: "Schlachtensee", type: "lake", area: "Zehlendorf", indoor: false, hours: "open", date: null, cost: 0 },
          why: "Your lake, now on the sunny day — best swimming 10:00–16:00.",
          swapped: false, swapNote: null, changed: false, changeNote: null,
        },
        {
          time: "AFTERNOON",
          timestamp: "14:30",
          venue: { name: "Tempelhofer Feld", type: "park", area: "Tempelhof", indoor: false, hours: "open", date: null, cost: 0 },
          why: "Wide-open park while the sun holds — no repeat of the lake.",
          swapped: false, swapNote: null, changed: false, changeNote: null,
        },
        {
          time: "EVENING",
          timestamp: "20:00",
          venue: { name: "Waldbuehne Open-Air Concert", type: "openair", area: "Westend", indoor: false, hours: null, date: "2026-07-05", cost: 55 },
          why: "Open-air concert pinned to its real date — outdoor finish on the dry day.",
          swapped: false, swapNote: null, changed: false, changeNote: null,
        },
      ],
    },
  ],
};
