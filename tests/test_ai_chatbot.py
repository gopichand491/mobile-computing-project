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


def test_api_credentials_session_state_gemini_key():
    st.session_state["GEMINI_API_KEY"] = "AIzaSyTestKeyFromSessionDirect"
    creds = get_api_credentials()
    assert creds["is_configured"] is True
    assert creds["provider"] == "gemini"
    assert creds["key"] == "AIzaSyTestKeyFromSessionDirect"
    # Reset
    del st.session_state["GEMINI_API_KEY"]


def test_missing_api_key_uses_local_ai(sample_student_id):
    st.session_state["custom_gemini_key"] = ""
    st.session_state["custom_openai_key"] = ""
    if "GEMINI_API_KEY" in st.session_state:
        del st.session_state["GEMINI_API_KEY"]
    if "OPENAI_API_KEY" in st.session_state:
        del st.session_state["OPENAI_API_KEY"]

    import os
    orig_g = os.environ.pop("GEMINI_API_KEY", None)
    orig_o = os.environ.pop("OPENAI_API_KEY", None)
    orig_google = os.environ.pop("GOOGLE_API_KEY", None)

    try:
        # Should NOT raise an error; should return a helpful Built-in Local AI response
        response = generate_ai_response("What careers should I choose?", [], student_id=sample_student_id)
        assert isinstance(response, str)
        assert len(response) > 50
        assert "Career" in response or "SkillMatch" in response or "Recommendation" in response
    finally:
        if orig_g:
            os.environ["GEMINI_API_KEY"] = orig_g
        if orig_o:
            os.environ["OPENAI_API_KEY"] = orig_o
        if orig_google:
            os.environ["GOOGLE_API_KEY"] = orig_google


def test_generate_local_ai_response_intents(sample_student_id):
    from modules.ai_chatbot import generate_local_ai_response

    # 1. Career recommendation query
    resp_career = generate_local_ai_response("What are the best career paths for me?", sample_student_id)
    assert isinstance(resp_career, str)
    assert len(resp_career) > 40

    # 2. Skill gap query
    resp_gap = generate_local_ai_response("What are my skill gaps for Data Scientist?", sample_student_id)
    assert isinstance(resp_gap, str)
    assert "Skill" in resp_gap or "Gap" in resp_gap or "Match" in resp_gap

    # 3. Roadmap query
    resp_roadmap = generate_local_ai_response("Give me a 3-month roadmap to learn Python and Machine Learning", sample_student_id)
    assert isinstance(resp_roadmap, str)
    assert "Roadmap" in resp_roadmap or "Month" in resp_roadmap or "Phase" in resp_roadmap

    # 4. Interview prep query
    resp_interview = generate_local_ai_response("What are common interview questions for software engineers?", sample_student_id)
    assert isinstance(resp_interview, str)
    assert "Interview" in resp_interview or "Questions" in resp_interview

    # 5. ML query
    resp_ml = generate_local_ai_response("How do I build a machine learning model pipeline?", sample_student_id)
    assert isinstance(resp_ml, str)
    assert "Machine Learning" in resp_ml or "Pipeline" in resp_ml or "Scikit" in resp_ml

    # 6. Portfolio Project query
    resp_proj = generate_local_ai_response("What portfolio projects should I build for my resume?", sample_student_id)
    assert isinstance(resp_proj, str)
    assert "Project" in resp_proj or "Portfolio" in resp_proj


def test_is_plausible_gemini_key():
    from modules.ai_chatbot import is_plausible_gemini_key

    assert is_plausible_gemini_key(None) is False
    assert is_plausible_gemini_key("") is False
    assert is_plausible_gemini_key("your_api_key_here") is False
    assert is_plausible_gemini_key("None") is False
    assert is_plausible_gemini_key("dummy") is False
    assert is_plausible_gemini_key("AIzaSyD-RealLookingGeminiKey39CharactersLong") is True


def test_invalid_api_key_graceful_fallback(sample_student_id, monkeypatch):
    """
    Simulate Google returning 400 API_KEY_INVALID.
    Verify that generate_ai_response does NOT throw an unhandled exception or display raw error.
    """
    from modules.ai_chatbot import generate_ai_response, GeminiApiKeyInvalidError
    import requests

    class Mock400Response:
        status_code = 400
        text = '{"error": {"code": 400, "message": "API key not valid. Please pass a valid API key.", "status": "INVALID_ARGUMENT"}}'
        def json(self):
            return json.loads(self.text)

    import json
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: Mock400Response())

    # Set dummy valid-looking key in session state
    st.session_state["GEMINI_API_KEY"] = "AIzaSyFakeKeyThatFailsAtGoogle400"
    try:
        reply = generate_ai_response("What are my skill gaps?", [], student_id=sample_student_id)
        assert isinstance(reply, str)
        # Should contain answer from local AI
        assert len(reply) > 100
        # Should NOT contain raw JSON error trace
        assert '{"error": {"code": 400' not in reply
        # Should contain friendly notice
        assert "Notice" in reply or "API" in reply
    finally:
        del st.session_state["GEMINI_API_KEY"]

