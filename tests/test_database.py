"""
Tests – Database operations
Run with: python -m pytest tests/ -v
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
from modules.student_registration import (
    create_student, get_student_by_id, get_student_by_email,
    save_student_skills, get_student_skills, validate_student_input, login_student,
)

TEST_DB = os.path.join(tempfile.gettempdir(), "skillmatch_test_db.db")
_orig_db_path = dbc.DB_PATH


@pytest.fixture(autouse=True)
def fresh_db():
    """Create a fresh database for each test and point connection to it."""
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


def test_validation():
    valid, err = validate_student_input("A", "invalid_email", "CSE", "B.Tech", "3rd Year")
    assert not valid
    assert "Full Name" in err

    valid, err = validate_student_input("Arjun Sharma", "invalid_email", "CSE", "B.Tech", "3rd Year")
    assert not valid
    assert "email" in err.lower()

    valid, err = validate_student_input("Arjun Sharma", "arjun@example.com", "", "B.Tech", "3rd Year")
    assert not valid
    assert "department" in err.lower()

    valid, err = validate_student_input("Arjun Sharma", "arjun@example.com", "CSE", "B.Tech", "3rd Year")
    assert valid
    assert err == ""


def test_create_student():
    sid = create_student(
        name="Test User",
        email="test@example.com",
        education_level="B.Tech (Pursuing)",
        degree="B.Tech CS",
        department="Computer Science & Engineering",
        year_of_study="3rd Year",
        interests="Data Science",
    )
    assert isinstance(sid, int)
    assert sid > 0


def test_get_student_by_id():
    sid = create_student("Alice", "alice@test.com", "B.Tech", "CS", "CSE", "4th Year", "AI")
    student = get_student_by_id(sid)
    assert student is not None
    assert student["name"] == "Alice"
    assert student["email"] == "alice@test.com"


def test_get_student_by_email_and_login():
    create_student("Bob", "bob@test.com", "M.Tech", "CS", "CSE", "2nd Year", "DevOps")
    student = get_student_by_email("BOB@TEST.COM")
    assert student is not None
    assert student["name"] == "Bob"

    logged_in = login_student("bob@test.com")
    assert logged_in is not None
    assert logged_in["id"] == student["id"]

    missing = login_student("notfound@test.com")
    assert missing is None


def test_save_and_retrieve_skills():
    sid = create_student("Carol", "carol@test.com", "B.Tech", "IT", "IT", "3rd Year", "Web")
    skills = [
        {"skill_name": "Python", "skill_type": "technical", "proficiency": 4},
        {"skill_name": "Communication", "skill_type": "soft", "proficiency": 3},
    ]
    save_student_skills(sid, skills)
    retrieved = get_student_skills(sid)
    assert len(retrieved) == 2
    names = {s["skill_name"] for s in retrieved}
    assert "Python" in names
    assert "Communication" in names


def test_duplicate_email_handling():
    sid1 = create_student("Dave", "dave@test.com", "B.Tech", "ECE", "ECE", "2nd Year", "IoT")
    # Updating existing student with same email
    sid2 = create_student("Dave Updated", "dave@test.com", "B.Tech", "ECE", "ECE", "3rd Year", "IoT")
    assert sid1 == sid2
    student = get_student_by_id(sid1)
    assert student["name"] == "Dave Updated"
    assert student["year_of_study"] == "3rd Year"
