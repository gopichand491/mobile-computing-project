# SkillMatch – Mobile Skill-Based Learning and Career Recommendation System

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/gopichand491/mobile-computing-project)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SkillMatch** is a fully functional, intelligent career guidance and skill development application developed as a B.Tech academic project. It analyzes a student's skills and interests, calculates real-time match scores against occupational career profiles using Machine Learning, identifies 3-tier skill gaps, generates multi-level learning roadmaps, tracks progress persistently in SQLite, and exports official downloadable PDF reports.

- **GitHub Repository**: [https://github.com/gopichand491/mobile-computing-project](https://github.com/gopichand491/mobile-computing-project)
- **Live Deployment Platform**: Streamlit Community Cloud

---

## 📋 Table of Contents
1. [Project Objectives](#1-project-objectives)
2. [Problem Statement & Proposed Solution](#2-problem-statement--proposed-solution)
3. [Technology Stack](#3-technology-stack)
4. [Dataset Details & Transparency](#4-dataset-details--transparency)
5. [Machine Learning Algorithm](#5-machine-learning-algorithm)
6. [Core Modules & Architecture](#6-core-modules--architecture)
7. [Application Pages (12 Pages)](#7-application-pages-12-pages)
8. [Live Demonstration Guide](#8-live-demonstration-guide)
9. [Installation & Local Execution](#9-installation--local-execution)
10. [Streamlit Community Cloud Deployment](#10-streamlit-community-cloud-deployment)
11. [Testing & Verification](#11-testing--verification)

---

## 1. Project Objectives

1. **Student Registration & Profiling**: Collect and validate academic records, educational level, technical skills, soft skills, and career interests.
2. **Interactive Skill Assessment**: Provide diagnostic multiple-choice quiz questions and domain rating matrices to benchmark competencies automatically.
3. **Machine Learning Recommendations**: Compute dynamic match percentages using TF-IDF Vectorization and Cosine Similarity against occupational requirements.
4. **Skill Gap Diagnosis**: Categorize competencies into Competent (>=3.0), Low-Proficiency (<3.0), and Missing Gaps.
5. **Multi-Career Comparison**: Enable side-by-side comparison of 3+ career roles with requirements matrices and best-fit verdicts.
6. **3-Tier Personalized Learning Pathway**: Curate structured roadmaps divided into Beginner, Intermediate, and Advanced tiers with verified learning resources.
7. **Persistent Progress Tracking**: Allow students to check off topics with real-time SQLite persistence across application restarts.
8. **Downloadable Career Report**: Export an official academic career dossier in PDF format using ReportLab.
9. **Smart AI Career Assistant Chatbot**: 24/7 interactive AI career counselor powered by real Google Gemini / OpenAI APIs with live student profile context injection.

---

## 2. Problem Statement & Proposed Solution

### Problem Statement
Graduating engineering students frequently lack clarity on which career trajectories align with their true competencies. Traditional career portals provide generic advice without diagnosing specific skill deficits or mapping step-by-step remediation roadmaps.

### Existing System vs. SkillMatch Proposed System

| Feature | Existing Portals | SkillMatch Proposed System |
| :--- | :--- | :--- |
| **Personalization** | Static questionnaires, generic lists | Deterministic ML matching using TF-IDF + Cosine Similarity |
| **Dataset** | Hardcoded or undocumented | Standardized U.S. DOL O*NET occupational dataset (53+ careers) |
| **Competency Diagnosis**| Binary yes/no | 3-Tier: Competent (>=3.0), Low-Proficiency (<3.0), Missing Gap |
| **Career Comparison** | None or manual notes | Automated side-by-side comparison across 3+ target roles |
| **Curriculum Pathway** | Generic course ads | 3-Tier (Beginner, Intermediate, Advanced) roadmaps |
| **Persistence** | Session-only or requires cloud SaaS | Local SQLite database with ACID transactions and foreign keys |
| **Reporting** | Web-only text | Downloadable official academic PDF report |

---

## 3. Technology Stack

- **Programming Language**: Python 3.9+
- **Web Frontend**: Streamlit (Responsive dark blue & white UI)
- **Data Processing**: Pandas & NumPy
- **Machine Learning**: Scikit-learn (`TfidfVectorizer`, `cosine_similarity`)
- **Data Visualizations**: Plotly Graph Objects & Plotly Express (Radar, Bar, Pie charts)
- **Database**: SQLite3 (WAL mode, foreign key enforcement, connection timeouts)
- **PDF Generation**: ReportLab
- **Automated Testing**: Pytest (30 test cases)

---

## 4. Dataset Details & Transparency

- **Primary Source**: O*NET Online Occupational Information Network
- **Provider**: U.S. Department of Labor / Employment and Training Administration
- **URL**: https://www.onetcenter.org/database.html
- **License**: Public Domain (U.S. Government Open Data)
- **Version**: O*NET 28.1 Database
- **Processed File**: `data/processed/cleaned_career_skills.csv` (53 curated career profiles spanning 7 domains: Technology & IT, Data Science & Analytics, Business & Management, Healthcare, Engineering, Creative & Design, Education)
- **Sample Upload**: Students can also upload their own custom CSV dataset directly in the application under Page 11 (`Dataset Information`).

---

## 5. Machine Learning Algorithm

SkillMatch uses **TF-IDF Vectorization combined with Cosine Similarity**.

### Mathematical Formulation

1. **Term Frequency – Inverse Document Frequency (TF-IDF)**:
   $$\text{TF}(t, d) = \frac{\text{count of term } t \text{ in document } d}{\text{total terms in } d}$$
   $$\text{IDF}(t) = \log\left(\frac{1 + N}{1 + \text{df}(t)}\right) + 1$$
   $$\text{TF-IDF}(t, d) = \text{TF}(t, d) \times \text{IDF}(t)$$
   Each career's required skills list is treated as a document. Specialized skills receive higher weights, while ubiquitous skills receive normalized weights.

2. **Student Vector Projection**:
   The student's registered and assessed skills are projected into the identical $N$-dimensional TF-IDF space.

3. **Cosine Similarity**:
   $$\text{Cosine Similarity}(S, C) = \frac{S \cdot C}{\|S\| \times \|C\|} = \frac{\sum_{i=1}^n S_i C_i}{\sqrt{\sum_{i=1}^n S_i^2} \sqrt{\sum_{i=1}^n C_i^2}}$$
   - $\text{Match Percentage} = \min(100.0, \text{Cosine Similarity} \times 100\%)$

4. **Transparent Explainability**:
   For every recommended career, the system dynamically outputs an explainable rationale breaking down exactly which skills match, which missing skills should be acquired, and how the role relates to the student's career interests.

---

## 6. Core Modules & Architecture

```
SkillMatch/
│
├── app.py                          # Main entry point & Dynamic Live Dashboard
├── requirements.txt                # Project dependencies
├── README.md                       # Comprehensive documentation
├── .gitignore                      # Git ignore rules
│
├── data/
│   ├── raw/                        # Source data directory
│   ├── processed/
│   │   └── cleaned_career_skills.csv  # 53 Cleaned occupational profiles
│   ├── sample/
│   │   └── sample_student_data.csv    # Sample student profiles
│   └── DATASET_INFO.md             # Dataset data dictionary & citation
│
├── database/
│   ├── db_connection.py            # SQLite connection pool with timeout & WAL
│   ├── db_setup.py                 # 6-table relational schema definition
│   └── skillmatch.db               # SQLite database file
│
├── modules/
│   ├── student_registration.py     # Student CRUD, validation & login
│   ├── skill_assessment.py         # MCQ grading, rating matrix, and profile sync
│   ├── learner_profile.py          # Profile metric aggregation
│   ├── career_recommendation.py    # Database persistence of recommendations
│   ├── skill_gap_analysis.py       # 3-tier gap deficit diagnosis
│   ├── learning_pathway.py         # 3-tier roadmap generator (Beg/Int/Adv)
│   ├── progress_tracking.py        # Cross-career topic completion accounting
│   └── report_generator.py         # ReportLab PDF dossier generation
│
├── ml/
│   ├── data_preprocessing.py       # Data cleaning & sample dataset loader
│   ├── feature_engineering.py      # TF-IDF SkillFeatureEncoder class
│   ├── recommendation_model.py     # Cosine similarity engine & rationale generator
│   └── model_evaluation.py         # Recommendation diversity & coverage metrics
│
├── pages/
│   ├── 1_Dashboard.py              # Dashboard redirect / view
│   ├── 2_Registration.py           # Student Registration & Login
│   ├── 3_Skill_Assessment.py       # Interactive MCQ Quiz & Rating Matrix
│   ├── 4_Learner_Profile.py        # Visual Analytics (Radar, Bar, Pie)
│   ├── 5_Career_Recommendations.py # Top 5 ML Recommendations + Explanations
│   ├── 6_Skill_Gap_Analysis.py     # Competent, Low-Proficiency & Missing Gaps
│   ├── 7_Career_Comparison.py      # Multi-Career Side-by-Side Comparison
│   ├── 8_Learning_Pathway.py       # 3-Tier Roadmap (Beginner/Int/Adv)
│   ├── 9_Progress_Tracking.py      # Real-time Topic Completion Tracking
│   ├── 10_Career_Report.py         # Live Dossier Preview & PDF Download
│   ├── 11_Dataset_Information.py   # O*NET Dataset Explorer & CSV Uploader
│   └── 12_About_Project.py         # System Architecture & Algorithms
│
├── assets/styles/style.css         # Dark blue & white responsive theme
│
└── tests/
    ├── test_database.py            # Registration, login, validation & DB tests
    ├── test_preprocessing.py       # Data integrity, O*NET codes & columns
    ├── test_recommendation.py      # Recommendation engine & cosine metrics
    └── test_workflow_and_report.py # Quiz grading, 3-tier roadmaps, PDF generation
```

---

## 7. Application Pages (13 Pages)

1. **🏠 Home Dashboard (`app.py`)**: Real-time academic metrics for logged-in students, guided workflow pipeline, and 1-click Demo Account loader.
2. **📝 Student Registration (`pages/2_Registration.py`)**: Input validation, new account creation, email login, and instant demo account initialization.
3. **📊 Skill Assessment (`pages/3_Skill_Assessment.py`)**: 12 interactive multiple-choice questions across Python, Java, SQL, ML, Git, and Soft Skills with instant score calculation and database synchronization.
4. **👤 Learner Profile (`pages/4_Learner_Profile.py`)**: Interactive Plotly radar chart, horizontal competency bars, and proficiency distribution pie chart.
5. **🎯 Career Recommendations (`pages/5_Career_Recommendations.py`)**: Top 5 careers ranked by match percentage with domain filters, competency coverage bars, and recommendation explanations.
6. **📉 Skill Gap Analysis (`pages/6_Skill_Gap_Analysis.py`)**: 3-tier classification: Competent skills (>=3), Low-Proficiency skills (<3), and Missing Gaps with cross-career priority frequency ranking.
7. **⚖️ Career Comparison (`pages/7_Career_Comparison.py`)**: Side-by-side comparison of 3+ target roles with skill requirement matrices and best-fit verdicts.
8. **🗺️ Learning Pathway (`pages/8_Learning_Pathway.py`)**: 3-tier roadmap (🟢 Beginner, 🟡 Intermediate, 🔴 Advanced) with direct educational links and interactive completion checkboxes.
9. **✅ Progress Tracking (`pages/9_Progress_Tracking.py`)**: Cross-career progress cards, stacked completion bar charts, and step status checklists.
10. **📄 Career Report (`pages/10_Career_Report.py`)**: Official downloadable PDF report generated in real-time from SQLite records using ReportLab.
11. **🗄️ Dataset Information (`pages/11_Dataset_Information.py`)**: Overview of O*NET tables, skills explorer, and custom CSV upload feature.
12. **ℹ️ About Project (`pages/12_About_Project.py`)**: System architecture, mathematical ML explanations, and complete technology stack.
13. **🤖 AI Career Assistant (`pages/13_AI_Career_Assistant.py`)**: Intelligent, real-time AI guidance counselor with live student profile context, typewriter streaming animations, question chips, and floating accessibility on every page.

---

## 8. Live Demonstration Guide

### Quick Demonstration Steps for College Guide:

1. **Launch the application**:
   ```bash
   streamlit run app.py
   ```
2. **Step 1 - Instant Demo Login**:
   - On the Home Dashboard or Registration page, click **"⚡ Load Demo Profile (Arjun Sharma)"**.
   - Notice the dashboard instantly updates with live metrics from SQLite: 8 Skills Assessed, 8 Tracked Skills, Top Career Match: Data Analyst (68.2%), and 0% Pathway Completion.
3. **Step 2 - Interactive MCQ Quiz**:
   - Navigate to **Skill Assessment**.
   - Show the interactive diagnostic test covering Python, Java, SQL, ML, and Soft Skills.
   - Submit answers and show how the profile and radar chart update immediately.
4. **Step 3 - ML Career Recommendations**:
   - Navigate to **Career Recommendations**.
   - Point out the Top 5 careers, dynamic match percentages, matching skills, missing skills, and the **transparent recommendation rationale**.
5. **Step 4 - 3-Tier Skill Gap Diagnosis**:
   - Navigate to **Skill Gap Analysis**.
   - Show how skills are classified into Competent (>=3.0), Low-Proficiency (<3.0), and Missing.
   - Point out the cross-career priority skills chart.
6. **Step 5 - Side-by-Side Career Comparison**:
   - Navigate to **Career Comparison**.
   - Select 3 careers (e.g., Data Analyst, Data Scientist, Software Developer) and highlight the Best-Fit verdict and requirements matrix.
7. **Step 6 - 3-Tier Learning Pathway & Progress Tracking**:
   - Navigate to **Learning Pathway**.
   - Show the 🟢 Beginner, 🟡 Intermediate, and 🔴 Advanced roadmap steps.
   - Check off a topic (e.g. "Excel for Data Analysis").
   - Switch to **Progress Tracking** to show that completion percentage increased in SQLite.
8. **Step 7 - Download Official PDF Report**:
   - Navigate to **Career Report**.
   - Click **"📥 Download Career Report (PDF)"**.
   - Open the generated PDF to showcase student details, assessment scores, recommendations, skill gaps, and roadmap.

---

## 9. Installation & Local Execution

### Prerequisites
- Python 3.9, 3.10, or 3.11 installed.
- Git installed.

### Step-by-Step Commands:

```bash
# 1. Clone the repository:
git clone https://github.com/gopichand491/mobile-computing-project.git
cd mobile-computing-project

# 2. Install all dependencies:
pip install -r requirements.txt

# 3. Launch the Streamlit application:
streamlit run app.py
```

The application will open in your default browser at: `http://localhost:8501`.

---

## 10. Streamlit Community Cloud Deployment

This project is pre-configured for 1-click deployment on **Streamlit Community Cloud**:

### Deployment Steps:
1. Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account (`gopichand491`).
2. Click **"New app"**.
3. Configure the deployment settings:
   - **Repository:** `gopichand491/mobile-computing-project`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **"Deploy!"**.
5. Streamlit Community Cloud will automatically build dependencies from `requirements.txt` and launch the live web application.

---

## 11. Testing & Verification

Execute the comprehensive automated test suite with pytest:

```bash
python -m pytest tests/ -v
```

### Test Results Summary:
- **`tests/test_ai_chatbot.py`**: 7 tests passed (API credentials lookup, session override, student context compilation, prompt engineering, streaming generator, missing key exception)
- **`tests/test_database.py`**: 6 tests passed (validation, creation, retrieval, case-insensitive login, skill upsert, duplicate email handling)
- **`tests/test_preprocessing.py`**: 11 tests passed (O*NET schema, column completeness, lowercase normalization, feature encoding)
- **`tests/test_recommendation.py`**: 9 tests passed (cosine similarity ranking, category filtering, empty skill handling, diversity evaluation)
- **`tests/test_workflow_and_report.py`**: 7 tests passed (MCQ quiz grading, 3-tier roadmap generation, SQLite progress tracking, ReportLab PDF generation, dynamic roadmap generation for any O*NET career, persistence across reconnect, XML character escaping)
- **Total: 40 passed in ~5 seconds (100% pass rate)**.
