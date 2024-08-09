import logging
from langgraph.graph import StateGraph
from agents.agent.graph.graph_state import GraphState, retrieve, generate, web_search, decide_to_generate
from agents.agent.rag_agent import initialize_rag
from agents.agent.data.data_management import load_and_prepare_data
from agents.agent.rag.rag_chain_setup import setup_rag_chain
from agents.agent.search_tools.search_tools import get_web_search_tool

def setup_workflow(data_urls):
    logging.info("Setting up the workflow graph...")
    retriever, rag_chain, web_search_tool = initialize_rag(data_urls)
    
    workflow = StateGraph(GraphState)
    workflow.add_node("retrieve", lambda x: retrieve(x, retriever))
    workflow.add_node("generate", lambda x: generate(x, rag_chain))
    workflow.add_node("web_search", lambda x: web_search(x, web_search_tool))

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
    return graph, retriever, rag_chain, web_search_tool