import sys
import os
import logging 
from agent.core.config import * 
from agent_config import DATA_URLS
from agent.data.data_management import load_and_prepare_data
from agent.rag.rag_chain_setup import setup_rag_chain
from agent.graph.graph_workflow import setup_workflow
from agent.search_tools.search_tools import get_web_search_tool 

# Get the absolute path of the current file
current_path = os.path.abspath(__file__)

# Navigate up to the agents directory (1 level up from rag_agent.py)
agents_dir = os.path.dirname(os.path.dirname(current_path))

# Add the agents directory to sys.path
sys.path.append(agents_dir)
# Setup
retriever = load_and_prepare_data(DATA_URLS)
rag_chain = setup_rag_chain()
graph = setup_workflow()
web_search_tool = get_web_search_tool()

def get_rag_response(question: str):
    logging.info(f"Generating response for question: {question}")
    response = graph.invoke({"question": question, "steps": []})
    return response["generation"], response["steps"]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        logging.info(f"Received question: {question}")
        answer, steps = get_rag_response(question)
        print(f"Answer: {answer}")
        print("\nSteps:")
        for step in steps:
            print(f"- {step}")
    else:
        print("Please provide a question as a command-line argument.")