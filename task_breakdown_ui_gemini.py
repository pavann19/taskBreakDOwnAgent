import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# --- Constants ---
MODEL_NAME = "gemini-1.5-flash-latest"
PAGE_TITLE = "Task Breakdown Chat"
PAGE_ICON = "🛠️"
FAQ_SUGGESTIONS = [
    "Build a REST API in Python",
    "Create a chatbot using Flask",
    "Build a Snake game",
]

# --- Functions ---

def configure_genai():
    """
    Loads the Google API key from .env and configures the genai library.
    Shows an error and stops the app if the key is not found.
    """
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("❌ GOOGLE_API_KEY not found in .env file!")
        st.stop()
    genai.configure(api_key=api_key)

def build_task_breakdown_prompt(task: str) -> str:
    """
    Creates a detailed prompt for the Gemini model to act as a task breakdown agent.
    """
    return f"""
    You are a Task Breakdown Agent.
    Break the following high-level task into clear, numbered subtasks.
    For each subtask, explain:
    1. What to do
    2. Why it’s important
    3. Tools or skills needed
    
    Task: {task}
    """

def stream_gemini_reply(prompt: str):
    """
    Calls the Gemini API with the given prompt and streams back the text chunks.
    """
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        stream = model.generate_content(prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        st.error(f"An error occurred with the Gemini API: {e}")
        yield "Sorry, I couldn't process your request. Please try again."

def handle_new_message(prompt: str):
    """
    Central function to process a new user prompt.
    """
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Display assistant response
    with st.chat_message("assistant"):
        agent_prompt = build_task_breakdown_prompt(prompt)
        response_generator = stream_gemini_reply(agent_prompt)
        full_response = st.write_stream(response_generator)
    
    # Add assistant response to state
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    # We don't need a rerun here as write_stream handles the display.
    # A rerun would clear the "Copy" box if it was open.

# --- Page & UI Setup ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")
configure_genai()

# --- Custom CSS for Gemini-like UI ---
st.markdown("""
    <style>
        /* General Body Styles */
        body {
            background-color: #131316;
            color: #e5e5e5;
        }
        
        /* Main container */
        .stApp {
            background-color: #131316;
        }

        /* Chat bubbles */
        .stChatMessage {
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            border: 1px solid transparent;
        }

        /* User message */
        div[data-testid="stChatMessage"]:has(div[data-testid*="stAvatar--user"]) {
            background-color: #2f3136;
        }

        /* Assistant message */
        div[data-testid="stChatMessage"]:has(div[data-testid*="stAvatar--assistant"]) {
             background-color: #1e1f22;
        }

        /* Suggestion buttons */
        .stButton>button {
            background-color: #2f3136;
            color: #e5e5e5;
            border: 1px solid #40444b;
            border-radius: 20px;
            padding: 0.5rem 1rem;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #40444b;
            border-color: #52575f;
        }
        
        /* Feedback buttons */
        .feedback-buttons {
            display: flex;
            gap: 5px;
            margin-top: 10px;
        }
        .feedback-buttons .stButton>button {
            background-color: transparent;
            border: none;
            font-size: 18px;
            padding: 0;
            color: #a0a0a0;
        }
        .feedback-buttons .stButton>button:hover {
            color: #ffffff;
        }

        /* Chat input */
        [data-testid="stChatInput"] {
            background-color: #131316;
        }
        [data-testid="stTextInput"] textarea {
            color: #e5e5e5;
        }
        h1, p {
           color: #e5e5e5;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_copy_box" not in st.session_state:
    st.session_state.show_copy_box = -1 # Use -1 to indicate no box is shown

# --- UI Rendering ---

# Display chat history
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Add feedback buttons for assistant messages
        if msg["role"] == "assistant":
            col1, col2, col3, _ = st.columns([1, 1, 1, 8])
            with col1:
                if st.button("👍", key=f"like_{i}"):
                    st.toast("Thanks for your feedback!")
            with col2:
                if st.button("👎", key=f"dislike_{i}"):
                    st.toast("Thanks for your feedback!")
            with col3:
                if st.button("📋", key=f"copy_{i}"):
                    # Toggle the visibility of the copy box for this specific message
                    st.session_state.show_copy_box = i if st.session_state.show_copy_box != i else -1
                    st.rerun()

            # Show the copyable text box if the state matches the message index
            if st.session_state.show_copy_box == i:
                st.code(msg["content"], language=None)


# Show intro screen if no messages
if not st.session_state.messages:
    st.markdown(
        f"""
        <div style='text-align: center; margin-top: 5%;'>
            <h1 style='color: #e5e5e5;'>Hello!</h1>
            <p style='font-size: 24px; color: #a0a0a0;'>How can I help you today?</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    cols = st.columns(len(FAQ_SUGGESTIONS))
    for i, suggestion in enumerate(FAQ_SUGGESTIONS):
        if cols[i].button(suggestion, key=f"suggestion_{i}"):
            handle_new_message(suggestion)
            st.rerun()

# Permanent chat input
if prompt := st.chat_input("Ask me anything..."):
    handle_new_message(prompt)
