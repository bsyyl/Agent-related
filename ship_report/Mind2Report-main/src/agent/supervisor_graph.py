from langgraph.graph import END, START, StateGraph

from .message import ReportState
from .router_graph import build_router_graph
from .report_graph import build_report_graph


router_graph = build_router_graph()
report_graph = build_report_graph()


def run_router_agent(state: ReportState, config):
    # Run router subgraph; it will either finish (generic/clarify confirm)
    # or set next_agent="report" to hand off to the report agent.
    result = router_graph.invoke(state, config=config)
    return result


def route_after_router(state: ReportState):
    return "report" if state.get("next_agent") == "report" else "__end__"


def run_report_agent(state: ReportState, config):
    # Clear marker to avoid accidental re-routing.
    if "next_agent" in state:
        state = dict(state)
        state.pop("next_agent", None)
    return report_graph.invoke(state, config=config)


def build_supervisor_graph():
    """
    Supervisor graph (multi-agent orchestrator).

    Flow:
    START -> router_agent -> (report_agent | END)
    """
    g = StateGraph(ReportState)
    g.add_node("router_agent", run_router_agent)
    g.add_node("report_agent", run_report_agent)

    g.add_edge(START, "router_agent")
    g.add_conditional_edges(
        "router_agent",
        route_after_router,
        ["report_agent", END],
    )
    g.add_edge("report_agent", END)

    return g.compile()

