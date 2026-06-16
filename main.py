import os
import requests
import pandas as pd
from sqlalchemy import create_engine

# for 보안: API 키와 DB URL은 환경변수로 관리
API_KEY = os.environ.get("FOOTBALL_API_KEY")
CLOUD_DB_URL = os.environ.get("SUPABASE_DB_URL")
# ==========================================

# 헤더(출입증)와 파라미터(질문: 39번 프리미어리그, 2024년 시작 시즌) 
headers = {'x-apisports-key': API_KEY}
params = {'league': '39', 'season': '2025'}

print("🌐 API 서버에서 24/25 시즌 데이터를 가져오는 중...")
response = requests.get(url, headers=headers, params=params)
data = response.json()

# ==========================================
# 2. Transform (데이터 가공: 우리 입맛에 맞게 정제)
# ==========================================
print("⚙️ 데이터 가공 중...")
matches = data.get('response', [])
match_list = []

for match in matches:
    # 아직 경기가 안 열려서 골 데이터가 없는 경우는 건너뜁니다
    if match['goals']['home'] is None:
        continue

    home_team = match['teams']['home']['name']
    away_team = match['teams']['away']['name']
    home_goals = match['goals']['home']
    away_goals = match['goals']['away']

    # AI 예측기를 위한 Result(승무패) 정답지 자동 생성
    if home_goals > away_goals:
        result = 'H'
    elif home_goals == away_goals:
        result = 'D'
    else:
        result = 'A'

    match_list.append({
        'Home_Team': home_team,
        'Away_Team': away_team,
        'Home_Goals': home_goals,
        'Away_Goals': away_goals,
        'Result': result
    })

df = pd.DataFrame(match_list)
print(f"📊 총 {len(df)}개의 최신 경기 데이터를 준비했습니다.")

# ==========================================
# 3. Load (데이터 적재: Supabase 클라우드 DB로 전송)
# ==========================================
CLOUD_DB_URL = "postgresql://postgres.gjyubaddzcmpzjesqakq:ghkddnjswo1!@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres"

print("☁️ 클라우드 DB에 최신 데이터 덮어쓰기 업로드 중...")
engine = create_engine(CLOUD_DB_URL)

# if_exists='replace' : 매일 실행될 때마다 기존 데이터를 최신으로 깔끔하게 덮어씁니다
df.to_sql('epl_matches', engine, if_exists='replace', index=False)

print("🎉 완벽합니다! 실시간 파이프라인 수집 및 DB 적재 성공!")
