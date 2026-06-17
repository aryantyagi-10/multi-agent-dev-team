from langgraph.graph import StateGraph, END

from backend.agents.state import AgentState
from backend.agents.nodes import (
    product_manager, developer, qa_engineer, route_after_qa
)


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("product_manager", product_manager)
    g.add_node("developer", developer)
    g.add_node("qa_engineer", qa_engineer)

    g.set_entry_point("product_manager")
    g.add_edge("product_manager", "developer")
    g.add_edge("developer", "qa_engineer")
    g.add_conditional_edges(
        "qa_engineer",
        route_after_qa,
        {"developer": "developer", "end": END},
    )
    return g.compile()


compiled_graph = build_graph()
