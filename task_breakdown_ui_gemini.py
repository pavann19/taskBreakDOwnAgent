import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load API key ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY not found in .env file!")
    st.stop()

genai.configure(api_key=api_key)

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

FAQ_SUGGESTIONS = [
    "Build a REST API in Python",
    "Create a chatbot using Flask",
    "Build a Snake game",
]

# --- Gemini Streaming ---
def stream_gemini_reply(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    stream = model.generate_content(prompt, stream=True)
    full_response = ""
    for chunk in stream:
        if chunk.text:
            full_response += chunk.text
            yield full_response

# --- Task Breakdown Prompt ---
def build_task_breakdown_prompt(task):
    return f"""
    You are a Task Breakdown Agent.
    Break the following high-level task into clear, numbered subtasks.
    For each subtask, explain:
    1. What to do
    2. Why it’s important
    3. Tools or skills needed
    Task: {task}
    """

# --- Page Config ---
st.set_page_config(page_title="Task Breakdown Chat", page_icon="🛠", layout="centered")

# --- Intro Screen ---
if not st.session_state.messages:
    st.markdown(
        """
        <div style='text-align: center; margin-top: 20%;'>
            <h1>🛠 Task Breakdown Chat</h1>
            <p style='font-size: 18px;'>Ask about any task, or click a suggestion to get started.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Suggestion Buttons
    cols = st.columns(len(FAQ_SUGGESTIONS))
    for i, suggestion in enumerate(FAQ_SUGGESTIONS):
        if cols[i].button(suggestion):
            st.session_state.messages.append({"role": "user", "content": suggestion})
            with st.chat_message("user"):
                st.markdown(suggestion)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_reply = ""
                for chunk in stream_gemini_reply(build_task_breakdown_prompt(suggestion)):
                    full_reply = chunk
                    placeholder.markdown(full_reply)
                st.session_state.messages.append({"role": "assistant", "content": full_reply})
            st.stop()

# --- Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Permanent Input Box ---
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_reply = ""
        for chunk in stream_gemini_reply(build_task_breakdown_prompt(prompt)):
            full_reply = chunk
            placeholder.markdown(full_reply)
        st.session_state.messages.append({"role": "assistant", "content": full_reply})
