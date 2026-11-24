"""
Page 5 – Career Recommendations
ML-powered career matching using TF-IDF + Cosine Similarity.
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

from assets.premium_ui import inject_premium_ui, premium_header, neon_divider
inject_premium_ui("recommendations")

from modules.student_registration import get_student_by_id, get_student_skills
from modules.skill_assessment import get_assessment
from modules.career_recommendation import save_recommendations, format_match_badge
from ml.recommendation_model import get_recommender

premium_header("ML Career Recommendations",
               "Intelligent career matching using O*NET occupational data and TF-IDF vectorization.", "🎯")
neon_divider()

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student_name = st.session_state.student_name
student = get_student_by_id(student_id)

skills = get_student_skills(student_id)
assessment = get_assessment(student_id)

skill_names = [s["skill_name"] for s in skills]
assessment_skills = list(assessment.keys())
all_student_skills = list(set(skill_names + assessment_skills))

if not all_student_skills:
    st.warning("⚠️ Please add your skills and complete the Skill Assessment first.")
    st.stop()

# ── Settings sidebar ──────────────────────────────────────────────
recommender = get_recommender()
categories = recommender.get_categories()

with st.sidebar:
    st.markdown("### ⚙️ Recommendation Settings")
    top_n = st.slider("Number of recommendations", 3, 10, 5)
    category_filter = st.selectbox("Filter by career domain", categories)
    if st.button("🔄 Recalculate", use_container_width=True):
        st.session_state.recommendations = []

# ── Run model ─────────────────────────────────────────────────────
if not st.session_state.get("recommendations"):
    with st.spinner("🤖 Running ML TF-IDF & Cosine Similarity engine..."):
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

# ── Algorithm banner ──────────────────────────────────────────────
st.info(
    "🤖 **ML Engine**: Scikit-learn TF-IDF Vectorizer + Cosine Similarity | "
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
        colorscale=[[0, "#7B2FFF"], [0.5, "#00D4FF"], [1, "#00F5D4"]],
        showscale=True,
        colorbar=dict(title="Match %"),
    ),
    text=[f"{r['match_pct']}%" for r in recs],
    textposition="outside",
))
fig.update_layout(
    xaxis=dict(color="#7B8FA3", tickangle=-15),
    yaxis=dict(title="Match %", color="#7B8FA3", range=[0, 115], gridcolor="rgba(255,255,255,0.06)"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#B0C4DE"),
    height=340,
    margin=dict(l=20, r=20, t=20, b=80),
)
st.plotly_chart(fig, use_container_width=True)

# ── Career Cards ──────────────────────────────────────────────────
for i, rec in enumerate(recs, 1):
    badge = format_match_badge(rec["match_pct"])
    medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else '🎖️'

    with st.expander(f"{medal} #{i} {rec['career_title']}  –  {rec['match_pct']}% Match  {badge}", expanded=(i == 1)):
        # Rationale
        st.markdown(f"""
        <div class="glass-card" style="padding:0.8rem 1rem; border-left:3px solid rgba(0,212,255,0.4);">
            <p style="color:#B0C4DE !important; margin:0; font-size:0.88rem;">
                <b style="color:#00D4FF;">💡 Recommendation Rationale:</b> {rec.get('explanation')}</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**📋 Role Description:** {rec['description']}")
            st.markdown(f"**🏷️ Domain:** {rec['category']} &nbsp;|&nbsp; **O\\*NET-SOC:** `{rec['onet_code']}`")

        with col2:
            st.markdown("**✅ Matching Skills**")
            if rec["matching_skills"]:
                for sk in rec["matching_skills"][:8]:
                    st.markdown(f"<span style='color:#00F5D4;'>✓</span> {sk}", unsafe_allow_html=True)
            else:
                st.write("None detected")

        with col3:
            st.markdown("**❌ Missing Skills**")
            if rec["missing_skills"]:
                for sk in rec["missing_skills"][:8]:
                    st.markdown(f"<span style='color:#FF006E;'>✗</span> {sk}", unsafe_allow_html=True)
            else:
                st.write("Full match!")

        # Coverage bar
        total = len(rec["required_skills"])
        matched = len(rec["matching_skills"])
        pct = matched / total if total > 0 else 0
        st.markdown(f"**Coverage:** {matched}/{total} required skills ({rec['match_pct']}%)")
        st.progress(pct)

        # Action Buttons
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button(f"🗺️ Learning Pathway for {rec['career_title']}", key=f"lp_btn_{i}"):
                st.session_state.selected_career = rec["career_title"]
                st.session_state.selected_career_data = rec
                st.success(f"Selected **{rec['career_title']}**! Navigate to Learning Pathway.")
        with c_btn2:
            if st.button(f"⚖️ Compare {rec['career_title']}", key=f"comp_btn_{i}"):
                st.session_state.selected_career = rec["career_title"]
                st.success(f"Added **{rec['career_title']}** to Comparison!")

        if rec.get("suggested_learning"):
            st.markdown("**🎯 Recommended Learning Actions:**")
            for tip in rec["suggested_learning"][:3]:
                st.markdown(f"&nbsp;&nbsp;• {tip}")
