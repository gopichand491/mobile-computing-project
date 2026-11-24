"""
SkillMatch – Learning Pathway Module
Generates structured multi-level learning roadmaps (Beginner, Intermediate, Advanced)
with verified educational resources and database persistence.
"""

from typing import List, Dict, Optional
from database.db_connection import execute_query, execute_many

"""
SkillMatch – Learning Pathway Module
Generates structured multi-level learning roadmaps (Beginner, Intermediate, Advanced)
with verified educational resources and database persistence.
Supports all O*NET careers dynamically with targeted missing-skill injection.
"""

from typing import List, Dict, Optional, Any
import os
import pandas as pd
from database.db_connection import execute_query, execute_many

# Curated resource links for common technical and soft skills
SKILL_RESOURCES: Dict[str, str] = {
    "python": "https://www.kaggle.com/learn/python",
    "sql": "https://mode.com/sql-tutorial/",
    "git": "https://learngitbranching.js.org/",
    "docker": "https://docs.docker.com/get-started/",
    "kubernetes": "https://kubernetes.io/docs/tutorials/",
    "aws": "https://aws.amazon.com/getting-started/",
    "azure": "https://learn.microsoft.com/en-us/training/azure/",
    "gcp": "https://cloud.google.com/training",
    "linux": "https://linuxcommand.org/",
    "html": "https://developer.mozilla.org/en-US/docs/Learn/HTML",
    "css": "https://developer.mozilla.org/en-US/docs/Learn/CSS",
    "javascript": "https://javascript.info/",
    "typescript": "https://www.typescriptlang.org/docs/",
    "react": "https://react.dev/",
    "node.js": "https://nodejs.org/en/docs/",
    "java": "https://dev.java/learn/",
    "c++": "https://www.learncpp.com/",
    "c#": "https://learn.microsoft.com/en-us/dotnet/csharp/",
    "machine learning": "https://scikit-learn.org/stable/tutorial/index.html",
    "deep learning": "https://www.deeplearning.ai/",
    "data structures": "https://leetcode.com/explore/",
    "algorithms": "https://leetcode.com/explore/",
    "excel": "https://support.microsoft.com/en-us/excel",
    "power bi": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi",
    "tableau": "https://www.tableau.com/learn/training",
    "statistics": "https://www.khanacademy.org/math/statistics-probability",
    "cybersecurity": "https://www.cybrary.it/",
    "network security": "https://www.sans.org/",
    "networking": "https://www.cisco.com/c/en/us/training-events.html",
    "flutter": "https://docs.flutter.dev/get-started",
    "kotlin": "https://kotlinlang.org/docs/home.html",
    "swift": "https://developer.apple.com/swift/",
    "react native": "https://reactnative.dev/docs/getting-started",
    "spark": "https://spark.apache.org/docs/latest/",
    "hadoop": "https://hadoop.apache.org/docs/stable/",
    "kafka": "https://kafka.apache.org/documentation/",
    "airflow": "https://airflow.apache.org/docs/",
    "ci/cd": "https://docs.github.com/en/actions",
    "jenkins": "https://www.jenkins.io/doc/",
    "terraform": "https://developer.hashicorp.com/terraform/tutorials",
    "ansible": "https://docs.ansible.com/",
    "rest apis": "https://fastapi.tiangolo.com/",
    "graphql": "https://graphql.org/learn/",
    "communication": "https://www.coursera.org/learn/wharton-communication-skills",
    "problem solving": "https://leetcode.com/",
    "teamwork": "https://www.linkedin.com/learning/teamwork-foundations",
    "leadership": "https://www.coursera.org/learn/strategic-leadership",
    "agile": "https://www.atlassian.com/agile",
    "scrum": "https://www.scrum.org/resources/what-is-scrum",
    "ui design": "https://www.figma.com/resource-library/",
    "ux design": "https://www.nngroup.com/articles/",
    "penetration testing": "https://www.hackthebox.com/",
    "ethical hacking": "https://www.cybrary.it/",
    "siem": "https://www.splunk.com/en_us/training.html",
    "cryptography": "https://cryptopals.com/",
}


def get_resource_url(topic_or_skill: str) -> str:
    """Return an authoritative educational resource link for a given topic or skill."""
    clean = topic_or_skill.strip().lower()
    for key, url in SKILL_RESOURCES.items():
        if key in clean:
            return url
    return f"https://www.google.com/search?q={topic_or_skill.replace(' ', '+')}+tutorial+documentation"


# Curated 3-tier roadmaps for top technology careers
TIERED_ROADMAPS: Dict[str, Dict[str, List[Dict]]] = {
    "Data Analyst": {
        "Beginner": [
            {"step": 1, "topic": "Excel for Data Analysis", "description": "Master formulas, PivotTables, VLOOKUP/XLOOKUP, and essential data cleaning.", "url": "https://support.microsoft.com/en-us/excel"},
            {"step": 2, "topic": "SQL Fundamentals", "description": "Learn SELECT, WHERE, GROUP BY, HAVING, and relational filtering.", "url": "https://mode.com/sql-tutorial/"},
            {"step": 3, "topic": "Python for Data Basics", "description": "Variables, data structures, loops, functions, and working with CSV data.", "url": "https://www.kaggle.com/learn/python"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Advanced SQL & Joins", "description": "Multi-table INNER/LEFT/FULL JOINs, subqueries, and window functions.", "url": "https://www.sqlzoo.net/"},
            {"step": 5, "topic": "Pandas & Data Wrangling", "description": "Dataframe manipulation, handling missing data, grouping, and aggregations.", "url": "https://www.kaggle.com/learn/pandas"},
            {"step": 6, "topic": "Business Intelligence (Power BI / Tableau)", "description": "Building interactive executive dashboards and KPI visualizations.", "url": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi"},
        ],
        "Advanced": [
            {"step": 7, "topic": "Applied Statistics & A/B Testing", "description": "Hypothesis testing, confidence intervals, p-values, and experimentation.", "url": "https://www.khanacademy.org/math/statistics-probability"},
            {"step": 8, "topic": "End-to-End Analytics Capstone", "description": "Build, document, and present a complete business data analysis project on GitHub.", "url": "https://www.kaggle.com/competitions"},
        ],
    },
    "Data Scientist": {
        "Beginner": [
            {"step": 1, "topic": "Python & Scientific Computing", "description": "NumPy array operations, vectorized calculations, and Pandas foundations.", "url": "https://numpy.org/doc/stable/user/absolute_beginners.html"},
            {"step": 2, "topic": "Probability & Applied Statistics", "description": "Bayes theorem, random variables, central limit theorem, and distributions.", "url": "https://www.khanacademy.org/math/statistics-probability"},
            {"step": 3, "topic": "Exploratory Data Analysis (EDA)", "description": "Feature distributions, correlation matrices, outlier detection, and Plotly visualization.", "url": "https://www.kaggle.com/learn/data-visualization"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Supervised & Unsupervised ML", "description": "Regression, Decision Trees, Random Forests, XGBoost, and K-Means clustering.", "url": "https://scikit-learn.org/stable/tutorial/index.html"},
            {"step": 5, "topic": "Feature Engineering & Cross-Validation", "description": "Target encoding, scaling, imputation pipelines, and stratified K-fold validation.", "url": "https://www.kaggle.com/learn/feature-engineering"},
            {"step": 6, "topic": "Relational & NoSQL Databases", "description": "Complex SQL queries, database indexing, and query optimization.", "url": "https://mode.com/sql-tutorial/"},
        ],
        "Advanced": [
            {"step": 7, "topic": "Deep Learning & Neural Networks", "description": "Feedforward networks, CNNs, Transformers using PyTorch or TensorFlow.", "url": "https://www.deeplearning.ai/"},
            {"step": 8, "topic": "Production ML & Model Deployment", "description": "Serving models via FastAPI, Docker containerization, and monitoring.", "url": "https://mlops.community/"},
        ],
    },
    "Software Developer": {
        "Beginner": [
            {"step": 1, "topic": "Core Programming (Python or Java)", "description": "Variables, control flow, functions, collections, and modular design.", "url": "https://realpython.com/"},
            {"step": 2, "topic": "Object-Oriented Programming (OOP)", "description": "Classes, encapsulation, inheritance, polymorphism, and abstraction.", "url": "https://refactoring.guru/design-patterns"},
            {"step": 3, "topic": "Git Version Control", "description": "Commits, branching strategies, merge conflicts, pull requests, and GitHub.", "url": "https://learngitbranching.js.org/"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Data Structures & Algorithms", "description": "Linked lists, stacks, queues, trees, sorting algorithms, and complexity analysis.", "url": "https://leetcode.com/"},
            {"step": 5, "topic": "Database Design & SQL", "description": "Normalized database schema design, ACID principles, indexing, and queries.", "url": "https://www.sqlzoo.net/"},
            {"step": 6, "topic": "RESTful API Engineering", "description": "Building and consuming REST endpoints, JSON validation, status codes, and security.", "url": "https://fastapi.tiangolo.com/"},
        ],
        "Advanced": [
            {"step": 7, "topic": "Automated Testing & CI/CD", "description": "Unit testing with PyTest/JUnit, mocking, integration tests, and GitHub Actions.", "url": "https://docs.pytest.org/"},
            {"step": 8, "topic": "Microservices & Distributed Systems", "description": "System architecture, caching (Redis), message queues, and cloud deployment.", "url": "https://microservices.io/"},
        ],
    },
    "Machine Learning Engineer": {
        "Beginner": [
            {"step": 1, "topic": "Python for High Performance ML", "description": "NumPy vectorized operations, OOP Python, and memory profiling.", "url": "https://realpython.com/"},
            {"step": 2, "topic": "Linear Algebra & Calculus for ML", "description": "Matrices, eigenvalues, vector spaces, gradient descent, and partial derivatives.", "url": "https://www.3blue1brown.com/"},
            {"step": 3, "topic": "Core Machine Learning Algorithms", "description": "Loss functions, regularization (L1/L2), gradient boosting, and evaluation metrics.", "url": "https://www.coursera.org/learn/machine-learning"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Deep Learning Architectures", "description": "PyTorch tensors, autograd, backpropagation, CNNs, and sequence models.", "url": "https://pytorch.org/tutorials/"},
            {"step": 5, "topic": "Docker & Containerized Environments", "description": "Writing Dockerfiles, managing container dependencies, and reproducibility.", "url": "https://docs.docker.com/"},
            {"step": 6, "topic": "Model Optimization & Quantization", "description": "ONNX runtime, TensorRT, pruning, mixed precision, and hyperparameter tuning.", "url": "https://optuna.org/"},
        ],
        "Advanced": [
            {"step": 7, "topic": "MLOps Pipelines & Feature Stores", "description": "Automated training pipelines, data validation, experiment tracking with MLflow.", "url": "https://mlflow.org/"},
            {"step": 8, "topic": "Cloud Scaled Inference (AWS/GCP)", "description": "Deploying scalable low-latency inference services with auto-scaling.", "url": "https://aws.amazon.com/sagemaker/"},
        ],
    },
    "Web Developer": {
        "Beginner": [
            {"step": 1, "topic": "HTML5 & Modern CSS3", "description": "Semantic markup, Flexbox, CSS Grid, media queries, and responsive layouts.", "url": "https://developer.mozilla.org/"},
            {"step": 2, "topic": "JavaScript Essentials", "description": "ES6+ syntax, DOM manipulation, promises, async/await, and fetch API.", "url": "https://javascript.info/"},
            {"step": 3, "topic": "Git & Web Workflows", "description": "Version control, npm package management, and browser developer tools.", "url": "https://learngitbranching.js.org/"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Frontend Framework (React / Vue)", "description": "State management, component hooks, lifecycle, routing, and virtual DOM.", "url": "https://react.dev/"},
            {"step": 5, "topic": "Backend Server (Node.js / Express)", "description": "HTTP request handling, middleware, REST routes, and JWT authentication.", "url": "https://nodejs.org/"},
            {"step": 6, "topic": "Database Integration (SQL / MongoDB)", "description": "CRUD operations, ORMs/ODMs, schema validation, and database migrations.", "url": "https://www.mongodb.com/university"},
        ],
        "Advanced": [
            {"step": 7, "topic": "Full-Stack Security & Performance", "description": "CORS, CSRF, XSS prevention, lazy loading, caching, and Lighthouse audits.", "url": "https://owasp.org/www-project-top-ten/"},
            {"step": 8, "topic": "Full-Stack Production Deployment", "description": "Dockerizing web apps, setting up CI/CD pipelines, and cloud hosting.", "url": "https://vercel.com/"},
        ],
    },
    "Cybersecurity Analyst": {
        "Beginner": [
            {"step": 1, "topic": "Computer Networking & Protocols", "description": "OSI 7-layer model, TCP/IP, DNS, DHCP, subnetting, and packet structures.", "url": "https://www.cisco.com/"},
            {"step": 2, "topic": "Linux Administration & Bash", "description": "File permissions, processes, system logging (syslog), and shell scripting.", "url": "https://linuxcommand.org/"},
            {"step": 3, "topic": "Cybersecurity Fundamentals", "description": "CIA triad, threat modeling, security hygiene, and attack surfaces.", "url": "https://www.cybrary.it/"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Vulnerability Assessment & Scanners", "description": "Network scanning with Nmap, Wireshark packet capture, and vulnerability scanners.", "url": "https://www.wireshark.org/"},
            {"step": 5, "topic": "Applied Cryptography & PKI", "description": "Symmetric vs asymmetric encryption, hashing, digital signatures, and SSL/TLS.", "url": "https://cryptopals.com/"},
            {"step": 6, "topic": "SIEM & Security Monitoring", "description": "Log correlation, anomaly detection, alert rules, and threat hunting.", "url": "https://www.splunk.com/"},
        ],
        "Advanced": [
            {"step": 7, "topic": "Incident Response & Forensics", "description": "Containment strategies, evidence preservation, memory dumps, and post-mortems.", "url": "https://www.sans.org/"},
            {"step": 8, "topic": "Penetration Testing & Security Audit", "description": "OWASP Top 10 web vulnerabilities, ethical exploitation, and formal reporting.", "url": "https://www.hackthebox.com/"},
        ],
    },
    "Mobile App Developer": {
        "Beginner": [
            {"step": 1, "topic": "Mobile Foundations (Kotlin / Swift)", "description": "Core mobile programming syntax, mobile OS architectures, and SDK setup.", "url": "https://kotlinlang.org/docs/home.html"},
            {"step": 2, "topic": "Mobile UI/UX & Layout Systems", "description": "Constraint layouts, flex layouts, responsive widgets, and touch gestures.", "url": "https://developer.android.com/guide/topics/ui"},
            {"step": 3, "topic": "Version Control & Mobile Git", "description": "Branching, asset management, and collaboration on GitHub.", "url": "https://learngitbranching.js.org/"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Cross-Platform Framework (Flutter / React Native)", "description": "State management, navigation stacks, asynchronous hooks, and platform channels.", "url": "https://docs.flutter.dev/get-started"},
            {"step": 5, "topic": "REST APIs & Local Storage (SQLite / Room)", "description": "Consuming JSON APIs, offline caching, ORM entities, and sync strategies.", "url": "https://developer.android.com/training/data-storage/room"},
            {"step": 6, "topic": "Firebase & Push Notifications", "description": "Cloud Firestore, user authentication, FCM notifications, and crash analytics.", "url": "https://firebase.google.com/docs"},
        ],
        "Advanced": [
            {"step": 7, "topic": "Mobile Performance & Security", "description": "Memory leak profiling, secure keystores, certificate pinning, and app bundle optimization.", "url": "https://owasp.org/www-project-mobile-top-10/"},
            {"step": 8, "topic": "App Store Deployment & CI/CD", "description": "Automated builds with Fastlane, signing keys, and Google Play / App Store publishing.", "url": "https://fastlane.tools/"},
        ],
    },
    "DevOps Engineer": {
        "Beginner": [
            {"step": 1, "topic": "Linux Systems Administration & Shell", "description": "Process management, cron jobs, file systems, permissions, and Bash automation.", "url": "https://linuxcommand.org/"},
            {"step": 2, "topic": "Networking Fundamentals & DNS", "description": "TCP/IP, routing, firewalls, reverse proxies (Nginx), and TLS certificates.", "url": "https://www.cisco.com/"},
            {"step": 3, "topic": "Git & Collaborative Workflows", "description": "Git hooks, branching models (Trunk/GitFlow), and repository hygiene.", "url": "https://learngitbranching.js.org/"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Docker Containerization", "description": "Building lightweight multi-stage Dockerfiles, image layers, and docker-compose.", "url": "https://docs.docker.com/"},
            {"step": 5, "topic": "CI/CD Pipelines (GitHub Actions / Jenkins)", "description": "Automated build, test, lint, and deploy workflows with environment secrets.", "url": "https://docs.github.com/en/actions"},
            {"step": 6, "topic": "Infrastructure as Code (Terraform)", "description": "Declarative cloud provisioning, state management, and reusable modules.", "url": "https://developer.hashicorp.com/terraform"},
        ],
        "Advanced": [
            {"step": 7, "topic": "Kubernetes Orchestration", "description": "Pods, Deployments, Services, Ingress controllers, Helm charts, and cluster scaling.", "url": "https://kubernetes.io/docs/tutorials/"},
            {"step": 8, "topic": "Observability & SRE (Prometheus & Grafana)", "description": "Metrics scraping, alerting rules, distributed tracing, and SLA/SLO engineering.", "url": "https://prometheus.io/docs/introduction/overview/"},
        ],
    },
    "Cloud Architect": {
        "Beginner": [
            {"step": 1, "topic": "Cloud Computing Fundamentals", "description": "IaaS, PaaS, SaaS concepts, cloud economics, availability zones, and regions.", "url": "https://aws.amazon.com/getting-started/"},
            {"step": 2, "topic": "Networking in the Cloud (VPC)", "description": "Subnets, route tables, internet gateways, NAT, and security groups.", "url": "https://docs.aws.amazon.com/vpc/"},
            {"step": 3, "topic": "Identity & Access Management (IAM)", "description": "Principle of least privilege, roles, policies, MFA, and SSO federation.", "url": "https://docs.aws.amazon.com/iam/"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Compute & Storage Architectures", "description": "EC2 auto-scaling, serverless functions (Lambda), S3 storage classes, and block volumes.", "url": "https://aws.amazon.com/architecture/"},
            {"step": 5, "topic": "Database & Caching Services", "description": "Managed relational databases (RDS/Aurora), NoSQL (DynamoDB), and ElastiCache.", "url": "https://aws.amazon.com/products/databases/"},
            {"step": 6, "topic": "Infrastructure as Code & Automation", "description": "Terraform and CloudFormation for reproducible multi-region architectures.", "url": "https://developer.hashicorp.com/terraform"},
        ],
        "Advanced": [
            {"step": 7, "topic": "High Availability & Disaster Recovery", "description": "Multi-region failover, RPO/RTO optimization, load balancing, and chaos testing.", "url": "https://aws.amazon.com/well-architected/"},
            {"step": 8, "topic": "Cloud Security, Compliance & FinOps", "description": "Cloud security posture management, encryption at rest/transit, and cost governance.", "url": "https://www.finops.org/"},
        ],
    },
    "Database Administrator": {
        "Beginner": [
            {"step": 1, "topic": "Relational Theory & SQL Mastery", "description": "DDL, DML, relational integrity, constraints, joins, and aggregations.", "url": "https://mode.com/sql-tutorial/"},
            {"step": 2, "topic": "Database Architecture & Storage Engines", "description": "Pages, buffers, WAL, transaction logs, and InnoDB/PostgreSQL storage architectures.", "url": "https://www.postgresql.org/docs/"},
            {"step": 3, "topic": "Data Modeling & Normalization", "description": "1NF through 3NF/BCNF normalization, ER diagrams, and entity relationships.", "url": "https://www.sqlzoo.net/"},
        ],
        "Intermediate": [
            {"step": 4, "topic": "Indexing Strategies & Query Optimization", "description": "B-Tree, Hash, GIN indexes, EXPLAIN plan analysis, and query tuning.", "url": "https://use-the-index-luke.com/"},
            {"step": 5, "topic": "Backup, Recovery & Point-in-Time Restore", "description": "Full, differential, and transaction log backups, PITR recovery simulations.", "url": "https://www.postgresql.org/docs/current/backup.html"},
            {"step": 6, "topic": "Database Security, Roles & Auditing", "description": "Role-based access control, column-level encryption, SSL connections, and audit logging.", "url": "https://dev.mysql.com/doc/refman/8.0/en/security.html"},
        ],
        "Advanced": [
            {"step": 7, "topic": "High Availability & Replication", "description": "Primary-replica streaming replication, failover clustering, and connection pooling.", "url": "https://www.postgresql.org/docs/current/high-availability.html"},
            {"step": 8, "topic": "Database Sharding & Distributed DBs", "description": "Horizontal partitioning, Vitess/Citus sharding, and NoSQL hybrid architectures.", "url": "https://martinfowler.com/articles/patterns-of-distributed-systems/"},
        ],
    },
}

GENERIC_ROADMAP_TEMPLATE = {
    "Beginner": [
        {"step": 1, "topic": "Foundations & Prerequisites", "description": "Core terminology, domain principles, and fundamental industry concepts.", "url": "https://www.coursera.org/"},
        {"step": 2, "topic": "Basic Tooling & Environment", "description": "Setting up professional development environment and standard toolsets.", "url": "https://github.com/"},
    ],
    "Intermediate": [
        {"step": 3, "topic": "Core Technical Skills Mastery", "description": "Practical application of required technologies through structured exercises.", "url": "https://www.udemy.com/"},
        {"step": 4, "topic": "Frameworks & Standards", "description": "Adopting industry best practices, architectural design patterns, and workflows.", "url": "https://www.kaggle.com/"},
        {"step": 5, "topic": "Professional Soft Skills", "description": "Technical documentation, stakeholder presentation, and team collaboration.", "url": "https://www.linkedin.com/learning/"},
    ],
    "Advanced": [
        {"step": 6, "topic": "Industry Certification Prep", "description": "Validating competencies through recognized credentials and exams.", "url": "https://www.credly.com/"},
        {"step": 7, "topic": "Comprehensive Capstone Project", "description": "Designing and building a real-world, production-ready portfolio project.", "url": "https://github.com/"},
    ],
}


def _get_career_required_skills(career_title: str) -> List[str]:
    """Look up required skills for a career from cleaned_career_skills.csv or return defaults."""
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed", "cleaned_career_skills.csv")
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, encoding="utf-8")
            match = df[df["career_title"].str.strip().str.lower() == career_title.strip().lower()]
            if not match.empty:
                raw = str(match.iloc[0]["skills_list"])
                return [s.strip() for s in raw.split(",") if s.strip()]
        except Exception:
            pass
    return []


def generate_dynamic_career_roadmap(career_title: str, required_skills: List[str]) -> Dict[str, List[Dict]]:
    """Dynamically build a 3-tier roadmap for any career from its required skills list."""
    if not required_skills:
        return GENERIC_ROADMAP_TEMPLATE

    # Partition skills
    n = len(required_skills)
    beg_slice = required_skills[:max(2, n // 3)]
    int_slice = required_skills[max(2, n // 3): max(4, (2 * n) // 3)]
    adv_slice = required_skills[max(4, (2 * n) // 3):]

    beg_items = []
    for idx, sk in enumerate(beg_slice, start=1):
        beg_items.append({
            "step": idx,
            "topic": f"Foundations: {sk}",
            "description": f"Master fundamental concepts, syntax, and principles of {sk}.",
            "url": get_resource_url(sk),
        })

    int_items = []
    for idx, sk in enumerate(int_slice, start=len(beg_items) + 1):
        int_items.append({
            "step": idx,
            "topic": f"Core Practice: {sk}",
            "description": f"Build practical hands-on projects and apply {sk} in realistic scenarios.",
            "url": get_resource_url(sk),
        })

    adv_items = []
    for idx, sk in enumerate(adv_slice, start=len(beg_items) + len(int_items) + 1):
        adv_items.append({
            "step": idx,
            "topic": f"Specialization: {sk}",
            "description": f"Advanced patterns, performance tuning, and enterprise applications of {sk}.",
            "url": get_resource_url(sk),
        })

    # Always ensure a capstone in advanced
    adv_items.append({
        "step": len(beg_items) + len(int_items) + len(adv_items) + 1,
        "topic": f"{career_title} Production Capstone",
        "description": f"Design, document, and publish an end-to-end portfolio project validating your {career_title} competencies.",
        "url": "https://github.com/",
    })

    return {
        "Beginner": beg_items,
        "Intermediate": int_items,
        "Advanced": adv_items,
    }


def get_learning_path(career_title: str, missing_skills: Optional[List[str]] = None) -> List[Dict]:
    """
    Return a 3-tier (Beginner, Intermediate, Advanced) learning path for any career.
    Dynamically injects missing skills into the Intermediate tier.
    """
    clean_title = career_title.strip()

    # 1. Match curated roadmap or dynamically generate from required skills
    matched_key = next((k for k in TIERED_ROADMAPS if k.lower() == clean_title.lower()), None)
    if matched_key:
        roadmap = TIERED_ROADMAPS[matched_key]
    else:
        req_skills = _get_career_required_skills(clean_title)
        roadmap = generate_dynamic_career_roadmap(clean_title, req_skills)

    flat_path: List[Dict] = []

    # 1. Beginner Tier
    for item in roadmap.get("Beginner", []):
        it = dict(item)
        it["level"] = "Beginner"
        flat_path.append(it)

    # 2. Intermediate Tier (Dynamically inject student's missing skills here)
    int_items = [dict(x) for x in roadmap.get("Intermediate", [])]
    if missing_skills:
        for idx, skill in enumerate(missing_skills[:3]):
            int_items.insert(idx, {
                "step": 0,
                "topic": f"Targeted Mastery: {skill}",
                "description": f"Bridging detected skill gap: develop competency in {skill} required for {clean_title}.",
                "url": get_resource_url(skill),
            })
    for item in int_items:
        item["level"] = "Intermediate"
        flat_path.append(item)

    # 3. Advanced Tier
    for item in roadmap.get("Advanced", []):
        it = dict(item)
        it["level"] = "Advanced"
        flat_path.append(it)

    # Renumber sequentially
    for i, item in enumerate(flat_path, start=1):
        item["step"] = i

    return flat_path


def save_pathway(student_id: int, career_title: str, path: List[Dict]):
    """Save a learning pathway with level to the database."""
    clean_title = career_title.strip()
    execute_query(
        "DELETE FROM learning_pathways WHERE student_id = ? AND LOWER(TRIM(career_title)) = LOWER(TRIM(?))",
        (student_id, clean_title),
    )
    sql = """
        INSERT INTO learning_pathways (student_id, career_title, level, step_number, topic, description, resource_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    data = [
        (
            student_id,
            clean_title,
            item.get("level", "Beginner"),
            item.get("step", item.get("step_number", idx)),
            item["topic"],
            item.get("description", ""),
            item.get("url", item.get("resource_url", "")),
        )
        for idx, item in enumerate(path, start=1)
    ]
    execute_many(sql, data)


def get_pathway(student_id: int, career_title: str) -> List[Dict]:
    """Retrieve saved pathway from database."""
    clean_title = career_title.strip()
    rows = execute_query(
        """SELECT level, step_number, topic, description, resource_url
           FROM learning_pathways WHERE student_id = ? AND LOWER(TRIM(career_title)) = LOWER(TRIM(?))
           ORDER BY step_number""",
        (student_id, clean_title),
        fetch="all",
    )
    if not rows:
        return []
    result = []
    for r in rows:
        d = dict(r)
        d["step"] = d["step_number"]
        d["url"] = d.get("resource_url", "")
        result.append(d)
    return result
