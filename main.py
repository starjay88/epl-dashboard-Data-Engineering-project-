import os
import time
import requests
import pandas as pd
from sqlalchemy import create_engine

# 1. API 키와 DB 주소 금고에서 꺼내기
API_KEY = os.environ.get("FOOTBALL_API_KEY")
CLOUD_DB_URL = os.environ.get("SUPABASE_DB_URL")

url = "https://v3.football.api-sports.io/fixtures"
headers = {'x-apisports-key': API_KEY}

# 우리가 수집할 7개 시즌 리스트 (2020 ~ 2026)
seasons = ['2020', '2021', '2022', '2023', '2024', '2025', '2026']
all_matches = []

print("🌐 7년 치 다중 시즌 데이터 수집을 시작합니다...")

# ==========================================
# 1 & 2. Extract & Transform (수집 및 가공)
# ==========================================
for season in seasons:
    print(f"👉 {season} 시즌 데이터 가져오는 중...")
    params = {'league': '39', 'season': season}
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    matches = data.get('response', [])
    
    for match in matches:
        # 아직 경기가 안 열려서 골 데이터가 없는 경우는 건너뜁니다
        if match['goals']['home'] is None:
            continue

        home_team = match['teams']['home']['name']
        away_team = match['teams']['away']['name']
        home_goals = match['goals']['home']
        away_goals = match['goals']['away']

        # 승무패 정답지 생성
        if home_goals > away_goals:
            result = 'H'
        elif home_goals == away_goals:
            result = 'D'
        else:
            result = 'A'

        # 리스트에 데이터 추가 (Season 꼬리표 달기!)
        all_matches.append({
            'Season': season,
            'Home_Team': home_team,
            'Away_Team': away_team,
            'Home_Goals': home_goals,
            'Away_Goals': away_goals,
            'Result': result
        })
    
    # API 서버가 다운되지 않게 1초씩 쉬어줍니다 (Rate Limit 방지)
    time.sleep(1)

# 하나의 거대한 데이터프레임으로 합치기
df = pd.DataFrame(all_matches)
print(f"📊 총 {len(df)}개의 다중 시즌 경기 데이터를 준비했습니다.")

# ==========================================
# 3. Load (클라우드 DB에 적재)
# ==========================================
print("☁️ 클라우드 DB에 최신 데이터 덮어쓰기 업로드 중...")
engine = create_engine(CLOUD_DB_URL)
df.to_sql('epl_matches', engine, if_exists='replace', index=False)

print("🎉 완벽합니다! 7년 치 파이프라인 수집 및 DB 적재 성공!")