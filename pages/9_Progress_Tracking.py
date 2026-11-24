"""
Page 9 – Progress Tracking
Monitors student's learning journey and topic completion across all enrolled career pathways.
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

from assets.premium_ui import inject_premium_ui, premium_header, neon_divider, glass_card
inject_premium_ui("progress")

from modules.progress_tracking import get_overall_progress, get_progress, mark_topic_complete
from modules.learning_pathway import get_pathway, get_learning_path, save_pathway
from modules.student_registration import get_student_by_id, get_student_skills
from ml.recommendation_model import get_recommender

premium_header("Learning Progress Tracking",
               "Track and analyze your topic completion across all enrolled pathways.", "✅")
neon_divider()

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student_name = st.session_state.get("student_name", "Student")

overall = get_overall_progress(student_id)

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
    st.info("📚 No learning pathway progress recorded yet. Visit the **Learning Pathway** page to enroll in a career roadmap!")
    st.stop()

# ── Overall Summary ───────────────────────────────────────────────
total_topics = sum(o["total_topics"] for o in overall)
total_completed = sum(o["completed_topics"] for o in overall)
overall_pct = round(total_completed / total_topics * 100, 1) if total_topics > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📚 Active Roadmaps", len(overall))
with col2:
    st.metric("📋 Total Topics", total_topics)
with col3:
    st.metric("✅ Completed", total_completed)
with col4:
    st.metric("📈 Overall Rate", f"{overall_pct}%")

st.markdown(f"**Overall Learning Progress ({total_completed}/{total_topics} topics completed):**")
st.progress(overall_pct / 100.0)
st.markdown("<br>", unsafe_allow_html=True)

# ── Per-Career Cards ──────────────────────────────────────────────
st.markdown("### 🏆 Progress by Career Pathway")
for entry in overall:
    ct = entry["career_title"]
    pct = entry["progress_pct"]
    comp = entry["completed_topics"]
    tot = entry["total_topics"]

    bar_color = "#00F5D4" if pct >= 75 else "#00D4FF" if pct >= 40 else "#FFD700"
    emoji = "🥇" if pct == 100 else "🔥" if pct >= 75 else "📖"

    st.markdown(f"""
    <div class="glass-card" style="margin-bottom:0.75rem; padding:1.1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="color:white; font-weight:700; font-size:1.05rem;">{emoji} {ct}</span>
            <span style="color:{bar_color}; font-weight:800; font-size:1.15rem;">{pct}%</span>
        </div>
        <p style="color:#7B8FA3; margin:0.3rem 0; font-size:0.85rem;">{comp} of {tot} topics finished</p>
    </div>
    """, unsafe_allow_html=True)
    st.progress(pct / 100.0)

# ── Visual Progress Chart ─────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📊 Progress Distribution Chart")
df = pd.DataFrame(overall)
if not df.empty:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["career_title"], y=df["completed_topics"],
        name="Completed", marker_color="#00F5D4",
        text=df["completed_topics"], textposition="outside",
    ))
    fig.add_trace(go.Bar(
        x=df["career_title"], y=df["total_topics"] - df["completed_topics"],
        name="Remaining", marker_color="rgba(255,255,255,0.1)",
        text=(df["total_topics"] - df["completed_topics"]), textposition="outside",
    ))
    fig.update_layout(
        barmode="stack",
        xaxis=dict(color="#7B8FA3", tickangle=-15),
        yaxis=dict(title="Topics Count", color="#7B8FA3", gridcolor="rgba(255,255,255,0.06)"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#B0C4DE"),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.06)"),
        height=340, margin=dict(l=20, r=20, t=20, b=60),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Detailed Interactive Checklist ───────────────────────────────
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

        card_class = "pathway-topic completed" if is_done else "pathway-topic"
        status_txt = "✅ COMPLETED" if is_done else "⬜ PENDING"
        status_col = "#00F5D4" if is_done else "#7B8FA3"

        st.markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="color:white; font-weight:600;">Step {step} [{level}]: {topic}</span>
                <span style="color:{status_col}; font-weight:700; font-size:0.8rem;">{status_txt}</span>
            </div>
            <p style="color:#B0C4DE; font-size:0.82rem; margin:0.2rem 0 0 0;">{desc}</p>
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
