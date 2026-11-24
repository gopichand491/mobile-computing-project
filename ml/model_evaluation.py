"""
SkillMatch – Model Evaluation Module
Provides metrics and diagnostics for the recommendation engine.
"""

import numpy as np
import pandas as pd
from typing import List, Dict


def precision_at_k(recommended: List[str], relevant: List[str], k: int = 5) -> float:
    """Precision@K: fraction of top-K recommendations that are relevant."""
    top_k = recommended[:k]
    hits = sum(1 for r in top_k if r in relevant)
    return hits / k if k > 0 else 0.0


def coverage(recommended_careers: List[List[str]], all_careers: List[str]) -> float:
    """Catalog coverage: fraction of careers ever recommended."""
    unique_recommended = set(c for recs in recommended_careers for c in recs)
    return len(unique_recommended) / len(all_careers) if all_careers else 0.0


def diversity_score(recommendations: List[Dict]) -> float:
    """
    Simple diversity: ratio of unique categories among recommendations.
    Score of 1.0 means every recommendation is from a different category.
    """
    categories = [r.get("category", "Unknown") for r in recommendations]
    if not categories:
        return 0.0
    return len(set(categories)) / len(categories)


def evaluate_recommendations(recommendations: List[Dict]) -> Dict:
    """
    Compute a summary evaluation report for a set of recommendations.
    """
    if not recommendations:
        return {}

    scores = [r["match_score"] for r in recommendations]
    return {
        "num_recommendations": len(recommendations),
        "avg_match_score": round(np.mean(scores), 4),
        "max_match_score": round(np.max(scores), 4),
        "min_match_score": round(np.min(scores), 4),
        "diversity": round(diversity_score(recommendations), 4),
        "avg_missing_skills": round(
            np.mean([len(r["missing_skills"]) for r in recommendations]), 2
        ),
        "avg_matching_skills": round(
            np.mean([len(r["matching_skills"]) for r in recommendations]), 2
        ),
    }
