"""
SkillMatch – Feature Engineering Module
Encodes student skills and career skill lists into TF-IDF vectors.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Tuple


class SkillFeatureEncoder:
    """
    Encodes career skill documents and student skill lists into a shared
    TF-IDF vector space for cosine similarity computation.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            tokenizer=lambda x: [t.strip() for t in x.split(",")],
            preprocessor=lambda x: x.lower(),
            token_pattern=None,
            ngram_range=(1, 2),
            min_df=1,
        )
        self.career_matrix = None
        self.career_titles = []
        self.is_fitted = False

    def fit_careers(self, df: pd.DataFrame):
        """
        Fit the vectorizer on all career skill documents.
        df must have 'career_title' and 'skills_list' columns.
        """
        self.career_titles = df["career_title"].tolist()
        # Use comma-separated skills_list (not skills_text) so tokenizer works
        docs = df["skills_list"].fillna("").tolist()
        self.career_matrix = self.vectorizer.fit_transform(docs)
        self.is_fitted = True

    def encode_student(self, student_skills: List[str]) -> np.ndarray:
        """
        Transform a list of student skill strings into the fitted TF-IDF space.
        """
        if not self.is_fitted:
            raise RuntimeError("Call fit_careers() before encode_student().")
        doc = ",".join(student_skills)
        return self.vectorizer.transform([doc])

    def get_feature_names(self) -> List[str]:
        return self.vectorizer.get_feature_names_out().tolist()
