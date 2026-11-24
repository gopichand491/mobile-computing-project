"""
SkillMatch – Recommendation Model Module
Implements TF-IDF + Cosine Similarity based career recommendation.
Algorithm:
  1. Fit TF-IDF vectorizer on career skill documents.
  2. Transform student skill list into the same vector space.
  3. Compute cosine similarity between student vector and all career vectors.
  4. Rank careers by similarity score.
  5. Compute skill gap: required_skills - student_skills.
  6. Generate explainable recommendation rationale for each career.
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional

from ml.feature_engineering import SkillFeatureEncoder
from ml.data_preprocessing import load_or_create_processed_data


class CareerRecommender:
    """
    Skill-based career recommender using TF-IDF and Cosine Similarity.
    """

    def __init__(self):
        self.encoder = SkillFeatureEncoder()
        self.career_df: Optional[pd.DataFrame] = None
        self.data_source: str = "unknown"

    def load_and_fit(self):
        """Load career data and fit the encoder."""
        df, source = load_or_create_processed_data()
        self.career_df = df.copy()
        self.data_source = source
        self.encoder.fit_careers(df)

    def recommend(
        self,
        student_skills: List[str],
        top_n: int = 5,
        category_filter: Optional[str] = None,
        student_interests: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return top_n career recommendations for a student based on skills and interests.

        Parameters
        ----------
        student_skills   : list of str – the student's skills
        top_n            : int – number of recommendations
        category_filter  : str or None – optional career category filter
        student_interests: str or None – optional interest string to augment matching

        Returns
        -------
        list of dicts with keys:
            career_title, onet_code, category, description,
            match_score, match_pct, required_skills,
            matching_skills, missing_skills, suggested_learning, explanation
        """
        if self.career_df is None:
            self.load_and_fit()

        clean_skills = [s.strip() for s in student_skills if s and s.strip()]
        if not clean_skills:
            clean_skills = ["Communication", "Problem Solving"]

        # Encode student vector
        student_vec = self.encoder.encode_student(clean_skills)
        scores = cosine_similarity(student_vec, self.encoder.career_matrix).flatten()

        df = self.career_df.copy()
        df["_score"] = scores

        # Apply category filter if specified
        if category_filter and category_filter != "All":
            df = df[df["category"] == category_filter]

        df = df.sort_values("_score", ascending=False).head(top_n)

        student_skills_set = {s.strip().lower() for s in clean_skills}
        interests_set = {i.strip().lower() for i in (student_interests or "").split(",") if i.strip()}

        results = []
        for _, row in df.iterrows():
            required = [s.strip() for s in str(row["skills_list"]).split(",") if s.strip()]
            matching = [s for s in required if s.lower() in student_skills_set]
            missing = [s for s in required if s.lower() not in student_skills_set]

            # Dynamic match percentage directly from cosine similarity
            # Scale cosine similarity (typical range 0.0 to 1.0) into percentage
            raw_score = float(row["_score"])
            match_pct = round(min(100.0, raw_score * 100), 1)

            # Generate transparent explanation
            explanation = self._build_explanation(
                career_title=row["career_title"],
                category=row.get("category", ""),
                match_pct=match_pct,
                matching_skills=matching,
                missing_skills=missing,
                interests_set=interests_set,
            )

            results.append({
                "career_title": row["career_title"],
                "onet_code": row.get("onet_code", "N/A"),
                "category": row.get("category", "General"),
                "description": row.get("description", "No description available."),
                "match_score": raw_score,
                "match_pct": match_pct,
                "required_skills": required,
                "matching_skills": matching,
                "missing_skills": missing,
                "suggested_learning": self._suggest_learning(missing[:5]),
                "explanation": explanation,
            })

        return results

    def _build_explanation(
        self,
        career_title: str,
        category: str,
        match_pct: float,
        matching_skills: List[str],
        missing_skills: List[str],
        interests_set: set,
    ) -> str:
        """Construct transparent, explainable reason why this career is recommended."""
        num_matched = len(matching_skills)
        matched_str = ", ".join(matching_skills[:4]) if matching_skills else "general foundational skills"
        
        interest_match = any(i in category.lower() or i in career_title.lower() for i in interests_set)
        interest_note = f" This matches your expressed interest in {category}." if interest_match else ""

        if num_matched >= 4:
            return (
                f"Highly recommended with a {match_pct}% match score.{interest_note} You already possess {num_matched} "
                f"core competencies ({matched_str}). Focus on bridging the remaining {len(missing_skills)} skills to become job-ready."
            )
        elif num_matched >= 2:
            return (
                f"Recommended based on your solid foundation in {matched_str} ({match_pct}% match).{interest_note} "
                f"Developing the key missing skills ({', '.join(missing_skills[:3])}) will significantly boost your qualification."
            )
        else:
            return (
                f"Emerging career match ({match_pct}%). While your profile shares common analytical and problem-solving skills, "
                f"this role requires dedicated learning in {', '.join(missing_skills[:3])}."
            )

    def _suggest_learning(self, missing_skills: List[str]) -> List[str]:
        """Generate tailored learning suggestions for missing skills."""
        suggestions = []
        for skill in missing_skills:
            s = skill.lower()
            if any(k in s for k in ["python", "java", "c++", "javascript", "sql"]):
                suggestions.append(f"Complete a hands-on {skill} programming course with practical projects.")
            elif any(k in s for k in ["machine learning", "deep learning", "ai", "tensorflow"]):
                suggestions.append(f"Study {skill} fundamentals through Stanford CS229 or DeepLearning.AI.")
            elif any(k in s for k in ["communication", "leadership", "teamwork"]):
                suggestions.append(f"Strengthen {skill} through group engineering projects, presentations, and code reviews.")
            elif any(k in s for k in ["excel", "power bi", "tableau"]):
                suggestions.append(f"Learn interactive dashboard building with {skill} using public datasets.")
            elif any(k in s for k in ["docker", "kubernetes", "aws", "cloud"]):
                suggestions.append(f"Set up containerized deployments and earn foundational {skill} cloud certifications.")
            else:
                suggestions.append(f"Acquire structured learning for {skill} through standard coursework.")
        return suggestions

    def get_skill_gap_data(self, recommendations: List[Dict]) -> Dict:
        """
        Aggregate skill gap data for visualization.
        """
        gap_data = {}
        for rec in recommendations:
            gap_data[rec["career_title"]] = {
                "total_required": len(rec["required_skills"]),
                "matching": len(rec["matching_skills"]),
                "missing": len(rec["missing_skills"]),
                "match_pct": rec["match_pct"],
                "missing_skills": rec["missing_skills"],
                "matching_skills": rec["matching_skills"],
            }
        return gap_data

    def get_categories(self) -> List[str]:
        """Return all unique career categories."""
        if self.career_df is None:
            self.load_and_fit()
        return ["All"] + sorted(self.career_df["category"].dropna().unique().tolist())


# Module-level singleton
_recommender = None


def get_recommender() -> CareerRecommender:
    global _recommender
    if _recommender is None:
        _recommender = CareerRecommender()
        _recommender.load_and_fit()
    return _recommender
