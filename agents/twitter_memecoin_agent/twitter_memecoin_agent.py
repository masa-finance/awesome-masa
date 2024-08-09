import sys
import os
import logging
import time
import streamlit as st
# Import add_logo from streamlit_extras
from streamlit_extras.app_logo import add_logo
from streamlit_extras.add_vertical_space import add_vertical_space


# Get the absolute path of the current file
current_path = os.path.abspath(__file__)

# Navigate up to the agents directory (2 levels up from twitter_memecoin_agent.py)
agents_dir = os.path.dirname(os.path.dirname(current_path))

# Add the agents directory to sys.path
sys.path.append(agents_dir)

# Now import rag_agent
from agent.rag_agent import get_rag_response, graph


def get_streaming_rag_response(question: str):
    logging.info(f"Generating response for question: {question}")
    response, steps = get_rag_response(question)
    
    words = response.split()
    for word in words:
        yield word + " "
        time.sleep(0.05)  # Adjust this delay as needed

# Set page config and add logo
st.set_page_config(page_title="Chat", page_icon="💬")
# Use add_logo to add a custom logo to the navigation bar
logo_path = os.path.join(os.path.dirname(__file__), '..', 'logo.png')
add_logo(logo_path, height=120)

st.title("💬 Masa Chat")

st.markdown("""
    Welcome to the Masa Dataset Chat!
    
    This interactive chat interface allows you to ask questions about the datasets you explored in the Datasets page.
    Our AI assistant will provide insights and answer your queries based on the available data.
    
    Start by asking a question about any of the datasets you're interested in.
""")

st.markdown("---")

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

def display_chat_history():
    for msg in st.session_state['message_history']:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

display_chat_history()

if prompt := st.chat_input("Ask a question about the datasets:"):
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