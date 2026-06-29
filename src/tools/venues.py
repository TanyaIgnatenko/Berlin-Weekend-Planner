"""Tool: search_venues.

Reads the local data/venues.json. From the graph's point of view this is an
external data source — it returns the same shape a live events/Maps API would.
Swapping it for a real API later means changing only this file (see backlog).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.schema import Venue

_DATA = Path(__file__).resolve().parents[2] / "data" / "venues.json"


def _load() -> list[Venue]:
    raw = json.loads(_DATA.read_text(encoding="utf-8"))
    return [Venue(**v) for v in raw]


def search_venues(
    type: Optional[str] = None,
    indoor: Optional[bool] = None,
    area: Optional[str] = None,
    date: Optional[str] = None,
) -> list[dict]:
    """Filter the local catalogue. All args optional; None means 'don't filter'.

    The ReAct node calls this with whatever slice it currently needs, e.g.
    search_venues(indoor=True) when it has just learned the weather is bad.
    """
    out = []
    for v in _load():
        if type is not None and v.type != type:
            continue
        if indoor is not None and v.indoor != indoor:
            continue
        if area is not None and area.lower() not in v.area.lower():
            continue
        if date is not None and v.date is not None and v.date != date:
            continue
        out.append(v.model_dump())
    return out


def all_types() -> list[str]:
    return sorted({v.type for v in _load()})
