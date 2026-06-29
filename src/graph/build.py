"""Wire the nodes into a LangGraph StateGraph.

Flow:
    parse_request -> react_gather -> plan -> validate -> (ok? finalize : replan -> plan)
The replan->plan edge is the self-correction loop; route_after_validate is the
conditional edge that closes it.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.graph.nodes import (finalize, parse_request, plan, react_gather,
                             replan, route_after_validate, validate)
from src.graph.state import PlannerState


def build_graph():
    g = StateGraph(PlannerState)

    g.add_node("parse_request", parse_request)
    g.add_node("react_gather", react_gather)
    g.add_node("plan", plan)
    g.add_node("validate", validate)
    g.add_node("replan", replan)
    g.add_node("finalize", finalize)

    g.add_edge(START, "parse_request")
    g.add_edge("parse_request", "react_gather")
    g.add_edge("react_gather", "plan")
    g.add_edge("plan", "validate")
    g.add_conditional_edges("validate", route_after_validate,
                            {"finalize": "finalize", "replan": "replan"})
    g.add_edge("replan", "plan")
    g.add_edge("finalize", END)

    return g.compile()
