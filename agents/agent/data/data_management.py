import logging
from src.agent.data.data_loader import load_documents
from src.agent.data.vector_store import create_vectorstore_and_retriever

def load_and_prepare_data(file_paths):
    logging.info("Loading data...")
    data = load_documents(file_paths)
    logging.info("Creating vectorstore and retriever...")
    retriever = create_vectorstore_and_retriever(data)
    return retriever