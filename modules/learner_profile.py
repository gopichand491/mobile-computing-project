"""
SkillMatch – Learner Profile Module
Builds profile data for visualization.
"""

from typing import List, Dict, Any
from modules.skill_assessment import get_proficiency_label, get_strong_skills, get_weak_skills


def build_profile(student: Dict, skills: List[Dict], assessment: Dict[str, float]) -> Dict[str, Any]:
    """
    Aggregate student data, skills, and assessment into a unified profile dict.
    """
    tech_skills = [s for s in skills if s["skill_type"] == "technical"]
    soft_skills = [s for s in skills if s["skill_type"] == "soft"]

    all_skill_scores = {s["skill_name"]: s["proficiency"] for s in skills}
    # Overlay assessment scores (more granular)
    all_skill_scores.update(assessment)

    strong = get_strong_skills(all_skill_scores)
    weak = get_weak_skills(all_skill_scores)

    return {
        "student": student,
        "technical_skills": tech_skills,
        "soft_skills": soft_skills,
        "assessment_scores": assessment,
        "all_skill_scores": all_skill_scores,
        "strong_skills": strong,
        "weak_skills": weak,
        "skill_count": len(skills),
        "avg_proficiency": (
            round(sum(all_skill_scores.values()) / len(all_skill_scores), 2)
            if all_skill_scores else 0
        ),
    }
