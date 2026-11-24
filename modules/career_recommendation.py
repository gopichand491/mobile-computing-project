"""
SkillMatch – Career Recommendation Module
Bridges database saving/retrieval with the ML model output.
"""

from typing import List, Dict, Any
from database.db_connection import execute_query, execute_many


def save_recommendations(student_id: int, recommendations: List[Dict]):
    """Persist top recommendations to the database."""
    execute_query(
        "DELETE FROM career_recommendations WHERE student_id = ?", (student_id,)
    )
    sql = """
        INSERT INTO career_recommendations (student_id, career_title, match_score, onet_code)
        VALUES (?, ?, ?, ?)
    """
    data = [
        (student_id, r["career_title"], r["match_score"], r.get("onet_code", "N/A"))
        for r in recommendations
    ]
    execute_many(sql, data)


def get_saved_recommendations(student_id: int) -> List[Dict]:
    """Retrieve saved recommendations for a student."""
    rows = execute_query(
        """SELECT career_title, match_score, onet_code, generated_at
           FROM career_recommendations WHERE student_id = ?
           ORDER BY match_score DESC""",
        (student_id,),
        fetch="all",
    )
    return [dict(r) for r in rows] if rows else []


def format_match_badge(match_pct: float) -> str:
    """Return an emoji badge based on match percentage."""
    if match_pct >= 70:
        return "🟢 Excellent"
    elif match_pct >= 50:
        return "🟡 Good"
    elif match_pct >= 30:
        return "🟠 Fair"
    else:
        return "🔴 Low"
