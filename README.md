# Clinical Study Synopsis Generator

A Streamlit application that automates the creation of clinical study synopses by aggregating data from **ClinicalTrials.gov** and **PubMed**.

## Features

- **Automated Synopsis**: Fetches study details using the ClinicalTrials.gov API (NCT ID, title, phase, objectives, methodology, etc.).
- **PubMed Integration**: Searches for relevant published articles and clinical trials.
- **Search History**: Stores all search queries and generated synopses in a **Supabase** database.
- **History Search**: Allows users to filter and view past searches.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/rtdatasci/clinical_synopsis.git
    cd clinical_synopsis
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Set up Supabase:
    - Create a Supabase project.
    - Run the SQL from `supabase_schema.sql` in your Supabase SQL Editor.
    - Create a `.streamlit/secrets.toml` file with your credentials (see `secrets.toml.example`).

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

## Technologies

- Python 3
- Streamlit
- ClinicalTrials.gov API v2
- PubMed Entrez API (Biopython not required, uses direct requests)
- Supabase (PostgreSQL)
