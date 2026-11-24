"""
Page 4 – Learner Profile
Displays comprehensive student profile with interactive Plotly analytics.
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
    with open(css_path, "r", encoding="utf-8", errors="replace") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from assets.premium_ui import inject_premium_ui, premium_header, neon_divider, glass_card
inject_premium_ui("profile")

from modules.student_registration import get_student_by_id, get_student_skills
from modules.skill_assessment import get_assessment, get_proficiency_label
from modules.learner_profile import build_profile

premium_header("Comprehensive Learner Profile",
               "Your academic competencies, assessed skill levels, and learning readiness.", "👤")
neon_divider()

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student = get_student_by_id(student_id)
if not student:
    st.error("Student profile not found. Please log in again.")
    st.stop()

skills = get_student_skills(student_id)
assessment = get_assessment(student_id)
profile = build_profile(student, skills, assessment)

# ── Profile Header Metrics ────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🎯 Total Skills", profile["skill_count"])
with col2:
    st.metric("⭐ Avg Proficiency", f"{profile['avg_proficiency']:.1f} / 5.0")
with col3:
    st.metric("💪 Strengths", len(profile["strong_skills"]))
with col4:
    st.metric("📚 Growth Areas", len(profile["weak_skills"]))

st.markdown("<br>", unsafe_allow_html=True)

# ── Student Card ──────────────────────────────────────────────────
glass_card(f"""
    <h2 style="color:white !important; margin:0; font-size:1.5rem;">👤 {student['name']}</h2>
    <p style="color:#7B8FA3 !important; margin:0.4rem 0; font-size:0.92rem;">
        🎓 <b style="color:#B0C4DE;">{student.get('education_level','B.Tech')}</b> &nbsp;|&nbsp;
        🏛️ <b style="color:#B0C4DE;">{student.get('department','Engineering')}</b> &nbsp;|&nbsp;
        📅 <b style="color:#B0C4DE;">{student.get('year_of_study','3rd Year')}</b>
    </p>
    <p style="color:#5A6B7D !important; margin:0.3rem 0; font-size:0.88rem;">
        🎯 <b style="color:#7B8FA3;">Interests:</b> {student.get('interests','General Technology')}
    </p>
""")

tab1, tab2, tab3 = st.tabs(["📊 Interactive Analytics", "🛠️ Technical Skills", "🤝 Soft Skills"])

# ── Tab 1: Charts ─────────────────────────────────────────────────
with tab1:
    all_scores = profile["all_skill_scores"]

    if not all_scores:
        st.info("Complete the Skill Assessment to visualize your competency radar.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🕸️ Competency Radar")
            categories = list(all_scores.keys())[:12]
            values = [all_scores[c] for c in categories]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor="rgba(0,212,255,0.12)",
                line=dict(color="#00D4FF", width=2),
            ))
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 5], gridcolor="rgba(255,255,255,0.06)", color="#7B8FA3"),
                    angularaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#7B8FA3"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#B0C4DE"),
                showlegend=False, height=380,
                margin=dict(l=40, r=40, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("#### 📊 Top Skills")
            sorted_skills = sorted(all_scores.items(), key=lambda x: -x[1])[:10]
            names = [s[0] for s in sorted_skills]
            vals = [s[1] for s in sorted_skills]
            colors = ["#00F5D4" if v >= 4 else "#00D4FF" if v >= 3 else "#FFD700" if v >= 2 else "#FF006E"
                      for v in vals]
            fig2 = go.Figure(go.Bar(
                x=vals, y=names, orientation="h",
                marker_color=colors,
                text=[f"{v:.1f}/5" for v in vals],
                textposition="outside",
            ))
            fig2.update_layout(
                xaxis=dict(range=[0, 6], color="#7B8FA3", gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(color="#B0C4DE", autorange="reversed"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#B0C4DE"),
                height=380, margin=dict(l=10, r=60, t=20, b=20),
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
            marker=dict(colors=["#00F5D4", "#00D4FF", "#FFD700", "#FF006E", "#5A6B7D"]),
        ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#B0C4DE"),
            height=300, margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig3, use_container_width=True)

# ── Tab 2: Technical Skills ───────────────────────────────────────
with tab2:
    tech = profile["technical_skills"]
    if not tech:
        st.info("No technical skills registered yet.")
    else:
        for skill in sorted(tech, key=lambda x: -x["proficiency"]):
            pct = skill["proficiency"] / 5.0
            label = get_proficiency_label(skill["proficiency"])
            c_badge = "🟢" if skill["proficiency"] >= 4 else "🔵" if skill["proficiency"] >= 3 else "🟡"
            st.markdown(f"{c_badge} **{skill['skill_name']}** — Level {skill['proficiency']}/5 ({label})")
            st.progress(pct)

# ── Tab 3: Soft Skills ────────────────────────────────────────────
with tab3:
    soft = profile["soft_skills"]
    if not soft:
        st.info("No soft skills registered yet.")
    else:
        for skill in sorted(soft, key=lambda x: -x["proficiency"]):
            pct = skill["proficiency"] / 5.0
            label = get_proficiency_label(skill["proficiency"])
            c_badge = "🟢" if skill["proficiency"] >= 4 else "🔵" if skill["proficiency"] >= 3 else "🟡"
            st.markdown(f"{c_badge} **{skill['skill_name']}** — Level {skill['proficiency']}/5 ({label})")
            st.progress(pct)

# ── Navigation Footer ─────────────────────────────────────────────
neon_divider()
c_act1, c_act2 = st.columns(2)
with c_act1:
    if st.button("📊 Take Skill Assessment →", use_container_width=True):
        st.switch_page("pages/3_Skill_Assessment.py")
with c_act2:
    if st.button("🎯 View Career Recommendations →", use_container_width=True):
        st.switch_page("pages/5_Career_Recommendations.py")
