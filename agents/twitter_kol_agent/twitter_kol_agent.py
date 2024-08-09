import sys
import os
import logging
import time
import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.append(project_root)

from agents.agent.rag_agent import get_rag_response, initialize_rag
from agents.twitter_kol_agent.agent_config import DATA_URLS

# Initialize the RAG components
retriever, rag_chain, web_search_tool = initialize_rag(DATA_URLS)

def get_streaming_rag_response(question: str):
    logging.info(f"Generating response for question: {question}")
    response, _ = get_rag_response(question, rag_chain)
    
    words = response.split()
    for word in words:
        yield word + " "
        time.sleep(0.05)  # Adjust this delay as needed

st.set_page_config(page_title="Masa Chat", page_icon="💬")
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
        for chunk in get_streaming_rag_response(prompt):
            thinking_placeholder.empty()  # Remove thinking animation
            full_response += chunk
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    st.session_state.message_history.append({"role": "assistant", "content": full_response})

add_vertical_space(5)