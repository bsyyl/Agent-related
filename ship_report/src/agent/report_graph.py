from langgraph.graph import END, START, StateGraph

from .message import ReportState
from .outline import outline_search_node, outline_node
from .learning import learning_node
from .generate import generate_node, save_local_node, save_report_local


def build_report_graph():
    """
    Report agent graph.

    Responsibilities:
    - Search outline knowledge
    - Generate outline (Chapter tree)
    - Deep research per chapter
    - Generate final report
    - Optionally save to local (md/html)
    """
    g = StateGraph(ReportState)

    g.add_node("outline_search", outline_search_node)
    g.add_node("outline", outline_node)
    g.add_node("learning", learning_node)
    g.add_node("generate", generate_node)
    g.add_node("save_local_node", save_local_node)

    g.add_edge(START, "outline_search")
    g.add_edge("outline_search", "outline")
    g.add_edge("learning", "generate")

    g.add_conditional_edges(
        "generate",
        save_report_local,
        ["save_local_node", END],
    )

    return g.compile()

