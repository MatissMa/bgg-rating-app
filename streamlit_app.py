import streamlit as st
import requests
import xml.etree.ElementTree as ET

# ---- Weights (adjusted and normalized)
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

# ---- BGG Search
def search_bgg_games(query):
    url = f"https://boardgamegeek.com/xmlapi2/search?query={query}&type=boardgame"
    response = requests.get(url)
    root = ET.fromstring(response.content)

    games = []
    for item in root.findall('item'):
        name = item.find('name').attrib['value']
        game_id = item.attrib['id']
        games.append({"name": name, "id": game_id})
    return games

# ---- Fetch Game Details (to get image)
def get_game_details(game_id):
    url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    item = root.find('item')

    if item is not None:
        name = item.find("name").attrib['value']
        thumbnail = item.find("thumbnail").text if item.find("thumbnail") is not None else None
        return {"name": name, "thumbnail": thumbnail}
    return {}

# ---- Streamlit UI
st.title("🎲 Rate a Board Game")

# Search input
search_query = st.text_input("🔍 Search for a game on BoardGameGeek")
selected_game = None
game_info = {}

if search_query:
    results = search_bgg_games(search_query)
    if results:
        titles = [f"{g['name']} (ID: {g['id']})" for g in results]
        selection = st.selectbox("Select a game:", titles)
        selected_game = next((g for g in results if f"{g['name']} (ID: {g['id']})" == selection), None)

        if selected_game:
            game_info = get_game_details(selected_game['id'])
    else:
        st.warning("No games found!")

# Manual fallback
if not game_info.get("name"):
    game_info["name"] = st.text_input("Or enter a game name manually:")

# Solo game checkbox
is_solo = st.checkbox("Is this a solo-only game?", value=False)

# Adjust weights if solo
adjusted_weights = weights.copy()
if is_solo:
    adjusted_weights.pop("interactivity", None)

# Normalize weights
total_weight = sum(adjusted_weights.values())
adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}

# Show image if available
if game_info.get("thumbnail"):
    st.image(game_info["thumbnail"], width=200, caption=game_info["name"])

# Rating form
ratings = {}
with st.form("rate_game"):
    st.subheader("📋 Rate Each Category (1–10)")
    for cat in adjusted_weights:
        ratings[cat] = st.slider(cat.replace("_", " ").title(), 1.0, 10.0, 7.0, 0.5)
    submitted = st.form_submit_button("🎯 Get Overall Rating")

# Display result
if submitted:
    game_name = game_info.get("name", "").strip()
    if not game_name:
        game_name = "Unnamed Game"

    weighted_total = sum(ratings[cat] * adjusted_weights[cat] for cat in ratings)
    final_score = round_half(weighted_total)

    st.success(f"✅ Overall Rating for **{game_name}**: **{final_score}**")

    st.markdown("### 🧾 Score Breakdown")
    st.table({
        "Category": [cat.replace("_", " ").title() for cat in ratings],
        "Rating": [ratings[cat] for cat in ratings],
        "Weight": [round(adjusted_weights[cat], 3) for cat in ratings]
    })
