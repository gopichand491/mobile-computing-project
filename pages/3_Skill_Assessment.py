"""
Page 3 – Skill Assessment
Interactive MCQ quiz and competency sliders. Auto-computes scores and syncs to SQLite.
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
inject_premium_ui("assessment")

from modules.skill_assessment import (
    QUIZ_QUESTIONS, ASSESSMENT_DOMAINS,
    calculate_quiz_scores, save_assessment, get_assessment, get_proficiency_label
)

premium_header("Interactive Skill Assessment",
               "Evaluate your technical and soft skills through structured diagnostic tests.", "📊")
neon_divider()

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student_name = st.session_state.student_name

existing = get_assessment(student_id)

tab_quiz, tab_rating = st.tabs(["🎯 Multiple-Choice Skill Quiz", "🎚️ Comprehensive Domain Rating"])

# ── TAB 1: MCQ QUIZ ───────────────────────────────────────────────
with tab_quiz:
    st.markdown("### 📝 Technical & Soft Skills Diagnostic Test")
    st.caption("Answer the diagnostic questions below. Proficiency is auto-calculated and synced.")

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
            st.markdown("<hr style='border-color:rgba(0,212,255,0.1); margin:0.4rem 0 1rem 0;'>", unsafe_allow_html=True)

        quiz_submitted = st.form_submit_button("🚀 Submit & Calculate Skill Scores", use_container_width=True)

    if quiz_submitted:
        calculated_scores, correct_cnt, total_cnt = calculate_quiz_scores(quiz_answers)
        merged_scores = dict(existing)
        merged_scores.update(calculated_scores)

        save_assessment(student_id, merged_scores)
        st.session_state["assessment_scores"] = merged_scores
        st.session_state["recommendations"] = []

        pct_score = round(correct_cnt / total_cnt * 100, 1)
        st.success(f"✅ Quiz Complete! Score: **{correct_cnt}/{total_cnt} ({pct_score}%)**. Profile updated!")

        with st.expander("🔍 View Breakdown & Explanations", expanded=True):
            for q in QUIZ_QUESTIONS:
                user_a = quiz_answers.get(q["id"])
                corr_a = q["correct"]
                if user_a == corr_a:
                    st.markdown(f"✅ **{q['skill']}**: Correct! {q['explanation']}")
                else:
                    st.markdown(f"❌ **{q['skill']}**: Selected *{user_a}* | Correct: **{corr_a}** — *{q['explanation']}*")

        st.rerun()

# ── TAB 2: DOMAIN RATINGS ─────────────────────────────────────────
with tab_rating:
    st.markdown("### 🎚️ Self-Assessment Rating Matrix")
    st.caption("Fine-tune your level across key domains. 1 = Novice → 5 = Expert")

    scores = {}
    with st.form("slider_assessment_form"):
        for domain_name, skill_tuples in ASSESSMENT_DOMAINS.items():
            with st.expander(f"📌 {domain_name}", expanded=True):
                cols = st.columns(len(skill_tuples))
                for i, (sk_name, sk_desc, sk_type) in enumerate(skill_tuples):
                    with cols[i]:
                        def_val = int(existing.get(sk_name, 3))
                        sc = st.slider(
                            sk_name, min_value=1, max_value=5, value=def_val,
                            help=sk_desc, key=f"sl_{sk_name}",
                        )
                        scores[sk_name] = sc
                        lbl = get_proficiency_label(sc)
                        c_hex = "#00F5D4" if sc >= 4 else "#00D4FF" if sc >= 3 else "#FFD700" if sc >= 2 else "#FF006E"
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
        st.success("✅ Assessment saved and synced with your skill profile!")
        st.rerun()

# ── CURRENT RADAR CHART ───────────────────────────────────────────
current_scores = get_assessment(student_id)
if current_scores:
    neon_divider()
    st.markdown("### 📊 Your Assessed Competency Radar")
    categories = list(current_scores.keys())[:12]
    values = [current_scores[c] for c in categories]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(0,212,255,0.15)",
        line=dict(color="#00D4FF", width=2),
        name="Assessed Level",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], gridcolor="rgba(255,255,255,0.06)", color="#7B8FA3"),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#7B8FA3"),
            bgcolor="rgba(10,22,40,0.3)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#B0C4DE"),
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
