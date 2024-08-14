import sys
import os
import logging
import time
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from dotenv import load_dotenv

st.set_page_config(page_title="Masa Chat", page_icon="💬")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URLs for data loading
DATA_URLS = [
    "data/__Bitcoin_Price__.json",
]

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.append(project_root)

from src.agent import rag_agent

# Initialize the agent only once per session
@st.cache_resource
def initialize_agent_cached():
    return rag_agent.initialize_agent(DATA_URLS)

# Use the cached agent initialization
graph = initialize_agent_cached()

def get_streaming_rag_response(question: str):
    logging.info(f"Generating response for question: {question}")
    try:
        response, steps = rag_agent.get_rag_response(graph, question)
        if not response:
            yield "No response generated."
        else:
            # Split the response into chunks based on full stops followed by a space
            chunks = response.split('. ')
            for chunk in chunks:
                # Check if the chunk ends with a full stop, if not, add it
                if not chunk.endswith('.'):
                    chunk += '.'
                # Add a space after commas for better readability
                chunk = chunk.replace(',', ', ')
                # Replace bullet points with markdown bullets and newlines if necessary
                chunk = chunk.replace("•", "\n\n• ")
                yield chunk + " "
                time.sleep(0.65)  # Simulate typing for each chunk
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        yield "An error occurred while generating the response."

st.title("💬 Masa Chat")

st.markdown("""
    Welcome to the Masa Dataset Chat!
    
    This interactive application is designed to let you explore and interact with datasets scraped by the Masa protocol. 
    It leverages a sophisticated AI to provide insights, answer questions, and facilitate understanding of complex datasets.
    
    Dive into the data collected by Masa, ask questions, and uncover hidden insights with the help of our AI assistant.
""")

st.markdown("---")

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

def display_chat_history():
    for msg in st.session_state['message_history']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

display_chat_history()

if prompt := st.chat_input("Ask a question:"):
    st.session_state.message_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Display thinking animation
        thinking_placeholder = st.empty()
        with thinking_placeholder:
            for i in range(3):
                for dot in [".", "..", "..."]:
                    thinking_placeholder.markdown(f"Thinking{dot}")
                    time.sleep(0.3)
        
        # Start streaming the response
        try:
            for chunk in get_streaming_rag_response(prompt):
                thinking_placeholder.empty()  # Remove thinking animation
                full_response += chunk
                # Display the response directly without appending cursor-like character
                message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"An error occurred: {e}")

    st.session_state.message_history.append({"role": "assistant", "content": full_response})

add_vertical_space(5)