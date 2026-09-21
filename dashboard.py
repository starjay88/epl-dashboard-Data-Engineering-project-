import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# ==========================================
# 1. Page Configuration & Background (Must be at the top)
# ==========================================
st.set_page_config(page_title="EPL Data Dashboard", layout="wide")

def set_background():
    # Set stadium image as background (High-res image from Unsplash)
    image_url = "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80"
    
    # Adjust to a bright tone (0.6 opacity) using rgba(255,255,255)
    page_bg_img = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.6)), url("{image_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_background()

# ==========================================
# 2. Cloud DB Connection & Data Loading
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    CLOUD_DB_URL = st.secrets["SUPABASE_DB_URL"]
    engine = create_engine(CLOUD_DB_URL)
    # main.py와 동일한 epl_matches 테이블로 완벽하게 통일
    query = "SELECT * FROM epl_matches"
    df = pd.read_sql(query, engine)
    return df

with st.spinner('Loading data from Cloud DB...'):
    df = load_data()

# Prevent errors if data is empty
if df.empty:
    st.error("No data found. Please run the data collection pipeline via GitHub Actions first.")
    st.stop()

# ==========================================
# 🗄️ 3. Sidebar Configuration
# ==========================================
st.sidebar.title("⚙️ Settings & Prediction")
st.sidebar.subheader("📅 Select Season")

# Get season list in descending order
season_list = sorted(df['Season'].unique(), reverse=True)
selected_season = st.sidebar.selectbox("Select a season to view", season_list)

# Filter data based on the selected season
filtered_df = df[df['Season'] == selected_season]

# ==========================================
# 🖥️ 4. Main Display (Data Table & Charts)
# ==========================================
st.title(f"⚽ {selected_season} Season Premier League Dashboard")
st.write("A dynamic data pipeline integrated with a Cloud Database (Supabase).")

# Clean UI using Tabs
tab1, tab2 = st.tabs(["🗄️ Raw Data Board", "🔥 Team Scoring Analysis"])

with tab1:
    st.subheader(f"{selected_season} Season Match Results")
    st.dataframe(filtered_df, use_container_width=True)

with tab2:
    st.subheader(f"🏟️ {selected_season} Season Home Team Goals Ranking")
    home_goals = filtered_df.groupby('Home_Team')['Home_Goals'].sum().sort_values(ascending=False)
    st.bar_chart(home_goals)

# ==========================================
# 🤖 5. AI Match Predictor (Sidebar Bottom)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 AI Match Predictor")
st.sidebar.caption("Calculates win probability based on historical data.")

@st.cache_resource
def train_model(data):
    # Generate match result labels if they don't exist
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

# Train the model
model, le = train_model(df)

# Extract only the teams that participated in the selected season
current_season_teams = sorted(pd.concat([filtered_df['Home_Team'], filtered_df['Away_Team']]).unique())

selected_home = st.sidebar.selectbox(
    "🏠 Home Team", 
    current_season_teams, 
    index=current_season_teams.index('Manchester United') if 'Manchester United' in current_season_teams else 0
)

selected_away = st.sidebar.selectbox(
    "✈️ Away Team", 
    current_season_teams, 
    index=current_season_teams.index('Manchester City') if 'Manchester City' in current_season_teams else 1
)

if st.sidebar.button("Predict Result 🚀"):
    if selected_home == selected_away:
        st.sidebar.warning("A team cannot play against itself! Please select different teams.")
    else:
        input_data = pd.DataFrame({
            'Home_Team_Code': [le.transform([selected_home])[0]],
            'Away_Team_Code': [le.transform([selected_away])[0]]
        })
        
        probabilities = model.predict_proba(input_data)[0]
        classes = model.classes_ 
        prob_dict = dict(zip(classes, probabilities))
        
        st.sidebar.success("✨ Analysis Complete!")
        st.sidebar.metric(label=f"🏠 {selected_home} Win", value=f"{prob_dict.get('H', 0) * 100:.1f}%")
        st.sidebar.metric(label=f"🤝 Draw", value=f"{prob_dict.get('D', 0) * 100:.1f}%")
        st.sidebar.metric(label=f"✈️ {selected_away} Win", value=f"{prob_dict.get('A', 0) * 100:.1f}%")