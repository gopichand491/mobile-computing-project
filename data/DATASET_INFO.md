# Dataset Information – SkillMatch

## Primary Dataset: O*NET Occupational Information Network

| Field | Details |
|-------|---------|
| **Source** | U.S. Department of Labor / Employment and Training Administration |
| **Database** | O*NET OnLine |
| **URL** | https://www.onetcenter.org/database.html |
| **License** | Public domain – U.S. Government works are not subject to copyright |
| **Format** | Excel / CSV (downloadable as zip archive) |
| **Version** | O*NET 28.1 Database |
| **Update Frequency** | Annually |

## Tables Used

| Table | Filename | Contents |
|-------|----------|---------|
| Occupation Data | Occupation Data.xlsx | O*NET-SOC code, Title, Description |
| Skills | Skills.xlsx | Skill names and importance/level ratings per occupation |
| Knowledge | Knowledge.xlsx | Knowledge domain ratings per occupation |
| Abilities | Abilities.xlsx | Ability ratings per occupation |

## Processed Output

After preprocessing (see `ml/data_preprocessing.py`), the data is saved to:

```
data/processed/cleaned_career_skills.csv
```

Columns:
- `career_title` – occupation name
- `onet_code` – O*NET-SOC identifier
- `description` – occupation description
- `skills_text` – space-separated normalized skill names
- `skills_list` – comma-separated skill names
- `category` – broad occupational category

## Fallback Sample Dataset

If O*NET cannot be fetched (no network, rate limit, etc.), the system uses a built-in sample dataset covering **50+ careers** across:

- Technology & IT
- Data Science & Analytics
- Business & Management
- Healthcare
- Engineering
- Creative & Design
- Education

The sample dataset is **clearly labelled** in the UI. It is a representative, manually curated dataset — not fabricated ML results.

## Data Dictionary

| Column | Type | Description |
|--------|------|-------------|
| career_title | string | Official occupation title |
| onet_code | string | O*NET-SOC code (e.g., 15-1252.00) |
| description | string | Brief occupation description |
| skills_text | string | All skills concatenated for TF-IDF |
| skills_list | string | Comma-separated list of required skills |
| category | string | Broad sector/domain |

## Citation

> National Center for O*NET Development. (2024). O*NET 28.1 Database.  
> O*NET Resource Center. U.S. Department of Labor.  
> Retrieved from https://www.onetcenter.org/database.html
