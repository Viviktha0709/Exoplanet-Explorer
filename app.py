import streamlit as st
import pandas as pd
import sqlite3
import requests

# --- Custom CSS ---
st.markdown("""
<style>
/* Apply Monoton font to all headers and subheaders */
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6,
.stMetricLabel, .stMetricValue {
    font-family: 'Monoton', cursive !important;
    color: #F0F8FF;
    text-shadow: 0px 0px 12px #B0E0E6, 0px 0px 1px #87CEEB;
}

/* Body text */
html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif !important;
    color: #E0E0E0;
}
</style>
""", unsafe_allow_html=True)


# --- DB connection ---
conn = sqlite3.connect("exoplanets.db")

def fetch_from_api():
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    query = "select pl_name,hostname,disc_year,pl_orbper,pl_rade from pscomppars"
    params = {"query": query, "format": "json"}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data)
    return df

def save_to_db(df):
    df.to_sql("planets", conn, if_exists="replace", index=False)

def table_exists():
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='planets'")
    return cursor.fetchone() is not None

def load_from_db():
    return pd.read_sql("SELECT * FROM planets LIMIT 50", conn)

# --- Streamlit UI ---
st.title("🪐 Exoplanet Explorer")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📥 Data", 
    "🔎 Filters", 
    "📈 Trends", 
    "📊 Stats", 
    "🌍 Earth & Compare"
])

# --- Tab 1: Data ---
with tab1:
    if st.button("Fetch latest NASA data"):
        df = fetch_from_api()
        save_to_db(df)
        st.success(f"Saved {len(df)} planets to database!")

    if st.button("Show sample from DB"):
        if table_exists():
            df = load_from_db()
            st.dataframe(df)
        else:
            st.warning("⚠️ No data in database yet! Click 'Fetch latest NASA data' first.")

# --- Tab 2: Trends ---
with tab2:
    st.subheader("📖 Planets Discovered per Year")

    if table_exists():
        df = pd.read_sql("SELECT disc_year FROM planets WHERE disc_year IS NOT NULL", conn)
        per_year = df.groupby("disc_year").size().reset_index(name="count")
        st.line_chart(per_year.set_index("disc_year"))
    else:
        st.info("No data yet. Fetch NASA data first!")

# --- Tab 3: Filters ---
with tab3:
    st.subheader("🔎 Planet Finder")

    if table_exists():
        name_filter = st.text_input("Search by name")
        year_range = st.slider("Discovery Year Range", 1990, 2025, (2000, 2020))
        min_radius, max_radius = st.slider("Planet Radius Range (Earth radii)", 0.0, 30.0, (0.0, 10.0))

        query = f"""
        SELECT * FROM planets
        WHERE disc_year BETWEEN {year_range[0]} AND {year_range[1]}
        AND pl_rade BETWEEN {min_radius} AND {max_radius}
        """
        if name_filter:
            query += f" AND pl_name LIKE '%{name_filter}%'"

        df = pd.read_sql(query, conn)
        st.write(f"Found {len(df)} planets matching filters")
        st.dataframe(df)
    else:
        st.info("No data yet. Fetch NASA data first!")

# --- Tab 4: Star Systems ---
with tab4:
    st.subheader("📊 Planetary Statistics")

    if table_exists():
        df = pd.read_sql("SELECT * FROM planets", conn)

        # --- Summary Metrics ---
        st.markdown("### 🌟 Key Metrics")
        col1, col2, col3 = st.columns([1, 1, 1])
        col1.metric("Total Planets", len(df))
        col2.metric("Mean Radius (Earth radii)", round(df['pl_rade'].mean(),2))
        col3.metric("Mean Orbital Period (days)", round(df['pl_orbper'].mean(),2))

        # --- Histograms ---
        st.markdown("### 📏 Planet Radius Distribution")
        st.bar_chart(df['pl_rade'].value_counts().sort_index())

        st.markdown("### ⏱ Orbital Period Distribution")
        st.bar_chart(df['pl_orbper'].value_counts().sort_index())

        # --- Top/Bottom Lists ---
        st.markdown("### 🏆 Top 5 Largest Planets")
        st.dataframe(df.sort_values("pl_rade", ascending=False).head(5)[['pl_name','pl_rade','pl_orbper','hostname']])

        st.markdown("### ⚡ Top 5 Shortest Orbit Planets")
        st.dataframe(df.sort_values("pl_orbper").head(5)[['pl_name','pl_rade','pl_orbper','hostname']])

        # --- Earth-like Planets ---
        st.markdown("### 🌍 Top 5 Earth-like Planets")
        max_radius = df["pl_rade"].max(skipna=True)
        max_orbit = df["pl_orbper"].max(skipna=True)
        df["ESI"] = 1 - (abs(df["pl_rade"] - 1) / max_radius) - (abs(df["pl_orbper"] - 365) / max_orbit)
        df_sorted_esi = df.sort_values("ESI", ascending=False).head(5)
        st.dataframe(df_sorted_esi[['pl_name','pl_rade','pl_orbper','hostname','ESI']])

        # --- Discovery per decade ---
        st.markdown("### 📅 Planets Discovered per Decade")
        df['decade'] = (df['disc_year']//10)*10
        per_decade = df.groupby('decade').size().reset_index(name='count')
        st.bar_chart(per_decade.set_index('decade'))

    else:
        st.info("No data yet. Fetch NASA data first!")

# ---------------- Tab 5: Earth Similarity + Compare ----------------
with tab5:
    st.subheader("🌍 Top Earth-like Planets")
    
    # Slider inside the tab
    top_n = st.slider("Show top N Earth-like planets", 5, 50, 10)

    # Load planets data
    df = pd.read_sql("SELECT pl_name, hostname, disc_year, pl_orbper, pl_rade FROM planets", conn)

    if not df.empty:
        # Compute simple Earth Similarity Index
        max_radius = df["pl_rade"].max(skipna=True)
        max_orbit = df["pl_orbper"].max(skipna=True)
        df["ESI"] = 1 - (abs(df["pl_rade"] - 1) / max_radius) - (abs(df["pl_orbper"] - 365) / max_orbit)

        df_sorted = df.sort_values("ESI", ascending=False).head(top_n)
        st.dataframe(df_sorted[["pl_name", "hostname", "disc_year", "pl_rade", "pl_orbper", "ESI"]])
    else:
        st.warning("⚠️ No data in database yet! Fetch NASA data first.")

    st.subheader("🆚 Compare Two Planets")
    
    # Multiselect inside the tab
    planets = df["pl_name"].sort_values().tolist()
    selected_planets = st.multiselect("Choose two planets to compare", planets, max_selections=2)

    if len(selected_planets) == 2:
        placeholders = ",".join([f"'{p}'" for p in selected_planets])
        df_compare = pd.read_sql(f"SELECT * FROM planets WHERE pl_name IN ({placeholders})", conn)
        st.dataframe(df_compare.set_index("pl_name"))

# ---------------- Sidebar Only: Planet of the Day ----------------
st.sidebar.header("🎲 Planet of the Day")
if st.sidebar.button("Surprise me!"):
    df_rand = pd.read_sql("SELECT pl_name FROM planets ORDER BY RANDOM() LIMIT 1", conn)
    # Display just the planet name
    st.sidebar.success(f"Your random planet is: **{df_rand['pl_name'].iloc[0]}**")

