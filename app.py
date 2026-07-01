import streamlit as st
import os

# --- THE MASTER KILL SWITCH ---
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import torch
from core.ingestion import process_and_store_documents
from core.generator import get_rag_chain
from core.config import SOURCE_DOCS_DIR

# --- PAGE CONFIGURATION & CUSTOM CSS ---
st.set_page_config(page_title="Cogniva AI | Workspace", page_icon="✨", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 850px; 
    }

    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .hero-title {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(45deg, #00F2FE, #4FACFE, #00F2FE);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient-shift 4s ease infinite;
        margin-bottom: 0.2rem;
    }

    .hero-subtitle {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-bottom: 3rem;
        animation: fadeIn 1s ease-out 0.5s both;
    }

    .fade-in-section {
        animation: fadeIn 0.8s ease-out;
    }

    .brand-logo {
        font-size: 1.8rem;
        font-weight: 700;
        color: #4FACFE;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

os.makedirs(SOURCE_DOCS_DIR, exist_ok=True)

# --- INITIALIZE SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_history_list" not in st.session_state:
    st.session_state.chat_history_list = ["Project Architecture Info", "Leave Policy Query", "System Telemetry Check"]
if "chain" not in st.session_state:
    with st.spinner("Waking up Cogniva AI..."): st.session_state.chain = get_rag_chain()

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(
            "<div class='fade-in-section' style='text-align: center;'><h1 style='font-size: 3rem;'><span style='color:#4FACFE;'>✨</span> Cogniva</h1><p style='color: gray;'>Enterprise Multi-Modal Intelligence.</p></div>",
            unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Workspace ID")
            password = st.text_input("Access Key", type="password")
            submitted = st.form_submit_button("Authenticate ➔", use_container_width=True)

            if submitted:
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True;
                    st.session_state.user_role = "Manager";
                    st.rerun()
                elif username == "employee" and password == "emp123":
                    st.session_state.logged_in = True;
                    st.session_state.user_role = "Employee";
                    st.rerun()
                else:
                    st.error("Access Denied. Check credentials.")

# --- MAIN APPLICATION ---
else:
    # 1. PURE SIDEBAR (All controls and uploads go here)
    with st.sidebar:
        st.markdown("<div class='brand-logo'>✨ Cogniva</div>", unsafe_allow_html=True)
        st.caption(f"Role: **{st.session_state.user_role}**")
        st.write("")

        if st.button("➕ New Chat", use_container_width=True):
            if st.session_state.messages:
                st.session_state.chat_history_list.insert(0, st.session_state.messages[-1]['content'][:20] + "...")
            st.session_state.messages = []
            st.rerun()

        st.divider()

        st.markdown("### 📚 Chat Library")
        for past_chat in st.session_state.chat_history_list[:5]:
            st.button(f"💬 {past_chat}", use_container_width=True, key=past_chat)

        st.divider()

        if st.session_state.user_role == "Manager":
            with st.expander("📁 Train Knowledge Base (PDF)", expanded=False):
                doc_category = st.selectbox("Tag", ["Tech", "HR", "Finance", "General"])
                uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
                if uploaded_files and st.button("Vectorize Data", use_container_width=True):
                    with st.spinner("Training..."):
                        file_paths = []
                        for u_file in uploaded_files:
                            path = os.path.join(SOURCE_DOCS_DIR, u_file.name)
                            with open(path, "wb") as f: f.write(u_file.getbuffer())
                            file_paths.append(path)
                        success, msg = process_and_store_documents(file_paths, doc_category)
                        if success:
                            st.success("Updated!"); st.session_state.chain = get_rag_chain()
                        else:
                            st.error(msg)

            # MOVED MEDIA UPLOAD TO SIDEBAR
            with st.expander("📎 Attach Media (Vision API)"):
                st.file_uploader("Upload Images/Videos", type=["jpg", "png", "mp4"])

        with st.expander("⚙️ Settings"):
            show_telemetry = st.checkbox("Show Telemetry", value=True)
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.messages = []
                st.rerun()

    # 2. MAIN CHAT AREA (Clean and uninterrupted)
    if not st.session_state.messages:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='hero-title'>✨ Cogniva</div>", unsafe_allow_html=True)
        st.markdown("<div class='hero-subtitle'>What are we working on today?</div>", unsafe_allow_html=True)

        st.markdown("<div class='fade-in-section'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        quick_prompt = None
        if col1.button("📑 Summarize Architecture",
                       use_container_width=True): quick_prompt = "Is document ka main purpose, architecture, aur conclusion kya hai?"
        if col2.button("🔍 Cross-Check Data",
                       use_container_width=True): quick_prompt = "Mujhe is system ke metrics aur GPU roles detail mein samjhao."
        if col3.button("📊 Security Audit",
                       use_container_width=True): quick_prompt = "Is system mein Role Based Access Control (RBAC) kaise implement kiya gaya hai?"
        st.markdown("</div>", unsafe_allow_html=True)

        if quick_prompt:
            st.session_state.messages.append({"role": "user", "content": quick_prompt})
            st.rerun()

    # Render Chat Messages (Crash Fixed - using valid emoji avatars)
    for message in st.session_state.messages:
        avatar = "🧑‍💻" if message["role"] == "user" else "✨"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.popover("📚 Citations"):
                    for src in message["sources"]: st.caption(src)

    if st.session_state.user_role == "Employee" and not st.session_state.messages:
        st.info("🔒 Restricted Mode Active.")

    user_input = st.chat_input("Message Cogniva AI...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(user_input)

        history_string = "\n".join([f"{'User' if m['role'] == 'user' else 'Cogniva AI'}: {m['content']}" for m in
                                    st.session_state.messages[-5:]])

        # FIXED CRASH HERE TOO
        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("Processing..."):
                res = st.session_state.chain.invoke({"query": user_input, "chat_history": history_string})
                st.markdown(res["result"])

                if show_telemetry:
                    col1, col2, col3 = st.columns(3)
                    col1.caption(f"⏱️ **{res['latency']}s** Latency")
                    col2.caption(f"🧠 **{res.get('prompt_tokens', 0)}** Input Tokens")
                    col3.caption(f"⚡ **{res.get('completion_tokens', 0)}** Output Tokens")

                if res["sources"]:
                    with st.popover("📚 Citations"):
                        for src in res["sources"]: st.caption(src)

                st.session_state.messages.append(
                    {"role": "assistant", "content": res["result"], "sources": res["sources"]})