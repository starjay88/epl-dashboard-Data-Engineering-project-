import os
import time
import requests
import pandas as pd
from sqlalchemy import create_engine

# ==========================================
# 1. Setup Environment Variables
# ==========================================
API_KEY = os.environ.get("FOOTBALL_API_KEY")
CLOUD_DB_URL = os.environ.get("SUPABASE_DB_URL")

url = "https://v3.football.api-sports.io/fixtures"
headers = {'x-apisports-key': API_KEY}

# Focus on the latest season to prevent Rate Limit Exceeded errors
season = '2026'
all_matches = []

print(f"🌐 Starting data collection for the {season} season...")

# ==========================================
# 2. Extract & Transform
# ==========================================
params = {'league': '39', 'season': season}
response = requests.get(url, headers=headers, params=params)

# Defensive logic: Check if the API request was successful
if response.status_code != 200:
    print(f"❌ API Request Failed! (Status Code: {response.status_code})")
    exit()

data = response.json()
matches = data.get('response', [])

# Check if data exists to prevent overriding the DB with empty data
if not matches:
    print("⚠️ No match data retrieved from the API. (Possible Rate Limit or invalid season ID)")
    exit()

for match in matches:
    # Skip matches that haven't been played yet (no goal data available)
    if match['goals']['home'] is None:
        continue

    home_team = match['teams']['home']['name']
    away_team = match['teams']['away']['name']
    home_goals = match['goals']['home']
    away_goals = match['goals']['away']

    # Generate match result (Home Win, Draw, Away Win)
    if home_goals > away_goals:
        result = 'H'
    elif home_goals == away_goals:
        result = 'D'
    else:
        result = 'A'

    all_matches.append({
        'Season': season,
        'Home_Team': home_team,
        'Away_Team': away_team,
        'Home_Goals': home_goals,
        'Away_Goals': away_goals,
        'Result': result
    })

df = pd.DataFrame(all_matches)

# Prevent data loss by stopping the process if the dataframe is empty
if df.empty:
    print("⚠️ No processed data available. Stopping DB update to prevent data loss.")
    exit()

print(f"📊 Successfully prepared {len(df)} match records.")

# ==========================================
# 3. Load to Cloud Database (Supabase)
# ==========================================
print("☁️ Uploading and replacing data in the Cloud DB...")
engine = create_engine(CLOUD_DB_URL)
# 파이프라인이 정상화되었으므로 epl_matches 테이블로 통일합니다.
df.to_sql('epl_matches', engine, if_exists='replace', index=False)

print("🎉 Success! Pipeline extraction and DB load completed.")