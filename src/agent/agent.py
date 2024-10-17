import os
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Configure logging
#logging.basicConfig(level=logging.INFO)

# Define the state
class GraphState(BaseModel):
    messages: List[dict] = Field(default_factory=list)
    prompt: str = ""
    retrieved_docs: List[Document] = Field(default_factory=list)
    generation: str = ""
    steps: List[str] = Field(default_factory=list)
    iterations: int = 0

    """Represents the state of the graph.

    Attributes:
        doc (Document): The document associated with the state.
    """
    doc: Optional[Document] = None

    class Config:
        """Pydantic configuration for the GraphState model."""
        arbitrary_types_allowed = True

# Agent class for retrieval
class RetrieveAgent:
    def __init__(self, retriever):
        self.retriever = retriever

    def __call__(self, state: GraphState):
        logging.info("Retrieving relevant documents...")
        question = state.prompt
        retrieved_docs = self.retriever.invoke(question)
        state.retrieved_docs = retrieved_docs
        state.steps.append("retrieved_docs")
        return state

# Agent class for generating response
class GenerateAgent:
    def __init__(self, env):
        self.env = env
        self.prompt_template = self.create_prompt_template()

    def create_prompt_template(self):
        """Sets up the prompt template for generating responses."""
        prompt = PromptTemplate(
            template="""You are an AI assistant specializing in analyzing and summarizing Twitter conversations about trading and cryptocurrency based on KOL tweet streams from the author's twitter replies. Your task is to provide concise, informative answers based on the given tweet data and my questions. It's currently July 28th 2024, so make sure you are getting data that is relevant to that date.

Guidelines:
1. Focus on extracting key information from the tweets, such as trading strategies, price movements, or market sentiment.
2. If the tweet mentions specific cryptocurrencies, trading pairs, or price levels, highlight these in your answer.
3. Provide context about the author's perspective or sentiment if relevant.
4. If the question asks about something not directly addressed in the tweets, say so, but offer a relevant insight from the available data if possible.
5. Keep your answer concise, vary your response between three to eight sentences, and use the system memory to improve your response from our previous chats. Do not use "Based on..." to start every response; be creative in your speech.

Relevant Tweet Data:
{data}""",
            input_variables=["data"],
        )
        return prompt

    def __call__(self, state: GraphState):
        """Generates a response based on the current state."""
        logging.info("Generating response...")
        question = state.prompt
        data_texts = "\n".join([doc.page_content for doc in state.retrieved_docs])

        # Prepare the prompt using the template
        prompt = self.prompt_template.format(data=data_texts)

        # Get the conversation history
        messages = self.env.list_messages()

        # Add the detailed prompt as a system message
        messages.append({"role": "system", "content": prompt})

        # Add the user's question as a user message
        messages.append({"role": "user", "content": question})

        # Call the language model
        response = self.env.completion(messages)
        state.generation = response
        state.steps.append("generated_answer")
        return state

def load_documents(file_path):
    """Load documents from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            tweet_data = json.load(file)
        docs = []
        for tweet_entry in tweet_data:
            if tweet_entry.get('Error') is None and 'Tweet' in tweet_entry:
                tweet = tweet_entry['Tweet']
                tweet_text = f"[Author: {tweet['Username']}] {tweet['Text']}"
                docs.append(Document(page_content=tweet_text))
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=0)
        split_docs = []
        for doc in docs:
            splits = text_splitter.split_text(doc.page_content)
            for split in splits:
                split_docs.append(Document(page_content=split))
        return split_docs
    except Exception as e:
        logging.error(f"Error loading tweets: {e}")
        return []

def create_vectorstore_and_retriever(documents):
    """
    Create vector store and retriever.

    :param documents: The list of documents.
    :type documents: List[Document]
    :return: The retriever object.
    :rtype: Retrieval
    """
    # Define tokenizer arguments to avoid the warning
    tokenizer_kwargs = {
        'clean_up_tokenization_spaces': True
    }

    # Initialize embeddings with tokenizer arguments
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={
            'tokenizer_kwargs': tokenizer_kwargs
        }
    )
    vectorstore = FAISS.from_documents(documents, embeddings)
    retriever = vectorstore.as_retriever(k=4)
    return retriever


# Define the main function
def main(env):
    """Main function to run the agent."""
    # Initialize the agent only once
    if not hasattr(main, "agent_initialized"):
        main.agent_initialized = True
        # Load and prepare data
        data_path = "data/twitter_data/memecoin_tweets.json"
        documents = load_documents(data_path)
        retriever = create_vectorstore_and_retriever(documents)
        # Assign agents
        main.retrieve_agent = RetrieveAgent(retriever)
        main.generate_agent = GenerateAgent(env)
        # Compile the graph
        graph_builder = StateGraph(GraphState)
        graph_builder.add_node("retrieve", main.retrieve_agent)
        graph_builder.add_node("generate", main.generate_agent)
        graph_builder.add_edge(START, "retrieve")
        graph_builder.add_edge("retrieve", "generate")
        graph_builder.add_edge("generate", END)
        main.graph = graph_builder.compile()

    messages = env.list_messages()
    next_actor = env.get_next_actor()

    if not messages:
        # No previous messages, initialize conversation
        env.set_next_actor("user")
        env.request_user_input()
        return

    if next_actor == "user":
        # After the user inputs a message, set next_actor to 'agent'
        env.set_next_actor("agent")
    elif next_actor == "agent":
        last_message = messages[-1]
        if last_message['role'] == 'user':
            question = last_message['content']
            initial_state = GraphState(prompt=question)
            # Invoke the graph and get the result
            result = main.graph.invoke(initial_state)
            agent_response = result['generation']
            # Add the agent's response to the environment
            env.add_message("agent", agent_response)
            env.set_next_actor("user")
    else:
        # Default behavior: request user input
        env.set_next_actor("user")
        env.request_user_input()
        return

    # Request user input if it's the user's turn
    if env.get_next_actor() == "user":
        env.request_user_input()


# Entry point for the agent
if __name__ == "__main__":
    main(env)