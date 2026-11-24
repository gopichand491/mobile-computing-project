"""
Page 13 – Smart AI Career Assistant Chatbot
Powered by real AI (Google Gemini / OpenAI) with secure Streamlit Secrets management.
Provides real-time personalized career guidance, doubt resolution, and skill roadmaps.
"""

import streamlit as st
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db_setup import setup_database
setup_database()

css_path = os.path.join(ROOT, "assets", "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8", errors="replace") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from assets.premium_ui import inject_premium_ui, premium_header, neon_divider, glass_card
inject_premium_ui("ai_assistant")

from modules.ai_chatbot import get_api_credentials, generate_ai_response, stream_text

# ── Header ────────────────────────────────────────────────────────────────────
premium_header("AI Career Assistant",
               "Your 24/7 personalized AI career mentor. Ask anything about skills, roadmaps, and jobs.", "🤖")
neon_divider()

# ── Session State for Chat ────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

student_name = st.session_state.get("student_name")
student_id = st.session_state.get("student_id")
target_career = st.session_state.get("selected_career", "Technology Careers")

# ── API Status & Configuration Check ──────────────────────────────────────────
creds = get_api_credentials()

# Sidebar Settings & Configuration
with st.sidebar:
    st.markdown("### 🤖 Assistant Settings")
    if creds["is_configured"]:
        provider_label = "Google Gemini" if creds["provider"] == "gemini" else "OpenAI"
        st.success(f"🟢 **AI Connected**: {provider_label}")
    else:
        st.warning("🔴 **AI Key Missing**")

    if student_name:
        st.markdown(f"""
        <div style="background:rgba(0,245,212,0.06); border:1px solid rgba(0,245,212,0.3);
                    border-radius:8px; padding:0.6rem 0.8rem; margin:0.5rem 0;">
            <p style="color:#00F5D4; margin:0; font-size:0.75rem; font-weight:700;">PERSONALIZED CONTEXT</p>
            <p style="color:white; margin:0.2rem 0 0 0; font-size:0.88rem;">👤 {student_name}</p>
            <p style="color:#7B8FA3; margin:0; font-size:0.75rem;">🎯 Target: {target_career}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Log in via Registration page to enable fully personalized advice based on your skills!")

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

    # Manual Key Override Option
    with st.expander("🔑 Configure / Override API Key", expanded=not creds["is_configured"]):
        st.markdown("""
        Enter your API key below if not configured in `.streamlit/secrets.toml`:
        """)
        user_key = st.text_input("Gemini API Key:", type="password", placeholder="AIzaSy...",
                                 value=st.session_state.get("custom_gemini_key", ""))
        if st.button("💾 Apply Key for Session", use_container_width=True):
            if user_key.strip():
                st.session_state["custom_gemini_key"] = user_key.strip()
                st.success("✅ Gemini key saved for this session!")
                st.rerun()
            else:
                st.warning("Please enter a valid key.")


# ── If API Key Missing: Show Clear Configuration Guide ─────────────────────────
if not creds["is_configured"]:
    st.markdown("""
    <div class="glass-card" style="border:1px solid rgba(255,215,0,0.4); padding:1.8rem; margin-bottom:1.5rem;">
        <div style="display:flex; align-items:center; gap:0.8rem;">
            <span style="font-size:2rem;">⚠️</span>
            <div>
                <h3 style="color:#FFD700 !important; margin:0;">AI API Key Configuration Required</h3>
                <p style="color:#B0C4DE !important; margin:0.2rem 0 0 0; font-size:0.9rem;">
                    To enable genuine, real-time AI responses just like ChatGPT, connect a free Google Gemini or OpenAI API key.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_setup1, col_setup2 = st.columns(2)

    with col_setup1:
        st.markdown("### 🌟 Option 1: Free Google Gemini API (Recommended)")
        st.markdown("""
        1. **Get Free Key**: Visit [Google AI Studio](https://aistudio.google.com/app/apikey) and sign in.
        2. Click **Create API Key** (100% free with generous rate limits).
        3. Paste it directly in the **Sidebar Key Input** (left) to use immediately!
        4. Or add it permanently to `.streamlit/secrets.toml`:
        ```toml
        # C:\\Users\\...\\SkillMatch\\.streamlit\\secrets.toml
        GEMINI_API_KEY = "AIzaSyYourKeyHere"
        ```
        """)

    with col_setup2:
        st.markdown("### 🌐 Option 2: Streamlit Community Cloud")
        st.markdown("""
        When deploying to **Streamlit Cloud**:
        1. Open your app dashboard on [share.streamlit.io](https://share.streamlit.io/).
        2. Go to **Settings** &rarr; **Secrets**.
        3. Add your key in TOML format:
        ```toml
        GEMINI_API_KEY = "AIzaSyYourKeyHere"
        ```
        4. Save and the AI Assistant activates automatically!
        """)

    st.markdown("---")
    st.info("💡 **Quick Test**: Paste your key in the sidebar under **'Configure / Override API Key'** to start chatting right away without editing files.")
    st.stop()


# ── Welcome Banner with Personalized Context ──────────────────────────────────
greeting_name = f", **{student_name}**" if student_name else ""
st.markdown(f"""
<div class="glass-card" style="padding:1rem 1.4rem; margin-bottom:1.2rem; border-left:3px solid #00F5D4;">
    <p style="color:#FFFFFF !important; margin:0; font-size:1.05rem;">
        👋 Hello{greeting_name}! I am your <b>SkillMatch AI Career Mentor</b>.
    </p>
    <p style="color:#7B8FA3 !important; margin:0.3rem 0 0 0; font-size:0.88rem;">
        Ask me about recommended career paths, skill gaps, learning roadmaps, programming doubts, interview preparation, or portfolio projects!
    </p>
</div>
""", unsafe_allow_html=True)


# ── Quick Suggestion Chips ────────────────────────────────────────────────────
st.markdown("##### 💡 Suggested Questions")
sug_col1, sug_col2 = st.columns(2)

selected_prompt = None
with sug_col1:
    if st.button("🎯 What career paths best match my current skills?", use_container_width=True):
        selected_prompt = "What career paths best match my current skills and academic profile?"
    if st.button(f"📉 What skill gaps do I need to bridge for {target_career}?", use_container_width=True):
        selected_prompt = f"What specific skill gaps do I have for {target_career}, and how should I start bridging them?"

with sug_col2:
    if st.button("🗺️ Give me a 3-month roadmap to master Python & ML", use_container_width=True):
        selected_prompt = "Provide a structured, step-by-step 3-month learning roadmap to master Python, SQL, and Machine Learning from scratch."
    if st.button("💼 What are top interview questions for entry-level tech roles?", use_container_width=True):
        selected_prompt = "What are the most frequent technical and HR interview questions asked to B.Tech students for entry-level software/data roles?"


# ── Render Existing Chat History ──────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(msg["content"])


# ── Chat Input Processing ─────────────────────────────────────────────────────
user_input = st.chat_input("Ask a question about careers, skills, or programming...")

prompt_to_process = selected_prompt or user_input

if prompt_to_process:
    # 1. Render user message
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt_to_process)

    # 2. Add to session history
    st.session_state.chat_messages.append({"role": "user", "content": prompt_to_process})

    # 3. Generate AI response
    with chat_container:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("SkillMatch AI is thinking..."):
                try:
                    response_text = generate_ai_response(
                        user_query=prompt_to_process,
                        chat_history=st.session_state.chat_messages[:-1],
                        student_id=student_id,
                    )
                    # Typewriter animation
                    st.write_stream(stream_text(response_text))
                    st.session_state.chat_messages.append({"role": "assistant", "content": response_text})

                except Exception as e:
                    err_msg = str(e)
                    if "NO_API_KEY" in err_msg:
                        st.error("⚠️ AI API key is not configured. Please add GEMINI_API_KEY to secrets or the sidebar.")
                    else:
                        st.error(f"⚠️ Error from AI service: {err_msg}")
