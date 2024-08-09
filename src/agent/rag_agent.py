import logging 
from src.agent.data.data_management import load_and_prepare_data
from src.agent.rag.rag_chain_setup import setup_rag_chain
from src.agent.graph.graph_workflow import setup_workflow
from src.agent.search_tools.search_tools import get_web_search_tool 

# Global variables to store the retriever, rag_chain, and web_search_tool
retriever = None
rag_chain = None
web_search_tool = None

def initialize_agent(data_urls):
    global retriever, rag_chain, web_search_tool
    retriever = load_and_prepare_data(data_urls)
    rag_chain = setup_rag_chain()
    graph = setup_workflow()
    web_search_tool = get_web_search_tool()
    return graph

def get_rag_response(graph, question: str):
    logging.info(f"Generating response for question: {question}")
    response = graph.invoke({"question": question, "steps": []})
    return response["generation"], response["steps"]