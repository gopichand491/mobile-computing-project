"""
SkillMatch – Progress Tracking Module
Manages learning progress per student per career.
Accurately calculates total topics from learning_pathways combined with topic completions.
"""

from typing import List, Dict
from database.db_connection import execute_query, execute_many
from datetime import datetime


def mark_topic_complete(student_id: int, career_title: str, topic: str, completed: bool):
    """Mark or unmark a topic as completed."""
    completed_at = datetime.now().isoformat() if completed else None
    execute_query(
        """INSERT OR REPLACE INTO learning_progress
               (student_id, career_title, topic, is_completed, completed_at)
           VALUES (?, ?, ?, ?, ?)""",
        (student_id, career_title.strip(), topic.strip(), 1 if completed else 0, completed_at),
    )


def get_progress(student_id: int, career_title: str) -> Dict[str, bool]:
    """Return {topic: is_completed} for a student's career path."""
    rows = execute_query(
        """SELECT topic, is_completed FROM learning_progress
           WHERE student_id = ? AND LOWER(TRIM(career_title)) = LOWER(TRIM(?))""",
        (student_id, career_title.strip()),
        fetch="all",
    )
    if not rows:
        return {}
    return {r["topic"].strip(): bool(r["is_completed"]) for r in rows}


def get_overall_progress(student_id: int) -> List[Dict]:
    """
    Return overall progress stats across all careers.
    Queries learning_pathways joined with learning_progress to give true total topics.
    """
    sql = """
        SELECT
            lp.career_title,
            COUNT(DISTINCT lp.id) as total_topics,
            COUNT(DISTINCT CASE WHEN p.is_completed = 1 THEN lp.id END) as completed_topics
        FROM learning_pathways lp
        LEFT JOIN learning_progress p
            ON lp.student_id = p.student_id
            AND LOWER(TRIM(lp.career_title)) = LOWER(TRIM(p.career_title))
            AND LOWER(TRIM(lp.topic)) = LOWER(TRIM(p.topic))
        WHERE lp.student_id = ?
        GROUP BY lp.career_title
    """
    rows = execute_query(sql, (student_id,), fetch="all")

    # If no pathways recorded yet, fallback to standalone learning_progress records
    if not rows:
        fallback_sql = """
            SELECT career_title,
                   COUNT(DISTINCT topic) as total_topics,
                   COUNT(DISTINCT CASE WHEN is_completed = 1 THEN topic END) as completed_topics
            FROM learning_progress WHERE student_id = ?
            GROUP BY career_title
        """
        rows = execute_query(fallback_sql, (student_id,), fetch="all")

    if not rows:
        return []

    result = []
    for r in rows:
        total = r["total_topics"] or 0
        completed = r["completed_topics"] or 0
        pct = round(completed / total * 100, 1) if total > 0 else 0.0
        result.append({
            "career_title": r["career_title"],
            "total_topics": total,
            "completed_topics": completed,
            "progress_pct": pct,
        })
    return result


def get_completed_topics(student_id: int, career_title: str) -> List[str]:
    """Return list of topic names marked completed for a career."""
    rows = execute_query(
        """SELECT topic FROM learning_progress
           WHERE student_id = ? AND LOWER(TRIM(career_title)) = LOWER(TRIM(?)) AND is_completed = 1""",
        (student_id, career_title.strip()),
        fetch="all",
    )
    return [r["topic"] for r in rows] if rows else []
