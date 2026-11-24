"""
Page 8 – Personalized Learning Pathway
Generates and displays structured multi-level learning roadmaps (Beginner, Intermediate, Advanced)
with topic checklists and real-time SQLite progress tracking.
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
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from modules.student_registration import get_student_by_id, get_student_skills
from modules.learning_pathway import get_learning_path, save_pathway, get_pathway
from modules.progress_tracking import get_progress, mark_topic_complete
from ml.recommendation_model import get_recommender
from ml.data_preprocessing import load_or_create_processed_data

st.markdown("# 🗺️ Personalized Learning Pathway")
st.markdown("Your structured, multi-tier curriculum designed to bridge skill gaps.")
st.markdown("---")

if not st.session_state.get("student_id"):
    st.warning("⚠️ Please register or log in first (Registration page).")
    st.stop()

student_id = st.session_state.student_id
student_info = get_student_by_id(student_id)
student_skills_data = get_student_skills(student_id)
student_skills = [s["skill_name"] for s in student_skills_data]

# Retrieve or calculate recommendations dynamically
recs = st.session_state.get("recommendations", [])
if not recs and student_skills:
    try:
        recommender = get_recommender()
        recs = recommender.recommend(
            student_skills,
            top_n=5,
            student_interests=student_info.get("interests") if student_info else "",
        )
        st.session_state["recommendations"] = recs
    except Exception:
        recs = []

# Load all available career titles from dataset
career_df, _ = load_or_create_processed_data()
all_careers = sorted(career_df["career_title"].unique().tolist()) if career_df is not None else []

# Order dropdown: recommended careers first, then all remaining careers
rec_titles = [r["career_title"] for r in recs]
remaining = [c for c in all_careers if c not in rec_titles]
career_options = rec_titles + remaining if rec_titles else (all_careers or ["Data Analyst", "Software Developer", "Data Scientist"])

# Career selector
default_career = st.session_state.get("selected_career", rec_titles[0] if rec_titles else career_options[0])
if default_career not in career_options:
    default_career = career_options[0]

career_title = st.selectbox(
    "🎯 Select Target Career Pathway:",
    career_options,
    index=career_options.index(default_career),
)
st.session_state["selected_career"] = career_title

# Determine matching and missing skills for this career
matching_skills = []
missing_skills = []
c_desc = ""
c_category = "Technology"

sel = next((r for r in recs if r["career_title"].lower() == career_title.lower()), None)
if sel:
    matching_skills = sel.get("matching_skills", [])
    missing_skills = sel.get("missing_skills", [])
    c_desc = sel.get("description", "")
    c_category = sel.get("category", "Technology")
elif career_df is not None:
    match_row = career_df[career_df["career_title"].str.lower() == career_title.lower()]
    if not match_row.empty:
        c_desc = str(match_row.iloc[0].get("description", ""))
        c_category = str(match_row.iloc[0].get("category", "Technology"))
        req_raw = str(match_row.iloc[0].get("skills_list", ""))
        req_list = [s.strip() for s in req_raw.split(",") if s.strip()]
        st_skills_set = {s.lower() for s in student_skills}
        matching_skills = [s for s in req_list if s.lower() in st_skills_set]
        missing_skills = [s for s in req_list if s.lower() not in st_skills_set]

# ── Career Overview & Gap Analysis Pill Card ──────────────────────────────────
match_pills = " ".join([f"<span style='background:#1B5E20; color:#E8F5E9; padding:2px 8px; border-radius:12px; font-size:0.8rem; margin-right:4px;'>✓ {s}</span>" for s in matching_skills]) or "<span style='color:#90CAF9; font-size:0.82rem;'>No exact matches recorded yet</span>"
gap_pills = " ".join([f"<span style='background:#B71C1C; color:#FFEBEE; padding:2px 8px; border-radius:12px; font-size:0.8rem; margin-right:4px;'>! {s}</span>" for s in missing_skills[:6]]) or "<span style='color:#A5D6A7; font-size:0.82rem;'>All key skills matched!</span>"

st.markdown(f"""
<div style="background:#132238; border:1px solid #1E3A5F; border-radius:10px; padding:1.2rem; margin-bottom:1rem;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3 style="color:#FFFFFF; margin:0;">🎯 {career_title}</h3>
        <span style="background:#1565C0; color:white; padding:3px 10px; border-radius:10px; font-size:0.75rem; font-weight:700;">{c_category}</span>
    </div>
    <p style="color:#BBDEFB; font-size:0.88rem; margin:0.4rem 0 0.8rem 0;">{c_desc}</p>
    <div style="margin-bottom:0.4rem;">
        <span style="color:#81C784; font-size:0.82rem; font-weight:700;">Matched Skills: </span>{match_pills}
    </div>
    <div>
        <span style="color:#EF9A9A; font-size:0.82rem; font-weight:700;">Target Skill Gaps: </span>{gap_pills}
    </div>
</div>
""", unsafe_allow_html=True)

# Action buttons
col_act1, col_act2 = st.columns([2, 1])
with col_act1:
    if st.button("🔄 Generate / Refresh Roadmap for " + career_title, use_container_width=True):
        new_path = get_learning_path(career_title, missing_skills)
        save_pathway(student_id, career_title, new_path)
        st.session_state[f"path_{career_title}"] = new_path
        st.success(f"✅ Generated fresh 3-tier roadmap for **{career_title}**!")
        st.rerun()

# Load saved pathway from DB
path = get_pathway(student_id, career_title)
if not path:
    path = get_learning_path(career_title, missing_skills)
    save_pathway(student_id, career_title, path)

# Load real progress from SQLite
progress = get_progress(student_id, career_title)
completed_count = sum(1 for t in path if progress.get(t.get("topic", "").strip(), False))
total_count = len(path)
pct = (completed_count / total_count) if total_count > 0 else 0.0

# ── Header Banner ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0D47A1,#1565C0); border-radius:12px;
            padding:1.4rem; margin-bottom:1rem; box-shadow:0 4px 12px rgba(0,0,0,0.3);">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h2 style="color:white; margin:0;">📚 3-Tier Curriculum: {career_title}</h2>
            <p style="color:#90CAF9; margin:0.3rem 0 0 0; font-size:0.9rem;">
                Structured Progression: <b>Beginner</b> (Foundations) &rarr; <b>Intermediate</b> (Skill Gaps) &rarr; <b>Advanced</b> (Capstone)
            </p>
        </div>
        <div style="text-align:right;">
            <div style="font-size:2.2rem; font-weight:800; color:#FFFFFF;">{round(pct*100, 1)}%</div>
            <p style="color:#BBDEFB; font-size:0.8rem; margin:0;">{completed_count} of {total_count} Topics Completed</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.progress(pct)
st.markdown("<br>", unsafe_allow_html=True)


def on_toggle_topic(topic_name, c_title, st_id, key_name):
    """Callback triggered whenever a topic checkbox is toggled."""
    is_checked = st.session_state.get(key_name, False)
    mark_topic_complete(st_id, c_title, topic_name, is_checked)


# ── Render by Tier (Beginner, Intermediate, Advanced) ─────────────────────────
tiers = [
    ("🟢 Beginner Level: Foundations & Core Concepts", "Beginner", "#2E7D32"),
    ("🟡 Intermediate Level: Practical Tools, Applied Skills & Skill Gaps", "Intermediate", "#F57F17"),
    ("🔴 Advanced Level: Specialization & Production Capstone", "Advanced", "#C62828"),
]

for tier_title, tier_key, tier_color in tiers:
    tier_items = [item for item in path if item.get("level", "Beginner") == tier_key]
    if not tier_items:
        continue

    st.markdown(f"### {tier_title}")

    for item in tier_items:
        step = item.get("step", item.get("step_number", "?"))
        topic = item.get("topic", "").strip()
        desc = item.get("description", "")
        url = item.get("resource_url", item.get("url", ""))

        is_done = progress.get(topic, False)
        bg = "#16281E" if is_done else "#141D2B"
        border = "#388E3C" if is_done else "#223145"
        status_badge = "✅ COMPLETED" if is_done else "⬜ PENDING"
        status_color = "#81C784" if is_done else "#90CAF9"

        st.markdown(f"""
        <div style="background:{bg}; border:1px solid {border}; border-radius:10px;
                    padding:1rem 1.2rem; margin-bottom:0.6rem;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="display:flex; align-items:center; gap:0.6rem;">
                    <span style="background:{tier_color}; color:white; border-radius:50%;
                                 width:1.6rem; height:1.6rem; display:inline-flex;
                                 align-items:center; justify-content:center;
                                 font-size:0.8rem; font-weight:700;">{step}</span>
                    <span style="color:white; font-weight:600; font-size:1rem;">{topic}</span>
                </div>
                <span style="color:{status_color}; font-size:0.75rem; font-weight:700;">{status_badge}</span>
            </div>
            <p style="color:#BBDEFB; margin:0.3rem 0 0 2.2rem; font-size:0.88rem;">{desc}</p>
            {'<a href="' + url + '" target="_blank" style="color:#64B5F6; font-size:0.8rem; margin-left:2.2rem; text-decoration:none; display:inline-block; margin-top:4px;">🔗 Access Verified Study Resource &rarr;</a>' if url else ''}
        </div>
        """, unsafe_allow_html=True)

        # Interactive Checkbox with instant callback
        checkbox_key = f"chk_path_{career_title}_{step}_{topic}"
        if checkbox_key not in st.session_state:
            st.session_state[checkbox_key] = is_done

        st.checkbox(
            f"Mark Step {step}: '{topic}' as completed",
            key=checkbox_key,
            on_change=on_toggle_topic,
            args=(topic, career_title, student_id, checkbox_key),
        )

    st.markdown("<br>", unsafe_allow_html=True)

# ── Summary & Next Action ──────────────────────────────────────────────────────
if pct == 1.0:
    st.balloons()
    st.success(f"🎉 Outstanding Achievement! You have completed the full learning pathway for **{career_title}**!")
else:
    rem = total_count - completed_count
    st.info(f"Keep going! **{rem}** topics remaining to complete your **{career_title}** roadmap.")
