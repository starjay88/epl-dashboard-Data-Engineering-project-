import os
import time
import requests
import pandas as pd
import logging
from sqlalchemy import create_engine

# ==========================================
# 0. Logging Configuration (실무 스타일 로깅 설정)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

logging.info(f"🌐 Starting data collection for the {season} season...")

# ==========================================
# 2. Extract & Transform
# ==========================================
params = {'league': '39', 'season': season}
response = requests.get(url, headers=headers, params=params)

# Defensive logic: Check if the API request was successful
if response.status_code != 200:
    logging.error(f"❌ API Request Failed! (Status Code: {response.status_code})")
    exit()

data = response.json()
matches = data.get('response', [])

# Check if data exists to prevent overriding the DB with empty data
if not matches:
    logging.warning("⚠️ No match data retrieved from the API. (Possible Rate Limit or invalid season ID)")
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
    logging.warning("⚠️ No processed data available. Stopping DB update to prevent data loss.")
    exit()

logging.info(f"📊 Successfully prepared {len(df)} match records.")

# ==========================================
# 3. Load to Cloud Database (Supabase)
# ==========================================
logging.info("☁️ Uploading and replacing data in the Cloud DB...")
engine = create_engine(CLOUD_DB_URL)
df.to_sql('epl_matches', engine, if_exists='replace', index=False)

logging.info("🎉 Success! Pipeline extraction and DB load completed.")