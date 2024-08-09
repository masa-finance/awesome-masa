import sys
import logging 
from agents.agent.data.data_management import load_and_prepare_data
from agents.agent.rag.rag_chain_setup import setup_rag_chain
from agents.agent.search_tools.search_tools import get_web_search_tool 

def initialize_rag(data_urls):
    # Setup
    retriever = load_and_prepare_data(data_urls)
    rag_chain = setup_rag_chain()
    web_search_tool = get_web_search_tool()
    return retriever, rag_chain, web_search_tool

def get_rag_response(question: str, rag_chain):
    logging.info(f"Generating response for question: {question}")
    response = rag_chain.invoke({"question": question, "data": ""})
    return response, []  # Return an empty list for steps as it's not used in this implementation

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