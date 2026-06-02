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

#-----------AI 예측 머신러닝-----------------------------------------------------------
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

st.markdown("---")
st.header("🤖 AI 매치 승패 예측기")
st.write("380경기의 과거 데이터를 바탕으로 머신러닝(Random Forest)이 가상 매치의 승률을 예측합니다.")


# AI 모델을 학습시키는 함수 (캐시를 사용해 한 번만 학습시킵니다)
@st.cache_resource
def train_model(data):
    # 0. [에러 해결!] Result(승무패) 정답지 컬럼 만들기
    # 원본 데이터에 Result 컬럼이 없다면, 골 수를 비교해서 우리가 직접 만들어줍니다!
    if 'Result' not in data.columns:
        data.loc[data['Home_Goals'] > data['Away_Goals'], 'Result'] = 'H'
        data.loc[data['Home_Goals'] == data['Away_Goals'], 'Result'] = 'D'
        data.loc[data['Home_Goals'] < data['Away_Goals'], 'Result'] = 'A'

    # 1. AI가 이해할 수 있게 팀 이름을 숫자(암호)로 바꿉니다.
    le = LabelEncoder()
    # 모든 팀 이름을 모아서 고유한 숫자를 부여합니다.
    all_teams = pd.concat([data['Home_Team'], data['Away_Team']]).unique()
    le.fit(all_teams)
    
    # 홈팀과 어웨이팀 이름을 숫자로 변환
    X = pd.DataFrame()
    X['Home_Team_Code'] = le.transform(data['Home_Team'])
    X['Away_Team_Code'] = le.transform(data['Away_Team'])
    
    # 정답지(Result) 설정 (이제 위에서 만들었기 때문에 에러가 나지 않습니다!)
    y = data['Result']
    
    # 2. 랜덤 포레스트(Random Forest) AI 모델 학습시키기
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model, le

# 모델 학습 실행 (데이터가 불러와져 있어야 합니다)
if 'df' in locals():
    model, le = train_model(df)
    
    # 3. 사용자 입력 받기 (웹 화면에 선택 창 띄우기)
    col1, col2 = st.columns(2)
    
    # 팀 목록을 알파벳 순으로 정렬
    team_list = sorted(le.classes_)
    
    with col1:
        selected_home = st.selectbox("🏠 홈팀 선택", team_list, index=team_list.index('Arsenal') if 'Arsenal' in team_list else 0)
    with col2:
        selected_away = st.selectbox("✈️ 어웨이팀 선택", team_list, index=team_list.index('Manchester City') if 'Manchester City' in team_list else 1)
        
    # 4. 예측 버튼 만들기
    if st.button("결과 예측하기 🚀"):
        if selected_home == selected_away:
            st.warning("같은 팀끼리는 경기를 할 수 없습니다! 다른 팀을 선택해 주세요.")
        else:
            # 선택한 팀을 다시 숫자로 변환해서 AI에게 질문할 준비
            input_data = pd.DataFrame({
                'Home_Team_Code': [le.transform([selected_home])[0]],
                'Away_Team_Code': [le.transform([selected_away])[0]]
            })
            
            # AI의 예측 결과 (승점/무/패 확률)
            probabilities = model.predict_proba(input_data)[0]
            classes = model.classes_ # ['A', 'D', 'H'] (원정승, 무승부, 홈승)
            
            # 보기 좋게 결과 매칭
            prob_dict = dict(zip(classes, probabilities))
            
            st.success("✨ AI 분석이 완료되었습니다!")
            
            # 화면에 큼직하게 예측 확률 보여주기
            st.metric(label=f"🏠 {selected_home} (홈) 승리 확률", value=f"{prob_dict.get('H', 0) * 100:.1f}%")
            st.metric(label=f"🤝 무승부 확률", value=f"{prob_dict.get('D', 0) * 100:.1f}%")
            st.metric(label=f"✈️ {selected_away} (어웨이) 승리 확률", value=f"{prob_dict.get('A', 0) * 100:.1f}%")
