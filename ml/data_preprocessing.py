"""
SkillMatch – Data Preprocessing Module
Downloads O*NET data or falls back to the built-in sample dataset.
Produces data/processed/cleaned_career_skills.csv
"""

import os
import io
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
PROCESSED_FILE = os.path.join(PROCESSED_DIR, "cleaned_career_skills.csv")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Built-in sample dataset – 60 careers across 7 domains
# This is the fallback when O*NET cannot be downloaded.
# ---------------------------------------------------------------------------
SAMPLE_CAREERS = [
    # Technology & IT
    {"career_title": "Software Developer", "onet_code": "15-1252.00", "category": "Technology & IT",
     "description": "Research, design, and develop computer software systems.",
     "skills_list": "Python,Java,JavaScript,SQL,Git,Data Structures,Algorithms,Problem Solving,Communication,Teamwork,Object-Oriented Programming,Software Testing,Agile,REST APIs"},
    {"career_title": "Web Developer", "onet_code": "15-1254.00", "category": "Technology & IT",
     "description": "Design and create websites and web applications.",
     "skills_list": "HTML,CSS,JavaScript,React,Node.js,SQL,Git,Responsive Design,Problem Solving,Communication,TypeScript,Bootstrap,REST APIs"},
    {"career_title": "Mobile App Developer", "onet_code": "15-1253.00", "category": "Technology & IT",
     "description": "Design and build mobile applications for Android and iOS.",
     "skills_list": "Java,Kotlin,Swift,Flutter,React Native,SQL,Git,Problem Solving,UI Design,Communication,Firebase,REST APIs,Agile"},
    {"career_title": "DevOps Engineer", "onet_code": "15-1244.00", "category": "Technology & IT",
     "description": "Implement and manage CI/CD pipelines and cloud infrastructure.",
     "skills_list": "Linux,Docker,Kubernetes,Jenkins,AWS,Git,Python,Bash,Terraform,Ansible,Problem Solving,Communication,Networking,CI/CD"},
    {"career_title": "Cloud Architect", "onet_code": "15-1299.08", "category": "Technology & IT",
     "description": "Design and manage cloud computing systems.",
     "skills_list": "AWS,Azure,GCP,Docker,Kubernetes,Terraform,Networking,Security,Python,SQL,Communication,Leadership,Problem Solving,Cost Optimization"},
    {"career_title": "Cybersecurity Analyst", "onet_code": "15-1212.00", "category": "Technology & IT",
     "description": "Plan and implement security measures to protect computer systems.",
     "skills_list": "Network Security,Penetration Testing,Firewalls,Linux,Python,Cryptography,Risk Assessment,SQL,SIEM,Incident Response,Problem Solving,Communication,Ethical Hacking"},
    {"career_title": "Network Engineer", "onet_code": "15-1241.00", "category": "Technology & IT",
     "description": "Design and implement computer networks.",
     "skills_list": "Networking,Cisco,TCP/IP,Routing,Switching,Firewalls,Linux,Python,Troubleshooting,Communication,CCNA,Network Security,VPN"},
    {"career_title": "Systems Administrator", "onet_code": "15-1244.00", "category": "Technology & IT",
     "description": "Install, configure, and maintain computer systems and servers.",
     "skills_list": "Linux,Windows Server,Active Directory,Networking,Python,Bash,Troubleshooting,SQL,Virtualization,Backup,Communication,Problem Solving"},
    {"career_title": "IT Support Specialist", "onet_code": "15-1232.00", "category": "Technology & IT",
     "description": "Provide technical assistance and support for computer systems.",
     "skills_list": "Troubleshooting,Hardware,Networking,Windows,Customer Service,Communication,SQL,Linux,Problem Solving,Documentation,Helpdesk"},
    {"career_title": "Database Administrator", "onet_code": "15-1242.00", "category": "Technology & IT",
     "description": "Coordinate database design and storage.",
     "skills_list": "SQL,MySQL,PostgreSQL,Oracle,Database Design,Python,Backup,Performance Tuning,Security,Communication,Problem Solving,Stored Procedures"},

    # Data Science & Analytics
    {"career_title": "Data Scientist", "onet_code": "15-2051.00", "category": "Data Science & Analytics",
     "description": "Use statistical and machine learning methods to analyze complex data.",
     "skills_list": "Python,R,Machine Learning,Statistics,SQL,Data Visualization,TensorFlow,Pandas,NumPy,Scikit-learn,Communication,Problem Solving,Big Data,Deep Learning"},
    {"career_title": "Data Analyst", "onet_code": "15-2041.00", "category": "Data Science & Analytics",
     "description": "Collect, process, and analyze data to generate business insights.",
     "skills_list": "SQL,Python,Excel,Power BI,Tableau,Statistics,Data Visualization,Communication,Problem Solving,Pandas,NumPy,R,Storytelling"},
    {"career_title": "Machine Learning Engineer", "onet_code": "15-2051.01", "category": "Data Science & Analytics",
     "description": "Design and build machine learning systems and models.",
     "skills_list": "Python,Machine Learning,Deep Learning,TensorFlow,PyTorch,Scikit-learn,SQL,Docker,Git,Mathematics,Statistics,Communication,Problem Solving,MLOps"},
    {"career_title": "Business Intelligence Analyst", "onet_code": "13-1111.00", "category": "Data Science & Analytics",
     "description": "Analyze data to provide business intelligence and insights.",
     "skills_list": "SQL,Power BI,Tableau,Excel,Python,Data Warehousing,ETL,Communication,Business Analysis,Problem Solving,Data Modeling,Statistics"},
    {"career_title": "Data Engineer", "onet_code": "15-1243.01", "category": "Data Science & Analytics",
     "description": "Build and maintain data pipelines and infrastructure.",
     "skills_list": "Python,SQL,Spark,Hadoop,Airflow,AWS,Docker,ETL,Data Warehousing,Kafka,Communication,Problem Solving,Linux,Scala"},
    {"career_title": "AI Research Scientist", "onet_code": "15-2051.02", "category": "Data Science & Analytics",
     "description": "Conduct research to advance the field of artificial intelligence.",
     "skills_list": "Python,Deep Learning,Machine Learning,Mathematics,Statistics,TensorFlow,PyTorch,Research,Communication,Problem Solving,NLP,Computer Vision,Publications"},
    {"career_title": "Statistician", "onet_code": "15-2041.00", "category": "Data Science & Analytics",
     "description": "Apply statistical theories and methods to collect, analyze, and interpret data.",
     "skills_list": "Statistics,R,Python,SAS,SPSS,Data Analysis,Mathematics,Communication,Problem Solving,Excel,Research,Data Visualization"},

    # Business & Management
    {"career_title": "Project Manager", "onet_code": "11-9199.01", "category": "Business & Management",
     "description": "Plan and coordinate projects to ensure they are completed on time and within budget.",
     "skills_list": "Project Management,Leadership,Communication,MS Project,Agile,Scrum,Risk Management,Budgeting,Teamwork,Problem Solving,Stakeholder Management,Excel,PMP"},
    {"career_title": "Business Analyst", "onet_code": "13-1111.00", "category": "Business & Management",
     "description": "Analyze business needs and recommend solutions.",
     "skills_list": "Business Analysis,SQL,Excel,Communication,Problem Solving,Requirements Gathering,UML,Process Modeling,Stakeholder Management,Agile,JIRA,Documentation"},
    {"career_title": "Product Manager", "onet_code": "11-2021.00", "category": "Business & Management",
     "description": "Define the vision and roadmap for a product.",
     "skills_list": "Product Management,Communication,Leadership,Agile,Data Analysis,Market Research,Stakeholder Management,Problem Solving,SQL,UX Design,Roadmapping"},
    {"career_title": "Marketing Manager", "onet_code": "11-2021.00", "category": "Business & Management",
     "description": "Plan, direct, and coordinate marketing activities.",
     "skills_list": "Marketing,Communication,Data Analysis,SEO,Social Media,Leadership,Creativity,Excel,CRM,Budgeting,Branding,Content Marketing,Problem Solving"},
    {"career_title": "Human Resources Manager", "onet_code": "11-3121.00", "category": "Business & Management",
     "description": "Plan and coordinate HR activities including recruitment and training.",
     "skills_list": "Human Resources,Communication,Leadership,Recruitment,Training,Excel,HRIS,Problem Solving,Employment Law,Conflict Resolution,Organizational Skills,Teamwork"},
    {"career_title": "Financial Analyst", "onet_code": "13-2051.00", "category": "Business & Management",
     "description": "Provide analysis and guidance on investment decisions.",
     "skills_list": "Finance,Excel,Financial Modeling,SQL,Python,Data Analysis,Communication,Problem Solving,Accounting,Forecasting,Bloomberg,Risk Analysis"},
    {"career_title": "Operations Manager", "onet_code": "11-1021.00", "category": "Business & Management",
     "description": "Plan, direct, and coordinate operations within an organization.",
     "skills_list": "Operations Management,Leadership,Communication,Problem Solving,Excel,Supply Chain,Process Improvement,Budgeting,Teamwork,Lean,Six Sigma,Data Analysis"},
    {"career_title": "Supply Chain Manager", "onet_code": "11-3071.00", "category": "Business & Management",
     "description": "Manage and optimize supply chain operations.",
     "skills_list": "Supply Chain,Logistics,Excel,ERP,SQL,Communication,Problem Solving,Leadership,Inventory Management,Data Analysis,Negotiation,SAP"},

    # Healthcare
    {"career_title": "Biomedical Engineer", "onet_code": "17-2031.00", "category": "Healthcare",
     "description": "Design and develop medical devices, equipment, and software.",
     "skills_list": "Biology,Engineering,CAD,MATLAB,Python,Problem Solving,Communication,Research,Medical Devices,Electronics,Teamwork,Data Analysis,Regulatory Affairs"},
    {"career_title": "Health Informatics Specialist", "onet_code": "11-9111.00", "category": "Healthcare",
     "description": "Manage health information systems and data.",
     "skills_list": "Health Informatics,SQL,Data Analysis,Communication,EHR,HL7,Python,Problem Solving,Healthcare,Database Management,Project Management,Teamwork"},
    {"career_title": "Clinical Data Analyst", "onet_code": "15-2041.01", "category": "Healthcare",
     "description": "Collect and analyze data from clinical trials.",
     "skills_list": "Data Analysis,SQL,R,Python,Statistics,Excel,Communication,Problem Solving,SAS,Clinical Research,Regulatory Compliance,Documentation"},
    {"career_title": "Public Health Analyst", "onet_code": "13-1041.00", "category": "Healthcare",
     "description": "Analyze data to improve public health outcomes.",
     "skills_list": "Public Health,Epidemiology,Statistics,R,Python,Data Analysis,Communication,Research,Excel,SAS,Problem Solving,Policy Analysis"},

    # Engineering
    {"career_title": "Mechanical Engineer", "onet_code": "17-2141.00", "category": "Engineering",
     "description": "Design and analyze mechanical systems.",
     "skills_list": "CAD,SolidWorks,MATLAB,Problem Solving,Mathematics,Communication,Thermodynamics,Fluid Mechanics,Manufacturing,Teamwork,Python,Finite Element Analysis"},
    {"career_title": "Electrical Engineer", "onet_code": "17-2071.00", "category": "Engineering",
     "description": "Design and develop electrical systems.",
     "skills_list": "Circuit Design,MATLAB,VHDL,Embedded Systems,Electronics,Problem Solving,Mathematics,Communication,CAD,Python,Signal Processing,Power Systems"},
    {"career_title": "Civil Engineer", "onet_code": "17-2051.00", "category": "Engineering",
     "description": "Plan, design, and supervise construction projects.",
     "skills_list": "CAD,AutoCAD,Structural Analysis,Problem Solving,Mathematics,Communication,Project Management,Surveying,Construction,Teamwork,STAAD.Pro,Excel"},
    {"career_title": "Electronics Engineer", "onet_code": "17-2072.00", "category": "Engineering",
     "description": "Design and test electronic components and systems.",
     "skills_list": "Circuit Design,PCB Design,MATLAB,Embedded Systems,C,C++,Electronics,Problem Solving,Mathematics,Communication,FPGA,Microcontrollers,Python"},
    {"career_title": "Automation Engineer", "onet_code": "17-2112.00", "category": "Engineering",
     "description": "Design and implement automation systems.",
     "skills_list": "PLC,SCADA,Python,C++,Robotics,Electronics,Problem Solving,Communication,CAD,Industrial Automation,Sensors,Control Systems"},
    {"career_title": "Robotics Engineer", "onet_code": "17-2199.08", "category": "Engineering",
     "description": "Design and build robotic systems.",
     "skills_list": "Robotics,Python,C++,ROS,Electronics,Problem Solving,Mathematics,Communication,CAD,Machine Learning,Computer Vision,Sensors,Control Systems"},
    {"career_title": "Embedded Systems Engineer", "onet_code": "17-2072.01", "category": "Engineering",
     "description": "Design firmware and hardware for embedded systems.",
     "skills_list": "C,C++,Embedded Systems,Microcontrollers,RTOS,Electronics,Problem Solving,Communication,Assembly,Python,IoT,PCB Design"},
    {"career_title": "IoT Engineer", "onet_code": "15-1299.09", "category": "Engineering",
     "description": "Design and develop Internet of Things solutions.",
     "skills_list": "IoT,Python,C,C++,Embedded Systems,MQTT,Cloud,AWS,Networking,Electronics,Problem Solving,Communication,Microcontrollers,Data Analysis"},

    # Creative & Design
    {"career_title": "UX/UI Designer", "onet_code": "27-1021.00", "category": "Creative & Design",
     "description": "Design user experiences and interfaces for digital products.",
     "skills_list": "Figma,Adobe XD,UI Design,UX Research,Prototyping,Wireframing,HTML,CSS,Communication,Creativity,Problem Solving,User Testing,Interaction Design"},
    {"career_title": "Graphic Designer", "onet_code": "27-1024.00", "category": "Creative & Design",
     "description": "Create visual concepts to communicate ideas.",
     "skills_list": "Adobe Photoshop,Adobe Illustrator,Typography,Color Theory,Creativity,Communication,Branding,InDesign,Problem Solving,UI Design,Print Design"},
    {"career_title": "Video Game Developer", "onet_code": "15-1299.14", "category": "Creative & Design",
     "description": "Design and program video games.",
     "skills_list": "Unity,Unreal Engine,C#,C++,Python,Game Design,Problem Solving,Creativity,Communication,Teamwork,3D Modeling,Animation,AI Programming"},
    {"career_title": "Digital Marketing Specialist", "onet_code": "13-1161.01", "category": "Creative & Design",
     "description": "Plan and execute digital marketing campaigns.",
     "skills_list": "SEO,SEM,Social Media,Content Marketing,Data Analysis,Google Analytics,Communication,Creativity,Excel,CRM,Email Marketing,Copywriting"},
    {"career_title": "Content Creator / Technical Writer", "onet_code": "27-3042.00", "category": "Creative & Design",
     "description": "Develop technical documentation and content.",
     "skills_list": "Technical Writing,Communication,Research,MS Word,HTML,Documentation,Problem Solving,Creativity,Proofreading,Content Management,SEO"},

    # Education
    {"career_title": "Computer Science Teacher", "onet_code": "25-1021.00", "category": "Education",
     "description": "Teach computer science concepts at secondary or post-secondary level.",
     "skills_list": "Python,Java,C++,Teaching,Communication,Curriculum Development,Problem Solving,Data Structures,Algorithms,Patience,Mentoring,Leadership"},
    {"career_title": "Corporate Trainer", "onet_code": "13-1151.00", "category": "Education",
     "description": "Design and deliver training programs for organizations.",
     "skills_list": "Training,Communication,Presentation,Leadership,Curriculum Development,Problem Solving,MS Office,LMS,Facilitation,Needs Assessment,Coaching"},
    {"career_title": "E-Learning Developer", "onet_code": "13-1151.00", "category": "Education",
     "description": "Create digital learning content and courses.",
     "skills_list": "Articulate Storyline,LMS,HTML,CSS,JavaScript,Instructional Design,Communication,Creativity,Video Editing,Multimedia,Problem Solving"},

    # Additional popular careers
    {"career_title": "Full Stack Developer", "onet_code": "15-1252.01", "category": "Technology & IT",
     "description": "Develop both front-end and back-end components of web applications.",
     "skills_list": "Python,JavaScript,React,Node.js,SQL,HTML,CSS,Git,REST APIs,Docker,Problem Solving,Communication,TypeScript,MongoDB"},
    {"career_title": "Data Visualization Specialist", "onet_code": "15-2041.02", "category": "Data Science & Analytics",
     "description": "Create compelling visual representations of data.",
     "skills_list": "Python,R,Tableau,Power BI,D3.js,Excel,Data Analysis,Communication,Creativity,Statistics,SQL,Plotly,Storytelling"},
    {"career_title": "Blockchain Developer", "onet_code": "15-1252.02", "category": "Technology & IT",
     "description": "Build decentralized applications on blockchain platforms.",
     "skills_list": "Solidity,JavaScript,Python,Ethereum,Smart Contracts,Cryptography,Web3,Git,Problem Solving,Communication,Node.js,REST APIs"},
    {"career_title": "Quantitative Analyst", "onet_code": "13-2099.01", "category": "Business & Management",
     "description": "Develop mathematical models for financial risk assessment.",
     "skills_list": "Mathematics,Statistics,Python,R,MATLAB,SQL,Financial Modeling,Machine Learning,Problem Solving,Communication,C++,Excel"},
    {"career_title": "Natural Language Processing Engineer", "onet_code": "15-2051.03", "category": "Data Science & Analytics",
     "description": "Build NLP systems for text understanding and generation.",
     "skills_list": "Python,NLP,Machine Learning,Deep Learning,TensorFlow,PyTorch,NLTK,SpaCy,Transformers,SQL,Mathematics,Communication,Problem Solving"},
    {"career_title": "Computer Vision Engineer", "onet_code": "15-2051.04", "category": "Data Science & Analytics",
     "description": "Develop systems that interpret visual information.",
     "skills_list": "Python,OpenCV,Deep Learning,TensorFlow,PyTorch,Computer Vision,Machine Learning,Mathematics,Problem Solving,Communication,C++,CUDA"},
    {"career_title": "Site Reliability Engineer", "onet_code": "15-1244.01", "category": "Technology & IT",
     "description": "Ensure reliability and uptime of large-scale production systems.",
     "skills_list": "Linux,Python,Go,Kubernetes,Docker,AWS,Monitoring,Incident Response,Problem Solving,Communication,Git,CI/CD,Automation"},
    {"career_title": "Penetration Tester", "onet_code": "15-1212.01", "category": "Technology & IT",
     "description": "Ethically hack systems to discover vulnerabilities.",
     "skills_list": "Ethical Hacking,Penetration Testing,Linux,Python,Kali Linux,Network Security,Cryptography,Problem Solving,Communication,Metasploit,Burp Suite,OWASP"},
]


def get_sample_dataframe() -> pd.DataFrame:
    """Return the built-in sample dataset as a DataFrame."""
    df = pd.DataFrame(SAMPLE_CAREERS)
    df["skills_text"] = df["skills_list"].apply(
        lambda x: " ".join(s.strip().lower().replace(" ", "_") for s in x.split(","))
    )
    return df


def normalize_skill(skill: str) -> str:
    """Lowercase and strip a skill name."""
    return skill.strip().lower()


def load_or_create_processed_data() -> tuple[pd.DataFrame, str]:
    """
    Load processed CSV if it exists, otherwise generate from sample.
    Returns (DataFrame, source_label).
    source_label is 'onet' or 'sample'.
    """
    if os.path.exists(PROCESSED_FILE):
        try:
            df = pd.read_csv(PROCESSED_FILE, encoding="utf-8")
            if len(df) > 0:
                return df, "processed"
        except Exception as e:
            logger.warning(f"Could not read processed file: {e}")

    # Generate from sample
    df = get_sample_dataframe()
    df.to_csv(PROCESSED_FILE, index=False, encoding="utf-8")
    return df, "sample"


def build_processed_dataset_from_onet(skills_df: pd.DataFrame, occupations_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build cleaned_career_skills.csv from raw O*NET tables.
    skills_df columns must include: 'O*NET-SOC Code', 'Element Name', 'Title'
    occupations_df columns must include: 'O*NET-SOC Code', 'Title', 'Description'
    """
    # Merge occupation descriptions
    merged = skills_df.merge(
        occupations_df[["O*NET-SOC Code", "Description"]],
        on="O*NET-SOC Code",
        how="left"
    )

    # Group skills per occupation
    grouped = (
        merged.groupby(["O*NET-SOC Code", "Title"])
        .agg(
            description=("Description", "first"),
            skills_list=("Element Name", lambda x: ",".join(sorted(set(x.dropna()))))
        )
        .reset_index()
        .rename(columns={"O*NET-SOC Code": "onet_code", "Title": "career_title"})
    )

    # Build TF-IDF text column
    grouped["skills_text"] = grouped["skills_list"].apply(
        lambda x: " ".join(s.strip().lower().replace(" ", "_") for s in x.split(","))
    )
    grouped["category"] = "O*NET Occupation"

    grouped.to_csv(PROCESSED_FILE, index=False, encoding="utf-8")
    return grouped
