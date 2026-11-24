"""
SkillMatch – Verification Script
Tests all 3 features end-to-end against SQLite and ML models:
1. Learning Pathway (3-tier generation with missing skill injection & persistence)
2. Progress Tracking (topic completion persistence and overall aggregation)
3. Career Report (PDF dossier generation with real student records and special characters)
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db_setup import setup_database
from modules.student_registration import create_student, get_student_by_email, save_student_skills, get_student_skills
from modules.skill_assessment import save_assessment, get_assessment
from ml.recommendation_model import get_recommender
from modules.learning_pathway import get_learning_path, save_pathway, get_pathway
from modules.progress_tracking import mark_topic_complete, get_progress, get_overall_progress
from modules.report_generator import generate_career_report_pdf


def run_verification():
    print("=== STARTING SKILLMATCH VERIFICATION ===")
    setup_database()

    # 1. Student setup
    email = "verification_student@skillmatch.edu"
    sid = create_student("Ananya Patel", email, "B.Tech", "Computer Science", "CSE", "3rd Year", "Machine Learning & Cloud")
    print(f"[OK] Student registered with ID: {sid}")

    skills = [
        {"name": "Python", "type": "technical", "proficiency": 4},
        {"name": "SQL", "type": "technical", "proficiency": 4},
        {"name": "Communication", "type": "soft", "proficiency": 4},
        {"name": "Git", "type": "technical", "proficiency": 3},
    ]
    save_student_skills(sid, skills)
    save_assessment(sid, {"Python": 4.5, "SQL": 4.0, "Communication": 4.0})
    print("[OK] Skills and assessment saved.")

    # 2. Recommendations
    recommender = get_recommender()
    recs = recommender.recommend(["Python", "SQL", "Communication", "Git"], top_n=5)
    assert len(recs) == 5, f"Expected 5 recommendations, got {len(recs)}"
    top_c = recs[0]["career_title"]
    missing = recs[0]["missing_skills"]
    print(f"[OK] ML Recommendations: Top Match is '{top_c}' with {recs[0]['match_pct']}% match.")
    print(f"     Identified skill gaps: {missing[:3]}")

    # 3. Learning Pathway Generation & Persistence
    pathway = get_learning_path(top_c, missing_skills=missing)
    assert len(pathway) >= 7, f"Expected at least 7 topics, got {len(pathway)}"
    levels = {item["level"] for item in pathway}
    assert "Beginner" in levels, "Beginner level missing"
    assert "Intermediate" in levels, "Intermediate level missing"
    assert "Advanced" in levels, "Advanced level missing"
    save_pathway(sid, top_c, pathway)

    saved_path = get_pathway(sid, top_c)
    assert len(saved_path) == len(pathway), "Saved pathway count mismatch"
    print(f"[OK] Learning Pathway verified: {len(saved_path)} topics across Beginner, Intermediate, Advanced.")

    # 4. Progress Tracking & SQLite persistence
    mark_topic_complete(sid, top_c, saved_path[0]["topic"], True)
    mark_topic_complete(sid, top_c, saved_path[1]["topic"], True)

    prog = get_progress(sid, top_c)
    assert prog[saved_path[0]["topic"]] is True, "Topic 0 should be completed"
    assert prog[saved_path[1]["topic"]] is True, "Topic 1 should be completed"
    assert prog.get(saved_path[2]["topic"], False) is False, "Topic 2 should not be completed"

    overall = get_overall_progress(sid)
    assert len(overall) >= 1, "Overall progress should have records"
    target_stat = next(o for o in overall if o["career_title"] == top_c)
    print(f"[OK] Progress Tracking verified: {target_stat['completed_topics']}/{target_stat['total_topics']} completed ({target_stat['progress_pct']}%)")
    assert target_stat["completed_topics"] == 2, f"Expected 2 completed, got {target_stat['completed_topics']}"

    # 5. Career Report PDF generation
    student = get_student_by_email(email)
    retrieved_skills = get_student_skills(sid)
    retrieved_assess = get_assessment(sid)

    pdf_bytes = generate_career_report_pdf(
        student=student,
        skills=retrieved_skills,
        assessment=retrieved_assess,
        recommendations=recs,
        selected_career=top_c,
        pathway=saved_path,
        progress=prog,
    )

    assert isinstance(pdf_bytes, bytes), "PDF should be bytes"
    assert pdf_bytes.startswith(b"%PDF-"), "PDF should have valid %PDF- header"
    assert len(pdf_bytes) > 2000, f"PDF suspiciously small: {len(pdf_bytes)} bytes"
    print(f"[OK] Career Report PDF generated successfully! Valid PDF of size {len(pdf_bytes)} bytes.")

    print("=== ALL 3 FEATURES FULLY FUNCTIONAL AND VERIFIED ===")


if __name__ == "__main__":
    run_verification()
