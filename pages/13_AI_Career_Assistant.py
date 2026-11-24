"""
Page 13 – Smart AI Career Assistant Chatbot
Powered by both:
1. Built-in Local Career AI Mode (100% offline, zero-key fallback with SQLite & O*NET data)
2. Live Cloud AI (Google Gemini / OpenAI REST APIs) with secure Streamlit Secrets management.
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
raw_target = st.session_state.get("selected_career")
target_career = raw_target if (raw_target and str(raw_target).strip().lower() != "none") else "Not Selected Yet"

# ── API Status & Configuration Check ──────────────────────────────────────────
creds = get_api_credentials()

# Sidebar Settings & Configuration
with st.sidebar:
    st.markdown("### 🤖 Assistant Settings")
    if creds["is_configured"]:
        provider_label = "Google Gemini" if creds["provider"] == "gemini" else "OpenAI"
        st.success(f"🟢 **Live AI Active**: {provider_label}")
    else:
        st.info("⚡ **Built-in Local AI** (Active)")

    if student_name:
        st.markdown(f"""
        <div style="background:rgba(0,245,212,0.06); border:1px solid rgba(0,245,212,0.3);
                    border-radius:8px; padding:0.6rem 0.8rem; margin:0.5rem 0;">
            <p style="color:#00F5D4; margin:0; font-size:0.75rem; font-weight:700;">PERSONALIZED CONTEXT</p>
            <p style="color:white; margin:0.2rem 0 0 0; font-size:0.88rem;">👤 <strong>{student_name}</strong></p>
            <p style="color:#7B8FA3; margin:0; font-size:0.75rem;">🎯 Target: <strong>{target_career}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Log in via Registration page to enable fully personalized advice based on your skills!")

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

    # Optional Live Cloud API Setup Expander
    with st.expander("⚙️ Connect Live Gemini / OpenAI API (Optional)", expanded=False):
        st.markdown("""
        Upgrade from Built-in Local AI to live cloud LLM responses anytime by entering your free API key:
        """)
        user_key = st.text_input(
            "Gemini API Key:",
            type="password",
            placeholder="AIzaSy...",
            value=st.session_state.get("GEMINI_API_KEY") or st.session_state.get("custom_gemini_key", "")
        )
        if st.button("💾 Activate AI for Session", use_container_width=True):
            if user_key.strip():
                st.session_state["GEMINI_API_KEY"] = user_key.strip()
                st.session_state["custom_gemini_key"] = user_key.strip()
                st.success("✅ Live Gemini Key Activated!")
                st.rerun()
            else:
                st.warning("Please enter a valid key.")

        st.caption("Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey). You can also configure it in `.streamlit/secrets.toml`.")


# ── Welcome Banner with Personalized Context ──────────────────────────────────
greeting_name = f", <strong>{student_name}</strong>" if student_name else ""
mode_tag = "🟢 <strong>Live Cloud AI Active</strong>" if creds["is_configured"] else "⚡ <strong>Built-in Local Career AI Active</strong> (Zero API Key Required)"

st.markdown(f"""
<div class="glass-card" style="padding:1rem 1.4rem; margin-bottom:1.2rem; border-left:3px solid #00F5D4;">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <p style="color:#FFFFFF !important; margin:0; font-size:1.05rem;">
            👋 Hello{greeting_name}! I am your <b>SkillMatch AI Career Mentor</b>.
        </p>
        <span style="font-size:0.8rem; color:#00D4FF;">{mode_tag}</span>
    </div>
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

    # 3. Generate AI response (handles both Cloud & Local fallback seamlessly)
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
                    st.error(f"⚠️ Error generating response: {e}")
