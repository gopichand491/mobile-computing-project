"""
Page 4 – Learner Profile
Displays comprehensive student profile, registered skills, assessment results,
and interactive Plotly analytics (radar, bar, and competency distribution charts).
"""

import streamlit as st
import os, sys
import plotly.graph_objects as go

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db_setup import setup_database
setup_database()

css_path = os.path.join(ROOT, "assets", "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from modules.student_registration import get_student_by_id, get_student_skills
from modules.skill_assessment import get_assessment, get_proficiency_label
from modules.learner_profile import build_profile

st.markdown("# 👤 Comprehensive Learner Profile")
st.markdown("Your academic competencies, assessed skill levels, and learning readiness overview.")
st.markdown("---")

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student = get_student_by_id(student_id)
if not student:
    st.error("Student profile not found in database. Please log in again.")
    st.stop()

skills = get_student_skills(student_id)
assessment = get_assessment(student_id)
profile = build_profile(student, skills, assessment)

# ── Profile Header Metrics ────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🎯 Total Tracked Skills", profile["skill_count"])
with col2:
    st.metric("⭐ Avg Proficiency Score", f"{profile['avg_proficiency']:.1f} / 5.0")
with col3:
    st.metric("💪 Identified Strengths", len(profile["strong_skills"]))
with col4:
    st.metric("📚 Growth Areas", len(profile["weak_skills"]))

st.markdown("<br>", unsafe_allow_html=True)

# ── Student Card ──────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#1A2332,#1E3048); border:1px solid #1E88E5;
            border-radius:12px; padding:1.4rem; margin-bottom:1.5rem;">
    <h2 style="color:white; margin:0; font-size:1.6rem;">👤 {student['name']}</h2>
    <p style="color:#90CAF9; margin:0.3rem 0; font-size:0.95rem;">
        🎓 <b>Program:</b> {student.get('education_level','B.Tech')} &nbsp;|&nbsp;
        🏛️ <b>Department:</b> {student.get('department','Engineering')} &nbsp;|&nbsp;
        📅 <b>Year:</b> {student.get('year_of_study','3rd Year')}
    </p>
    <p style="color:#BBDEFB; margin:0.3rem 0; font-size:0.9rem;">
        🎯 <b>Stated Career Interests:</b> {student.get('interests','General Technology')}
    </p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Interactive Analytics", "🛠️ Technical Competencies", "🤝 Soft Skills"])

# ── Tab 1: Charts ─────────────────────────────────────────────────────────────
with tab1:
    all_scores = profile["all_skill_scores"]

    if not all_scores:
        st.info("Complete the Skill Assessment to visualize your competency radar.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🕸️ Competency Radar Chart")
            categories = list(all_scores.keys())[:12]
            values = [all_scores[c] for c in categories]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor="rgba(21,101,192,0.25)",
                line=dict(color="#1E88E5", width=2),
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 5], gridcolor="#263340", color="#90CAF9"),
                    angularaxis=dict(gridcolor="#263340", color="#90CAF9"),
                    bgcolor="#1A2332",
                ),
                paper_bgcolor="#0A1628",
                font=dict(color="#FFFFFF"),
                showlegend=False,
                height=380,
                margin=dict(l=40, r=40, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### 📊 Top Assessed Skills")
            sorted_skills = sorted(all_scores.items(), key=lambda x: -x[1])[:10]
            names = [s[0] for s in sorted_skills]
            vals = [s[1] for s in sorted_skills]
            colors = ["#4CAF50" if v >= 4 else "#1E88E5" if v >= 3 else "#FF9800" if v >= 2 else "#F44336"
                      for v in vals]
            fig2 = go.Figure(go.Bar(
                x=vals, y=names, orientation="h",
                marker_color=colors,
                text=[f"{v:.1f}/5" for v in vals],
                textposition="outside",
            ))
            fig2.update_layout(
                xaxis=dict(range=[0, 6], color="#90CAF9", gridcolor="#263340"),
                yaxis=dict(color="#90CAF9", autorange="reversed"),
                paper_bgcolor="#0A1628",
                plot_bgcolor="#1A2332",
                font=dict(color="#FFFFFF"),
                height=380,
                margin=dict(l=10, r=60, t=20, b=20),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Proficiency distribution pie
        st.markdown("#### 🥧 Proficiency Tier Distribution")
        buckets = {"Expert (5)": 0, "Advanced (4)": 0, "Intermediate (3)": 0,
                   "Beginner (2)": 0, "Novice (1)": 0}
        for v in all_scores.values():
            if v >= 4.5: buckets["Expert (5)"] += 1
            elif v >= 3.5: buckets["Advanced (4)"] += 1
            elif v >= 2.5: buckets["Intermediate (3)"] += 1
            elif v >= 1.5: buckets["Beginner (2)"] += 1
            else: buckets["Novice (1)"] += 1

        fig3 = go.Figure(go.Pie(
            labels=list(buckets.keys()),
            values=list(buckets.values()),
            hole=0.45,
            marker=dict(colors=["#4CAF50", "#2196F3", "#FF9800", "#F44336", "#9E9E9E"]),
        ))
        fig3.update_layout(
            paper_bgcolor="#0A1628",
            font=dict(color="#FFFFFF"),
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig3, use_container_width=True)

# ── Tab 2: Technical Skills ───────────────────────────────────────────────────
with tab2:
    tech = profile["technical_skills"]
    if not tech:
        st.info("No technical skills registered yet. Add them in the Registration or Skill Assessment page.")
    else:
        for skill in sorted(tech, key=lambda x: -x["proficiency"]):
            pct = skill["proficiency"] / 5.0
            label = get_proficiency_label(skill["proficiency"])
            c_badge = "🟢" if skill["proficiency"] >= 4 else "🔵" if skill["proficiency"] >= 3 else "🟡"
            st.markdown(f"{c_badge} **{skill['skill_name']}** — Level {skill['proficiency']}/5 ({label})")
            st.progress(pct)

# ── Tab 3: Soft Skills ────────────────────────────────────────────────────────
with tab3:
    soft = profile["soft_skills"]
    if not soft:
        st.info("No soft skills registered yet. Complete your Skill Assessment to benchmark them.")
    else:
        for skill in sorted(soft, key=lambda x: -x["proficiency"]):
            pct = skill["proficiency"] / 5.0
            label = get_proficiency_label(skill["proficiency"])
            c_badge = "🟢" if skill["proficiency"] >= 4 else "🔵" if skill["proficiency"] >= 3 else "🟡"
            st.markdown(f"{c_badge} **{skill['skill_name']}** — Level {skill['proficiency']}/5 ({label})")
            st.progress(pct)

# ── Navigation Footer ─────────────────────────────────────────────────────────
st.markdown("---")
c_act1, c_act2 = st.columns(2)
with c_act1:
    if st.button("📊 Take Skill Assessment / Quiz →", use_container_width=True):
        st.switch_page("pages/3_Skill_Assessment.py")
with c_act2:
    if st.button("🎯 View Career Recommendations →", use_container_width=True):
        st.switch_page("pages/5_Career_Recommendations.py")
