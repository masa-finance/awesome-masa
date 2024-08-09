from langchain_community.vectorstores import SKLearnVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

def create_vectorstore_and_retriever(data):
    # Convert text to Document objects
    documents = [Document(page_content=text) for text in data]
    
    vectorstore = SKLearnVectorStore.from_documents(
        documents=documents,
        embedding=OpenAIEmbeddings(),
    )
    retriever = vectorstore.as_retriever(k=4)
    return retriever