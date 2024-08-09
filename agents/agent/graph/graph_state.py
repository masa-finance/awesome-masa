from typing import List, TypedDict
import logging

class GraphState(TypedDict):
    question: str
    generation: str
    search: str
    data: List[str]
    steps: List[str]

def retrieve(state):
    from agent.rag_agent import retriever  # Move import here
    logging.info(f"Retrieving data for question: {state['question']}")
    question = state["question"]
    data = retriever.invoke(question)
    steps = state["steps"]
    steps.append("retrieve_data")
    logging.info(f"Data retrieved for question: {question}")
    return {"data": data, "question": question, "steps": steps}

def generate(state):
    from agent.rag_agent import rag_chain  # Move import here
    logging.info(f"Generating answer for question: {state['question']}")
    question = state["question"]
    data = state["data"]
    generation = rag_chain.invoke({"data": data, "question": question})
    steps = state["steps"]
    steps.append("generate_answer")
    logging.info(f"Answer generated for question: {question}")
    return {
        "data": data,
        "question": question,
        "generation": generation,
        "steps": steps,
    }

def web_search(state):
    from agent.rag_agent import web_search_tool  # Move import here
    logging.info(f"Performing web search for question: {state['question']}")
    question = state["question"]
    data = state.get("data", [])
    steps = state["steps"]
    steps.append("web_search")
    web_results = web_search_tool.invoke({"query": question})
    data.extend(web_results)
    logging.info(f"Web search completed for question: {question}")
    return {"data": data, "question": question, "steps": steps}

def decide_to_generate(state):
    logging.info("Deciding whether to generate or search...")
    data = state.get("data", [])
    if not data:
        logging.info("No data found, deciding to search.")
        return "search"
    else:
        logging.info("Data found, deciding to generate.")
        return "generate"