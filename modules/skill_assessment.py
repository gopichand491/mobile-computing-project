"""
SkillMatch – Skill Assessment Module
Manages assessment questions, quiz grading, and immediate student profile synchronization.
"""

from typing import List, Dict, Optional, Tuple
from database.db_connection import execute_query, execute_many


# Interactive MCQ assessment questions with correct answers to calculate scores automatically
QUIZ_QUESTIONS = [
    {
        "id": "py_1",
        "skill": "Python",
        "category": "technical",
        "question": "In Python, which built-in data type is mutable and maintains an ordered collection of key-value pairs (as of Python 3.7+)?",
        "options": ["tuple", "dict", "set", "frozenset"],
        "correct": "dict",
        "explanation": "Dictionaries in Python store key-value pairs and are mutable."
    },
    {
        "id": "py_2",
        "skill": "Python",
        "category": "technical",
        "question": "What is the output of `[x**2 for x in range(4) if x % 2 == 0]` in Python?",
        "options": ["[0, 4]", "[1, 9]", "[0, 1, 4, 9]", "[4, 16]"],
        "correct": "[0, 4]",
        "explanation": "Even numbers under 4 are 0 and 2. 0**2=0, 2**2=4."
    },
    {
        "id": "java_1",
        "skill": "Java",
        "category": "technical",
        "question": "Which OOP principle allows a subclass to provide a specific implementation of a method already provided by its superclass in Java?",
        "options": ["Encapsulation", "Method Overriding (Polymorphism)", "Abstraction", "Interface Segregation"],
        "correct": "Method Overriding (Polymorphism)",
        "explanation": "Method overriding allows runtime polymorphism in Java."
    },
    {
        "id": "sql_1",
        "skill": "SQL",
        "category": "technical",
        "question": "Which SQL clause is used to filter aggregated grouped records (after GROUP BY)?",
        "options": ["WHERE", "HAVING", "LIMIT", "ORDER BY"],
        "correct": "HAVING",
        "explanation": "HAVING filters groups created by GROUP BY; WHERE filters individual rows before grouping."
    },
    {
        "id": "sql_2",
        "skill": "SQL",
        "category": "technical",
        "question": "What type of JOIN returns all records from the left table and matched records from the right table, filling nulls if no match?",
        "options": ["INNER JOIN", "CROSS JOIN", "LEFT JOIN", "RIGHT JOIN"],
        "correct": "LEFT JOIN",
        "explanation": "LEFT JOIN includes all rows from the left table regardless of right table matches."
    },
    {
        "id": "ml_1",
        "skill": "Machine Learning",
        "category": "technical",
        "question": "Which machine learning problem involves predicting a continuous target variable from input features?",
        "options": ["Classification", "Clustering", "Regression", "Dimensionality Reduction"],
        "correct": "Regression",
        "explanation": "Regression models predict continuous numerical quantities."
    },
    {
        "id": "ml_2",
        "skill": "Machine Learning",
        "category": "technical",
        "question": "Which metric is most appropriate for evaluating a binary classification model on a heavily imbalanced dataset?",
        "options": ["Accuracy", "F1-Score / PR-AUC", "Mean Squared Error", "R-squared"],
        "correct": "F1-Score / PR-AUC",
        "explanation": "Accuracy is misleading for imbalanced classes; F1-score balances Precision and Recall."
    },
    {
        "id": "ds_1",
        "skill": "Data Structures",
        "category": "technical",
        "question": "What is the average time complexity for searching an element in a balanced Binary Search Tree (AVL or Red-Black)?",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
        "correct": "O(log n)",
        "explanation": "Balanced BSTs divide search space by half at each level, giving O(log n)."
    },
    {
        "id": "git_1",
        "skill": "Git",
        "category": "technical",
        "question": "Which Git command integrates changes from another branch into your current active branch?",
        "options": ["git fetch", "git merge", "git commit", "git push"],
        "correct": "git merge",
        "explanation": "git merge combines histories of the target branch into the current one."
    },
    {
        "id": "comm_1",
        "skill": "Communication",
        "category": "soft",
        "question": "When presenting technical findings to non-technical stakeholders, what is the best practice?",
        "options": [
            "Use deep mathematical formulas to establish credibility",
            "Focus on business impact, actionable insights, and clear visuals",
            "Send raw database dumps and allow them to draw their own conclusions",
            "Avoid sharing any data until the entire project is completed"
        ],
        "correct": "Focus on business impact, actionable insights, and clear visuals",
        "explanation": "Effective communication translates technical complexity into business value."
    },
    {
        "id": "ps_1",
        "skill": "Problem Solving",
        "category": "soft",
        "question": "When faced with an unexpected production system failure, what is the first logical step?",
        "options": [
            "Rewrite the entire application codebase from scratch",
            "Triage the impact, isolate the error through logs, and formulate a reproducible test case",
            "Blame previous team members and wait for escalation",
            "Randomly restart servers until it starts working"
        ],
        "correct": "Triage the impact, isolate the error through logs, and formulate a reproducible test case",
        "explanation": "Systematic root cause analysis and impact containment is the core of engineering problem solving."
    },
    {
        "id": "team_1",
        "skill": "Teamwork",
        "category": "soft",
        "question": "In an Agile sprint, a teammate is blocked by an API dependency you manage. How should you respond?",
        "options": [
            "Ignore them until the end of the sprint review",
            "Prioritize unblocking your teammate or provide an agreed mock/contract interface",
            "Ask them to work on something unrelated",
            "Report them to the manager for delay"
        ],
        "correct": "Prioritize unblocking your teammate or provide an agreed mock/contract interface",
        "explanation": "Collaborative velocity and unblocking team members is key to agile teamwork."
    }
]

# Additional comprehensive skill rating bank
ASSESSMENT_DOMAINS = {
    "Programming & Core Tech": [
        ("Python", "Python programming, scripting, OOP, libraries", "technical"),
        ("Java", "Java core, OOP, multithreading, Spring basics", "technical"),
        ("SQL", "Relational database querying, joins, aggregations", "technical"),
        ("Data Structures", "Arrays, linked lists, trees, graphs, hash maps", "technical"),
        ("Git", "Version control, branching, merge conflicts, pull requests", "technical"),
    ],
    "Data Science & AI": [
        ("Machine Learning", "Supervised/unsupervised models, scikit-learn", "technical"),
        ("Statistics", "Probability distributions, hypothesis testing", "technical"),
        ("Data Visualization", "Plotly, Matplotlib, dashboarding, visual storytelling", "technical"),
        ("Deep Learning", "Neural networks, PyTorch, TensorFlow", "technical"),
        ("Excel", "Advanced formulas, PivotTables, VLOOKUP/XLOOKUP", "technical"),
    ],
    "Soft Skills & Leadership": [
        ("Communication", "Clear verbal and written technical explanations", "soft"),
        ("Problem Solving", "Analytical reasoning, root-cause diagnosis", "soft"),
        ("Teamwork", "Cross-functional collaboration, code reviews", "soft"),
        ("Leadership", "Project ownership, mentoring, initiative", "soft"),
        ("Time Management", "Prioritization, meeting deadlines, sprint planning", "soft"),
    ],
    "Systems & Cloud": [
        ("Linux", "Shell navigation, bash scripting, permissions", "technical"),
        ("Networking", "TCP/IP, HTTP/HTTPS, DNS, routing concepts", "technical"),
        ("Docker", "Containerization, Dockerfiles, compose", "technical"),
        ("AWS", "Cloud compute, storage, IAM, serverless basics", "technical"),
        ("Cybersecurity", "Authentication, encryption, vulnerability awareness", "technical"),
    ]
}


def calculate_quiz_scores(answers: Dict[str, str]) -> Tuple[Dict[str, float], int, int]:
    """
    Grade submitted quiz answers and map to skill scores (1 to 5 scale).
    Returns (skill_scores, correct_count, total_count).
    """
    total = len(QUIZ_QUESTIONS)
    correct_count = 0
    skill_results = {}  # skill -> [is_correct, is_correct]

    for q in QUIZ_QUESTIONS:
        qid = q["id"]
        skill = q["skill"]
        user_ans = answers.get(qid)
        is_corr = (user_ans == q["correct"])
        if is_corr:
            correct_count += 1
        skill_results.setdefault(skill, []).append(is_corr)

    # Convert correctness to 1-5 proficiency scale
    # 100% correct = 5, partial = 3.5, 0% = 2.0
    scores = {}
    for skill, bools in skill_results.items():
        ratio = sum(bools) / len(bools)
        proficiency = 2.0 + (ratio * 3.0)  # Maps 0.0 -> 2.0, 1.0 -> 5.0
        scores[skill] = round(proficiency, 1)

    return scores, correct_count, total


def save_assessment(student_id: int, scores: Dict[str, float], skill_types: Optional[Dict[str, str]] = None):
    """
    Save or update skill assessment scores in the database,
    AND immediately update the student's skill profile in student_skills!
    """
    # 1. Save to skill_assessments
    execute_query("DELETE FROM skill_assessments WHERE student_id = ?", (student_id,))
    sql_assess = "INSERT INTO skill_assessments (student_id, skill_name, score) VALUES (?, ?, ?)"
    data_assess = [(student_id, skill, float(score)) for skill, score in scores.items()]
    execute_many(sql_assess, data_assess)

    # 2. Sync to student_skills immediately
    soft_names = {"communication", "problem solving", "teamwork", "leadership", "time management", "creativity"}
    skills_to_save = []
    for skill, score in scores.items():
        stype = "soft" if skill.lower() in soft_names else "technical"
        if skill_types and skill in skill_types:
            stype = skill_types[skill]
        prof_int = max(1, min(5, int(round(score))))
        skills_to_save.append({
            "skill_name": skill,
            "skill_type": stype,
            "proficiency": prof_int
        })

    from modules.student_registration import save_student_skills
    save_student_skills(student_id, skills_to_save)


def get_assessment(student_id: int) -> Dict[str, float]:
    """Retrieve assessment scores for a student."""
    rows = execute_query(
        "SELECT skill_name, score FROM skill_assessments WHERE student_id = ?",
        (student_id,),
        fetch="all",
    )
    if not rows:
        return {}
    return {r["skill_name"]: float(r["score"]) for r in rows}


def get_proficiency_label(score: float) -> str:
    if score >= 4.5:
        return "Expert"
    elif score >= 3.5:
        return "Advanced"
    elif score >= 2.5:
        return "Intermediate"
    elif score >= 1.5:
        return "Beginner"
    else:
        return "Novice"


def get_strong_skills(scores: Dict[str, float], threshold: float = 3.5) -> List[str]:
    return [skill for skill, score in scores.items() if score >= threshold]


def get_weak_skills(scores: Dict[str, float], threshold: float = 2.5) -> List[str]:
    return [skill for skill, score in scores.items() if score < threshold]
