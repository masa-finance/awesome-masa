import logging
from langgraph.graph import StateGraph
from src.agent.graph.graph_state import GraphState, retrieve, generate, web_search, decide_to_generate

def setup_workflow():
    logging.info("Setting up the workflow graph...")
    workflow = StateGraph(GraphState)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)
    workflow.add_node("web_search", web_search)

    workflow.set_entry_point("retrieve")
    workflow.add_conditional_edges(
        "retrieve",
        decide_to_generate,
        {
            "search": "web_search",
            "generate": "generate",
        },
    )
    workflow.add_edge("web_search", "generate")

    graph = workflow.compile()
    return graph