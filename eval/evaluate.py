"""Offline eval harness — the metrics half of the Mercanis 'evaluation' bullet.

Runs eval/cases.json through the graph and reports:
  - constraint-satisfaction rate (validation.ok)
  - avg replan iterations
  - avg react steps
  - groundedness (every planned venue exists in candidates)

    python -m eval.evaluate            # run all cases
With Phoenix running (--trace), each run also shows up as a traced session.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.graph.build import build_graph
from src.observability.phoenix_setup import init_tracing

_CASES = Path(__file__).resolve().parent / "cases.json"


def groundedness(state: dict) -> float:
    names = {v["name"] for v in state.get("candidates", [])}
    plan = state.get("plan", [])
    if not plan:
        return 0.0
    return sum(1 for it in plan if it["venue"] in names) / len(plan)


def main() -> None:
    if "--trace" in sys.argv:
        init_tracing("berlin-weekend-planner-eval")

    cases = json.loads(_CASES.read_text(encoding="utf-8"))
    graph = build_graph()

    ok, replans, steps, grounded = 0, [], [], []
    for c in cases:
        st = graph.invoke({"request": c["request"]})
        passed = st.get("validation", {}).get("ok", False)
        ok += int(passed)
        replans.append(st.get("iterations", 0))
        steps.append(len(st.get("react_log", [])))
        grounded.append(groundedness(st))
        print(f"  [{ 'PASS' if passed else 'FAIL'}] {c['id']:16} "
              f"replans={st.get('iterations',0)} grounded={grounded[-1]:.2f}")

    n = len(cases)
    print("\n--- summary ---")
    print(f"constraint-satisfaction rate : {ok}/{n} = {ok/n:.0%}")
    print(f"avg replan iterations        : {sum(replans)/n:.2f}")
    print(f"avg react steps              : {sum(steps)/n:.2f}")
    print(f"avg groundedness             : {sum(grounded)/n:.2f}")


if __name__ == "__main__":
    main()
