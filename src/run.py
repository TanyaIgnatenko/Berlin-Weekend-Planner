"""CLI entry point.

    python -m src.run "Plan my Saturday 2026-07-04 in Berlin, I like museums and
                       lakes, max 3 things, avoid repeats"

Add --trace to turn on Phoenix.
"""
from __future__ import annotations

import sys

from src.graph.build import build_graph
from src.observability.phoenix_setup import init_tracing


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--trace"]
    if "--trace" in sys.argv:
        init_tracing()

    request = " ".join(args) or (
        "Plan my Saturday 2026-07-04 in Berlin. I like museums and lakes, "
        "max 3 things, avoid repeating the same type."
    )

    graph = build_graph()
    final_state = graph.invoke({"request": request})
    print("\n" + final_state.get("final", "(no plan produced)"))

    # quick peek at the agentic trace
    log = final_state.get("react_log", [])
    if log:
        print(f"\n[react_gather took {len(log)} steps, "
              f"{final_state.get('iterations', 0)} replans]")


if __name__ == "__main__":
    main()
