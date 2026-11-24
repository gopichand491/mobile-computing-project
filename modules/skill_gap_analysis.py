"""
SkillMatch – Skill Gap Analysis Module
Computes and formats skill gap data for visualization.
"""

from typing import List, Dict
import pandas as pd


def compute_gap(required_skills: List[str], student_skills: List[str]) -> Dict:
    """
    Compute the skill gap between required and student skills.
    Returns dict with matching, missing, and coverage %.
    """
    req_set = {s.strip().lower() for s in required_skills}
    stu_set = {s.strip().lower() for s in student_skills}

    matching = [s for s in required_skills if s.strip().lower() in stu_set]
    missing = [s for s in required_skills if s.strip().lower() not in stu_set]
    extra = [s for s in student_skills if s.strip().lower() not in req_set]

    coverage = len(matching) / len(required_skills) * 100 if required_skills else 0

    return {
        "matching_skills": matching,
        "missing_skills": missing,
        "extra_skills": extra,
        "total_required": len(required_skills),
        "coverage_pct": round(coverage, 1),
    }


def gap_summary_table(recommendations: List[Dict]) -> pd.DataFrame:
    """
    Build a summary DataFrame showing gap info for each recommended career.
    """
    rows = []
    for rec in recommendations:
        rows.append({
            "Career": rec["career_title"],
            "Match %": rec["match_pct"],
            "Matching Skills": len(rec["matching_skills"]),
            "Missing Skills": len(rec["missing_skills"]),
            "Total Required": len(rec["required_skills"]),
        })
    return pd.DataFrame(rows)


def priority_skills(missing_skills_per_career: Dict[str, List[str]]) -> List[str]:
    """
    Rank missing skills by frequency across all recommended careers.
    Skills missing in more careers are higher priority.
    """
    from collections import Counter
    counter = Counter()
    for skills in missing_skills_per_career.values():
        counter.update([s.lower() for s in skills])
    # Return in descending frequency order
    return [skill for skill, _ in counter.most_common()]
