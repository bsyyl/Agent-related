from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from .message import ReportState
from .prep import preprocess_node, rewrite_node, classify_node, clarify_node, generic_node


def handoff_to_report_node(state: ReportState):
    # Mark that router finished and report flow should run next.
    return Command(update={"next_agent": "report"}, goto="__end__")


def build_router_graph():
    """
    Router agent graph.

    Responsibilities:
    - Normalize input messages
    - Rewrite topic (if needed)
    - Classify domain / load logic & details
    - Optional clarification (1 round)
    - Decide whether to continue to report agent or finish via generic response
    """
    g = StateGraph(ReportState)

    g.add_node("preprocess", preprocess_node)
    g.add_node("rewrite", rewrite_node)
    g.add_node("classify", classify_node)
    g.add_node("clarify", clarify_node)
    g.add_node("generic", generic_node)
    g.add_node("handoff_to_report", handoff_to_report_node)

    g.add_edge(START, "preprocess")
    g.add_edge("rewrite", "classify")

    # Terminal route for the router agent.
    g.add_edge("generic", END)
    g.add_edge("handoff_to_report", END)

    return g.compile()

