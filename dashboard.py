import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# 1. 화면 설정 (가장 먼저 와야 함): 화면을 넓게 쓰고 제목 지정
st.set_page_config(page_title="EPL Data Dashboard", layout="wide")

# 2. 클라우드에서 데이터 가져오기
@st.cache_data(ttl=3600)
def load_data():
    CLOUD_DB_URL = st.secrets["SUPABASE_DB_URL"]
    engine = create_engine(CLOUD_DB_URL)
    query = "SELECT * FROM epl_matches"
    df = pd.read_sql(query, engine)
    return df

# 데이터 로딩
with st.spinner('클라우드 DB에서 7년 치 데이터를 불러오는 중...'):
    df = load_data()

# ==========================================
#  사이드바 (화면 왼쪽 서랍) 설정
# ==========================================
st.sidebar.title("⚙️ 설정 및 예측")

# [기능 1] 연도(시즌) 선택 필터
st.sidebar.subheader("📅 시즌 선택")
# DB에 있는 시즌 목록을 중복 없이 가져와서 최신순(내림차순) 정렬
season_list = sorted(df['Season'].unique(), reverse=True)
selected_season = st.sidebar.selectbox("데이터를 조회할 시즌을 선택하세요", season_list)

# 사용자가 선택한 시즌의 데이터만 잘라내기
filtered_df = df[df['Season'] == selected_season]


# ==========================================
#  메인 화면 설정
# ==========================================
st.title(f"⚽ {selected_season} 시즌 프리미어리그 대시보드")
st.write("클라우드 데이터베이스(Supabase)와 연동된 동적 데이터 파이프라인입니다.")

# 화면을 두 개의 탭으로 분리하여 깔끔하게 정리
tab1, tab2 = st.tabs(["🗄️ 원본 데이터 보드", "🔥 팀별 득점력 분석"])

with tab1:
    st.subheader(f"{selected_season} 시즌 전체 경기 결과")
    st.dataframe(filtered_df, use_container_width=True) # 화면 너비에 맞게 꽉 차게 그림

with tab2:
    st.subheader(f"🏟️ {selected_season} 시즌 홈팀 득점 랭킹")
    home_goals = filtered_df.groupby('Home_Team')['Home_Goals'].sum().sort_values(ascending=False)
    st.bar_chart(home_goals)


# ==========================================
#  AI 승패 예측기 (다시 사이드바 아래쪽으로)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI 승패 예측기")
st.sidebar.caption("7년 치 과거 데이터를 기반으로 승률을 계산합니다.")

@st.cache_resource
def train_model(data):
    if 'Result' not in data.columns:
        data.loc[data['Home_Goals'] > data['Away_Goals'], 'Result'] = 'H'
        data.loc[data['Home_Goals'] == data['Away_Goals'], 'Result'] = 'D'
        data.loc[data['Home_Goals'] < data['Away_Goals'], 'Result'] = 'A'

    le = LabelEncoder()
    all_teams = pd.concat([data['Home_Team'], data['Away_Team']]).unique()
    le.fit(all_teams)
    
    X = pd.DataFrame()
    X['Home_Team_Code'] = le.transform(data['Home_Team'])
    X['Away_Team_Code'] = le.transform(data['Away_Team'])
    y = data['Result']
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model, le

# AI는 필터링된 데이터가 아니라 전체 7년 치(df)를 보고 똑똑하게 학습함
if not df.empty:
    model, le = train_model(df)
    team_list = sorted(le.classes_)
    
    selected_home = st.sidebar.selectbox("🏠 홈팀", team_list, index=team_list.index('Manchester United') if 'Manchester United' in team_list else 0)
    selected_away = st.sidebar.selectbox("✈️ 원정팀", team_list, index=team_list.index('Manchester City') if 'Manchester City' in team_list else 1)
    
    if st.sidebar.button("결과 예측하기 🚀"):
        if selected_home == selected_away:
            st.sidebar.warning("다른 팀을 선택해 주세요.")
        else:
            input_data = pd.DataFrame({
                'Home_Team_Code': [le.transform([selected_home])[0]],
                'Away_Team_Code': [le.transform([selected_away])[0]]
            })
            
            probabilities = model.predict_proba(input_data)[0]
            classes = model.classes_ 
            prob_dict = dict(zip(classes, probabilities))
            
            st.sidebar.success("✨ 분석 완료!")
            st.sidebar.metric(label=f"🏠 {selected_home} 승리", value=f"{prob_dict.get('H', 0) * 100:.1f}%")
            st.sidebar.metric(label=f"🤝 무승부", value=f"{prob_dict.get('D', 0) * 100:.1f}%")
            st.sidebar.metric(label=f"✈️ {selected_away} 승리", value=f"{prob_dict.get('A', 0) * 100:.1f}%")