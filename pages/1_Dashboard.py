"""
Page 1 – Interactive Career Intelligence Dashboard
Comprehensive student analytics dashboard displaying real-time profile data,
skills breakdown, ML career recommendations, skill gap diagnosis, learning progress,
and career readiness scoring from SQLite.
"""

import os
import sys
import streamlit as st
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
    with open(css_path, "r", encoding="utf-8", errors="replace") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from assets.premium_ui import inject_premium_ui, premium_header, neon_divider, glass_card
inject_premium_ui("dashboard")

from database.db_connection import execute_query
from modules.student_registration import get_student_by_id, get_student_skills
from modules.skill_assessment import get_assessment
from modules.learning_pathway import get_pathway, get_learning_path, save_pathway
from modules.progress_tracking import get_overall_progress, get_progress, mark_topic_complete
from ml.recommendation_model import get_recommender
from ml.data_preprocessing import load_or_create_processed_data

premium_header(
    "Career Intelligence Dashboard",
    "Real-time analytics on your skills, career trajectory, competency gaps, and learning progression.",
    "📊"
)
neon_divider()

# ── Session State Check ───────────────────────────────────────────────────────
student_id = st.session_state.get("student_id")
career_df, data_source = load_or_create_processed_data()

# ══════════════════════════════════════════════════════════════════════════════
# GUEST / LOGGED-OUT STATE
# ══════════════════════════════════════════════════════════════════════════════
if not student_id:
    st.markdown("""
    <div class="glass-card" style="padding:1.4rem 1.6rem; margin-bottom:1.5rem; border-left:4px solid #00D4FF;">
        <h3 style="color:#FFFFFF !important; margin:0 0 0.5rem 0;">👋 Welcome to SkillMatch Career Intelligence</h3>
        <p style="color:#B0C4DE !important; margin:0; font-size:0.95rem; line-height:1.5;">
            Log in or register your academic profile to unlock real-time skill gap analysis, personalized ML career recommendations, 
            interactive learning roadmaps, and career readiness evaluations powered by O*NET occupational data.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c_demo, c_reg, c_login = st.columns([1.5, 1, 1])
    with c_demo:
        if st.button("⚡ Quick Load Demo Profile (Arjun Sharma)", use_container_width=True):
            from modules.student_registration import create_student, delete_student_skills, save_student_skills
            from modules.skill_assessment import save_assessment

            demo_id = create_student(
                name="Arjun Sharma",
                email="arjun.demo@skillmatch.edu",
                education_level="B.Tech (Pursuing)",
                degree="B.Tech Computer Science",
                department="Computer Science & Engineering",
                year_of_study="3rd Year",
                interests="Data Science & Analytics, Machine Learning & AI, Software Development",
            )
            demo_skills = [
                {"skill_name": "Python", "skill_type": "technical", "proficiency": 4},
                {"skill_name": "SQL", "skill_type": "technical", "proficiency": 4},
                {"skill_name": "Git", "skill_type": "technical", "proficiency": 4},
                {"skill_name": "Machine Learning", "skill_type": "technical", "proficiency": 3},
                {"skill_name": "Statistics", "skill_type": "technical", "proficiency": 3},
                {"skill_name": "Communication", "skill_type": "soft", "proficiency": 4},
                {"skill_name": "Problem Solving", "skill_type": "soft", "proficiency": 5},
                {"skill_name": "Teamwork", "skill_type": "soft", "proficiency": 4},
            ]
            delete_student_skills(demo_id)
            save_student_skills(demo_id, demo_skills)
            save_assessment(demo_id, {
                "Python": 4.5, "SQL": 4.0, "Git": 4.0, "Machine Learning": 3.5,
                "Statistics": 3.0, "Communication": 4.0, "Problem Solving": 5.0, "Teamwork": 4.0
            })
            st.session_state.student_id = demo_id
            st.session_state.student_name = "Arjun Sharma"
            st.session_state.recommendations = []
            st.session_state.selected_career = "Data Analyst"
            st.success("✅ Demo profile activated!")
            st.rerun()

    with c_reg:
        if st.button("📝 Register New Profile", use_container_width=True):
            st.switch_page("pages/2_Registration.py")

    with c_login:
        if st.button("🔑 Existing Student Login", use_container_width=True):
            st.switch_page("pages/2_Registration.py")

    st.markdown("<br>", unsafe_allow_html=True)

    # Global System Statistics
    st.markdown("### 🌐 Platform Occupational Intelligence")
    st_res = execute_query("SELECT COUNT(*) as cnt FROM students", fetch="one")
    registered_students = st_res["cnt"] if st_res else 0

    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.metric("🎯 Occupational Profiles", f"{len(career_df)}" if career_df is not None else "900+", "O*NET standard")
    with g2:
        st.metric("📂 Career Domains", f"{career_df['category'].nunique()}" if career_df is not None else "7", "Technology & Eng.")
    with g3:
        st.metric("👥 Registered Students", str(registered_students), "in SQLite")
    with g4:
        st.metric("🤖 Matching Algorithm", "TF-IDF + Cosine Sim", "Scikit-learn")

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# ACTIVE STUDENT DASHBOARD (AUTHENTICATED)
# ══════════════════════════════════════════════════════════════════════════════

# 1. Fetch live student record
student = get_student_by_id(student_id)
if not student:
    st.error("Student profile not found in database. Please log in again.")
    st.session_state.student_id = None
    st.stop()

student_name = student["name"]
st.session_state.student_name = student_name

# 2. Fetch skills and assessments
skills = get_student_skills(student_id)
tech_skills = [s for s in skills if s.get("skill_type") == "technical"]
soft_skills = [s for s in skills if s.get("skill_type") == "soft"]
assessment = get_assessment(student_id)

all_skill_names = list(set([s["skill_name"] for s in skills] + list(assessment.keys())))

# 3. Fetch or compute recommendations
recs = st.session_state.get("recommendations", [])
if not recs and all_skill_names:
    try:
        recommender = get_recommender()
        recs = recommender.recommend(
            all_skill_names,
            top_n=5,
            student_interests=student.get("interests", "")
        )
        st.session_state["recommendations"] = recs
    except Exception:
        recs = []

# Top career match calculation
top_career = recs[0]["career_title"] if recs else "Data Analyst"
top_match_pct = recs[0]["match_pct"] if recs else 70.0

# Active target career
target_career = st.session_state.get("selected_career") or top_career
st.session_state["selected_career"] = target_career

# 4. Fetch learning pathway and progress
pathway = get_pathway(student_id, target_career)
if not pathway:
    missing_for_target = []
    target_rec = next((r for r in recs if r["career_title"].lower() == target_career.lower()), None)
    if target_rec:
        missing_for_target = target_rec.get("missing_skills", [])
    pathway = get_learning_path(target_career, missing_for_target)
    save_pathway(student_id, target_career, pathway)

progress_data = get_progress(student_id, target_career)
overall_progress = get_overall_progress(student_id)

total_topics = progress_data["total_topics"]
completed_topics = progress_data["completed_topics"]
progress_pct = progress_data["progress_pct"]

# 5. Calculate Career Readiness Score
# Formula: 45% ML Career Match + 35% Pathway Completion + 20% Diagnostic Assessment Score
avg_assess_score = (sum(assessment.values()) / len(assessment)) if assessment else 3.0
assess_pct = (avg_assess_score / 5.0) * 100.0

career_readiness_score = round(
    (0.45 * top_match_pct) + (0.35 * progress_pct) + (0.20 * assess_pct), 1
)

if career_readiness_score >= 80:
    readiness_badge = "🌟 Highly Market-Ready"
    readiness_color = "#00F5D4"
elif career_readiness_score >= 60:
    readiness_badge = "🚀 Job Ready / Advancing"
    readiness_color = "#00D4FF"
elif career_readiness_score >= 40:
    readiness_badge = "📈 Core Competencies Developing"
    readiness_color = "#FFD700"
else:
    readiness_badge = "🌱 Foundational Phase"
    readiness_color = "#FF006E"


# ── KEY PERFORMANCE METRIC CARDS ──────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.metric("👤 Academic Status", student.get("year_of_study", "3rd Year"), student.get("degree", "B.Tech"))
with m2:
    st.metric("🛠️ Total Skills", f"{len(skills)} Added", f"{len(tech_skills)} Tech • {len(soft_skills)} Soft")
with m3:
    st.metric("🎯 Top Match", top_career[:16] + ("..." if len(top_career) > 16 else ""), f"{top_match_pct}% Match")
with m4:
    st.metric("📚 Pathway Progress", f"{completed_topics}/{total_topics} Done", f"{progress_pct}% Completed")
with m5:
    st.metric("🏅 Readiness Index", f"{career_readiness_score}%", readiness_badge.split()[1])

st.markdown("<br>", unsafe_allow_html=True)


# ── STUDENT PROFILE HERO CARD ─────────────────────────────────────────────────
interests_str = student.get("interests", "Technology & Software Development")
glass_card(f"""
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
        <h2 style="color:#FFFFFF !important; margin:0; font-size:1.45rem;">
            👤 {student_name}
        </h2>
        <p style="color:#B0C4DE !important; margin:0.3rem 0; font-size:0.9rem;">
            🎓 <b>{student.get('education_level', 'B.Tech')}</b> &nbsp;|&nbsp;
            🏛️ <b>{student.get('department', 'Engineering')}</b> &nbsp;|&nbsp;
            📅 <b>{student.get('year_of_study', '3rd Year')}</b>
        </p>
        <p style="color:#7B8FA3 !important; margin:0; font-size:0.85rem;">
            🎯 <b>Career Interests:</b> {interests_str}
        </p>
    </div>
    <div style="text-align:right;">
        <span style="background:rgba(0,212,255,0.12); color:#00D4FF; border:1px solid rgba(0,212,255,0.3); padding:4px 12px; border-radius:14px; font-size:0.82rem; font-weight:700;">
            Target: {target_career}
        </span>
        <div style="margin-top:0.4rem;">
            <span style="color:{readiness_color}; font-weight:700; font-size:0.95rem;">{readiness_badge}</span>
        </div>
    </div>
</div>
""")

st.markdown("<br>", unsafe_allow_html=True)


# ── INTERACTIVE ANALYTICS TABS ────────────────────────────────────────────────
tab_charts, tab_gaps, tab_pathway, tab_readiness = st.tabs([
    "📈 Career & Skill Visualizations",
    "📉 Live Skill Gap Diagnosis",
    "🗺️ Learning Pathway Milestones",
    "🎯 Readiness & Next Action Steps"
])

# ── TAB 1: VISUALIZATIONS ─────────────────────────────────────────────────────
with tab_charts:
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### 🏆 Top Recommended Career Trajectories")
        if recs:
            rec_df = pd.DataFrame(recs[:5])
            fig_bar = px.bar(
                rec_df,
                x="match_pct",
                y="career_title",
                orientation="h",
                text="match_pct",
                color="match_pct",
                color_continuous_scale=[[0, "#7B2FFF"], [0.5, "#00D4FF"], [1, "#00F5D4"]],
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#B0C4DE"),
                height=320,
                xaxis=dict(title="Match Percentage (%)", range=[0, 100], gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(title="", autorange="reversed"),
                coloraxis_showscale=False,
                margin=dict(l=10, r=20, t=10, b=30),
            )
            fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Run Career Recommendations to visualize your career match distribution.")

    with col_chart2:
        st.markdown("#### 📊 Learning Pathway Topic Completion")
        labels = ["Completed Topics", "Pending Topics"]
        values = [completed_topics, max(0, total_topics - completed_topics)]
        colors = ["#00F5D4", "rgba(255,255,255,0.1)"]

        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker=dict(colors=colors),
            textinfo="value",
            hoverinfo="label+percent",
        )])
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#B0C4DE"),
            height=320,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            margin=dict(l=10, r=10, t=10, b=10),
            annotations=[dict(text=f"<b>{progress_pct}%</b><br>Done", x=0.5, y=0.5, font_size=18, font_color="#00F5D4", showarrow=False)]
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Competency Score Horizontal Bar
    if assessment:
        st.markdown("#### 🎯 Diagnostic Assessment Competencies")
        assess_items = sorted(assessment.items(), key=lambda x: x[1], reverse=True)[:8]
        as_df = pd.DataFrame({"Skill": [k for k, v in assess_items], "Score": [v for k, v in assess_items]})
        fig_as = px.bar(
            as_df,
            x="Score",
            y="Skill",
            orientation="h",
            text="Score",
            color="Score",
            color_continuous_scale=[[0, "#FF006E"], [0.5, "#00D4FF"], [1, "#00F5D4"]],
            range_x=[0, 5.5],
        )
        fig_as.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#B0C4DE"),
            height=280,
            xaxis=dict(title="Proficiency Rating (1 - 5)", gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(title="", autorange="reversed"),
            coloraxis_showscale=False,
            margin=dict(l=10, r=20, t=10, b=30),
        )
        fig_as.update_traces(texttemplate="%{text:.1f} / 5", textposition="outside")
        st.plotly_chart(fig_as, use_container_width=True)


# ── TAB 2: SKILL GAP DIAGNOSIS ────────────────────────────────────────────────
with tab_gaps:
    st.markdown(f"### 📉 Skill Gap Diagnosis for Target Role: **{target_career}**")
    
    # Retrieve required skills from O*NET dataset
    matching_skills = []
    missing_skills = []
    if career_df is not None:
        match_row = career_df[career_df["career_title"].str.strip().str.lower() == target_career.strip().lower()]
        if not match_row.empty:
            req_list = [s.strip() for s in str(match_row.iloc[0]["skills_list"]).split(",") if s.strip()]
            student_skill_set = {s.lower() for s in all_skill_names}
            matching_skills = [s for s in req_list if s.lower() in student_skill_set]
            missing_skills = [s for s in req_list if s.lower() not in student_skill_set]

    c_match, c_missing = st.columns(2)
    with c_match:
        st.markdown("#### ✅ Matching Competencies")
        if matching_skills:
            for s in matching_skills:
                st.markdown(f"🟢 **{s}** — Validated in your student profile")
        else:
            st.info("No direct skill matches registered for this role yet. Explore learning topics below!")

    with c_missing:
        st.markdown("#### ❌ Missing Skill Gaps")
        if missing_skills:
            for s in missing_skills:
                st.markdown(f"🔴 **{s}** — Priority competency to bridge")
        else:
            st.success("🎉 Outstanding! You possess all primary prerequisite skills for this career!")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Open Full Skill Gap Analysis Page", use_container_width=True):
        st.switch_page("pages/6_Skill_Gap_Analysis.py")


# ── TAB 3: LEARNING PATHWAY MILESTONES ────────────────────────────────────────
with tab_pathway:
    st.markdown(f"### 🗺️ Target Learning Pathway: **{target_career}**")
    st.caption(f"Progress: {completed_topics} of {total_topics} topics completed ({progress_pct}%)")
    st.progress(progress_pct / 100.0)

    if pathway:
        for step in pathway:
            topic_name = step.get("topic", "")
            step_num = step.get("step_number", 1)
            level = step.get("level", "Beginner")
            is_done = progress_data["status_map"].get(topic_name, False)

            level_color = "#00F5D4" if level == "Beginner" else "#00D4FF" if level == "Intermediate" else "#FF006E"
            status_icon = "✅" if is_done else "⏳"
            
            c_check, c_body = st.columns([1, 8])
            with c_check:
                new_done = st.checkbox(
                    "Done",
                    value=is_done,
                    key=f"dash_topic_{step_num}_{topic_name}",
                    label_visibility="collapsed"
                )
                if new_done != is_done:
                    mark_topic_complete(student_id, target_career, topic_name, new_done)
                    st.rerun()

            with c_body:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:0.5rem 0.8rem; margin-bottom:0.4rem;">
                    <span style="color:{level_color}; font-weight:700; font-size:0.75rem; text-transform:uppercase;">[{level}]</span>
                    <span style="color:white; font-weight:600; margin-left:6px; font-size:0.92rem;">{status_icon} Step {step_num}: {topic_name}</span>
                    <p style="color:#7B8FA3; margin:0.2rem 0 0 0; font-size:0.8rem;">{step.get('description', '')}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No learning pathway generated yet. Visit the Learning Pathway page to initialize your curriculum.")

    if st.button("🗺️ Manage Full Learning Pathway & Resources", use_container_width=True):
        st.switch_page("pages/8_Learning_Pathway.py")


# ── TAB 4: READINESS & ACTION STEPS ───────────────────────────────────────────
with tab_readiness:
    st.markdown("### 🎯 Career Readiness Evaluation")
    
    st.markdown(f"""
    <div class="glass-card" style="padding:1.2rem; border-left:4px solid {readiness_color}; margin-bottom:1rem;">
        <h3 style="color:{readiness_color} !important; margin:0;">Score: {career_readiness_score}% – {readiness_badge}</h3>
        <p style="color:#B0C4DE !important; margin:0.4rem 0 0 0; font-size:0.92rem;">
            Your readiness score is dynamically calculated from your O*NET ML match score ({top_match_pct}%), 
            learning pathway completion ({progress_pct}%), and diagnostic assessment rating ({assess_pct:.1f}%).
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 📋 Recommended Immediate Next Steps:")
    step_1 = f"Complete the next pending topic in your **{target_career}** learning pathway."
    step_2 = f"Focus on bridging identified priority gap: **{missing_skills[0]}**" if missing_skills else "Build a capstone project demonstrating your technical competencies."
    step_3 = "Generate and download your official academic Career Report PDF for faculty or placement reviews."

    st.markdown(f"1. 📌 **Curriculum Milestone:** {step_1}")
    st.markdown(f"2. 💡 **Skill Priority:** {step_2}")
    st.markdown(f"3. 📄 **Official Dossier:** {step_3}")

    st.markdown("<br>", unsafe_allow_html=True)
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    with c_btn1:
        if st.button("📄 Download Career Report (PDF)", use_container_width=True):
            st.switch_page("pages/10_Career_Report.py")
    with c_btn2:
        if st.button("🤖 Ask AI Career Mentor", use_container_width=True):
            st.switch_page("pages/13_AI_Career_Assistant.py")
    with c_btn3:
        if st.button("📊 Update Skill Assessment", use_container_width=True):
            st.switch_page("pages/3_Skill_Assessment.py")
