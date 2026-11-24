"""
Page 9 – Dataset Information
"""

import streamlit as st
import os, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.db_setup import setup_database
setup_database()

css_path = os.path.join(ROOT, "assets", "styles", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from ml.data_preprocessing import load_or_create_processed_data, get_sample_dataframe

st.markdown("# 🗄️ Dataset Information")
st.markdown("Details about the occupational data powering SkillMatch.")
st.markdown("---")

# ── Source info ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1A2332,#1E3048); border:1px solid #1E88E5;
            border-radius:12px; padding:1.5rem; margin-bottom:1.5rem;">
    <h2 style="color:white; margin:0;">📊 O*NET Occupational Information Network</h2>
    <p style="color:#90CAF9; margin:0.5rem 0 0 0;">
        Primary data source for all career and skill information.
    </p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **Source Details**
    | Field | Value |
    |-------|-------|
    | Provider | U.S. Department of Labor |
    | Database | O*NET OnLine |
    | License | Public Domain |
    | Version | O*NET 28.1 |
    | Occupations | 900+ |
    """)

with col2:
    st.markdown("""
    **Tables Used**
    | Table | Purpose |
    |-------|---------|
    | Occupation Data | Career titles & descriptions |
    | Skills | Required skills per occupation |
    | Knowledge | Knowledge domain ratings |
    | Abilities | Ability ratings |
    """)

st.markdown("---")

# ── Current dataset ───────────────────────────────────────────────────────────
df, source = load_or_create_processed_data()

source_color = "#2E7D32" if source == "onet" else "#F57F17"
source_label = "✅ O*NET Official Database" if source == "onet" else "⚠️ Built-in Sample Dataset (O*NET-based)"

st.markdown(f"""
<div style="background:#1A2332; border-left:4px solid {source_color}; border-radius:8px; padding:1rem 1.5rem;">
    <h3 style="color:white; margin:0;">Active Dataset: {source_label}</h3>
    <p style="color:#90CAF9; margin:0.3rem 0 0 0;">
        {len(df)} career profiles loaded | {df['category'].nunique() if 'category' in df.columns else 'N/A'} categories
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Stats ─────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📋 Career Profiles", len(df))
with col2:
    st.metric("📂 Categories", df["category"].nunique() if "category" in df.columns else "N/A")
with col3:
    avg_skills = df["skills_list"].apply(lambda x: len(str(x).split(","))).mean()
    st.metric("⚙️ Avg Skills/Career", f"{avg_skills:.1f}")

# ── Category breakdown ────────────────────────────────────────────────────────
if "category" in df.columns:
    st.markdown("### 📂 Career Categories")
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    st.dataframe(cat_counts, use_container_width=True)

# ── Preview ───────────────────────────────────────────────────────────────────
st.markdown("### 👀 Dataset Preview")
display_df = df[["career_title", "category", "onet_code", "description"]].head(20)
st.dataframe(display_df, use_container_width=True)

# ── Skills explorer ───────────────────────────────────────────────────────────
st.markdown("### 🔍 Explore Skills for a Career")
career_sel = st.selectbox("Select a career", df["career_title"].tolist())
row = df[df["career_title"] == career_sel].iloc[0]

st.markdown(f"**Description:** {row.get('description', 'N/A')}")
st.markdown(f"**O\\*NET Code:** `{row.get('onet_code', 'N/A')}`")
st.markdown(f"**Category:** {row.get('category', 'N/A')}")
st.markdown("**Required Skills:**")
skills = [s.strip() for s in str(row.get("skills_list", "")).split(",") if s.strip()]
cols = st.columns(4)
for i, sk in enumerate(skills):
    cols[i % 4].markdown(f"<span style='background:#1565C0; color:white; padding:0.2rem 0.5rem; "
                          f"border-radius:12px; font-size:0.8rem; display:inline-block; margin:2px;'>{sk}</span>",
                          unsafe_allow_html=True)

# ── Upload custom dataset ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📂 Upload Your Own Dataset")
st.info("""
Upload a CSV with columns: **career_title**, **skills_list**, **description** (optional), **category** (optional).

The skills_list column should be comma-separated skills, e.g.:  
`Python, SQL, Machine Learning, Communication`
""")

uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded:
    try:
        custom_df = pd.read_csv(uploaded)
        required_cols = {"career_title", "skills_list"}
        if not required_cols.issubset(custom_df.columns):
            st.error(f"CSV must contain columns: {required_cols}. Found: {list(custom_df.columns)}")
        else:
            if "description" not in custom_df.columns:
                custom_df["description"] = "No description provided."
            if "category" not in custom_df.columns:
                custom_df["category"] = "Custom"
            if "onet_code" not in custom_df.columns:
                custom_df["onet_code"] = "CUSTOM"
            custom_df["skills_text"] = custom_df["skills_list"].apply(
                lambda x: " ".join(s.strip().lower().replace(" ", "_") for s in str(x).split(","))
            )

            processed_path = os.path.join(ROOT, "data", "processed", "cleaned_career_skills.csv")
            custom_df.to_csv(processed_path, index=False)

            # Reset recommender
            import ml.recommendation_model as rm
            rm._recommender = None

            st.success(f"✅ Custom dataset loaded! {len(custom_df)} careers imported.")
            st.dataframe(custom_df[["career_title", "category", "skills_list"]].head(10), use_container_width=True)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")

# ── Citation ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
### 📖 Citation
> National Center for O*NET Development. (2024). *O*NET 28.1 Database*.  
> O*NET Resource Center. U.S. Department of Labor.  
> Retrieved from [https://www.onetcenter.org/database.html](https://www.onetcenter.org/database.html)
""")
