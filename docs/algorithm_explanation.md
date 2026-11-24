# Algorithm Explanation – SkillMatch Recommendation Engine

## Overview

SkillMatch uses **TF-IDF Vectorization** combined with **Cosine Similarity** to recommend careers.
This is a proven, transparent, and computationally efficient NLP-based approach.

## Algorithm Steps

### Step 1 – Data Preparation

Each career's required skills are stored as a comma-separated list (skills_list):
```
Data Scientist → "Python, R, Machine Learning, Statistics, SQL, TensorFlow, Pandas, ..."
```

### Step 2 – TF-IDF Vectorization

**TF-IDF** (Term Frequency – Inverse Document Frequency) converts each career's skill list
into a numeric vector. Skills common across all careers (e.g., "Communication") receive lower
weights. Rare, specialized skills receive higher weights.

```
TF(t,d)   = (count of term t in document d) / (total terms in d)
IDF(t)    = log(total documents / documents containing t)
TF-IDF(t,d) = TF(t,d) × IDF(t)
```

Each career becomes a vector in an N-dimensional skill space.

### Step 3 – Student Vector Encoding

The student's skills are encoded into the **same TF-IDF space** using the fitted vectorizer:
```python
student_vec = vectorizer.transform(["Python, SQL, Machine Learning, Communication"])
```

### Step 4 – Cosine Similarity

The cosine similarity between the student vector S and each career vector C is computed:

```
cos(θ) = (S · C) / (|S| × |C|)
```

- Score = 1.0 → perfect overlap
- Score = 0.0 → no shared skills
- Range: [0, 1]

### Step 5 – Ranking

All careers are sorted by cosine similarity score (descending).
The top-N are returned as recommendations.
Match % = cosine_score × 100

### Step 6 – Skill Gap Analysis

```python
required_set = set(career["skills"])
student_set  = set(student["skills"])

matching = required_set ∩ student_set
missing  = required_set - student_set
coverage = len(matching) / len(required_set) × 100
```

## Implementation

```python
# Feature Engineering (ml/feature_engineering.py)
vectorizer = TfidfVectorizer(tokenizer=lambda x: x.split(","), ngram_range=(1,2))
career_matrix = vectorizer.fit_transform(career_docs)

# Recommendation (ml/recommendation_model.py)
student_vec = vectorizer.transform([student_skills_joined])
scores = cosine_similarity(student_vec, career_matrix).flatten()
top_careers = df.iloc[scores.argsort()[::-1][:top_n]]
```

## Complexity

| Operation | Complexity |
|-----------|------------|
| TF-IDF Fit | O(N × M) where N=careers, M=unique skills |
| Transform | O(M) per query |
| Cosine Similarity | O(N) per query |
| Total Query | O(N + M) ≈ O(N) |

With N=60 careers and M≈500 unique skills, this runs in <100ms.

## Why Not Deep Learning?

For this application:
- Dataset is small (60–900 careers)
- Skill matching is interpretable with TF-IDF
- Cosine similarity provides explainable match scores
- No training data required (unsupervised)
- Results are reproducible and transparent

Deep learning would be overkill and less interpretable for this use case.
