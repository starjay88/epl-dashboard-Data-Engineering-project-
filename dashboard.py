import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. 클라우드 DB 연결 주소 (아까 썼던 비밀번호 포함된 주소를 똑같이 넣습니다)
CLOUD_DB_URL = "postgresql://postgres.gjyubaddzcmpzjesqakq:ghkddnjswo1!@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres"

# 2. 클라우드에서 데이터 가져오기 (매번 요청하지 않게 캐시로 저장해두는 똑똑한 기능입니다)
@st.cache_data
def load_data():
    engine = create_engine(CLOUD_DB_URL)
    # 클라우드 DB의 Matches 테이블에서 데이터 전체 가져오기
    query = 'SELECT * FROM "Matches"'
    df = pd.read_sql(query, engine)
    return df

# --- 여기서부터 화면 그리기 ---

st.title("⚽ 2023-24 프리미어리그 대시보드")
st.write("클라우드 데이터베이스(Supabase)와 실시간으로 연동된 화면입니다.")

# 로딩 스피너 보여주기
with st.spinner('클라우드 DB에서 데이터를 불러오는 중...'):
    df = load_data()

# 1번 섹션: 전체 데이터 표 보여주기
st.subheader("🗄️ 클라우드 원본 데이터")
st.dataframe(df) # 엑셀처럼 예쁜 표로 그려줍니다.

# 2번 섹션: 간단한 데이터 시각화 (홈팀 기준 총 득점 랭킹)
st.subheader("🔥 팀별 홈 경기 득점력 분석")
# 판다스를 이용해 팀별 홈 득점을 합산하고 순서대로 정렬합니다.
home_goals = df.groupby('Home_Team')['Home_Goals'].sum().sort_values(ascending=False)
st.bar_chart(home_goals) # 막대 그래프로 그려줍니다.