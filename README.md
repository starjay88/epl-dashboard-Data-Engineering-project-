# ⚽ EPL Data Pipeline & ML Dashboard
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg) ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B.svg) ![PostgreSQL](https://img.shields.io/badge/Supabase-3ECF8E.svg) ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF.svg)

A personal project to practice end-to-end data engineering and machine learning deployment. This project automates the collection of English Premier League (EPL) match data (2023-2026), stores it in a cloud database, and visualizes it through an interactive web dashboard with an ML-based match predictor.

## 🏗️ Architecture & Data Flow

```mermaid
graph LR
    A[API-Sports] -->|Extract JSON| B(GitHub Actions)
    B -->|Transform / Clean| B
    B -->|Load (SQL)| C[(Supabase PostgreSQL)]
    C -->|Query| D[Streamlit Dashboard]
    D -->|Random Forest| E((Live ML Prediction))

