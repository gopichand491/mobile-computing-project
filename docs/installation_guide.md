# Installation Guide – SkillMatch

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Windows 10/11, macOS, or Linux

## Step 1 – Navigate to Project

```bash
cd path\to\SkillMatch
```

## Step 2 – (Optional) Create Virtual Environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

## Step 3 – Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt includes:**
- streamlit>=1.28.0
- pandas>=2.0.0
- numpy>=1.24.0
- scikit-learn>=1.3.0
- plotly>=5.17.0
- requests>=2.31.0
- openpyxl>=3.1.2

## Step 4 – Run the Application

```bash
streamlit run app.py
```

The application will open at: http://localhost:8501

## Step 5 – First Run

On first run:
1. The SQLite database is automatically created (`database/skillmatch.db`)
2. The sample career dataset is loaded (60+ careers from O*NET)
3. Navigate to **Student Registration** to create your profile

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Port already in use | Run `streamlit run app.py --server.port 8502` |
| Database locked | Delete `database/skillmatch.db` and restart |
| Slow on first load | Normal – TF-IDF model is being fitted |

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```
