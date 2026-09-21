# ⚽ EPL Data Pipeline & ML Dashboard
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg) ![PostgreSQL](https://img.shields.io/badge/Supabase-3ECF8E.svg) ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF.svg)

A personal project to practice end-to-end data engineering and machine learning deployment. This project automates the collection of English Premier League (EPL) match data (2023-2026), stores it in a cloud database, and visualizes it through an interactive web dashboard with an ML-based match predictor.

## 🏗️ Architecture & Data Flow

```mermaid
graph LR
    A[API-Sports] -->|Extract JSON| B(GitHub Actions)
    B -->|Transform & Clean| C[(Supabase DB)]
    C -->|Query SQL| D[Streamlit Dashboard]
    D -->|Random Forest| E((Live ML Predictor))

Data Pipeline: Python (requests, pandas)

Database: Supabase (PostgreSQL)

Automation: GitHub Actions

Frontend & ML: Streamlit, Scikit-learn (Random Forest Classifier)

💡 Key Features & Engineering Decisions
Automated ETL Pipeline & Failsafe Logic
Built a Python script (main.py) to extract match data from the API-Football, transform the data to include win/draw/loss labels, and load it into Supabase. GitHub Actions runs this script daily. Added robust defensive logic to prevent database overrides during API rate-limit exceedances.

Security Integration
Prevented credential leaks by separating sensitive information (API keys, DB connection strings) from the source code using GitHub Secrets and Streamlit Secrets.

Handling Promotion/Relegation (Domain Logic)
When building the ML predictor, I noticed that showing all 40 historic teams in a single dropdown caused logical errors (e.g., predicting matches for relegated teams). I solved this by dynamically filtering the UI to only show the 20 teams that actually participated in the user's selected season.

Cost & Performance Optimization
Applied Streamlit's @st.cache_data(ttl=3600) to the database querying function. This significantly reduces unnecessary DB calls, improves dashboard loading speed, and prevents potential cloud billing issues.
