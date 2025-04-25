import os
import streamlit as st
from agent import Research_Agent  # Import your agent class

os.environ["PATH"] = ".env"
st.secrets["PATH"]

# Title of the page
st.set_page_config(page_title="Web Research Agent")
st.title("🔎 Web Research Agent")

# Initialize agent (this will create the LangChain agent)
if "agent" not in st.session_state:
    st.session_state.agent = Research_Agent()

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "research_history" not in st.session_state:
    st.session_state.research_history = {}
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = 0

# Sidebar for history navigation
with st.sidebar:
    st.title("Research History")

    # Button to start a new research session
    if st.button("New Research Session"):
        # Create a new session ID
        new_session_id = max(list(st.session_state.research_history.keys()) + [0]) + 1
        st.session_state.current_session_id = new_session_id
        st.session_state.messages = []
        st.session_state.research_history[new_session_id] = []
        # Keep the same agent to maintain memory across sessions
        # st.experimental_rerun()
        st.rerun()

    # Display past research sessions
    st.subheader("Past Sessions")
    for session_id in sorted(st.session_state.research_history.keys(), reverse=True):
        # Get the first message of each session to use as title
        session_messages = st.session_state.research_history[session_id]
        if session_messages:
            first_message = next(
                (msg["content"] for msg in session_messages if msg["role"] == "user"), f"Session {session_id}")
            title = first_message[:30] + "..." if len(first_message) > 30 else first_message
        else:
            title = f"Session {session_id}"

        if st.button(f"{title}", key=f"session_{session_id}"):
            st.session_state.current_session_id = session_id
            st.session_state.messages = st.session_state.research_history[session_id].copy()
            # st.experimental_rerun()
            st.rerun()

# Main area for current research session
# Ensure current session exists in research_history
if st.session_state.current_session_id not in st.session_state.research_history:
    st.session_state.research_history[st.session_state.current_session_id] = st.session_state.messages.copy(
    )

# Show previous messages in current session
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get input for current session
if prompt := st.chat_input("Ask me to research something..."):
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Researching the web... (This may take a moment)"):
            try:
                # Run the agent - let it decide which tools to use
                response, news = st.session_state.agent.run(prompt)
            except Exception as e:
                response = f"❌ Error: {e}"
                news = []

        st.markdown(response)

        # Add assistant response to session state
        assistant_message = {"role": "assistant", "content": response}
        st.session_state.messages.append(assistant_message)

        # Update research history
        st.session_state.research_history[st.session_state.current_session_id] = st.session_state.messages.copy(
        )

# Add export functionality
with st.sidebar:
    if st.session_state.messages:
        if st.button("Export Current Session"):
            # Generate text for download
            export_text = ""
            for msg in st.session_state.messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                export_text += f"## {role}:\n{msg['content']}\n\n"

            # Create download button
            st.download_button(
                label="Download as Text",
                data=export_text,
                file_name=f"research_session_{st.session_state.current_session_id}.md",
                mime="text/markdown"
            )
