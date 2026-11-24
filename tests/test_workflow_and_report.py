"""
Tests – End-to-End Workflow, Learning Pathway, Progress Tracking, and PDF Report Generation
"""

import os
import sys
import pytest
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import database.db_connection as dbc
from database.db_setup import setup_database
from modules.student_registration import create_student, save_student_skills, get_student_skills
from modules.skill_assessment import calculate_quiz_scores, save_assessment, get_assessment
from ml.recommendation_model import get_recommender
from modules.learning_pathway import get_learning_path, save_pathway, get_pathway
from modules.progress_tracking import mark_topic_complete, get_progress, get_overall_progress
from modules.report_generator import generate_career_report_pdf

TEST_DB = os.path.join(tempfile.gettempdir(), "skillmatch_workflow_test.db")
_orig_db_path = dbc.DB_PATH


@pytest.fixture(autouse=True)
def fresh_db():
    dbc.DB_PATH = TEST_DB
    for ext in ["", "-wal", "-shm"]:
        f = TEST_DB + ext
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass
    setup_database()
    yield
    for ext in ["", "-wal", "-shm"]:
        f = TEST_DB + ext
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass
    dbc.DB_PATH = _orig_db_path


def test_quiz_grading_and_sync():
    # Test grading
    answers = {
        "py_1": "dict",
        "py_2": "[0, 4]",
        "sql_1": "HAVING",
        "ml_1": "Regression",
        "comm_1": "Focus on business impact, actionable insights, and clear visuals",
    }
    scores, correct, total = calculate_quiz_scores(answers)
    assert correct >= 5
    assert total == 12
    assert "Python" in scores
    assert scores["Python"] >= 4.0

    # Test saving & sync to student_skills
    sid = create_student("Test Student", "student@test.com", "B.Tech", "CSE", "CSE", "3rd Year", "AI")
    save_assessment(sid, scores)

    retrieved_assess = get_assessment(sid)
    assert "Python" in retrieved_assess
    assert retrieved_assess["Python"] == scores["Python"]

    # Verify student_skills was updated immediately
    student_skills = get_student_skills(sid)
    assert len(student_skills) > 0
    names = {s["skill_name"] for s in student_skills}
    assert "Python" in names


def test_pathway_tiers_and_persistence():
    sid = create_student("Pathway User", "path@test.com", "B.Tech", "CSE", "CSE", "4th Year", "Web")
    career = "Data Analyst"
    missing = ["Power BI", "Tableau"]

    # Generate 3-tier pathway
    path = get_learning_path(career, missing_skills=missing)
    assert len(path) >= 8
    levels = {item["level"] for item in path}
    assert "Beginner" in levels
    assert "Intermediate" in levels
    assert "Advanced" in levels

    # Save to SQLite and retrieve
    save_pathway(sid, career, path)
    saved = get_pathway(sid, career)
    assert len(saved) == len(path)
    assert saved[0]["topic"] == path[0]["topic"]
    assert saved[0]["level"] == path[0]["level"]


def test_progress_tracking():
    sid = create_student("Progress User", "prog@test.com", "B.Tech", "ECE", "ECE", "3rd Year", "IoT")
    career = "Software Developer"
    path = get_learning_path(career)
    save_pathway(sid, career, path)

    # Mark first 2 topics complete
    mark_topic_complete(sid, career, path[0]["topic"], True)
    mark_topic_complete(sid, career, path[1]["topic"], True)

    prog = get_progress(sid, career)
    assert prog[path[0]["topic"]] is True
    assert prog[path[1]["topic"]] is True
    assert prog.get(path[2]["topic"], False) is False

    # Check overall stats
    overall = get_overall_progress(sid)
    assert len(overall) == 1
    assert overall[0]["completed_topics"] == 2
    assert overall[0]["total_topics"] == len(path)
    assert overall[0]["progress_pct"] > 0


def test_pdf_report_generation():
    student = {
        "id": 1,
        "name": "Arjun Sharma",
        "email": "arjun@example.com",
        "education_level": "B.Tech (Pursuing)",
        "degree": "B.Tech Computer Science",
        "department": "Computer Science & Engineering",
        "year_of_study": "3rd Year",
        "interests": "Data Science & Analytics",
    }
    skills = [
        {"skill_name": "Python", "skill_type": "technical", "proficiency": 4},
        {"skill_name": "SQL", "skill_type": "technical", "proficiency": 4},
        {"skill_name": "Communication", "skill_type": "soft", "proficiency": 4},
    ]
    assessment = {"Python": 4.5, "SQL": 4.0, "Communication": 4.0}
    recommender = get_recommender()
    recs = recommender.recommend(["Python", "SQL", "Communication"], top_n=3)
    pathway = get_learning_path("Data Analyst")
    progress = {pathway[0]["topic"]: True}

    pdf_bytes = generate_career_report_pdf(
        student=student,
        skills=skills,
        assessment=assessment,
        recommendations=recs,
        selected_career="Data Analyst",
        pathway=pathway,
        progress=progress,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF files start with %PDF-
    assert pdf_bytes.startswith(b"%PDF-")


def test_dynamic_pathway_generation_for_any_career():
    """Verify that any O*NET career (e.g. Biomedical Engineer or Blockchain Developer) gets a full 3-tier roadmap."""
    career = "Biomedical Engineer"
    missing = ["Biomechanics", "Medical Imaging"]
    path = get_learning_path(career, missing_skills=missing)
    assert len(path) >= 6
    levels = [item["level"] for item in path]
    assert "Beginner" in levels
    assert "Intermediate" in levels
    assert "Advanced" in levels
    
    # Verify missing skills were injected into Intermediate tier
    int_topics = [item["topic"] for item in path if item["level"] == "Intermediate"]
    assert any("Biomechanics" in t for t in int_topics)


def test_progress_persistence_across_reconnect():
    """Verify topic completions survive connection resets and restart simulations."""
    sid = create_student("Restart User", "restart@test.com", "B.Tech", "CSE", "CSE", "3rd Year", "Cloud")
    career = "Cloud Architect"
    path = get_learning_path(career)
    save_pathway(sid, career, path)

    # Mark step 1 and 3 as complete
    mark_topic_complete(sid, career, path[0]["topic"], True)
    mark_topic_complete(sid, career, path[2]["topic"], True)

    # Simulate restart by reading progress afresh from database
    prog_after = get_progress(sid, career)
    assert prog_after[path[0]["topic"]] is True
    assert prog_after[path[2]["topic"]] is True
    assert prog_after.get(path[1]["topic"], False) is False

    # Verify overall progress reflects exact counts
    stats = get_overall_progress(sid)
    assert len(stats) == 1
    assert stats[0]["completed_topics"] == 2
    assert stats[0]["total_topics"] == len(path)


def test_pdf_report_with_special_characters():
    """Verify that XML characters in fields (e.g. 'R&D', 'C++ & C#', '<script>') don't break ReportLab."""
    student = {
        "id": 99,
        "name": "Jane Doe & Co.",
        "email": "jane@example.com",
        "education_level": "M.Tech <Honors>",
        "degree": "Computer Science & Engineering",
        "department": "Electronics & Communication",
        "year_of_study": "Final Year",
        "interests": "AI & ML, Big Data & Analytics, R&D",
    }
    skills = [
        {"skill_name": "C++ & C#", "skill_type": "technical", "proficiency": 5},
        {"skill_name": "Problem Solving & Analysis", "skill_type": "soft", "proficiency": 4},
    ]
    assessment = {"C++ & C#": 5.0}
    recs = [{
        "career_title": "Software Developer & Architect",
        "onet_code": "15-1252.00",
        "category": "Technology & IT",
        "match_pct": 95.5,
        "matching_skills": ["C++ & C#"],
        "missing_skills": ["Agile & Scrum"],
        "explanation": "High alignment with C++ & C# competencies <proven>.",
    }]
    pathway = [
        {"step": 1, "level": "Beginner", "topic": "C++ & STL Foundations", "description": "Variables, pointers & memory management.", "url": "https://isocpp.org/"},
        {"step": 2, "level": "Intermediate", "topic": "Targeted Mastery: Agile & Scrum", "description": "Sprints & backlog grooming.", "url": "https://scrum.org/"},
    ]
    progress = {"C++ & STL Foundations": True}

    pdf = generate_career_report_pdf(student, skills, assessment, recs, "Software Developer & Architect", pathway, progress)
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF-")
