"""
modules/ai_chatbot.py – AI Career Assistant Chatbot Engine
Supports Google Gemini API & OpenAI API with secure Streamlit Secrets management.
Builds personalized context based on live student data from SQLite.
"""

import os
import json
import time
import requests
import streamlit as st
from typing import Dict, List, Any, Optional, Generator

# ── API Key Management ────────────────────────────────────────────────────────

def get_api_credentials() -> Dict[str, Optional[str]]:
    """
    Retrieve AI API key securely from:
    1. st.secrets (Streamlit Community Cloud & local .streamlit/secrets.toml)
    2. Environment variables
    3. Session state (for temporary user testing in UI)
    """
    gemini_key = None
    openai_key = None

    # Check Streamlit secrets
    try:
        if hasattr(st, "secrets"):
            gemini_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
            openai_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass

    # Check environment variables
    if not gemini_key:
        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not openai_key:
        openai_key = os.environ.get("OPENAI_API_KEY")

    # Check session state override
    if not gemini_key and st.session_state.get("custom_gemini_key"):
        gemini_key = st.session_state.get("custom_gemini_key").strip()
    if not openai_key and st.session_state.get("custom_openai_key"):
        openai_key = st.session_state.get("custom_openai_key").strip()

    provider = None
    active_key = None

    if gemini_key:
        provider = "gemini"
        active_key = gemini_key
    elif openai_key:
        provider = "openai"
        active_key = openai_key

    return {
        "provider": provider,
        "key": active_key,
        "gemini_key": gemini_key,
        "openai_key": openai_key,
        "is_configured": active_key is not None and len(active_key) > 5,
    }


# ── Student Context Builder ───────────────────────────────────────────────────

def build_student_context(student_id: Optional[int] = None) -> str:
    """
    Fetch comprehensive student context from SQLite to give personalized AI responses.
    """
    if not student_id:
        student_id = st.session_state.get("student_id")

    if not student_id:
        return (
            "No specific student profile is currently logged in. "
            "You are speaking with a prospective student or visitor exploring engineering careers."
        )

    from modules.student_registration import get_student_by_id, get_student_skills
    from modules.skill_assessment import get_assessment
    from database.db_connection import execute_query

    student = get_student_by_id(student_id)
    if not student:
        return "Student profile could not be retrieved from the database."

    skills = get_student_skills(student_id)
    assessment = get_assessment(student_id)

    # Format skills
    tech_skills = [f"{s['skill_name']} (Lvl {s.get('proficiency', 3)}/5)" for s in skills if s.get('skill_type') == 'technical']
    soft_skills = [f"{s['skill_name']} (Lvl {s.get('proficiency', 3)}/5)" for s in skills if s.get('skill_type') == 'soft']

    # Assessed skills
    assessed = [f"{k}: {v}/5" for k, v in assessment.items()]

    # Recommendations
    recs_res = execute_query(
        "SELECT career_title, match_score FROM career_recommendations WHERE student_id = ? ORDER BY match_score DESC LIMIT 5",
        (student_id,), fetch="all"
    )
    recs = [f"{r['career_title']} ({round(r['match_score']*100, 1)}% match)" for r in recs_res] if recs_res else []

    # Selected target career & progress
    target_career = st.session_state.get("selected_career", "Not selected yet")

    prog_res = execute_query(
        "SELECT COUNT(*) as tot, SUM(is_completed) as comp FROM learning_progress WHERE student_id = ?",
        (student_id,), fetch="one"
    )
    progress_str = "0 topics completed"
    if prog_res and prog_res["tot"] and prog_res["tot"] > 0:
        comp_val = prog_res["comp"] or 0
        progress_str = f"{comp_val} of {prog_res['tot']} topics completed ({round(comp_val/prog_res['tot']*100, 1)}%)"

    context = f"""
--- CURRENT STUDENT PROFILE (CONFIDENTIAL CONTEXT) ---
• Student Name: {student.get('name', 'Student')}
• Education Level: {student.get('education_level', 'B.Tech')}
• Degree / Branch: {student.get('degree', 'Computer Science')}
• Department: {student.get('department', 'Engineering')}
• Year of Study: {student.get('year_of_study', '3rd Year')}
• Career Interests: {student.get('interests', 'Software & Data Science')}
• Technical Skills: {', '.join(tech_skills) if tech_skills else 'None registered'}
• Soft Skills: {', '.join(soft_skills) if soft_skills else 'None registered'}
• Diagnostic Skill Scores: {', '.join(assessed) if assessed else 'Assessment not completed yet'}
• Top ML Career Recommendations: {', '.join(recs) if recs else 'Recommendations not generated yet'}
• Selected Target Career: {target_career}
• Learning Pathway Progress: {progress_str}
------------------------------------------------------
"""
    return context.strip()


def get_system_prompt(student_id: Optional[int] = None) -> str:
    """
    Construct the authoritative AI Career Guidance System Prompt.
    """
    student_ctx = build_student_context(student_id)

    return f"""You are **SkillMatch AI**, an intelligent, empathetic, and highly knowledgeable Academic & Career Guidance Counselor and Senior Technical Mentor built into the SkillMatch career recommendation platform.

{student_ctx}

YOUR MISSION & ROLE:
1. **Personalized Guidance:** Always tailor your explanations to the student's branch, year, current skills, and target career. Address them warmly by name when known.
2. **Actionable & Practical:** Provide concrete, step-by-step advice. Recommend specific technologies, learning roadmaps, projects to build, interview preparation strategies, and industry best practices.
3. **Skill Gaps & Next Steps:** Help the student understand what skills they are missing for their desired career and how to bridge those gaps using online tutorials, documentation, and hands-on portfolio projects.
4. **Tone & Style:** Encouraging, professional, structured, and easy to read. Use clean Markdown formatting, bullet points, and code snippets when explaining programming concepts.
5. **Conciseness:** Keep answers focused and digestible (typically 2-4 structured paragraphs or bullet lists). Avoid overwhelming jargon unless explained clearly.
6. **Focus Area:** Keep your answers centered around careers, academic planning, programming, software engineering, AI/ML, data science, tech interviews, and professional growth.
"""


# ── AI API Calls ──────────────────────────────────────────────────────────────

def call_gemini_api(api_key: str, messages: List[Dict[str, str]], system_prompt: str) -> str:
    """
    Call Google Gemini REST API directly without heavy external dependencies.
    """
    # Try gemini-2.0-flash first, fallback to gemini-1.5-flash
    models = ["gemini-2.0-flash", "gemini-1.5-flash"]
    last_err = None

    # Convert conversation history to Gemini contents format
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": m["content"]}]
        })

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.95,
            "maxOutputTokens": 1024,
        }
    }

    headers = {"Content-Type": "application/json"}

    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                last_err = f"Gemini API Error ({resp.status_code}): {resp.text}"
        except Exception as e:
            last_err = f"Gemini Request Failed: {str(e)}"

    raise RuntimeError(last_err or "Gemini API failed to generate a response.")


def call_openai_api(api_key: str, messages: List[Dict[str, str]], system_prompt: str) -> str:
    """
    Call OpenAI Chat Completions REST API.
    """
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    formatted_msgs = [{"role": "system", "content": system_prompt}]
    for m in messages:
        formatted_msgs.append({"role": m["role"], "content": m["content"]})

    payload = {
        "model": "gpt-4o-mini",
        "messages": formatted_msgs,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=25)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    else:
        raise RuntimeError(f"OpenAI API Error ({resp.status_code}): {resp.text}")


def generate_ai_response(user_query: str, chat_history: List[Dict[str, str]], student_id: Optional[int] = None) -> str:
    """
    Main entry point: generates personalized response using configured AI API.
    """
    creds = get_api_credentials()
    if not creds["is_configured"]:
        raise ValueError("NO_API_KEY")

    system_prompt = get_system_prompt(student_id)

    # Append current user query
    current_conversation = list(chat_history)
    current_conversation.append({"role": "user", "content": user_query})

    if creds["provider"] == "gemini":
        return call_gemini_api(creds["key"], current_conversation, system_prompt)
    elif creds["provider"] == "openai":
        return call_openai_api(creds["key"], current_conversation, system_prompt)
    else:
        raise ValueError("Unsupported AI provider.")


def stream_text(text: str, delay: float = 0.015) -> Generator[str, None, None]:
    """
    Simulates authentic ChatGPT-style typing streaming effect in Streamlit.
    """
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(delay)
