"""Data models shared across the graph.

These are the contracts between nodes. Keep them small — every field here is
something the validator can check or the planner can ground on.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

VenueType = Literal["museum", "gallery", "zoo", "aquarium", "pool", "lake",
                    "park", "market", "concert", "exhibition", "openair", "food"]


class Venue(BaseModel):
    """One place or event in data/venues.json."""
    name: str
    type: VenueType
    indoor: bool
    area: str
    # Exactly one of `hours` / `date` is meaningful:
    #   - fixed-hours places (museum, pool): hours = "10:00-18:00" or "open"
    #   - dated events (concert, market): date = "2026-07-04"
    hours: Optional[str] = None
    date: Optional[str] = None
    # Approx entry cost per person in EUR (0 = free). Powers the derived
    # "€ / person" summary and budget-based refines on the frontend.
    cost: float = 0.0


class PlanRequest(BaseModel):
    """Structured intent parsed from the user's free text (parse_request node)."""
    dates: list[str] = Field(default_factory=list)          # ISO dates, e.g. ["2026-07-04"]
    liked_types: list[VenueType] = Field(default_factory=list)
    disliked_types: list[VenueType] = Field(default_factory=list)
    preferred_areas: list[str] = Field(default_factory=list)
    max_per_day: int = 3
    avoid_repeat_types: bool = True
    notes: str = ""


class PlanItem(BaseModel):
    date: str
    slot: str            # "morning" | "afternoon" | "evening" — free text is fine
    venue: str           # must match a Venue.name that was actually gathered
    reason: str = ""


class Violation(BaseModel):
    item: str            # which plan item / venue
    rule: str            # which constraint was broken
    detail: str


class ValidationResult(BaseModel):
    ok: bool
    violations: list[Violation] = Field(default_factory=list)
