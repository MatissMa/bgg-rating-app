import streamlit as st
import requests
import xml.etree.ElementTree as ET
import json
import pandas as pd

# ---------------------
# CONFIG: Weights
# ---------------------
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

def get_game_details(game_id):
    try:
        url = f"https://boardgamegeek.com/xmlapi2/thing?id={game_id}&stats=1"
        response = requests.get(url)
        root = ET.fromstring(response.content)
        item = root.find('item')
        if item is not None:
            def get_val(xpath):
                el = item.find(xpath)
                return el.text if el is not None else None

            details = {
                "name": item.find("name").attrib.get('value', '') if item.find("name") is not None else '',
                "thumbnail": get_val("thumbnail"),
                "minplayers": item.find("minplayers").attrib.get('value', '') if item.find("minplayers") is not None else '',
                "maxplayers": item.find("maxplayers").attrib.get('value', '') if item.find("maxplayers") is not None else '',
                "playingtime": get_val("playingtime"),
                "average": get_val("statistics/ratings/average"),
                "id": game_id
            }
            return details
    except Exception as e:
        st.warning(f"Error fetching BGG data: {e}")
    return {}

def generate_review(name, score, ratings):
    review = f"**{name}**\nRated: {score}/10 🎯\n"
    for cat, val in ratings.items():
        review += f"- {cat.replace('_', ' ').title()}: {val}\n"
    return review

# ---------------------
# STREAMLIT UI
# ---------------------
st.set_page_config(page_title="BGG Game Rater", page_icon="🎲")
st.title("🎲 BGG Game Rating App")

# Search or manual input
search_query = st.text_input("🔍 Search for a board game on BGG")
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

# Fallback to manual input
if not game_info.get("name"):
    game_info["name"] = st.text_input("Or enter the game name manually:")

is_solo = st.checkbox("Is this a solo-only game?", value=False)

# Adjust weights if solo
adjusted_weights = weights.copy()
if is_solo:
    adjusted_weights.pop("interactivity", None)

# Normalize weights
total_weight = sum(adjusted_weights.values())
adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}

# Show BGG image/info if available
if game_info.get("thumbnail"):
    st.image(game_info["thumbnail"], width=200, caption=game_info.get("name", "Unknown Game"))

try:
    playtime = game_info.get("playingtime", "")
    minp = game_info.get("minplayers", "")
    maxp = game_info.get("maxplayers", "")
    if playtime and minp and maxp:
        st.markdown(f"⏱️ Play time: {playtime} min | 👥 Players: {minp}–{maxp}")
except:
    pass

avg = game_info.get("average", "")
try:
    avg_val = round(float(avg), 2)
    st.markdown(f"📊 BGG Avg Rating: {avg_val}")
except (ValueError, TypeError):
    pass

# Init session
if "ratings" not in st.session_state:
    st.session_state.ratings = []

# --- Rating Form
with st.form("rate_game"):
    st.subheader("📋 Rate Each Category (1–10)")
    ratings = {}
    for cat in adjusted_weights:
        ratings[cat] = st.slider(cat.replace("_", " ").title(), 1.0, 10.0, 7.0, 0.5)
    submitted = st.form_submit_button("✅ Save Rating")

if submitted:
    score = round_half(sum(ratings[c] * adjusted_weights[c] for c in ratings))
    st.success(f"✅ Overall Rating: {score}/10 for **{game_info['name']}**")

    # Show Review
    st.markdown("### 📝 Generated Review")
    review_text = generate_review(game_info["name"], score, ratings)
    st.code(review_text, language="markdown")

    # Save to session
    st.session_state.ratings.append({
        "name": game_info["name"],
        "score": score,
        "ratings": ratings
    })

# --- Ratings Table
if st.session_state.ratings:
    st.markdown("## 📊 Game Comparison Table")
    table_data = []
    for r in st.session_state.ratings:
        row = {"Game": r["name"], "Overall": r["score"]}
        row.update(r["ratings"])
        table_data.append(row)
    st.dataframe(pd.DataFrame(table_data).set_index("Game"))

# --- Export/Import JSON
st.markdown("### 📦 Save or Load Ratings")
col1, col2 = st.columns(2)

with col1:
    if st.download_button("💾 Export Ratings as JSON", json.dumps(st.session_state.ratings, indent=2), file_name="ratings.json"):
        st.success("Ratings exported!")

with col2:
    uploaded = st.file_uploader("📂 Load Ratings from JSON", type="json")
    if uploaded:
        st.session_state.ratings = json.load(uploaded)
        st.success("Ratings loaded from file!")
