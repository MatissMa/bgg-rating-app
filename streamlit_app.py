import streamlit as st
import requests
import xml.etree.ElementTree as ET

# ---- Weights (can be adjusted)
weights = {
    "artwork": 0.05,
    "gameplay": 0.20,
    "setup": 0.05,
    "length": 0.05,
    "fun_factor": 0.15,
    "price": 0.05,
    "learning_curve": 0.05,
    "replayability": 0.10,
    "interactivity": 0.08,
    "production_quality": 0.06,
    "theme_integration": 0.06,
    "player_count": 0.05,
    "storage": 0.05
}

def round_half(x):
    return round(x * 2) / 2

# ---- BGG Game Search Function
def search_bgg_games(query):
    url = f"https://boardgamegeek.com/xmlapi2/search?query={query}&type=boardgame"
    response = requests.get(url)
    root = ET.fromstring(response.content)

    games = []
    for item in root.findall('item'):
        name = item.find('name').attrib['value']
        game_id = item.attrib['id']
        games.append(f"{name} (ID: {game_id})")
    return games

# ---- Streamlit UI
st.title("🎲 Rate a Board Game")

# Search box for BGG integration
search_query = st.text_input("🔍 Search for a game on BoardGameGeek")
game_name = None

if search_query:
    results = search_bgg_games(search_query)
    if results:
        selected = st.selectbox("Select a game:", results)
        game_name = selected.split(" (ID")[0]
    else:
        st.warning("No games found!")

# Fallback if not using search
if not game_name:
    game_name = st.text_input("Or enter a game name manually:")

is_solo = st.checkbox("Is this a solo-only game?", value=False)

# Adjust interactivity if solo
adjusted_weights = weights.copy()
if is_solo:
    adjusted_weights.pop("interactivity")

# Normalize weights
total_weight = sum(adjusted_weights.values())
adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}

ratings = {}
with st.form("rate_game"):
    st.subheader("📋 Rate Each Category (1–10)")
    for cat in adjusted_weights:
        ratings[cat] = st.slider(cat.replace("_", " ").title(), 1.0, 10.0, 7.0, 0.5)
    submitted = st.form_submit_button("🎯 Get Overall Rating")

if submitted and game_name:
    weighted_total = sum(ratings[cat] * adjusted_weights[cat] for cat in ratings)
    final_score = round_half(weighted_total)

    st.success(f"✅ Overall Rating for **{game_name}**: **{final_score}**")

    st.markdown("### 🧾 Score Breakdown")
    st.table({
        "Category": [cat.replace("_", " ").title() for cat in ratings],
        "Rating": [ratings[cat] for cat in ratings],
        "Weight": [adjusted_weights[cat] for cat in ratings]
    })
