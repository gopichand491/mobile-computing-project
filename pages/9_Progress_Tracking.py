"""
Page 9 – Progress Tracking
Monitors the student's learning journey and topic completion across all enrolled career pathways.
Supports interactive topic completion with persistent SQLite storage.
"""

import streamlit as st
import os, sys
import plotly.graph_objects as go
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db_setup import setup_database
setup_database()

css_path = os.path.join(ROOT, "assets", "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from modules.progress_tracking import get_overall_progress, get_progress, mark_topic_complete
from modules.learning_pathway import get_pathway, get_learning_path, save_pathway
from modules.student_registration import get_student_by_id, get_student_skills
from ml.recommendation_model import get_recommender

st.markdown("# ✅ Learning Progress Tracking")
st.markdown("Track and analyze your topic completion across all enrolled pathways.")
st.markdown("---")

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student_name = st.session_state.get("student_name", "Student")

overall = get_overall_progress(student_id)

# If no progress recorded yet, attempt to auto-initialize for the student's target career
if not overall:
    selected_c = st.session_state.get("selected_career")
    if not selected_c:
        skills = [s["skill_name"] for s in get_student_skills(student_id)]
        if skills:
            try:
                rec = get_recommender().recommend(skills, top_n=1)
                if rec:
                    selected_c = rec[0]["career_title"]
            except Exception:
                selected_c = "Data Analyst"
        else:
            selected_c = "Data Analyst"

    if selected_c:
        init_path = get_learning_path(selected_c)
        save_pathway(student_id, selected_c, init_path)
        overall = get_overall_progress(student_id)

if not overall:
    st.info("📚 No learning pathway progress recorded yet. Visit the **Learning Pathway** page to select a career and start marking completed topics!")
    st.stop()

# ── Overall Summary ───────────────────────────────────────────────────────────
total_topics = sum(o["total_topics"] for o in overall)
total_completed = sum(o["completed_topics"] for o in overall)
overall_pct = round(total_completed / total_topics * 100, 1) if total_topics > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📚 Active Roadmaps", len(overall))
with col2:
    st.metric("📋 Total Topics", total_topics)
with col3:
    st.metric("✅ Completed Topics", total_completed)
with col4:
    st.metric("📈 Overall Completion", f"{overall_pct}%")

st.markdown(f"**Overall Learning Progress ({total_completed}/{total_topics} topics completed):**")
st.progress(overall_pct / 100.0)
st.markdown("<br>", unsafe_allow_html=True)

# ── Per-Career Cards ──────────────────────────────────────────────────────────
st.markdown("### 🏆 Progress by Career Pathway")
for entry in overall:
    ct = entry["career_title"]
    pct = entry["progress_pct"]
    comp = entry["completed_topics"]
    tot = entry["total_topics"]

    bar_color = "#4CAF50" if pct >= 75 else "#1E88E5" if pct >= 40 else "#FF9800"
    emoji = "🥇" if pct == 100 else "🔥" if pct >= 75 else "📖"

    st.markdown(f"""
    <div style="background:#132238; border:1px solid #1E3A5F; border-radius:10px; padding:1.2rem; margin-bottom:0.75rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:white; font-weight:700; font-size:1.05rem;">{emoji} {ct}</span>
            <span style="color:{bar_color}; font-weight:800; font-size:1.15rem;">{pct}%</span>
        </div>
        <p style="color:#90CAF9; margin:0.3rem 0; font-size:0.85rem;">{comp} of {tot} topics finished</p>
    </div>
    """, unsafe_allow_html=True)
    st.progress(pct / 100.0)

# ── Visual Progress Chart ─────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📊 Progress Distribution Chart")
df = pd.DataFrame(overall)
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["career_title"],
        y=df["completed_topics"],
        name="Completed",
        marker_color="#2E7D32",
        text=df["completed_topics"],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        x=df["career_title"],
        y=df["total_topics"] - df["completed_topics"],
        name="Remaining",
        marker_color="#37474F",
        text=(df["total_topics"] - df["completed_topics"]),
        textposition="outside",
    ))
    fig.update_layout(
        barmode="stack",
        xaxis=dict(color="#90CAF9", tickangle=-15),
        yaxis=dict(title="Topics Count", color="#90CAF9", gridcolor="#263340"),
        paper_bgcolor="#0A1628",
        plot_bgcolor="#132238",
        font=dict(color="#FFFFFF"),
        legend=dict(bgcolor="#132238", bordercolor="#1E3A5F"),
        height=340,
        margin=dict(l=20, r=20, t=20, b=60),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Detailed Interactive Checklist ───────────────────────────────────────────
st.markdown("### 🔍 Interactive Pathway Checklist")
selected_c = st.selectbox("Select an enrolled pathway to inspect / update:", [o["career_title"] for o in overall])
path_items = get_pathway(student_id, selected_c)
prog_map = get_progress(student_id, selected_c)


def on_checklist_toggle(t_name, c_name, s_id, k_name):
    is_done = st.session_state.get(k_name, False)
    mark_topic_complete(s_id, c_name, t_name, is_done)


if path_items:
    for item in path_items:
        topic = item.get("topic", "").strip()
        step = item.get("step", item.get("step_number", "?"))
        level = item.get("level", "Beginner")
        desc = item.get("description", "")
        url = item.get("url", item.get("resource_url", ""))
        is_done = prog_map.get(topic, False)

        bg = "#16281E" if is_done else "#141D2B"
        border = "#388E3C" if is_done else "#223145"
        status_txt = "✅ COMPLETED" if is_done else "⬜ PENDING"
        status_col = "#81C784" if is_done else "#90CAF9"

        st.markdown(f"""
        <div style="background:{bg}; border:1px solid {border}; border-radius:8px; padding:0.8rem 1rem; margin-bottom:0.5rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="color:white; font-weight:600;">Step {step} [{level}]: {topic}</span>
                <span style="color:{status_col}; font-weight:700; font-size:0.8rem;">{status_txt}</span>
            </div>
            <p style="color:#BBDEFB; font-size:0.82rem; margin:0.2rem 0 0 0;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

        k_name = f"prog_page_chk_{selected_c}_{step}_{topic}"
        if k_name not in st.session_state:
            st.session_state[k_name] = is_done

        st.checkbox(
            f"Toggle completion for Step {step}: '{topic}'",
            key=k_name,
            on_change=on_checklist_toggle,
            args=(topic, selected_c, student_id, k_name),
        )
