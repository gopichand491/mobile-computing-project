"""
tests/test_ai_chatbot.py – Unit tests for AI Career Assistant Chatbot Module
"""

import pytest
import streamlit as st
from modules.ai_chatbot import (
    get_api_credentials,
    build_student_context,
    get_system_prompt,
    generate_ai_response,
    stream_text,
)


def test_api_credentials_unconfigured():
    # Clear any session state keys
    st.session_state["custom_gemini_key"] = ""
    st.session_state["custom_openai_key"] = ""

    creds = get_api_credentials()
    assert isinstance(creds, dict)
    assert "is_configured" in creds
    # When no key is provided in environment or secrets, it should be False or match env
    if not creds["gemini_key"] and not creds["openai_key"]:
        assert creds["is_configured"] is False


def test_api_credentials_session_override():
    st.session_state["custom_gemini_key"] = "AIzaSyTestKey12345678"
    creds = get_api_credentials()
    assert creds["is_configured"] is True
    assert creds["provider"] == "gemini"
    assert creds["key"] == "AIzaSyTestKey12345678"

    # Reset
    st.session_state["custom_gemini_key"] = ""


def test_build_student_context_none():
    ctx = build_student_context(student_id=None)
    assert isinstance(ctx, str)
    assert len(ctx) > 0


from modules.student_registration import create_student

@pytest.fixture
def sample_student_id():
    return create_student(
        name="Test Student AI",
        email="ai_test@skillmatch.edu",
        education_level="B.Tech (Pursuing)",
        degree="B.Tech Computer Science",
        department="Computer Science & Engineering",
        year_of_study="3rd Year",
        interests="AI & ML, Software Development",
    )


def test_build_student_context_with_student(sample_student_id):
    ctx = build_student_context(student_id=sample_student_id)
    assert isinstance(ctx, str)
    assert "CURRENT STUDENT PROFILE" in ctx
    assert "Student Name" in ctx


def test_get_system_prompt(sample_student_id):
    prompt = get_system_prompt(student_id=sample_student_id)
    assert "SkillMatch AI" in prompt
    assert "Personalized Guidance" in prompt


def test_stream_text_generator():
    sample = "Hello student, welcome to SkillMatch AI!"
    chunks = list(stream_text(sample, delay=0.001))
    reconstructed = "".join(chunks)
    assert reconstructed == sample


def test_missing_api_key_raises_error():
    st.session_state["custom_gemini_key"] = ""
    st.session_state["custom_openai_key"] = ""
    # Ensure env doesn't have it
    import os
    orig_g = os.environ.pop("GEMINI_API_KEY", None)
    orig_o = os.environ.pop("OPENAI_API_KEY", None)
    orig_google = os.environ.pop("GOOGLE_API_KEY", None)

    try:
        with pytest.raises(ValueError, match="NO_API_KEY"):
            generate_ai_response("What careers should I choose?", [], student_id=None)
    finally:
        if orig_g:
            os.environ["GEMINI_API_KEY"] = orig_g
        if orig_o:
            os.environ["OPENAI_API_KEY"] = orig_o
        if orig_google:
            os.environ["GOOGLE_API_KEY"] = orig_google
