#  ⚽ EPL Data Pipeline & ML Prediction Dashboard

EPL Dashboard LINK:   https://epl-dashboard2024.streamlit.app/

_**Project Overview**_

A personal project to practice end-to-end data engineering and machine learning deployment. This project automates the collection of English Premier League (EPL) match data (2020-2026), stores it in a cloud database, and visualizes it through an interactive web dashboard with an ML-based match predictor.

데이터 수집부터 클라우드 적재, 웹 배포 및 머신러닝 예측까지 데이터 엔지니어링의 전체 파이프라인을 직접 구축해 보기 위한 개인 프로젝트입니다. 프리미어리그(EPL) 7년 치 경기 데이터를 자동으로 수집하고, 이를 바탕으로 시각화 및 승률 예측을 제공하는 대시보드를 개발했습니다.


_**Tech Stack**_

Data Pipeline: Python (requests, pandas)

Database: Supabase (PostgreSQL)

Automation: GitHub Actions

Frontend & ML: Streamlit, Scikit-learn (Random Forest)


_**Key Features & Engineering Decisions**_

1.  Automated ETL Pipeline: Built a Python script (main.py) to extract match data from the API-Football, transform the data to include win/draw/loss labels, and load it into Supabase. GitHub Actions runs this script daily at midnight to keep the database up-to-date.

2.  Security Integration: Prevented credential leaks by separating sensitive information (API keys, DB connection strings) from the source code using GitHub Secrets and Streamlit Secrets.

3.  Handling Promotion/Relegation (Domain Logic): When building the ML predictor, I noticed that showing all 40 historic teams in a single dropdown caused logical errors (e.g., predicting matches for relegated teams). I solved this by dynamically filtering the UI to only show the 20 teams that actually participated in the user's selected season.

4.  Cost & Performance Optimization: Applied Streamlit's @st.cache_data(ttl=3600) to the database querying function. This reduces unnecessary DB calls and prevents potential cloud billing issues.

_KR)_

1. ETL 파이프라인 자동화: 외부 API(API-Football)에서 데이터를 추출하고, 승무패 정답지 레이블을 가공한 뒤 Supabase 클라우드 DB에 적재하는 파이썬 코드를 작성했습니다. GitHub Actions 스케줄러를 활용해 매일 자정 최신 데이터가 자동으로 업데이트되도록 구현했습니다.

2. 보안(Security) 내재화: 소스 코드에 API 키와 DB 주소가 노출되는 것을 방지하기 위해, GitHub Secrets와 Streamlit Secrets를 환경 변수로 연동하여 보안성을 높였습니다.

3. 승강제(Promotion/Relegation) 도메인 로직 반영: 7년 치 데이터를 ML 모델에 학습시킬 때, 과거 강등된 팀이 현재 시즌 예측 목록에 나타나는 논리적 오류를 발견했습니다. 이를 해결하기 위해 사용자가 선택한 특정 시즌에 실제로 참가했던 20개 팀만 동적으로 필터링하여 UI에 노출하도록 코드를 개선했습니다.

4. 자원 최적화: 클라우드 DB의 과도한 호출과 비용 발생을 막기 위해 스트림릿의 캐싱 기능(@st.cache_data)을 적용하여 1시간 단위로만 DB를 조회하도록 최적화했습니다.

