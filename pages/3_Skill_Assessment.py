"""
Page 3 – Skill Assessment
Provides interactive multiple-choice quiz questions and competency sliders
covering Python, Java, SQL, Machine Learning, Communication, Problem Solving, etc.
Automatically computes scores and immediately updates the student's skill profile in SQLite.
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

from modules.skill_assessment import (
    QUIZ_QUESTIONS, ASSESSMENT_DOMAINS,
    calculate_quiz_scores, save_assessment, get_assessment, get_proficiency_label
)

st.markdown("# 📊 Interactive Skill Assessment")
st.markdown("Evaluate your technical and soft skills through structured quiz questions and domain assessments.")
st.markdown("---")

# Auth check
if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student_name = st.session_state.student_name

existing = get_assessment(student_id)

tab_quiz, tab_rating = st.tabs(["🎯 Multiple-Choice Skill Quiz", "🎚️ Comprehensive Domain Rating"])

# ── TAB 1: MCQ QUIZ ───────────────────────────────────────────────────────────
with tab_quiz:
    st.markdown("### 📝 Technical & Soft Skills Multiple-Choice Test")
    st.caption("Answer the diagnostic questions below. Your proficiency will be automatically calculated and synced to your profile.")

    with st.form("mcq_assessment_form"):
        quiz_answers = {}
        for idx, q in enumerate(QUIZ_QUESTIONS, start=1):
            st.markdown(f"**Q{idx}. [{q['skill']}]** {q['question']}")
            choice = st.radio(
                label=f"q_{q['id']}",
                options=q["options"],
                index=0,
                key=f"mcq_{q['id']}",
                label_visibility="collapsed"
            )
            quiz_answers[q["id"]] = choice
            st.markdown("<hr style='border-color:#263340; margin:0.4rem 0 1rem 0;'>", unsafe_allow_html=True)

        quiz_submitted = st.form_submit_button("🚀 Submit & Calculate Skill Scores", use_container_width=True)

    if quiz_submitted:
        calculated_scores, correct_cnt, total_cnt = calculate_quiz_scores(quiz_answers)
        merged_scores = dict(existing)
        merged_scores.update(calculated_scores)

        save_assessment(student_id, merged_scores)
        st.session_state["assessment_scores"] = merged_scores
        st.session_state["recommendations"] = []

        pct_score = round(correct_cnt / total_cnt * 100, 1)
        st.success(f"✅ Quiz Evaluation Complete! You scored **{correct_cnt}/{total_cnt} ({pct_score}%)**. Your skill profile has been updated immediately!")

        with st.expander("🔍 View Question-by-Question Breakdown & Explanations", expanded=True):
            for q in QUIZ_QUESTIONS:
                user_a = quiz_answers.get(q["id"])
                corr_a = q["correct"]
                if user_a == corr_a:
                    st.markdown(f"✅ **{q['skill']}**: Correct! {q['explanation']}")
                else:
                    st.markdown(f"❌ **{q['skill']}**: Selected *{user_a}* | Correct: **{corr_a}** — *{q['explanation']}*")

        st.rerun()

# ── TAB 2: DOMAIN RATINGS ─────────────────────────────────────────────────────
with tab_rating:
    st.markdown("### 🎚️ Self-Assessment Rating Matrix")
    st.caption("Fine-tune your assessed level across key domains. Rating scale: 1 = Novice → 5 = Expert")

    scores = {}
    with st.form("slider_assessment_form"):
        for domain_name, skill_tuples in ASSESSMENT_DOMAINS.items():
            with st.expander(f"📌 {domain_name}", expanded=True):
                cols = st.columns(len(skill_tuples))
                for i, (sk_name, sk_desc, sk_type) in enumerate(skill_tuples):
                    with cols[i]:
                        def_val = int(existing.get(sk_name, 3))
                        sc = st.slider(
                            sk_name,
                            min_value=1,
                            max_value=5,
                            value=def_val,
                            help=sk_desc,
                            key=f"sl_{sk_name}",
                        )
                        scores[sk_name] = sc
                        lbl = get_proficiency_label(sc)
                        c_hex = "#4CAF50" if sc >= 4 else "#2196F3" if sc >= 3 else "#FF9800" if sc >= 2 else "#F44336"
                        st.markdown(
                            f'<p style="color:{c_hex}; font-size:0.75rem; text-align:center; margin:0;">{lbl}</p>',
                            unsafe_allow_html=True,
                        )

        slider_submitted = st.form_submit_button("💾 Save Domain Assessment", use_container_width=True)

    if slider_submitted:
        merged_scores = dict(existing)
        merged_scores.update(scores)
        save_assessment(student_id, merged_scores)
        st.session_state["assessment_scores"] = merged_scores
        st.session_state["recommendations"] = []
        st.success("✅ Assessment saved and synchronized with your student skill profile in SQLite!")
        st.rerun()

# ── CURRENT RADAR CHART ───────────────────────────────────────────────────────
current_scores = get_assessment(student_id)
if current_scores:
    st.markdown("---")
    st.markdown("### 📊 Your Assessed Competency Radar")
    categories = list(current_scores.keys())[:12]
    values = [current_scores[c] for c in categories]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(30,136,229,0.3)",
        line=dict(color="#42A5F5", width=2),
        name="Assessed Level",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], gridcolor="#263340", color="#90CAF9"),
            angularaxis=dict(gridcolor="#263340", color="#90CAF9"),
            bgcolor="#1A2332",
        ),
        paper_bgcolor="#0A1628",
        plot_bgcolor="#0A1628",
        font=dict(color="#FFFFFF"),
        showlegend=False,
        height=450,
        margin=dict(l=40, r=40, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    c_s1, c_s2 = st.columns(2)
    strong_list = [k for k, v in current_scores.items() if v >= 3.5]
    weak_list = [k for k, v in current_scores.items() if v < 2.5]
    with c_s1:
        st.markdown("#### 💪 Key Strengths")
        for s in strong_list[:6]:
            st.markdown(f"✅ **{s}** – Level {current_scores[s]}/5 ({get_proficiency_label(current_scores[s])})")
    with c_s2:
        st.markdown("#### 📚 Growth Opportunities")
        for s in weak_list[:6]:
            st.markdown(f"⚠️ **{s}** – Level {current_scores[s]}/5 ({get_proficiency_label(current_scores[s])})")
