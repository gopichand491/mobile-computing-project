# System Architecture – SkillMatch

## Overview

SkillMatch follows a layered architecture separating UI, business logic, ML, and data storage.

## Layer Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                       │
│    Streamlit Multi-Page App (app.py + pages/*.py)             │
│    Blue/White Theme | Plotly Charts | Responsive UI           │
└──────────────────────┬────────────────────────────────────────┘
                       │ Python function calls
┌──────────────────────▼────────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                       │
│    modules/student_registration.py  – Student CRUD            │
│    modules/skill_assessment.py      – Assessment Q&A          │
│    modules/learner_profile.py       – Profile aggregation      │
│    modules/career_recommendation.py – Rec DB persistence      │
│    modules/skill_gap_analysis.py    – Gap computation         │
│    modules/learning_pathway.py      – Path generation         │
│    modules/progress_tracking.py     – Progress management     │
└──────────┬───────────────────────────────┬────────────────────┘
           │                               │
┌──────────▼───────────────┐  ┌───────────▼────────────────────┐
│      ML LAYER (ml/)       │  │    DATABASE LAYER (database/)   │
│  data_preprocessing.py    │  │  db_connection.py               │
│  feature_engineering.py   │  │  db_setup.py                    │
│  recommendation_model.py  │  │  skillmatch.db (SQLite)         │
│  model_evaluation.py      │  └────────────────────────────────┘
└──────────┬────────────────┘
           │
┌──────────▼────────────────────────────────────────────────────┐
│                       DATA LAYER (data/)                       │
│  raw/        – Original O*NET CSV/Excel files                  │
│  processed/  – cleaned_career_skills.csv (ML-ready)           │
│  sample/     – sample_student_data.csv (demo)                  │
└───────────────────────────────────────────────────────────────┘
```

## Database Schema

```sql
students (id, name, email, education_level, degree, department, year_of_study, interests, created_at)
student_skills (id, student_id FK, skill_name, skill_type, proficiency)
skill_assessments (id, student_id FK, skill_name, score, assessed_at)
career_recommendations (id, student_id FK, career_title, match_score, onet_code, generated_at)
learning_pathways (id, student_id FK, career_title, step_number, topic, description, resource_url)
learning_progress (id, student_id FK, career_title, topic, is_completed, completed_at)
```

## Data Flow

```
Student Input → Skill Parser → DB (student_skills)
                              ↓
O*NET Data → TF-IDF Fit → Career Matrix
                              ↓
Student Skills → TF-IDF Transform → Student Vector
                              ↓
Cosine Similarity → Score per Career → Top-N Ranking
                              ↓
Skill Gap: Required - Student = Missing
                              ↓
Learning Pathway → DB (learning_pathways)
                              ↓
Progress Checkboxes → DB (learning_progress)
```
