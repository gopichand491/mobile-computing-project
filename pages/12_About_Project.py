"""
Page 12 – About Project
Comprehensive overview of SkillMatch: problem statement, architecture, ML breakdown, tech stack.
"""

import streamlit as st
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

css_path = os.path.join(ROOT, "assets", "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8", errors="replace") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from assets.premium_ui import inject_premium_ui, premium_header, neon_divider, glass_card
inject_premium_ui("about")

premium_header("About SkillMatch System",
               "Mobile Skill-Based Learning and Career Recommendation System", "ℹ️")
neon_divider()

# ── Hero ──────────────────────────────────────────────────────────
glass_card("""
    <div style="text-align:center; padding:1.2rem 1rem;">
        <div style="font-size:3.5rem; animation:float 3s ease-in-out infinite;">🎯</div>
        <h1 style="color:white !important; font-size:2.2rem; font-weight:800; margin:0.3rem 0; font-family:'Orbitron',sans-serif;">
            SkillMatch
        </h1>
        <h3 style="color:#00D4FF !important; font-weight:500; margin:0; font-size:1.1rem;">
            AI-Powered Career Guidance & Skill Intelligence Platform
        </h3>
        <p style="color:#7B8FA3 !important; margin:0.6rem 0 0 0; font-size:0.92rem;">
            B.Tech Academic Project | O*NET Occupational Data + Scikit-learn TF-IDF Machine Learning
        </p>
    </div>
""")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Project Overview", "🤖 ML Recommendation Algorithm", "🏗️ System Architecture", "📦 Tech Stack"])

# ── Tab 1: Overview ───────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🎯 Core Objectives")
        objectives = [
            "Accurately analyze student technical and soft skills through structured assessments",
            "Recommend top-fit careers dynamically using TF-IDF and Cosine Similarity",
            "Perform comprehensive 3-tier skill gap analysis (competent, low-proficiency, missing)",
            "Enable side-by-side career comparison across 3+ target roles",
            "Generate personalized learning roadmaps categorized into Beginner, Intermediate, and Advanced tiers",
            "Track topic completion persistently in SQLite across application sessions",
            "Generate downloadable academic Career Report dossiers in PDF format",
            "Provide 24/7 AI Career Assistant Chatbot with live student context",
        ]
        for obj in objectives:
            st.markdown(f"✅ {obj}")

        st.markdown("### ⚠️ Problem Statement")
        st.markdown("""
        B.Tech engineering graduates frequently struggle to bridge the divide between theoretical coursework
        and dynamic industry requirements. Generic career advice fails to diagnose specific competency deficits.
        SkillMatch solves this through data-driven recommendations and explainable skill gap roadmaps.
        """)

    with col2:
        st.markdown("### 💡 Implemented Modules")
        features = [
            ("📝", "Student Registration & Auth", "Validation, profile storage, and login via SQLite"),
            ("📊", "Interactive Skill Assessment", "MCQ diagnostic test + competency matrix with direct profile sync"),
            ("👤", "Learner Profile Dashboard", "Interactive Plotly radar, horizontal bars, and distribution pies"),
            ("🤖", "ML Recommendation Engine", "Cosine similarity scoring with explainable rationale"),
            ("📉", "Skill Gap Diagnosis", "Deficit categorization: competent, low-proficiency, missing"),
            ("⚖️", "Multi-Career Comparison", "Side-by-side evaluation of up to 4 roles"),
            ("🗺️", "3-Tier Learning Pathway", "Beginner, Intermediate, and Advanced curricula with verified resources"),
            ("✅", "Progress Tracking", "Real-time checkbox topic completion stored in SQLite"),
            ("📄", "Downloadable PDF Report", "Official multi-page student dossier via ReportLab"),
            ("💬", "AI Career Assistant Chatbot", "Personalized real-time AI guidance with live database context"),
        ]
        for icon, title, desc in features:
            st.markdown(f"""
            <div class="glass-card" style="padding:0.6rem 0.9rem; margin-bottom:0.4rem; border-left:3px solid #00D4FF;">
                <span style="font-size:1.1rem;">{icon}</span>
                <strong style="color:white;"> {title}</strong>
                <p style="color:#7B8FA3; margin:0; font-size:0.82rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

# ── Tab 2: Algorithm ──────────────────────────────────────────────
with tab2:
    st.markdown("### 🧮 Recommendation Algorithm: TF-IDF + Cosine Similarity")
    st.markdown("""
    SkillMatch implements a transparent, reproducible, and explainable Machine Learning pipeline
    built upon **Scikit-learn's TF-IDF Vectorization** and **Cosine Similarity Metric**.
    """)

    steps = [
        ("1", "Occupational Corpus Preparation",
         "Standardized skill sets for each O*NET occupation are preprocessed, deduplicated, and converted into skill documents."),
        ("2", "TF-IDF Vector Space Construction",
         "The TfidfVectorizer computes term frequencies and inverse document frequencies across all careers. "
         "Ubiquitous skills receive balanced weighting, while specialized technical skills receive elevated importance."),
        ("3", "Student Competency Encoding",
         "The student's registered and assessed skills are projected into the identical N-dimensional TF-IDF feature space."),
        ("4", "Cosine Similarity Computation",
         "cos(θ) = (S · C) / (||S|| × ||C||). Measures directional alignment between student vector S and career vector C. Returns scores in [0.0, 1.0]."),
        ("5", "Ranking & Rationale Generation",
         "Careers are sorted descending. Top-N matches are outputted alongside dynamic, transparent explanations detailing matched vs missing skills."),
    ]

    for step_num, title, desc in steps:
        st.markdown(f"""
        <div class="glass-card" style="padding:0.8rem 1.1rem; margin-bottom:0.5rem; display:flex; gap:1rem;">
            <div style="background:linear-gradient(135deg,#00D4FF,#7B2FFF); color:white; border-radius:50%; width:1.8rem; height:1.8rem;
                        display:flex; align-items:center; justify-content:center;
                        font-weight:800; min-width:1.8rem; font-size:0.9rem;">{step_num}</div>
            <div>
                <strong style="color:white; font-size:0.95rem;">{title}</strong>
                <p style="color:#7B8FA3; margin:0.2rem 0 0 0; font-size:0.85rem;">{desc}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Tab 3: Architecture ───────────────────────────────────────────
with tab3:
    st.markdown("### 🏗️ Complete System Architecture")
    st.markdown("""
    ```
    ┌────────────────────────────────────────────────────────────────────────┐
    │                        STREAMLIT PRESENTATION LAYER                     │
    │  app.py (Dashboard) + 13 Pages (Auth, Quiz, Profile, Recs, Gap,        │
    │  Comparison, Roadmap, Tracking, PDF Dossier, AI Assistant, Info...)    │
    └───────────────────────────────────┬────────────────────────────────────┘
                                        │
    ┌───────────────────────────────────▼────────────────────────────────────┐
    │                          BUSINESS LOGIC LAYER                          │
    │  ai_chatbot.py           – Real-time Gemini/OpenAI API + context       │
    │  student_registration.py – Input validation, authentication, CRUD      │
    │  skill_assessment.py     – MCQ grading & real-time profile sync        │
    │  learner_profile.py      – Radar, bar, and proficiency aggregation     │
    │  career_recommendation.py– Recommendation DB persistence               │
    │  skill_gap_analysis.py   – Competent, low-proficiency & missing gaps   │
    │  learning_pathway.py     – 3-tier roadmap generator (Beginner/Int/Adv) │
    │  progress_tracking.py    – Cross-career topic completion accounting    │
    │  report_generator.py     – ReportLab dynamic PDF dossier generator     │
    └──────────────────┬─────────────────────────────────┬───────────────────┘
                       │                                 │
    ┌──────────────────▼────────────┐  ┌─────────────────▼───────────────────┐
    │       ML ENGINE (ml/)         │  │       DATABASE LAYER (database/)    │
    │  data_preprocessing.py        │  │  db_connection.py (WAL + Timeout)   │
    │  feature_engineering.py       │  │  db_setup.py (Relational Schema)    │
    │  recommendation_model.py      │  │  skillmatch.db (SQLite with 6 tables│
    │  model_evaluation.py          │  │  students, student_skills,          │
    │                               │  │  assessments, recs, pathways, prog) │
    └──────────────────┬────────────┘  └─────────────────────────────────────┘
                       │
    ┌──────────────────▼─────────────────────────────────────────────────────┐
    │                          DATA LAYER (data/)                            │
    │  raw/        – Source O*NET occupational tables                        │
    │  processed/  – cleaned_career_skills.csv (53 curated career profiles)  │
    │  sample/     – sample_student_data.csv (demonstration accounts)        │
    └────────────────────────────────────────────────────────────────────────┘
    ```
    """)

# ── Tab 4: Tech Stack ─────────────────────────────────────────────
with tab4:
    st.markdown("### 📦 Technology Stack & Libraries")
    tech_items = [
        ("🐍", "Python 3.9+", "Core runtime environment and business logic"),
        ("🌐", "Streamlit 1.57+", "Reactive web frontend with session state & dialogs"),
        ("🤖", "Google Gemini / OpenAI", "AI Career Assistant API integration"),
        ("🐼", "Pandas & NumPy", "Vectorized dataset manipulation and feature arrays"),
        ("🤖", "Scikit-learn", "TF-IDF vectorization and Cosine Similarity computation"),
        ("📊", "Plotly Express & Graph Objects", "Interactive radar charts, grouped bars, and donuts"),
        ("🗄️", "SQLite", "Persistent relational database with foreign keys and WAL mode"),
        ("📄", "ReportLab", "Programmatic PDF dossier rendering"),
        ("🌐", "O*NET Database", "U.S. Department of Labor occupational skills dataset"),
    ]
    for icon, name, desc in tech_items:
        c1, c2 = st.columns([1, 4])
        with c1:
            st.markdown(f"<div style='text-align:center; font-size:1.8rem;'>{icon}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**{name}** – {desc}")

    neon_divider()
    st.markdown("""
    <div style="text-align:center; color:#7B8FA3; padding:0.5rem;">
        <p>🎯 SkillMatch | B.Tech Academic Project Ready for Demonstration</p>
    </div>
    """, unsafe_allow_html=True)
