"""
SkillMatch – Mobile Skill-Based Learning and Career Recommendation System
Main Application Entry Point and Interactive Dashboard
Run with: streamlit run app.py
"""

import streamlit as st
import os
import sys

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SkillMatch – Career Guidance System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "SkillMatch – B.Tech Academic Project | Skill-Based Career Recommendation System",
    },
)

# ── Load CSS ─────────────────────────────────────────────────────────────────
css_path = os.path.join(ROOT, "assets", "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Database initialization ───────────────────────────────────────────────────
from database.db_setup import setup_database
setup_database()

# ── Session state defaults ────────────────────────────────────────────────────
if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "student_name" not in st.session_state:
    st.session_state.student_name = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "selected_career" not in st.session_state:
    st.session_state.selected_career = None

# ── Database Helpers for Live Metrics ──────────────────────────────────────────
from database.db_connection import execute_query
from ml.data_preprocessing import load_or_create_processed_data

career_df, data_source = load_or_create_processed_data()

# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
        <div style="font-size: 2.8rem;">🎯</div>
        <h1 style="color:white; font-size:1.6rem; margin:0; font-weight:800;">SkillMatch</h1>
        <p style="color:#90CAF9; font-size:0.8rem; margin:0;">Career Guidance & Upskilling</p>
    </div>
    <hr style="border-color: rgba(255,255,255,0.15); margin-top:0;">
    """, unsafe_allow_html=True)

    # Demo Account Quick Button
    if not st.session_state.student_id:
        st.markdown("### 🎓 Quick Demo Access")
        if st.button("⚡ Load Demo Profile (Arjun Sharma)", use_container_width=True):
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
            st.rerun()

    # Logged-in badge
    if st.session_state.student_name:
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.1); border:1px solid #4CAF50; border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:1rem;">
            <p style="color:#C8E6C9; margin:0; font-size:0.75rem;">Active Session</p>
            <p style="color:white; margin:0; font-weight:700; font-size:0.95rem;">👤 {st.session_state.student_name}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Log Out", key="sidebar_logout", use_container_width=True):
            st.session_state.student_id = None
            st.session_state.student_name = None
            st.session_state.recommendations = []
            st.session_state.selected_career = None
            st.rerun()

    st.markdown("### 📋 Navigation")
    st.page_link("app.py", label="🏠 Home Dashboard")

    st.markdown("**Student Module**")
    st.page_link("pages/2_Registration.py", label="📝 Registration & Login")
    st.page_link("pages/3_Skill_Assessment.py", label="📊 Skill Assessment")
    st.page_link("pages/4_Learner_Profile.py", label="👤 Learner Profile")

    st.markdown("**Career & ML Engine**")
    st.page_link("pages/5_Career_Recommendations.py", label="🎯 Career Recommendations")
    st.page_link("pages/6_Skill_Gap_Analysis.py", label="📉 Skill Gap Analysis")
    st.page_link("pages/7_Career_Comparison.py", label="⚖️ Career Comparison")
    st.page_link("pages/8_Learning_Pathway.py", label="🗺️ Learning Pathway")
    st.page_link("pages/9_Progress_Tracking.py", label="✅ Progress Tracking")
    st.page_link("pages/10_Career_Report.py", label="📄 Career Report (PDF)")

    st.markdown("**Documentation & Data**")
    st.page_link("pages/11_Dataset_Information.py", label="🗄️ Dataset Information")
    st.page_link("pages/12_About_Project.py", label="ℹ️ About Project")

    st.markdown("<hr style='border-color:rgba(255,255,255,0.15);'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#90CAF9; font-size:0.75rem; text-align:center;'>B.Tech Project Demonstration<br>Powered by O*NET Data + ML</p>",
        unsafe_allow_html=True,
    )

# ── Main Dashboard Header ─────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:1.5rem 0 1rem 0;">
    <h1 style="color:white; font-size:2.4rem; font-weight:800; margin:0;">
        🎯 SkillMatch Career Intelligence System
    </h1>
    <p style="color:#90CAF9; font-size:1.05rem; margin-top:0.4rem;">
        Data-driven career recommendation, competency diagnosis, and personalized learning roadmap.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Dynamic Stats Row ─────────────────────────────────────────────────────────
if st.session_state.student_id:
    sid = st.session_state.student_id

    # 1. Total assessments completed
    assess_res = execute_query("SELECT COUNT(*) as cnt FROM skill_assessments WHERE student_id = ?", (sid,), fetch="one")
    total_assessments = assess_res["cnt"] if assess_res else 0

    # 2. Total registered skills
    skills_res = execute_query("SELECT COUNT(*) as cnt FROM student_skills WHERE student_id = ?", (sid,), fetch="one")
    total_skills = skills_res["cnt"] if skills_res else 0

    # 3. Top career recommendation
    recs_res = execute_query(
        "SELECT career_title, match_score FROM career_recommendations WHERE student_id = ? ORDER BY match_score DESC LIMIT 1",
        (sid,), fetch="one"
    )
    if recs_res:
        top_career = recs_res["career_title"]
        top_score = f"{round(recs_res['match_score']*100, 1)}%"
    else:
        top_career = "Run Model"
        top_score = "Pending"

    # 4. Learning pathway progress
    prog_res = execute_query(
        "SELECT COUNT(*) as tot, SUM(is_completed) as comp FROM learning_progress WHERE student_id = ?",
        (sid,), fetch="one"
    )
    if prog_res and prog_res["tot"] and prog_res["tot"] > 0:
        comp_val = prog_res["comp"] or 0
        path_pct = f"{round(comp_val / prog_res['tot'] * 100, 1)}%"
    else:
        path_pct = "0.0%"

    st.markdown("### 📊 Your Live Academic Progress Metrics")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("📝 Skills Assessed", str(total_assessments), "in SQLite")
    with m2:
        st.metric("🛠️ Tracked Skills", str(total_skills), "competencies")
    with m3:
        st.metric("🎯 Top Career Match", top_career[:18] + ("..." if len(top_career) > 18 else ""), top_score)
    with m4:
        st.metric("📈 Pathway Completion", path_pct, "topics done")

else:
    # System-level stats
    st_res = execute_query("SELECT COUNT(*) as cnt FROM students", fetch="one")
    student_count = st_res["cnt"] if st_res else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("🎯 Career Profiles", f"{len(career_df)}", "in database")
    with m2:
        st.metric("📂 Career Domains", f"{career_df['category'].nunique()}", "categories")
    with m3:
        st.metric("👥 Registered Students", str(student_count), "in SQLite")
    with m4:
        st.metric("🤖 ML Engine", "TF-IDF + CosSim", "scikit-learn")

st.markdown("<br>", unsafe_allow_html=True)

# ── Dynamic Action Center ─────────────────────────────────────────────────────
st.markdown("## 🚀 Guided Student Workflow")

st.markdown("""
<div style="background:#1A2332; border:1px solid #263340; border-radius:12px; padding:1.2rem; margin-bottom:1.5rem;">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <span style="color:#FFFFFF; font-weight:700;">Workflow Step:</span>
        <span style="color:#90CAF9;">1. Register</span> →
        <span style="color:#90CAF9;">2. Assess Skills</span> →
        <span style="color:#90CAF9;">3. View Profile</span> →
        <span style="color:#90CAF9;">4. ML Recommendations</span> →
        <span style="color:#90CAF9;">5. Gap Analysis</span> →
        <span style="color:#90CAF9;">6. Compare Careers</span> →
        <span style="color:#90CAF9;">7. Follow Pathway</span> →
        <span style="color:#90CAF9;">8. Download PDF Report</span>
    </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("""
    <div style="background:#1A2332; border:1px solid #1E88E5; border-radius:10px; padding:1.2rem; height:200px;">
        <div style="font-size:2.2rem;">📝</div>
        <h4 style="color:white; margin:0.3rem 0;">1. Skill Profiling</h4>
        <p style="color:#90CAF9; font-size:0.85rem;">
            Enter technical and soft skills, or take our interactive MCQ diagnostic test.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Start Assessment →", key="dash_btn_1", use_container_width=True):
        st.switch_page("pages/3_Skill_Assessment.py")

with c2:
    st.markdown("""
    <div style="background:#1A2332; border:1px solid #00ACC1; border-radius:10px; padding:1.2rem; height:200px;">
        <div style="font-size:2.2rem;">🤖</div>
        <h4 style="color:white; margin:0.3rem 0;">2. ML Matching</h4>
        <p style="color:#90CAF9; font-size:0.85rem;">
            TF-IDF and Cosine Similarity compute real-time match scores against O*NET data.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Get Recommendations →", key="dash_btn_2", use_container_width=True):
        st.switch_page("pages/5_Career_Recommendations.py")

with c3:
    st.markdown("""
    <div style="background:#1A2332; border:1px solid #FF6F00; border-radius:10px; padding:1.2rem; height:200px;">
        <div style="font-size:2.2rem;">⚖️</div>
        <h4 style="color:white; margin:0.3rem 0;">3. Career Comparison</h4>
        <p style="color:#90CAF9; font-size:0.85rem;">
            Compare 3+ careers side-by-side to discover the lowest skill gap and highest match.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Compare Careers →", key="dash_btn_3", use_container_width=True):
        st.switch_page("pages/7_Career_Comparison.py")

with c4:
    st.markdown("""
    <div style="background:#1A2332; border:1px solid #2E7D32; border-radius:10px; padding:1.2rem; height:200px;">
        <div style="font-size:2.2rem;">📄</div>
        <h4 style="color:white; margin:0.3rem 0;">4. Download Report</h4>
        <p style="color:#90CAF9; font-size:0.85rem;">
            Generate an official PDF dossier with complete profile, recommendations, and roadmap.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Generate PDF Report →", key="dash_btn_4", use_container_width=True):
        st.switch_page("pages/10_Career_Report.py")

# ── Data Source Info ───────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
source_label = "O*NET Official Database" if data_source == "onet" else "Cleaned Occupational Dataset (O*NET-aligned)"
st.markdown(f"""
<div style="background:#1A2332; border-left:4px solid #4CAF50; border-radius:8px; padding:1rem 1.4rem;">
    <p style="color:white; margin:0; font-weight:700;">🗄️ Dataset Source: {source_label}</p>
    <p style="color:#90CAF9; margin:0.2rem 0 0 0; font-size:0.85rem;">
        Contains {len(career_df)} occupational profiles with standardized skills across 7 domains.
        Public domain U.S. Department of Labor O*NET database.
    </p>
</div>
""", unsafe_allow_html=True)
