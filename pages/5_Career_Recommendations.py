"""
Page 5 – Career Recommendations
ML-powered career matching based on student skills and interests using TF-IDF + Cosine Similarity.
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
from modules.skill_assessment import get_assessment
from modules.career_recommendation import save_recommendations, format_match_badge
from ml.recommendation_model import get_recommender

st.markdown("# 🎯 Machine Learning Career Recommendations")
st.markdown("Intelligent career matching based on your skill profile and interests using O*NET occupational data.")
st.markdown("---")

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student_name = st.session_state.student_name
student = get_student_by_id(student_id)

# Gather student skills
skills = get_student_skills(student_id)
assessment = get_assessment(student_id)

skill_names = [s["skill_name"] for s in skills]
assessment_skills = list(assessment.keys())
all_student_skills = list(set(skill_names + assessment_skills))

if not all_student_skills:
    st.warning("⚠️ Please add your skills in Registration and complete the Skill Assessment first.")
    st.stop()

# ── Settings sidebar ──────────────────────────────────────────────────────────
recommender = get_recommender()
categories = recommender.get_categories()

with st.sidebar:
    st.markdown("### ⚙️ Recommendation Settings")
    top_n = st.slider("Number of recommendations", 3, 10, 5)
    category_filter = st.selectbox("Filter by career domain", categories)
    if st.button("🔄 Recalculate Recommendations", use_container_width=True):
        st.session_state.recommendations = []

# ── Run model dynamically ─────────────────────────────────────────────────────
if not st.session_state.get("recommendations"):
    with st.spinner("🤖 Running ML TF-IDF & Cosine Similarity recommendation engine..."):
        recs = recommender.recommend(
            student_skills=all_student_skills,
            top_n=top_n,
            category_filter=category_filter,
            student_interests=student.get("interests", "") if student else "",
        )
        st.session_state.recommendations = recs
        save_recommendations(student_id, recs)

recs = st.session_state.recommendations

if not recs:
    st.error("No recommendations generated. Try resetting the domain filter or updating your skills.")
    st.stop()

# ── Algorithm explanation banner ──────────────────────────────────────────────
st.info(
    "🤖 **ML Engine**: Scikit-learn TF-IDF Vectorizer + Cosine Similarity | "
    "Match % = Cosine Similarity Score × 100% | "
    f"Evaluated against {len(recommender.career_df)} occupational profiles from O*NET database."
)

st.markdown(f"### 🏆 Top Career Recommendations for **{student_name}**")

# Match score chart
st.markdown("#### 📊 Match Percentage Distribution")
fig = go.Figure(go.Bar(
    x=[r["career_title"] for r in recs],
    y=[r["match_pct"] for r in recs],
    marker=dict(
        color=[r["match_pct"] for r in recs],
        colorscale="Blues",
        showscale=True,
        colorbar=dict(title="Match %"),
    ),
    text=[f"{r['match_pct']}%" for r in recs],
    textposition="outside",
))
fig.update_layout(
    xaxis=dict(color="#90CAF9", tickangle=-15),
    yaxis=dict(title="Match Percentage", color="#90CAF9", range=[0, 115], gridcolor="#263340"),
    paper_bgcolor="#0A1628",
    plot_bgcolor="#1A2332",
    font=dict(color="#FFFFFF"),
    height=340,
    margin=dict(l=20, r=20, t=20, b=80),
)
st.plotly_chart(fig, use_container_width=True)

# ── Career Cards with Transparent Rationale ───────────────────────────────────
for i, rec in enumerate(recs, 1):
    badge = format_match_badge(rec["match_pct"])

    with st.expander(
        f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else '🎖️'} "
        f"#{i} {rec['career_title']}  –  {rec['match_pct']}% Match  {badge}",
        expanded=(i == 1),
    ):
        # Recommendation Rationale
        st.markdown(f"""
        <div style="background:#1E3048; border-left:4px solid #1E88E5; border-radius:6px; padding:0.8rem 1rem; margin-bottom:0.8rem;">
            <p style="color:#BBDEFB; margin:0; font-size:0.88rem;"><b>💡 Recommendation Rationale:</b> {rec.get('explanation')}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**📋 Role Description:** {rec['description']}")
            st.markdown(f"**🏷️ Domain:** {rec['category']} &nbsp;|&nbsp; **O\\*NET-SOC:** `{rec['onet_code']}`")

        with col2:
            st.markdown("**✅ Your Matching Skills**")
            if rec["matching_skills"]:
                for sk in rec["matching_skills"][:8]:
                    st.markdown(f"<span style='color:#4CAF50;'>✓</span> {sk}", unsafe_allow_html=True)
            else:
                st.write("None detected")

        with col3:
            st.markdown("**❌ Missing Skills Gap**")
            if rec["missing_skills"]:
                for sk in rec["missing_skills"][:8]:
                    st.markdown(f"<span style='color:#F44336;'>✗</span> {sk}", unsafe_allow_html=True)
            else:
                st.write("Full match!")

        # Coverage bar
        total = len(rec["required_skills"])
        matched = len(rec["matching_skills"])
        pct = matched / total if total > 0 else 0
        st.markdown(f"**Competency Coverage:** {matched}/{total} required skills ({rec['match_pct']}%)")
        st.progress(pct)

        # Action Buttons
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button(f"🗺️ Open Learning Pathway for {rec['career_title']}", key=f"lp_btn_{i}"):
                st.session_state.selected_career = rec["career_title"]
                st.session_state.selected_career_data = rec
                st.success(f"Selected **{rec['career_title']}**! Navigate to Learning Pathway to view curriculum.")
        with c_btn2:
            if st.button(f"⚖️ Compare {rec['career_title']} with other careers", key=f"comp_btn_{i}"):
                st.session_state.selected_career = rec["career_title"]
                st.success(f"Added **{rec['career_title']}** to Comparison! Navigate to Career Comparison.")

        if rec.get("suggested_learning"):
            st.markdown("**🎯 Recommended Learning Actions:**")
            for tip in rec["suggested_learning"][:3]:
                st.markdown(f"&nbsp;&nbsp;• {tip}")
