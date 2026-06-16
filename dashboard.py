import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# ==========================================
# 1. 화면 전체 설정 및 배경화면 (반드시 최상단에 위치)
# ==========================================
st.set_page_config(page_title="EPL Data Dashboard", layout="wide")

def set_background():
    # 웅장한 올드 트래포드(또는 EPL 구장) 느낌의 배경화면 주입
    image_url = "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80"
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{image_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_background()

# ==========================================
# 2. 클라우드 DB 연결 및 데이터 로드
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    CLOUD_DB_URL = st.secrets["SUPABASE_DB_URL"]
    engine = create_engine(CLOUD_DB_URL)
    query = "SELECT * FROM epl_matches"
    df = pd.read_sql(query, engine)
    return df

with st.spinner('클라우드 DB에서 7년 치 데이터를 불러오는 중...'):
    df = load_data()

# 데이터가 비어있을 경우 에러 방지
if df.empty:
    st.error("데이터가 없습니다. 깃허브 Actions에서 수집 파이프라인을 먼저 실행해 주세요.")
    st.stop()

# ==========================================
# 🗄️ 3. 사이드바 (화면 왼쪽 서랍) 설정
# ==========================================
st.sidebar.title("⚙️ 설정 및 예측")
st.sidebar.subheader("📅 시즌 선택")

# 시즌 목록 가져오기 (최신순)
season_list = sorted(df['Season'].unique(), reverse=True)
selected_season = st.sidebar.selectbox("데이터를 조회할 시즌을 선택하세요", season_list)

# 사용자가 선택한 시즌의 데이터만 필터링
filtered_df = df[df['Season'] == selected_season]

# ==========================================
# 🖥️ 4. 메인 화면 설정 (데이터 표 & 그래프)
# ==========================================
st.title(f"⚽ {selected_season} 시즌 프리미어리그 대시보드")
st.write("클라우드 데이터베이스(Supabase)와 연동된 동적 데이터 파이프라인입니다.")

# 탭을 활용한 깔끔한 UI
tab1, tab2 = st.tabs(["🗄️ 원본 데이터 보드", "🔥 팀별 득점력 분석"])

with tab1:
    st.subheader(f"{selected_season} 시즌 전체 경기 결과")
    st.dataframe(filtered_df, use_container_width=True)

with tab2:
    st.subheader(f"🏟️ {selected_season} 시즌 홈팀 득점 랭킹")
    home_goals = filtered_df.groupby('Home_Team')['Home_Goals'].sum().sort_values(ascending=False)
    st.bar_chart(home_goals)

# ==========================================
# 🤖 5. AI 승패 예측기 (사이드바 하단)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI 승패 예측기")
st.sidebar.caption("7년 치 과거 전체 데이터를 기반으로 승률을 계산합니다.")

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

# 모델 학습 진행 (7년 치 전체 데이터 활용)
model, le = train_model(df)

# ✨ 수정된 부분: 선택한 시즌에 실제로 참가했던 20개 팀만 추출
current_season_teams = sorted(pd.concat([filtered_df['Home_Team'], filtered_df['Away_Team']]).unique())

selected_home = st.sidebar.selectbox(
    "🏠 홈팀", 
    current_season_teams, 
    index=current_season_teams.index('Manchester United') if 'Manchester United' in current_season_teams else 0
)

selected_away = st.sidebar.selectbox(
    "✈️ 원정팀", 
    current_season_teams, 
    index=current_season_teams.index('Manchester City') if 'Manchester City' in current_season_teams else 1
)

if st.sidebar.button("결과 예측하기 🚀"):
    if selected_home == selected_away:
        st.sidebar.warning("같은 팀끼리는 경기를 할 수 없습니다! 다른 팀을 선택해 주세요.")
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