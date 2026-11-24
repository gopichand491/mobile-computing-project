"""
Page 2 – Student Registration & Authentication
Validates student details, registers student in SQLite, and provides secure profile login.
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
    with open(css_path, "r", encoding="utf-8", errors="replace") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from assets.premium_ui import inject_premium_ui, premium_header, neon_divider, glass_card
inject_premium_ui("registration")

from modules.student_registration import (
    create_student, get_student_by_email, save_student_skills,
    get_all_students, get_student_by_id, get_student_skills,
    delete_student_skills, validate_student_input, login_student,
)

premium_header("Student Registration & Login",
               "Register your academic profile, log in, and manage your competencies.", "📝")
neon_divider()

tab1, tab2, tab3 = st.tabs(["🆕 New Registration", "🔑 Student Login", "🚀 1-Click Demo"])

# ── TAB 1: New Registration ───────────────────────────────────────
with tab1:
    with st.form("registration_form"):
        st.markdown("### 👤 Personal & Academic Details")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *", placeholder="e.g. Arjun Sharma")
            email = st.text_input("Email Address *", placeholder="arjun@college.edu")
            education_level = st.selectbox(
                "Education Level *",
                ["B.Tech (Pursuing)", "B.Tech (Completed)", "M.Tech (Pursuing)",
                 "M.Tech (Completed)", "BCA", "MCA", "B.Sc", "M.Sc", "Diploma", "Other"],
            )
        with c2:
            degree = st.text_input("Degree / Major", placeholder="e.g. B.Tech Computer Science")
            department = st.selectbox(
                "Department *",
                ["Computer Science & Engineering", "Information Technology",
                 "Electronics & Communication", "Electrical Engineering",
                 "Mechanical Engineering", "Civil Engineering",
                 "Data Science", "Artificial Intelligence & ML",
                 "Biotechnology", "Chemical Engineering", "Other"],
            )
            year_of_study = st.selectbox("Year of Study *", ["1st Year", "2nd Year", "3rd Year", "4th Year", "Graduated"])

        st.markdown("### 🎯 Areas of Career Interest")
        interest_options = [
            "Software Development", "Data Science & Analytics", "Machine Learning & AI",
            "Web Development", "Mobile App Development", "Cybersecurity",
            "Cloud Computing", "DevOps & Automation", "Database Administration",
            "UI/UX Design", "Networking", "Embedded Systems & IoT",
            "Business Analysis", "Project Management", "Research & Academia",
        ]
        interests = st.multiselect("Select your career interests (up to 5):", interest_options)

        st.markdown("### 🛠️ Initial Technical Skills")
        st.caption("Enter skills you currently know (one per line, format: SkillName, Level 1-5)")
        tech_skills_input = st.text_area(
            "Technical Skills",
            value="Python, 4\nSQL, 3\nGit, 4\nMachine Learning, 3",
            height=120,
        )

        st.markdown("### 🤝 Initial Soft Skills")
        soft_skills_input = st.text_area(
            "Soft Skills",
            value="Communication, 4\nProblem Solving, 5\nTeamwork, 4",
            height=100,
        )

        submitted = st.form_submit_button("✅ Register & Save Profile", use_container_width=True)

    if submitted:
        is_valid, err_msg = validate_student_input(name, email, department, education_level, year_of_study)
        if not is_valid:
            st.error(f"⚠️ Validation Error: {err_msg}")
        elif len(interests) == 0:
            st.warning("⚠️ Please select at least one area of interest.")
        else:
            tech_skills = []
            for line in tech_skills_input.strip().splitlines():
                if line.strip():
                    parts = [p.strip() for p in line.split(",")]
                    sk_name = parts[0]
                    try:
                        prof = max(1, min(5, int(parts[1]))) if len(parts) > 1 else 3
                    except ValueError:
                        prof = 3
                    if sk_name:
                        tech_skills.append({"skill_name": sk_name, "skill_type": "technical", "proficiency": prof})

            soft_skills = []
            for line in soft_skills_input.strip().splitlines():
                if line.strip():
                    parts = [p.strip() for p in line.split(",")]
                    sk_name = parts[0]
                    try:
                        prof = max(1, min(5, int(parts[1]))) if len(parts) > 1 else 3
                    except ValueError:
                        prof = 3
                    if sk_name:
                        soft_skills.append({"skill_name": sk_name, "skill_type": "soft", "proficiency": prof})

            all_skills = tech_skills + soft_skills

            try:
                student_id = create_student(
                    name=name, email=email, education_level=education_level,
                    degree=degree, department=department,
                    year_of_study=year_of_study, interests=", ".join(interests),
                )
                if all_skills:
                    delete_student_skills(student_id)
                    save_student_skills(student_id, all_skills)

                st.session_state.student_id = student_id
                st.session_state.student_name = name.strip()
                st.session_state.recommendations = []

                st.success(f"✅ Registration successful! Welcome, **{name.strip()}**! (ID: #{student_id})")
                st.balloons()
                st.info("Next: Proceed to **Skill Assessment** to complete diagnostic evaluation.")

            except Exception as e:
                st.error(f"Error registering student: {e}")

# ── TAB 2: Login ──────────────────────────────────────────────────
with tab2:
    st.markdown("### 🔑 Log in to Existing Profile")

    login_col1, login_col2 = st.columns(2)
    with login_col1:
        login_email = st.text_input("Enter Registered Email:", placeholder="student@college.edu")
        if st.button("🔓 Log In via Email", use_container_width=True):
            if not login_email.strip():
                st.warning("Please enter your email address.")
            else:
                user = login_student(login_email.strip())
                if user:
                    st.session_state.student_id = user["id"]
                    st.session_state.student_name = user["name"]
                    st.session_state.recommendations = []
                    st.success(f"✅ Welcome back, **{user['name']}**!")
                    st.rerun()
                else:
                    st.error("No account found. Please check spelling or register under Tab 1.")

    with login_col2:
        all_students = get_all_students()
        if all_students:
            student_dict = {f"{s['name']} ({s['email']})": s["id"] for s in all_students}
            chosen_label = st.selectbox("Or select from registered accounts:", list(student_dict.keys()))
            if st.button("🚀 Load Selected Profile", use_container_width=True):
                sid = student_dict[chosen_label]
                user = get_student_by_id(sid)
                st.session_state.student_id = sid
                st.session_state.student_name = user["name"]
                st.session_state.recommendations = []
                st.success(f"✅ Loaded profile for **{user['name']}**!")
                st.rerun()

# ── TAB 3: 1-Click Demo Account ───────────────────────────────────
with tab3:
    st.markdown("### 🎓 Instant Demonstration Account")
    st.caption("Click below to immediately populate a complete sample B.Tech student profile.")

    if st.button("⚡ Initialize & Log In as Demo Student (Arjun Sharma)", use_container_width=True):
        demo_id = create_student(
            name="Arjun Sharma", email="arjun.demo@skillmatch.edu",
            education_level="B.Tech (Pursuing)", degree="B.Tech Computer Science",
            department="Computer Science & Engineering", year_of_study="3rd Year",
            interests="Data Science & Analytics, Machine Learning & AI, Software Development",
        )
        demo_skills = [
            {"skill_name": "Python", "skill_type": "technical", "proficiency": 4},
            {"skill_name": "SQL", "skill_type": "technical", "proficiency": 4},
            {"skill_name": "Git", "skill_type": "technical", "proficiency": 4},
            {"skill_name": "Machine Learning", "skill_type": "technical", "proficiency": 3},
            {"skill_name": "Statistics", "skill_type": "technical", "proficiency": 3},
            {"skill_name": "Data Visualization", "skill_type": "technical", "proficiency": 3},
            {"skill_name": "Communication", "skill_type": "soft", "proficiency": 4},
            {"skill_name": "Problem Solving", "skill_type": "soft", "proficiency": 5},
            {"skill_name": "Teamwork", "skill_type": "soft", "proficiency": 4},
        ]
        delete_student_skills(demo_id)
        save_student_skills(demo_id, demo_skills)

        from modules.skill_assessment import save_assessment
        save_assessment(demo_id, {
            "Python": 4.5, "SQL": 4.0, "Git": 4.0, "Machine Learning": 3.5,
            "Statistics": 3.0, "Data Visualization": 3.5, "Communication": 4.0,
            "Problem Solving": 5.0, "Teamwork": 4.0
        })

        st.session_state.student_id = demo_id
        st.session_state.student_name = "Arjun Sharma"
        st.session_state.recommendations = []
        st.session_state.selected_career = "Data Analyst"

        st.success("🎉 Demo Profile Active! Arjun Sharma (B.Tech CSE, 3rd Year) loaded with pre-configured skills.")
        st.rerun()

# ── Session Footer ────────────────────────────────────────────────
neon_divider()
if st.session_state.student_id:
    st.success(f"✅ **Active Student**: {st.session_state.student_name} (ID: #{st.session_state.student_id})")
else:
    st.warning("⚠️ No student profile active. Please register or select an account above.")
