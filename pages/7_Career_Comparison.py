"""
Page 7 – Career Comparison
Allows students to compare multiple recommended careers side-by-side with required skills,
match percentages, skill gap metrics, and best-fit recommendations.
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

from ml.recommendation_model import get_recommender

st.markdown("# ⚖️ Multi-Career Comparison")
st.markdown("Compare up to 4 careers side-by-side to evaluate match scores, required skills, and effort needed.")
st.markdown("---")

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

recommender = get_recommender()
all_careers = recommender.career_df["career_title"].tolist() if recommender.career_df is not None else []
recs = st.session_state.get("recommendations", [])

# Default selection: top 3 recommended careers if available, else first 3
rec_titles = [r["career_title"] for r in recs]
default_selected = rec_titles[:3] if len(rec_titles) >= 3 else all_careers[:3]

col_sel1, col_sel2 = st.columns([3, 1])
with col_sel1:
    selected_careers = st.multiselect(
        "Select at least 3 careers to compare:",
        options=all_careers,
        default=default_selected,
        max_selections=4,
        help="Choose 3 or 4 careers to view side-by-side comparison.",
    )
with col_sel2:
    st.caption("Quick Action:")
    if recs and st.button("Top 3 Recommendations", use_container_width=True):
        selected_careers = rec_titles[:3]
        st.rerun()

if len(selected_careers) < 2:
    st.info("💡 Please select at least 2 (preferably 3 or 4) careers to see the comparison.")
    st.stop()

# Build comparison data
comparison_data = []
student_skills_all = []
from modules.student_registration import get_student_skills
from modules.skill_assessment import get_assessment
skills = get_student_skills(st.session_state.student_id)
assessment = get_assessment(st.session_state.student_id)
student_skills_set = {s["skill_name"].lower() for s in skills} | {k.lower() for k in assessment.keys()}

for ctitle in selected_careers:
    row = recommender.career_df[recommender.career_df["career_title"] == ctitle].iloc[0]
    required = [s.strip() for s in str(row["skills_list"]).split(",") if s.strip()]
    matching = [s for s in required if s.lower() in student_skills_set]
    missing = [s for s in required if s.lower() not in student_skills_set]

    # Find match percentage from current recommendations or calculate
    rec_match = next((r for r in recs if r["career_title"] == ctitle), None)
    if rec_match:
        match_pct = rec_match["match_pct"]
    else:
        # Calculate on the fly
        temp_recs = recommender.recommend(list(student_skills_set), top_n=len(all_careers))
        m = next((r for r in temp_recs if r["career_title"] == ctitle), None)
        match_pct = m["match_pct"] if m else 0.0

    comparison_data.append({
        "career_title": ctitle,
        "category": row.get("category", "General"),
        "match_pct": match_pct,
        "required_skills": required,
        "matching_skills": matching,
        "missing_skills": missing,
        "total_required": len(required),
        "total_matching": len(matching),
        "total_missing": len(missing),
        "description": row.get("description", "No description available."),
    })

# Sort by match percentage descending
comparison_data = sorted(comparison_data, key=lambda x: -x["match_pct"])
best_match = comparison_data[0]

# ── Best Match Highlight ───────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg, #1B5E20, #2E7D32); border:1px solid #4CAF50;
            border-radius:12px; padding:1.2rem 1.5rem; margin-bottom:1.5rem;">
    <h3 style="color:white; margin:0;">🏆 Best Profile Fit: {best_match['career_title']} ({best_match['match_pct']}% Match)</h3>
    <p style="color:#C8E6C9; margin:0.4rem 0 0 0; font-size:0.95rem;">
        You already meet <b>{best_match['total_matching']} of {best_match['total_required']}</b> required skills.
        Bridging <b>{best_match['total_missing']} skills</b> will achieve complete qualification for this career.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Side-by-Side Comparison Metrics ───────────────────────────────────────────
st.markdown("### 📊 Side-by-Side Overview")
cols = st.columns(len(comparison_data))

for idx, cdata in enumerate(comparison_data):
    with cols[idx]:
        is_best = (idx == 0)
        border_col = "#4CAF50" if is_best else "#1E88E5"
        st.markdown(f"""
        <div style="background:#1A2332; border:2px solid {border_col}; border-radius:10px; padding:1.2rem; min-height:320px;">
            <p style="color:#90CAF9; font-size:0.8rem; margin:0;">{'👑 RANK #1 BEST FIT' if is_best else f'OPTION #{idx+1}'}</p>
            <h3 style="color:white; margin:0.3rem 0; font-size:1.15rem;">{cdata['career_title']}</h3>
            <p style="color:#BBDEFB; font-size:0.85rem; margin-bottom:0.8rem;">📂 {cdata['category']}</p>
            <div style="font-size:2rem; font-weight:800; color:{'#4CAF50' if cdata['match_pct']>=60 else '#2196F3' if cdata['match_pct']>=40 else '#FF9800'};">
                {cdata['match_pct']}%
            </div>
            <p style="color:#90CAF9; font-size:0.85rem; margin-top:0.2rem;">Match Score</p>
            <hr style="border-color:#263340; margin:0.6rem 0;">
            <p style="color:white; font-size:0.85rem; margin:0.2rem 0;">✅ <b>{cdata['total_matching']}</b> Matched Skills</p>
            <p style="color:#F44336; font-size:0.85rem; margin:0.2rem 0;">❌ <b>{cdata['total_missing']}</b> Missing Skills</p>
            <p style="color:#B0BEC5; font-size:0.85rem; margin:0.2rem 0;">📋 <b>{cdata['total_required']}</b> Total Required</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"🎯 Select {cdata['career_title'][:15]}", key=f"sel_comp_{idx}"):
            st.session_state.selected_career = cdata['career_title']
            st.success(f"Selected **{cdata['career_title']}**! Go to Learning Pathway page.")

# ── Visual Comparison Charts ──────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📈 Visual Comparison")

tab_bar, tab_radar = st.tabs(["📊 Bar Comparison", "🕸️ Skill Overlap Breakdown"])

with tab_bar:
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Matching Skills",
        x=[c["career_title"] for c in comparison_data],
        y=[c["total_matching"] for c in comparison_data],
        marker_color="#4CAF50",
        text=[c["total_matching"] for c in comparison_data],
        textposition="outside",
    ))
    fig_bar.add_trace(go.Bar(
        name="Missing Skills (Gap)",
        x=[c["career_title"] for c in comparison_data],
        y=[c["total_missing"] for c in comparison_data],
        marker_color="#F44336",
        text=[c["total_missing"] for c in comparison_data],
        textposition="outside",
    ))
    fig_bar.update_layout(
        barmode="group",
        xaxis=dict(color="#90CAF9"),
        yaxis=dict(title="Number of Skills", color="#90CAF9", gridcolor="#263340"),
        paper_bgcolor="#0A1628",
        plot_bgcolor="#1A2332",
        font=dict(color="#FFFFFF"),
        legend=dict(bgcolor="#1A2332", bordercolor="#263340"),
        height=360,
        margin=dict(l=20, r=20, t=20, b=40),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with tab_radar:
    # Skill comparison table
    st.markdown("#### 🔍 Detailed Skill Requirements Matrix")
    all_compared_skills = sorted(list({s for c in comparison_data for s in c["required_skills"]}))
    matrix_rows = []
    for sk in all_compared_skills:
        has_skill = sk.lower() in student_skills_set
        row_dict = {
            "Skill": sk,
            "Your Status": "✅ Possessed" if has_skill else "❌ Need to Learn"
        }
        for c in comparison_data:
            req = sk in c["required_skills"]
            row_dict[c["career_title"]] = "Required" if req else "—"
        matrix_rows.append(row_dict)

    df_matrix = pd.DataFrame(matrix_rows)
    st.dataframe(df_matrix, use_container_width=True)
