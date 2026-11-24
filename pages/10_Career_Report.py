"""
Page 10 – Career Report Generation & Download
Generates a comprehensive, downloadable PDF Career Report using live database records.
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
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from assets.premium_ui import inject_premium_ui, premium_header, neon_divider, glass_card
inject_premium_ui("report")

from modules.student_registration import get_student_by_id, get_student_skills
from modules.skill_assessment import get_assessment
from modules.learning_pathway import get_pathway, get_learning_path, save_pathway
from modules.progress_tracking import get_progress
from modules.report_generator import generate_career_report_pdf
from ml.recommendation_model import get_recommender

premium_header("Comprehensive Career Report",
               "Generate and download your official academic career guidance and skill development report.", "📄")
neon_divider()

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student = get_student_by_id(student_id)
if not student:
    st.error("Student record not found.")
    st.stop()

skills = get_student_skills(student_id)
assessment = get_assessment(student_id)

recs = st.session_state.get("recommendations", [])
if not recs and skills:
    try:
        recommender = get_recommender()
        recs = recommender.recommend(
            [s["skill_name"] for s in skills],
            top_n=5,
            student_interests=student.get("interests", ""),
        )
        st.session_state["recommendations"] = recs
    except Exception:
        recs = []

selected_career = st.session_state.get("selected_career")
if not selected_career:
    selected_career = recs[0]["career_title"] if recs else "Data Analyst"
    st.session_state["selected_career"] = selected_career

target_rec = next((r for r in recs if r["career_title"].lower() == selected_career.lower()), None)
missing_for_target = target_rec.get("missing_skills", []) if target_rec else []

pathway = get_pathway(student_id, selected_career)
if not pathway:
    pathway = get_learning_path(selected_career, missing_for_target)
    save_pathway(student_id, selected_career, pathway)

progress = get_progress(student_id, selected_career)

# ── Preview Card ──────────────────────────────────────────────────
glass_card(f"""
    <h2 style="color:white !important; margin:0; font-size:1.4rem;">📋 SkillMatch Official Career Guidance Dossier</h2>
    <p style="color:#B0C4DE !important; margin:0.4rem 0 0 0; font-size:0.92rem;">
        Prepared for <b style="color:#00F5D4;">{student['name']}</b> ({student.get('education_level', 'B.Tech')} - {student.get('department', 'Engineering')})
    </p>
""")

# ── Metrics Summary ───────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("👤 Student ID", f"#{student['id']}")
with col2:
    st.metric("🛠️ Tracked Skills", len(skills))
with col3:
    top_c = recs[0]["career_title"] if recs else selected_career
    st.metric("🎯 Primary Target", top_c[:18] + ("..." if len(top_c) > 18 else ""))
with col4:
    match_val = f"{recs[0]['match_pct']}%" if recs else "N/A"
    st.metric("⭐ ML Match Score", match_val)

st.markdown("<br>", unsafe_allow_html=True)

# ── Generate PDF ──────────────────────────────────────────────────
with st.spinner("Compiling official PDF dossier from database..."):
    pdf_bytes = generate_career_report_pdf(
        student=student, skills=skills, assessment=assessment,
        recommendations=recs, selected_career=selected_career,
        pathway=pathway, progress=progress,
    )

st.success("✅ Your personalized Career Report PDF is generated and ready to download!")

c_down1, c_down2 = st.columns([2, 2])
with c_down1:
    file_name = f"SkillMatch_Report_{student['name'].replace(' ', '_')}.pdf"
    st.download_button(
        label="📥 Download Career Report (PDF)",
        data=pdf_bytes,
        file_name=file_name,
        mime="application/pdf",
        use_container_width=True,
    )
with c_down2:
    st.caption("Includes: Personal profile, skill assessment scores, ML career recommendations, skill gap analysis, and tailored 3-tier learning roadmap.")

neon_divider()

# ── Live Contents Inspection ──────────────────────────────────────
st.markdown("### 🔍 Live Report Content Summary")

tab_profile, tab_recs, tab_pathway = st.tabs(["👤 Profile & Skills", "🎯 Recommendations & Gaps", "🗺️ Roadmap & Status"])

with tab_profile:
    st.markdown(f"**Full Name:** {student['name']}")
    st.markdown(f"**Email:** {student['email']}")
    st.markdown(f"**Academic Program:** {student.get('education_level', 'B.Tech')} - {student.get('degree', '')}")
    st.markdown(f"**Department:** {student.get('department', '')}")
    st.markdown(f"**Interests:** {student.get('interests', 'N/A')}")
    st.markdown("---")
    st.markdown("#### Registered & Assessed Skills:")
    if skills:
        cols = st.columns(3)
        for i, sk in enumerate(skills):
            cols[i % 3].markdown(f"• **{sk['skill_name']}** ({sk.get('skill_type', 'technical')}): Level {sk.get('proficiency', 3)}/5")
    else:
        st.write("No skills recorded yet.")

with tab_recs:
    if recs:
        for idx, r in enumerate(recs[:5], start=1):
            st.markdown(f"**#{idx} {r['career_title']}** – **{r['match_pct']}% Match**")
            st.markdown(f"*Rationale:* {r.get('explanation', 'Matching required competencies.')}")
            st.markdown(f"• Matching: `{', '.join(r.get('matching_skills', [])) or 'None'}`")
            st.markdown(f"• Missing Gap: `{', '.join(r.get('missing_skills', [])) or 'None'}`")
            st.markdown("")
    else:
        st.info("Run career recommendations to preview recommendations here.")

with tab_pathway:
    if pathway:
        st.markdown(f"**Target Career Curriculum:** {selected_career}")
        for item in pathway:
            done = progress.get(item.get("topic", "").strip(), False)
            status_emoji = "✅" if done else "⬜"
            st.markdown(f"{status_emoji} **Step {item.get('step', '?')} [{item.get('level', 'Beginner')}]:** {item.get('topic', '')} — *{item.get('description', '')}*")
    else:
        st.info("Select a career on the Learning Pathway page to include the step-by-step roadmap in this report.")
