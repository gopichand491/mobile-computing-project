"""
Tests – Data preprocessing
"""

import os
import sys
import pytest
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ml.data_preprocessing import (
    get_sample_dataframe,
    normalize_skill,
    load_or_create_processed_data,
    SAMPLE_CAREERS,
)
from ml.feature_engineering import SkillFeatureEncoder


def test_sample_dataframe_not_empty():
    df = get_sample_dataframe()
    assert len(df) > 0
    assert len(df) >= 50  # We have 60+ sample careers


def test_sample_dataframe_columns():
    df = get_sample_dataframe()
    required_cols = {"career_title", "onet_code", "category", "description", "skills_list", "skills_text"}
    assert required_cols.issubset(set(df.columns))


def test_no_missing_career_titles():
    df = get_sample_dataframe()
    assert df["career_title"].isna().sum() == 0


def test_no_missing_skills():
    df = get_sample_dataframe()
    assert df["skills_list"].isna().sum() == 0


def test_skills_text_is_lowercase():
    df = get_sample_dataframe()
    for text in df["skills_text"].head(10):
        assert text == text.lower(), f"skills_text not lowercase: {text}"


def test_normalize_skill():
    assert normalize_skill("  Python  ") == "python"
    assert normalize_skill("Machine Learning") == "machine learning"
    assert normalize_skill("SQL") == "sql"


def test_load_or_create_processed_data():
    df, source = load_or_create_processed_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert source in ("processed", "sample", "onet")


def test_feature_encoder_fit():
    df = get_sample_dataframe()
    encoder = SkillFeatureEncoder()
    encoder.fit_careers(df)
    assert encoder.is_fitted
    assert len(encoder.career_titles) == len(df)


def test_feature_encoder_transform():
    df = get_sample_dataframe()
    encoder = SkillFeatureEncoder()
    encoder.fit_careers(df)
    vec = encoder.encode_student(["Python", "SQL", "Machine Learning"])
    assert vec.shape[0] == 1
    assert vec.shape[1] > 0


def test_all_sample_careers_have_onet_code():
    for career in SAMPLE_CAREERS:
        assert "onet_code" in career, f"Missing onet_code in {career['career_title']}"
        assert career["onet_code"]  # Not empty


def test_duplicate_career_titles():
    df = get_sample_dataframe()
    # Career titles should be unique
    duplicates = df[df.duplicated(subset=["career_title"], keep=False)]
    assert len(duplicates) == 0, f"Duplicate career titles: {duplicates['career_title'].tolist()}"
