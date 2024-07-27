import streamlit as st
import ollama

def get_ai_response(messages):
    try:
        response = ollama.chat(
            model="llama3.1",
            messages=messages
        )
        return response['message']['content']
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def main():
    st.title("LLama 3.1 Chatbot")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What is your message?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        ai_response = get_ai_response(st.session_state.messages)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(ai_response)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

if __name__ == "__main__":
    main()