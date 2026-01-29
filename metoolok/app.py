import streamlit as st
import asyncio
from core.brain import AssistantBrain
from core.data_manager import DataManager

# ---------------------------------------------------------
# 1. Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Metin Mert AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. Async Bridge (Streamlit Safe)
# ---------------------------------------------------------
def run_async(coro):
    """
    Safely bridges Streamlit (sync) with async core logic.
    Handles existing or missing event loops gracefully to prevent RuntimeErrors.
    """
    try:
        # Check if there is an existing loop in the current thread
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Create a new loop if none exists
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        # If we are in a running loop (rare in simple scripts but possible), use threadsafe execution
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()
    else:
        # Standard execution for Streamlit
        return loop.run_until_complete(coro)

# ---------------------------------------------------------
# 3. Session State Initialization (Singleton)
# ---------------------------------------------------------
if "data_manager" not in st.session_state:
    st.session_state.data_manager = DataManager()

if "brain" not in st.session_state:
    # Inject DataManager into Brain
    st.session_state.brain = AssistantBrain(
        data_manager=st.session_state.data_manager
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

    # Load persistent conversation history from JSON
    history = st.session_state.brain.context_memory.get(
        "conversation_history", []
    )

    for item in history:
        st.session_state.messages.append(
            {"role": "user", "content": item["user"]}
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": item["assistant"]}
        )

# ---------------------------------------------------------
# 4. Sidebar – Control Panel
# ---------------------------------------------------------
with st.sidebar:
    st.title("🎛️ System Control")

    # ------------------
    # File Upload
    # ------------------
    st.subheader("📂 Document Upload")
    uploaded_file = st.file_uploader(
        "Upload PDF for analysis",
        type=["pdf"]
    )

    if uploaded_file:
        dm = st.session_state.data_manager
        file_path = dm.upload_file(uploaded_file)

        if file_path:
            st.success(f"📄 {uploaded_file.name} uploaded successfully")

            # Save file path to shared memory
            st.session_state.brain.context_memory["last_uploaded_file"] = file_path
            dm.save_context()

            # Optional system note in chat (UI Feedback)
            # st.toast("PDF loaded. You can now ask for summaries.", icon="✅")

    st.divider()

    # ------------------
    # Active Skills Dashboard
    # ------------------
    st.subheader("🧠 Active Skills")
    skills = st.session_state.brain.skill_objects

    if not skills:
        st.error("No skills loaded in `skills/` folder.")
    else:
        for name, skill in skills.items():
            # Check configuration (API keys, etc.)
            ready = skill.check_configuration()
            icon = "🟢" if ready else "🔴"

            with st.expander(f"{icon} {name.capitalize()}"):
                st.caption(f"**Description:** {skill.description}")
                st.caption(f"**Executions:** {skill.execution_count}")
                st.caption(f"**Timeout:** {skill.timeout}s")

    st.divider()

    # ------------------
    # Memory Management
    # ------------------
    if st.button("🗑️ Clear Memory"):
        st.session_state.messages.clear()
        st.session_state.brain.context_memory["conversation_history"] = []
        st.session_state.brain.context_memory["last_uploaded_file"] = None
        st.session_state.data_manager.save_context()
        st.success("Short-term memory wiped.")
        st.rerun()

# ---------------------------------------------------------
# 5. Main Chat UI
# ---------------------------------------------------------
st.title("🤖 AI Personal Assistant")
st.caption(
    "Modular Skill Architecture • Async Core • Production Ready"
)

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------
# 6. User Interaction
# ---------------------------------------------------------
if prompt := st.chat_input("How can I help you today?"):
    # 1. Display User Message
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                # Bridge the sync UI with the async Brain
                response = run_async(
                    st.session_state.brain.process_input(prompt)
                )

                st.markdown(response)

                # 3. Save to Session State (History is already saved in Brain)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

            except Exception as e:
                error_msg = f"❌ System Error: {str(e)}"
                st.error(error_msg)