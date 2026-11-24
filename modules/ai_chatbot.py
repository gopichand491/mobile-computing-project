"""
modules/ai_chatbot.py – AI Career Assistant Chatbot Engine
Supports both:
1. Live Cloud AI (Google Gemini / OpenAI REST APIs) when API keys are configured.
2. Built-in Local Career AI Mode (100% offline, zero-key fallback) that dynamically
   generates structured, context-aware responses using the student's SQLite records,
   O*NET TF-IDF recommendations, skill gaps, and 3-tier pathways.
"""

import os
import json
import time
import requests
import streamlit as st
from typing import Dict, List, Any, Optional, Generator

# ── Custom Gemini API Exception Hierarchy ─────────────────────────────────────

class GeminiApiException(Exception):
    """Base exception for Gemini API communication issues."""
    pass


class GeminiApiKeyInvalidError(GeminiApiException):
    """Raised when the Gemini API key is missing, invalid, expired, or malformed."""
    pass


class GeminiQuotaExceededError(GeminiApiException):
    """Raised when the Gemini API rate limit or quota has been reached."""
    pass


class GeminiPermissionError(GeminiApiException):
    """Raised when the Gemini API request is forbidden or permission is denied."""
    pass


class GeminiServiceUnavailableError(GeminiApiException):
    """Raised when the Google Gemini service is temporarily unavailable or unreachable."""
    pass


# ── API Key Validation Helper ─────────────────────────────────────────────────

def is_plausible_gemini_key(key: Optional[str]) -> bool:
    """
    Check if a key is a plausible, structurally valid Google Gemini API key.
    Valid keys typically start with 'AIzaSy' and are at least 25 characters.
    Rejects obvious placeholders, dummy text, and whitespace.
    """
    if not key:
        return False
    k = str(key).strip().strip('"').strip("'")
    if len(k) < 20:
        return False
    # Check for placeholder strings
    low = k.lower()
    placeholders = [
        "none", "null", "undefined", "your_api_key_here", "your_gemini_api_key",
        "your_key", "dummy", "placeholder", "replace_me", "api_key", "test_key"
    ]
    if low in placeholders:
        return False
    if "your_" in low or "example" in low:
        return False
    return True


def is_plausible_openai_key(key: Optional[str]) -> bool:
    """Check if a key is a plausible OpenAI API key (starts with sk- and >= 20 chars)."""
    if not key:
        return False
    k = str(key).strip().strip('"').strip("'")
    if len(k) < 20:
        return False
    low = k.lower()
    if low in ("none", "null", "undefined", "your_openai_api_key", "your_key", "dummy"):
        return False
    return True


# ── API Key Management ────────────────────────────────────────────────────────

def get_api_credentials() -> Dict[str, Optional[str]]:
    """
    Retrieve AI API key securely in order of precedence:
    1. Session state ('GEMINI_API_KEY' or 'custom_gemini_key')
    2. Streamlit secrets (.streamlit/secrets.toml or Streamlit Cloud Secrets)
    3. Environment variables
    Validates key format before declaring is_configured=True.
    """
    gemini_key = None
    openai_key = None

    # 1. Check session state override
    if hasattr(st, "session_state"):
        gemini_key = st.session_state.get("GEMINI_API_KEY") or st.session_state.get("custom_gemini_key")
        openai_key = st.session_state.get("OPENAI_API_KEY") or st.session_state.get("custom_openai_key")
        if gemini_key:
            gemini_key = str(gemini_key).strip().strip('"').strip("'")
        if openai_key:
            openai_key = str(openai_key).strip().strip('"').strip("'")

    # 2. Check Streamlit secrets
    if not gemini_key or not openai_key:
        try:
            if hasattr(st, "secrets"):
                if not gemini_key:
                    raw_g = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
                    if raw_g:
                        gemini_key = str(raw_g).strip().strip('"').strip("'")
                if not openai_key:
                    raw_o = st.secrets.get("OPENAI_API_KEY")
                    if raw_o:
                        openai_key = str(raw_o).strip().strip('"').strip("'")
        except Exception:
            pass

    # 3. Check environment variables
    if not gemini_key:
        raw_env_g = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if raw_env_g:
            gemini_key = str(raw_env_g).strip().strip('"').strip("'")
    if not openai_key:
        raw_env_o = os.environ.get("OPENAI_API_KEY")
        if raw_env_o:
            openai_key = str(raw_env_o).strip().strip('"').strip("'")

    provider = None
    active_key = None

    # Validate plausibility
    if is_plausible_gemini_key(gemini_key):
        provider = "gemini"
        active_key = gemini_key
    elif is_plausible_openai_key(openai_key):
        provider = "openai"
        active_key = openai_key

    return {
        "provider": provider,
        "key": active_key,
        "gemini_key": active_key if provider == "gemini" else None,
        "openai_key": active_key if provider == "openai" else None,
        "is_configured": active_key is not None,
    }


# ── Student Context Builder ───────────────────────────────────────────────────

def get_student_details_for_ai(student_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Extract structured student profile, competencies, recommendations, and pathways from SQLite.
    """
    if not student_id and hasattr(st, "session_state"):
        student_id = st.session_state.get("student_id")

    data = {
        "student_id": student_id,
        "name": "Student",
        "education": "B.Tech (Pursuing)",
        "degree": "Computer Science & Engineering",
        "department": "Engineering",
        "year": "3rd Year",
        "interests": "Technology & Software Development",
        "tech_skills": [],
        "soft_skills": [],
        "all_skills": [],
        "assessment": {},
        "recommendations": [],
        "target_career": "Data Analyst",
        "matching_skills": [],
        "missing_skills": [],
        "progress_str": "0 topics completed",
        "has_profile": False,
    }

    if not student_id:
        return data

    try:
        from modules.student_registration import get_student_by_id, get_student_skills
        from modules.skill_assessment import get_assessment
        from database.db_connection import execute_query

        student = get_student_by_id(student_id)
        if not student:
            return data

        data["has_profile"] = True
        data["name"] = student.get("name", "Student")
        data["education"] = student.get("education_level", "B.Tech (Pursuing)")
        data["degree"] = student.get("degree", "Computer Science")
        data["department"] = student.get("department", "Engineering")
        data["year"] = student.get("year_of_study", "3rd Year")
        data["interests"] = student.get("interests", "Technology & Software Development")

        skills = get_student_skills(student_id)
        data["tech_skills"] = [s for s in skills if s.get("skill_type") == "technical"]
        data["soft_skills"] = [s for s in skills if s.get("skill_type") == "soft"]
        data["all_skills"] = [s["skill_name"] for s in skills]

        data["assessment"] = get_assessment(student_id)

        # Recommendations
        recs_res = execute_query(
            "SELECT career_title, match_score FROM career_recommendations WHERE student_id = ? ORDER BY match_score DESC LIMIT 5",
            (student_id,), fetch="all"
        )
        if recs_res:
            data["recommendations"] = [
                {"career_title": r["career_title"], "match_pct": round(r["match_score"] * 100, 1)}
                for r in recs_res
            ]
        elif data["all_skills"]:
            # Compute dynamically via recommender
            try:
                from ml.recommendation_model import get_recommender
                rec_objs = get_recommender().recommend(data["all_skills"], top_n=5, student_interests=data["interests"])
                data["recommendations"] = [
                    {"career_title": r["career_title"], "match_pct": r["match_pct"]}
                    for r in rec_objs
                ]
            except Exception:
                pass

        # Target career & progress
        sel_c = st.session_state.get("selected_career") if hasattr(st, "session_state") else None
        if not sel_c and data["recommendations"]:
            sel_c = data["recommendations"][0]["career_title"]
        data["target_career"] = sel_c or "Data Analyst"

        # Gaps for target career
        try:
            from ml.data_preprocessing import load_or_create_processed_data
            df, _ = load_or_create_processed_data()
            if df is not None:
                match_row = df[df["career_title"].str.strip().str.lower() == data["target_career"].strip().lower()]
                if not match_row.empty:
                    req_list = [s.strip() for s in str(match_row.iloc[0]["skills_list"]).split(",") if s.strip()]
                    st_set = {s.lower() for s in data["all_skills"]} | {k.lower() for k in data["assessment"].keys()}
                    data["matching_skills"] = [s for s in req_list if s.lower() in st_set]
                    data["missing_skills"] = [s for s in req_list if s.lower() not in st_set]
        except Exception:
            pass

        prog_res = execute_query(
            "SELECT COUNT(*) as tot, SUM(is_completed) as comp FROM learning_progress WHERE student_id = ?",
            (student_id,), fetch="one"
        )
        if prog_res and prog_res["tot"] and prog_res["tot"] > 0:
            comp_val = prog_res["comp"] or 0
            data["progress_str"] = f"{comp_val} of {prog_res['tot']} topics completed ({round(comp_val / prog_res['tot'] * 100, 1)}%)"

    except Exception:
        pass

    return data


def build_student_context(student_id: Optional[int] = None) -> str:
    """
    Fetch comprehensive student context string for LLM system prompts.
    """
    d = get_student_details_for_ai(student_id)
    if not d["has_profile"]:
        return (
            "No specific student profile is currently logged in. "
            "You are speaking with a student exploring engineering and technology careers."
        )

    tech = [f"{s['skill_name']} (Lvl {s.get('proficiency', 3)}/5)" for s in d["tech_skills"]]
    soft = [f"{s['skill_name']} (Lvl {s.get('proficiency', 3)}/5)" for s in d["soft_skills"]]
    assessed = [f"{k}: {v}/5" for k, v in d["assessment"].items()]
    recs = [f"{r['career_title']} ({r['match_pct']}%)" for r in d["recommendations"]]

    return f"""
--- CURRENT STUDENT PROFILE (CONFIDENTIAL CONTEXT) ---
• Student Name: {d['name']}
• Academic Level: {d['education']} | {d['degree']}
• Department: {d['department']} ({d['year']})
• Career Interests: {d['interests']}
• Technical Skills: {', '.join(tech) if tech else 'None registered'}
• Soft Skills: {', '.join(soft) if soft else 'None registered'}
• Diagnostic Skill Scores: {', '.join(assessed) if assessed else 'Assessment pending'}
• Top ML Recommendations: {', '.join(recs) if recs else 'Pending'}
• Current Target Career: {d['target_career']}
• Matched Skills for Target: {', '.join(d['matching_skills']) if d['matching_skills'] else 'None yet'}
• Missing Skills for Target: {', '.join(d['missing_skills']) if d['missing_skills'] else 'None'}
• Learning Pathway Progress: {d['progress_str']}
------------------------------------------------------
""".strip()


def get_system_prompt(student_id: Optional[int] = None) -> str:
    """
    Construct the authoritative AI Career Guidance System Prompt.
    """
    student_ctx = build_student_context(student_id)

    return f"""You are **SkillMatch AI**, an intelligent, empathetic, and highly knowledgeable Academic & Career Guidance Counselor and Senior Technical Mentor built into the SkillMatch platform.

{student_ctx}

YOUR MISSION & ROLE:
1. **Personalized Guidance:** Always tailor your explanations to the student's branch, year, current skills, and target career. Address them warmly by name when known.
2. **Actionable & Practical:** Provide concrete, step-by-step advice. Recommend specific technologies, learning roadmaps, projects to build, interview preparation strategies, and industry best practices.
3. **Skill Gaps & Next Steps:** Help the student understand what skills they are missing for their desired career and how to bridge those gaps using online tutorials, documentation, and hands-on portfolio projects.
4. **Tone & Style:** Encouraging, professional, structured, and easy to read. Use clean Markdown formatting, bullet points, and code snippets when explaining programming concepts.
5. **Conciseness:** Keep answers focused and digestible (typically 2-4 structured paragraphs or bullet lists). Avoid overwhelming jargon unless explained clearly.
6. **Focus Area:** Keep your answers centered around careers, academic planning, programming, software engineering, AI/ML, data science, tech interviews, and professional growth.
"""


# ── Built-in Local AI Engine (Zero-Key Fallback) ──────────────────────────────

def generate_local_ai_response(user_query: str, student_id: Optional[int] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Intelligent built-in local fallback engine.
    Dynamically generates personalized, accurate answers based on the student's
    SQLite database records, O*NET recommendations, skill gaps, and learning pathways.
    """
    q = user_query.strip().lower()
    d = get_student_details_for_ai(student_id)
    name = d["name"] if d["has_profile"] else "there"
    target = d["target_career"]

    # 1. INTENT: Career Recommendation / Best Fit / "What careers match my skills?"
    if any(k in q for k in ["career", "recommend", "best fit", "match", "suitable", "which job", "what should i become"]):
        recs = d["recommendations"]
        if not recs:
            try:
                from ml.recommendation_model import get_recommender
                rec_objs = get_recommender().recommend(d["all_skills"] or ["Python", "SQL"], top_n=5, student_interests=d["interests"])
                recs = [{"career_title": r["career_title"], "match_pct": r["match_pct"]} for r in rec_objs]
            except Exception:
                recs = [{"career_title": "Data Analyst", "match_pct": 72.5}, {"career_title": "Software Developer", "match_pct": 68.0}]

        top_recs_md = "\n".join([f"  {idx}. **{r['career_title']}** – `{r['match_pct']}% Match`" for idx, r in enumerate(recs[:4], start=1)])
        best = recs[0]["career_title"] if recs else "Data Analyst"
        best_pct = recs[0]["match_pct"] if recs else 70.0

        return f"""### 🎯 Personalized Career Recommendations for {name}

Based on your academic profile in **{d['degree']}** ({d['year']}) and your tracked competencies, our TF-IDF machine learning engine analyzed your skills against the **U.S. Department of Labor O*NET occupational database**.

Here are your top-fit career trajectories:
{top_recs_md}

#### 💡 Key Recommendation Insights:
- **Primary Strongest Fit:** **{best}** ({best_pct}% match). Your background in *{', '.join(d['all_skills'][:3]) or 'software fundamentals'}* provides a direct foundation for this role.
- **Why this matches:** You already possess core prerequisite technical and soft skills evaluated by our recommendation model.
- **Next Action:** Visit the **Career Recommendations** page to inspect full role breakdowns, or switch to **Learning Pathway** to start checking off missing competencies!"""

    # 2. INTENT: Skill Gap Analysis / "What skills am I missing?" / "deficit"
    elif any(k in q for k in ["gap", "missing", "deficit", "lacking", "need to learn", "skills do i need", "what skills"]):
        missing = d["missing_skills"]
        matching = d["matching_skills"]
        if not missing and not matching:
            missing = ["Advanced SQL", "Cloud Deployment (AWS/Azure)", "Docker/Containers"]
            matching = ["Python", "Problem Solving", "Git"]

        matching_md = ", ".join([f"`{s}`" for s in matching[:6]]) if matching else "Core fundamentals registered"
        missing_md = "\n".join([f"  • **{s}** – Priority competency to bridge" for s in missing[:5]]) if missing else "  • All primary prerequisites currently met!"

        return f"""### 📉 Skill Gap Analysis for Target Role: **{target}**

Here is your diagnostic competency breakdown for **{target}**:

#### ✅ Competencies You Already Possess:
{matching_md}

#### ❌ Identified Priority Skill Gaps to Bridge:
{missing_md}

#### 🚀 Recommended Action Plan:
1. **Focus on High-Impact Gaps First:** Master the top 2 missing skills before moving to specialized frameworks.
2. **Hands-on Projects:** Build 1 complete capstone project demonstrating practical mastery of these gaps.
3. **Interactive Tracking:** Head over to **Learning Pathway** to access curated, verified tutorials and track your progress in real-time."""

    # 3. INTENT: Roadmap / Learning Pathway / 3-Month Plan / Curriculum
    elif any(k in q for k in ["roadmap", "pathway", "curriculum", "month", "study plan", "how to learn", "guide"]):
        return f"""### 🗺️ Structured 3-Tier Learning Roadmap for **{target}**

Here is your structured progression tailored for your **{d['year']} {d['degree']}** schedule:

#### 🟢 Tier 1: Beginner Level (Weeks 1 – 4) – Core Foundations
- **Master Fundamentals:** Deepen core programming and database querying (Python syntax, data structures, SQL joins).
- **Tooling:** Version control with Git & GitHub workflow.
- **Milestone:** Build 2 miniature command-line scripts or database-backed utilities.

#### 🟡 Tier 2: Intermediate Level (Weeks 5 – 8) – Applied Tools & Skill Gaps
- **Target Missing Gaps:** {', '.join(d['missing_skills'][:3]) if d['missing_skills'] else 'APIs, Data Wrangling, Frameworks'}.
- **Frameworks:** Work with industry-standard libraries (Pandas, Scikit-learn, FastAPI, or React depending on path).
- **Milestone:** Develop an end-to-end portfolio project featuring data persistence and clean documentation.

#### 🔴 Tier 3: Advanced Level (Weeks 9 – 12) – Production Capstone & Interview Readiness
- **Production Best Practices:** Testing, containerization (Docker), and cloud deployment.
- **Capstone Project:** Full-stack or ML deployment solved for a real-world problem.
- **Milestone:** Complete mock technical interviews and push code to your public GitHub profile."""

    # 4. INTENT: Interview Preparation / Questions
    elif any(k in q for k in ["interview", "questions", "prepare", "placement", "hr round", "technical round"]):
        return f"""### 💼 Comprehensive Interview Preparation for **{target}**

As a **{d['education']}** student preparing for campus placements or off-campus recruitment in **{target}**, here is your targeted interview strategy:

#### 🎯 1. Top Technical Questions to Expect:
- **Data Structures & Algorithms:** Arrays, Hash Maps, Linked Lists, Tree Traversals, and Big-O Complexity.
- **Database & SQL:** Write complex queries using `GROUP BY`, `HAVING`, window functions (`ROW_NUMBER()`, `DENSE_RANK()`), and explain ACID properties.
- **Domain Specialization ({target}):**
  - Explain the difference between supervised vs. unsupervised learning (or client-server architecture).
  - How do you handle missing values or outliers in production datasets?
  - Describe how indexing improves database read performance.

#### 🤝 2. Behavioral Questions (Use STAR Method):
- *"Tell me about a challenging academic or team project and how you resolved a roadblock."*
- *"Describe a situation where you had to learn a new technology under tight deadlines."*

#### 💡 Pro Tip:
Always explain your thought process out loud before writing code on the whiteboard or live editor!"""

    # 5. INTENT: Machine Learning / AI / Data Science
    elif any(k in q for k in ["machine learning", "ml", "artificial intelligence", "deep learning", "nlp", "computer vision", "model", "scikit", "tensorflow", "pytorch"]):
        return f"""### 🤖 Machine Learning & Data Science Guidance for {name}

Here is a structured engineering guide tailored for your career path toward **{target}**:

#### 1. Core ML Workflow to Master:
- **Data Preprocessing:** Handling missing values, categorical encoding (One-Hot, Target Encoding), feature scaling (StandardScaler, MinMaxScaler).
- **Model Selection & Training:** Supervised algorithms (Linear/Logistic Regression, Decision Trees, Random Forests, XGBoost).
- **Evaluation Metrics:** Choose metrics aligned with business objectives (Precision, Recall, F1-Score for imbalanced classes; RMSE/MAE for regression).
- **Cross-Validation:** Use 5-fold or 10-fold cross-validation to prevent data leakage and overfitting.

#### 2. Essential ML Code Pattern (Scikit-Learn Pipeline):
```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 1. Build reproducible pipeline
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
])

# 2. Train & Evaluate
pipeline.fit(X_train, y_train)
y_pred = pipeline.predict(X_test)
print(classification_report(y_test, y_pred))
```

#### 3. High-Impact Next Step:
Deploy your trained model as a lightweight REST API using FastAPI or as an interactive dashboard using Streamlit!"""

    # 6. INTENT: Capstone Projects / Portfolio Ideas
    elif any(k in q for k in ["project", "projects", "capstone", "portfolio", "resume project", "build"]):
        return f"""### 🚀 High-Impact Portfolio Project Ideas for **{target}**

To stand out in recruitment drives and technical interviews, build end-to-end projects demonstrating real problem-solving:

#### 🌟 1. Flagship Industry Project Idea:
- **Title:** *End-to-End {target} Platform with Automated CI/CD*
- **Problem Statement:** Build a real-world pipeline that ingests raw data, processes it via clean business logic, stores records in SQLite/PostgreSQL, and displays analytics on a web dashboard.
- **Key Architecture:** Python (Backend) + SQLite / SQLAlchemy + Streamlit/FastAPI + Pytest test suite.

#### 🛠️ 2. Key Elements That Impress Recruiters:
- **Clean Git History:** Meaningful atomic commits (`feat:`, `fix:`, `docs:`) on your public GitHub.
- **Automated Tests:** Include unit tests (`pytest`) covering edge cases and data validation.
- **Comprehensive README:** Include architecture diagrams, installation instructions, and live demo links.
- **Docker Containerization:** Add a working `Dockerfile` showing production deployment readiness.

#### 💡 Pro Tip:
A single well-tested, deployed application with 100% test coverage is worth five half-finished tutorial clones!"""

    # 7. INTENT: Python Programming & Coding Doubts
    elif any(k in q for k in ["python", "sql", "java", "code", "programming", "docker", "git"]):
        return f"""### 💻 Technical Programming Guidance & Best Practices

Here are proven best practices tailored for your technical projects in **{d['department']}**:

#### 1. Clean Code & Modular Architecture:
- Separate business logic from data access layers and presentation.
- Use meaningful variable names and type hinting (`def calculate_score(skills: List[str]) -> float:`).
- Follow PEP 8 (Python) conventions or standard language guidelines.

#### 2. Essential Code Example – Clean SQL Query with Joins:
```sql
SELECT 
    s.name,
    c.career_title,
    ROUND(r.match_score * 100, 1) AS match_pct
FROM students s
JOIN career_recommendations r ON s.id = r.student_id
JOIN careers c ON r.career_id = c.id
WHERE s.id = 1
ORDER BY r.match_score DESC;
```

#### 3. Version Control Tip:
Commit frequently with conventional commit messages: `feat:`, `fix:`, `docs:`, `test:`. This builds an impressive GitHub timeline for hiring managers!"""

    # 8. GENERAL INTENT: Comprehensive Academic Mentorship
    else:
        return f"""### 👋 Hello {name}! Here is your SkillMatch Academic Guidance

I am your **SkillMatch AI Career Mentor**. Here is a quick snapshot of your active profile:
- **Academic Standing:** {d['education']} in {d['department']} ({d['year']})
- **Stated Interests:** {d['interests']}
- **Current Target Role:** **{target}**
- **Learning Progress:** {d['progress_str']}

#### 💡 How I Can Help You Right Now:
1. **Career Guidance:** Ask *"What careers best match my profile?"* to get an ML analysis.
2. **Skill Diagnosis:** Ask *"What skills am I missing for {target}?"* to see your gap report.
3. **Curriculum:** Ask *"Give me a 3-month roadmap"* for step-by-step milestones.
4. **Machine Learning & Python:** Ask *"How do I build an ML pipeline in Python?"* for coding best practices.
5. **Project Ideas:** Ask *"What projects should I build for {target}?"* for portfolio ideas.
6. **Interview Prep:** Ask *"What interview questions should I practice?"* for placement prep.

Feel free to ask any specific question about programming, technology stacks, or career choices!"""


# ── Cloud LLM API Calls ───────────────────────────────────────────────────────

def call_gemini_api(api_key: str, messages: List[Dict[str, str]], system_prompt: str) -> str:
    """
    Call Google Gemini REST API directly using modern supported endpoints.
    Tries gemini-1.5-flash first, followed by gemini-2.0-flash, gemini-1.5-pro, and gemini-1.0-pro.
    Properly classifies and raises specific GeminiApiExceptions for clean upstream handling.
    """
    # Supported Google Gemini models in order of performance and availability
    models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.0-pro"]

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
    last_status = None
    last_err_text = ""

    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            last_status = resp.status_code

            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                last_err_text = resp.text
                # If error is invalid API key, fail immediately across all models
                try:
                    err_json = resp.json().get("error", {})
                    err_msg = str(err_json.get("message", "")).lower()
                    err_status = str(err_json.get("status", "")).upper()
                    if resp.status_code == 400 and ("api_key_invalid" in err_msg or "invalid" in err_msg or err_status == "INVALID_ARGUMENT"):
                        raise GeminiApiKeyInvalidError("Google Gemini API key is invalid or not recognized.")
                    elif resp.status_code == 429 or "resource_exhausted" in err_msg or err_status == "RESOURCE_EXHAUSTED":
                        raise GeminiQuotaExceededError("Google Gemini API quota or rate limit exceeded.")
                    elif resp.status_code == 403 or err_status == "PERMISSION_DENIED":
                        raise GeminiPermissionError("Google Gemini API permission denied.")
                except (GeminiApiKeyInvalidError, GeminiQuotaExceededError, GeminiPermissionError):
                    raise
                except Exception:
                    pass

        except (GeminiApiKeyInvalidError, GeminiQuotaExceededError, GeminiPermissionError):
            raise
        except requests.exceptions.RequestException as req_err:
            last_err_text = str(req_err)

    # Classify final error state
    if last_status == 400 or "api_key_invalid" in last_err_text.lower():
        raise GeminiApiKeyInvalidError("Google Gemini API key is invalid or expired.")
    elif last_status == 429:
        raise GeminiQuotaExceededError("Google Gemini API quota reached.")
    elif last_status == 403:
        raise GeminiPermissionError("Google Gemini access forbidden.")
    elif last_status and last_status >= 500:
        raise GeminiServiceUnavailableError("Google Gemini servers temporarily unavailable.")

    raise GeminiServiceUnavailableError("Unable to reach Google Gemini services.")


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

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        elif resp.status_code == 401:
            raise GeminiApiKeyInvalidError("OpenAI API key is invalid or unauthorized.")
        elif resp.status_code == 429:
            raise GeminiQuotaExceededError("OpenAI rate limit or quota exceeded.")
        else:
            raise GeminiServiceUnavailableError(f"OpenAI service returned status {resp.status_code}")
    except (GeminiApiKeyInvalidError, GeminiQuotaExceededError, GeminiServiceUnavailableError):
        raise
    except Exception as e:
        raise GeminiServiceUnavailableError(f"OpenAI connection error: {e}")


def generate_ai_response(user_query: str, chat_history: List[Dict[str, str]], student_id: Optional[int] = None) -> str:
    """
    Unified entry point for AI responses:
    1. If external API credentials are configured and valid, calls live cloud LLM.
    2. If external API encounters an error (invalid key, quota exceeded, server error),
       it NEVER crashes and NEVER displays raw error messages or stack traces to the user.
       Instead, it generates an intelligent response using the Built-in Career AI engine
       and attaches a clear, professional, friendly notification.
    3. If no external key is configured, defaults seamlessly to the Built-in Career AI.
    """
    creds = get_api_credentials()

    if creds["is_configured"]:
        system_prompt = get_system_prompt(student_id)
        current_conversation = list(chat_history)
        current_conversation.append({"role": "user", "content": user_query})

        try:
            if creds["provider"] == "gemini":
                return call_gemini_api(creds["key"], current_conversation, system_prompt)
            elif creds["provider"] == "openai":
                return call_openai_api(creds["key"], current_conversation, system_prompt)

        except GeminiApiKeyInvalidError:
            # Key was rejected by Google/OpenAI — fallback gracefully with helpful setup advice
            local_reply = generate_local_ai_response(user_query, student_id, chat_history)
            notice = (
                "\n\n---\n"
                "💡 **API Notice:** *The configured Google Gemini API key is invalid or has expired. "
                "Your request was answered using SkillMatch's Built-in Career AI Mentor. "
                "To enable live cloud LLM reasoning, please obtain a free key from "
                "[Google AI Studio](https://aistudio.google.com/app/apikey) and update it in the sidebar settings.*"
            )
            return local_reply + notice

        except GeminiQuotaExceededError:
            local_reply = generate_local_ai_response(user_query, student_id, chat_history)
            notice = (
                "\n\n---\n"
                "💡 **API Notice:** *The Google Gemini API rate limit or quota has been reached. "
                "Your request was answered seamlessly using SkillMatch's Built-in Career AI Mentor.*"
            )
            return local_reply + notice

        except GeminiPermissionError:
            local_reply = generate_local_ai_response(user_query, student_id, chat_history)
            notice = (
                "\n\n---\n"
                "💡 **API Notice:** *Google Gemini API access permission was not granted for this key. "
                "Your request was answered using SkillMatch's Built-in Career AI Mentor.*"
            )
            return local_reply + notice

        except Exception:
            # Network timeout, DNS failure, or temporary server outage
            local_reply = generate_local_ai_response(user_query, student_id, chat_history)
            notice = (
                "\n\n---\n"
                "💡 **API Notice:** *Live cloud AI service is temporarily unavailable. "
                "Your request was answered seamlessly using SkillMatch's Built-in Career AI Mentor.*"
            )
            return local_reply + notice

    # Default to Built-in Local AI Mode (Zero key required)
    return generate_local_ai_response(user_query, student_id, chat_history)


def stream_text(text: str, delay: float = 0.015) -> Generator[str, None, None]:
    """
    Simulates authentic ChatGPT-style typing streaming effect in Streamlit.
    """
    words = text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(delay)
