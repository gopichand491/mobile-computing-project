"""
Page 6 – Skill Gap Analysis
Compares student skills against career requirements to detect completely missing skills,
low-proficiency skills needing improvement, and competent strengths.
"""

import streamlit as st
import os, sys
import plotly.graph_objects as go
import plotly.express as px
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

from modules.student_registration import get_student_skills
from modules.skill_assessment import get_assessment
from modules.skill_gap_analysis import gap_summary_table, priority_skills

st.markdown("# 📉 Skill Gap Analysis & Deficit Diagnosis")
st.markdown("Analyze missing requirements and identify low-proficiency competencies that need strengthening.")
st.markdown("---")

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
skills = get_student_skills(student_id)
assessment = get_assessment(student_id)

# Build student proficiency dictionary (skill_lower -> numeric proficiency 1-5)
prof_dict = {}
for s in skills:
    prof_dict[s["skill_name"].lower()] = float(s.get("proficiency", 3))
for sname, sc in assessment.items():
    prof_dict[sname.lower()] = float(sc)

recs = st.session_state.get("recommendations", [])
if not recs:
    st.warning("⚠️ Please run Career Recommendations first to perform gap analysis.")
    st.stop()

# ── Summary Across All Recommendations ────────────────────────────────────────
st.markdown("### 📊 Overall Competency Gap Matrix")
summary_df = gap_summary_table(recs)
st.dataframe(summary_df.style.background_gradient(subset=["Match %"], cmap="Blues"), use_container_width=True)

# ── Multi-Bar Breakdown ───────────────────────────────────────────────────────
st.markdown("### 📊 Matching vs Missing Skills Distribution")
fig = go.Figure()
fig.add_trace(go.Bar(
    name="Matching Skills",
    x=summary_df["Career"],
    y=summary_df["Matching Skills"],
    marker_color="#4CAF50",
    text=summary_df["Matching Skills"],
    textposition="outside",
))
fig.add_trace(go.Bar(
    name="Missing Skills Gap",
    x=summary_df["Career"],
    y=summary_df["Missing Skills"],
    marker_color="#F44336",
    text=summary_df["Missing Skills"],
    textposition="outside",
))
fig.update_layout(
    barmode="group",
    xaxis=dict(color="#90CAF9", tickangle=-15),
    yaxis=dict(title="Skill Count", color="#90CAF9", gridcolor="#263340"),
    paper_bgcolor="#0A1628",
    plot_bgcolor="#1A2332",
    font=dict(color="#FFFFFF"),
    legend=dict(bgcolor="#1A2332", bordercolor="#263340"),
    height=340,
    margin=dict(l=20, r=20, t=20, b=80),
)
st.plotly_chart(fig, use_container_width=True)

# ── Priority Skills Across All Careers ────────────────────────────────────────
st.markdown("### 🏆 Highest Priority Skills to Learn")
st.caption("Skills that appear as missing most frequently across all your recommended careers:")
missing_map = {r["career_title"]: r["missing_skills"] for r in recs}
priority = priority_skills(missing_map)

if priority:
    from collections import Counter
    counter = Counter()
    for skl in missing_map.values():
        counter.update([s.strip().title() for s in skl])

    top_skills = [{"Skill": k, "Missing In": v} for k, v in counter.most_common(12)]
    pdf = pd.DataFrame(top_skills)

    fig2 = px.bar(
        pdf, x="Missing In", y="Skill", orientation="h",
        color="Missing In", color_continuous_scale="Reds",
        title="Cross-Career Missing Skill Frequency",
    )
    fig2.update_layout(
        paper_bgcolor="#0A1628",
        plot_bgcolor="#1A2332",
        font=dict(color="#FFFFFF"),
        height=380,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Detailed Per-Career Deficit Inspection ────────────────────────────────────
st.markdown("---")
st.markdown("### 🔍 Deep-Dive: 3-Tier Skill Analysis for Specific Career")

career_select = st.selectbox("Select target career to diagnose:", [r["career_title"] for r in recs])
sel_rec = next(r for r in recs if r["career_title"] == career_select)

# Categorize into: Strong, Low-Proficiency, Missing
competent_skills = []
low_prof_skills = []
for sk in sel_rec["matching_skills"]:
    score = prof_dict.get(sk.lower(), 3.0)
    if score >= 3.0:
        competent_skills.append((sk, score))
    else:
        low_prof_skills.append((sk, score))

missing_skills = sel_rec["missing_skills"]

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("#### 🟢 Competent Skills (>= 3.0)")
    if competent_skills:
        for sk, sc in competent_skills:
            st.markdown(f"✅ **{sk}** (Proficiency: {sc:.1f}/5)")
    else:
        st.write("None meeting >= 3.0")

with c2:
    st.markdown("#### 🟡 Low-Proficiency Skills (< 3.0)")
    if low_prof_skills:
        for sk, sc in low_prof_skills:
            st.markdown(f"⚠️ **{sk}** (Needs improvement: {sc:.1f}/5)")
    else:
        st.write("No matching skills with low proficiency.")

with c3:
    st.markdown("#### 🔴 Missing Skills Gap")
    if missing_skills:
        for sk in missing_skills:
            st.markdown(f"❌ **{sk}** (Not possessed)")
    else:
        st.success("Full coverage! No missing skills.")

# Donut chart
total_cnt = len(sel_rec["required_skills"])
c_cnt = len(competent_skills)
lp_cnt = len(low_prof_skills)
m_cnt = len(missing_skills)

fig3 = go.Figure(go.Pie(
    labels=["Competent (>=3)", "Low Proficiency (<3)", "Completely Missing"],
    values=[c_cnt, lp_cnt, m_cnt],
    hole=0.6,
    marker=dict(colors=["#4CAF50", "#FF9800", "#F44336"]),
    textfont=dict(color="#FFFFFF"),
))
fig3.update_layout(
    paper_bgcolor="#0A1628",
    font=dict(color="#FFFFFF"),
    height=300,
    margin=dict(l=20, r=20, t=20, b=20),
    annotations=[dict(
        text=f"{sel_rec['match_pct']}%<br><span style='font-size:11px'>Match</span>",
        x=0.5, y=0.5,
        font_size=20, showarrow=False, font_color="#FFFFFF"
    )],
)
st.plotly_chart(fig3, use_container_width=True)
