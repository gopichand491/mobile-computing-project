"""
Tests – Recommendation engine
"""

import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml.recommendation_model import CareerRecommender
from ml.model_evaluation import evaluate_recommendations, diversity_score


@pytest.fixture
def recommender():
    r = CareerRecommender()
    r.load_and_fit()
    return r


def test_recommender_loads(recommender):
    assert recommender.career_df is not None
    assert len(recommender.career_df) > 0


def test_recommend_returns_results(recommender):
    skills = ["Python", "SQL", "Machine Learning", "Statistics", "Communication"]
    recs = recommender.recommend(skills, top_n=5)
    assert isinstance(recs, list)
    assert len(recs) > 0
    assert len(recs) <= 5


def test_recommendation_has_required_fields(recommender):
    skills = ["JavaScript", "React", "HTML", "CSS", "Node.js"]
    recs = recommender.recommend(skills, top_n=3)
    for rec in recs:
        assert "career_title" in rec
        assert "match_pct" in rec
        assert "matching_skills" in rec
        assert "missing_skills" in rec
        assert "required_skills" in rec
        assert 0 <= rec["match_pct"] <= 100


def test_match_scores_are_sorted(recommender):
    skills = ["Python", "Docker", "Linux", "Kubernetes", "AWS"]
    recs = recommender.recommend(skills, top_n=10)
    scores = [r["match_score"] for r in recs]
    assert scores == sorted(scores, reverse=True)


def test_skill_gap_computation(recommender):
    skills = ["Python", "SQL"]
    recs = recommender.recommend(skills, top_n=1)
    if recs:
        rec = recs[0]
        all_skills = set(s.lower() for s in rec["required_skills"])
        matching = set(s.lower() for s in rec["matching_skills"])
        missing = set(s.lower() for s in rec["missing_skills"])
        assert matching | missing == all_skills


def test_category_filter(recommender):
    skills = ["Python", "SQL", "Machine Learning"]
    recs = recommender.recommend(skills, top_n=5, category_filter="Data Science & Analytics")
    for rec in recs:
        assert rec["category"] == "Data Science & Analytics"


def test_empty_skills(recommender):
    recs = recommender.recommend([], top_n=5)
    # Should return results but with low scores
    assert isinstance(recs, list)


def test_evaluate_recommendations(recommender):
    skills = ["Python", "SQL", "Machine Learning", "Communication"]
    recs = recommender.recommend(skills, top_n=5)
    eval_result = evaluate_recommendations(recs)
    assert "num_recommendations" in eval_result
    assert "avg_match_score" in eval_result
    assert "diversity" in eval_result
    assert 0 <= eval_result["diversity"] <= 1


def test_diversity_score():
    recs = [
        {"category": "Technology & IT"},
        {"category": "Data Science & Analytics"},
        {"category": "Business & Management"},
    ]
    score = diversity_score(recs)
    assert score == 1.0  # All different categories

    recs_same = [{"category": "Technology & IT"}] * 3
    score_same = diversity_score(recs_same)
    assert score_same < 1.0
