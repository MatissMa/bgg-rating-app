import streamlit as st
import pandas as pd
import os

# --- Define Weights ---
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


# --- Helper: Round to nearest 0.5 ---
def round_half(x):
    return round(x * 2) / 2


# --- Rating Form ---
st.title("🎲 Board Game Rating App")

game_name = st.text_input("Board Game Title")

is_solo = st.checkbox("Is this a solo-only game?", value=False)

# Adjust weights if interactivity should be skipped
adjusted_weights = weights.copy()
if is_solo:
    adjusted_weights.pop("interactivity")

# Normalize
total_weight = sum(adjusted_weights.values())
adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}

ratings = {}
with st.form("rate_game"):
    st.subheader("📋 Rate Each Category (1–10)")
    for cat in adjusted_weights:
        ratings[cat] = st.slider(cat.replace("_", " ").title(), 1.0, 10.0, 7.0, 0.5)
    submitted = st.form_submit_button("Submit Rating")

if submitted:
    weighted_total = sum(ratings[cat] * adjusted_weights[cat] for cat in ratings)
    final_score = round_half(weighted_total)

    st.success(f"✅ Overall Rating for **{game_name}**: **{final_score}**")

    # Show full breakdown
    st.markdown("### 🧾 Score Breakdown")
    breakdown = pd.DataFrame({
        "Category": [cat.replace("_", " ").title() for cat in ratings],
        "Rating": [ratings[cat] for cat in ratings],
        "Weight": [adjusted_weights[cat] for cat in ratings]
    })
    st.dataframe(breakdown)

    # Export to CSV
    result = {"Game": game_name, **ratings, "Overall": final_score}
    csv_file = "ratings.csv"

    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
    else:
        df = pd.DataFrame([result])
    
    df.to_csv(csv_file, index=False)
    st.success("📁 Rating saved to `ratings.csv`")