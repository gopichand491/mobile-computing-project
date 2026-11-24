"""
SkillMatch – Database Setup Module
Creates all tables on first run. Safe to call multiple times (CREATE IF NOT EXISTS).
"""

from database.db_connection import get_connection


def setup_database(seed_demo: bool = True):
    """Create all required tables if they do not already exist."""
    conn = get_connection()
    cur = conn.cursor()

    # Students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            email           TEXT UNIQUE NOT NULL,
            education_level TEXT,
            degree          TEXT,
            department      TEXT,
            year_of_study   TEXT,
            interests       TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Student skills table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_skills (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            skill_name  TEXT NOT NULL,
            skill_type  TEXT CHECK(skill_type IN ('technical','soft')),
            proficiency INTEGER CHECK(proficiency BETWEEN 1 AND 5),
            UNIQUE(student_id, skill_name)
        )
    """)

    # Skill assessments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS skill_assessments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            skill_name  TEXT NOT NULL,
            score       REAL,
            assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Career recommendations table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS career_recommendations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            career_title    TEXT NOT NULL,
            match_score     REAL,
            onet_code       TEXT,
            generated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Learning pathways table (includes level: Beginner, Intermediate, Advanced)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS learning_pathways (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            career_title    TEXT NOT NULL,
            level           TEXT DEFAULT 'Beginner',
            step_number     INTEGER,
            topic           TEXT,
            description     TEXT,
            resource_url    TEXT
        )
    """)

    # Ensure level column exists in learning_pathways if table was created previously without it
    cur.execute("PRAGMA table_info(learning_pathways)")
    lp_cols = [c[1] for c in cur.fetchall()]
    if "level" not in lp_cols:
        cur.execute("ALTER TABLE learning_pathways ADD COLUMN level TEXT DEFAULT 'Beginner'")

    # Learning progress table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS learning_progress (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            career_title    TEXT NOT NULL,
            topic           TEXT NOT NULL,
            is_completed    INTEGER DEFAULT 0,
            completed_at    TIMESTAMP,
            UNIQUE(student_id, career_title, topic)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database tables created / verified.")

    if seed_demo:
        seed_demo_student()


def seed_demo_student():
    """Seed the demo student profile (Arjun Sharma) if not already present."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM students WHERE LOWER(email) = ?", ("arjun.demo@skillmatch.edu",))
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO students (name, email, education_level, degree, department, year_of_study, interests)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Arjun Sharma",
            "arjun.demo@skillmatch.edu",
            "B.Tech (Pursuing)",
            "B.Tech Computer Science",
            "Computer Science & Engineering",
            "3rd Year",
            "Data Science & Analytics, Machine Learning & AI, Software Development",
        ))
        demo_id = cur.lastrowid
        demo_skills = [
            (demo_id, "Python", "technical", 4),
            (demo_id, "SQL", "technical", 4),
            (demo_id, "Git", "technical", 4),
            (demo_id, "Machine Learning", "technical", 3),
            (demo_id, "Statistics", "technical", 3),
            (demo_id, "Data Visualization", "technical", 3),
            (demo_id, "Communication", "soft", 4),
            (demo_id, "Problem Solving", "soft", 5),
            (demo_id, "Teamwork", "soft", 4),
        ]
        cur.executemany("""
            INSERT OR REPLACE INTO student_skills (student_id, skill_name, skill_type, proficiency)
            VALUES (?, ?, ?, ?)
        """, demo_skills)
        demo_assessments = [
            (demo_id, "Python", 4.5),
            (demo_id, "SQL", 4.0),
            (demo_id, "Machine Learning", 3.5),
            (demo_id, "Communication", 4.0),
            (demo_id, "Problem Solving", 4.5),
        ]
        cur.executemany("""
            INSERT OR REPLACE INTO skill_assessments (student_id, skill_name, score)
            VALUES (?, ?, ?)
        """, demo_assessments)
        conn.commit()
        print("[DB] Demo student 'Arjun Sharma' seeded successfully.")
    conn.close()


if __name__ == "__main__":
    setup_database()
