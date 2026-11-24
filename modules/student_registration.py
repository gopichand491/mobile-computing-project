"""
SkillMatch – Student Registration Module
Handles validation, database operations for student profiles, authentication, and skills.
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from database.db_connection import execute_query, execute_many


def validate_student_input(
    name: str,
    email: str,
    department: str,
    education_level: str,
    year_of_study: str,
) -> Tuple[bool, str]:
    """Validate student registration inputs. Returns (is_valid, error_message)."""
    if not name or len(name.strip()) < 2:
        return False, "Full Name must be at least 2 characters long."
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email.strip()):
        return False, "Please enter a valid email address (e.g., student@college.edu)."
    if not department or department.strip() == "":
        return False, "Please select or enter your Department."
    if not education_level or education_level.strip() == "":
        return False, "Please select your Education Level."
    if not year_of_study or year_of_study.strip() == "":
        return False, "Please select your Year of Study."
    return True, ""


# ── Student CRUD ────────────────────────────────────────────────────────────

def create_student(
    name: str,
    email: str,
    education_level: str,
    degree: str,
    department: str,
    year_of_study: str,
    interests: str,
) -> int:
    """
    Insert a new student or update an existing one by email.
    Returns the student ID.
    """
    clean_email = email.strip().lower()
    clean_name = name.strip()

    existing = get_student_by_email(clean_email)
    if existing:
        update_student(
            existing["id"],
            name=clean_name,
            education_level=education_level,
            degree=degree.strip(),
            department=department,
            year_of_study=year_of_study,
            interests=interests.strip(),
        )
        return existing["id"]

    sql = """
        INSERT INTO students
            (name, email, education_level, degree, department, year_of_study, interests)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    student_id = execute_query(
        sql,
        (clean_name, clean_email, education_level, degree.strip(), department, year_of_study, interests.strip()),
    )
    return student_id


def get_all_students() -> List[Dict]:
    """Return all students as list of dicts."""
    rows = execute_query("SELECT * FROM students ORDER BY created_at DESC", fetch="all")
    if not rows:
        return []
    return [dict(r) for r in rows]


def get_student_by_id(student_id: int) -> Optional[Dict]:
    """Return a single student by ID."""
    row = execute_query(
        "SELECT * FROM students WHERE id = ?", (student_id,), fetch="one"
    )
    return dict(row) if row else None


def get_student_by_email(email: str) -> Optional[Dict]:
    """Return a single student by email (case-insensitive)."""
    clean_email = email.strip().lower()
    row = execute_query(
        "SELECT * FROM students WHERE LOWER(email) = ?", (clean_email,), fetch="one"
    )
    return dict(row) if row else None


def login_student(email: str) -> Optional[Dict]:
    """Authenticate/retrieve student by email for login."""
    return get_student_by_email(email)


def update_student(student_id: int, **kwargs):
    """Update student fields dynamically."""
    allowed = {"name", "email", "education_level", "degree", "department", "year_of_study", "interests"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [student_id]
    execute_query(f"UPDATE students SET {set_clause} WHERE id = ?", tuple(values))


# ── Student Skills CRUD ──────────────────────────────────────────────────────

def save_student_skills(student_id: int, skills: List[Dict]):
    """
    Upsert student skills.
    skills: list of {'skill_name': str, 'skill_type': str, 'proficiency': int}
    """
    if not skills:
        return
    # Ensure proficiency is integer between 1 and 5
    cleaned_data = []
    for s in skills:
        sname = (s.get("skill_name") or s.get("name") or "").strip()
        if not sname:
            continue
        prof = int(s.get("proficiency", 3))
        prof = max(1, min(5, prof))
        stype = s.get("skill_type") or s.get("type") or "technical"
        if stype not in ("technical", "soft"):
            stype = "technical"
        cleaned_data.append((student_id, sname, stype, prof))

    sql = """
        INSERT OR REPLACE INTO student_skills (student_id, skill_name, skill_type, proficiency)
        VALUES (?, ?, ?, ?)
    """
    execute_many(sql, cleaned_data)


def get_student_skills(student_id: int) -> List[Dict]:
    """Return all skills for a student."""
    rows = execute_query(
        "SELECT * FROM student_skills WHERE student_id = ? ORDER BY skill_type, proficiency DESC",
        (student_id,),
        fetch="all",
    )
    return [dict(r) for r in rows] if rows else []


def delete_student_skills(student_id: int):
    """Remove all skills for a student."""
    execute_query("DELETE FROM student_skills WHERE student_id = ?", (student_id,))
