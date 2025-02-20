import os
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns

# ✅ Define SQLite database path (works locally & online)
db_path = os.path.join(os.path.dirname(__file__), "database.db")

# ✅ Function to check if a table exists
def table_exists(table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# ✅ Fetch team data (averages per game)
def fetch_team_data():
    if not table_exists("Teams"):
        st.error("⚠️ Error: 'Teams' table not found in the database.")
        return pd.DataFrame()  # Return empty DataFrame

    conn = sqlite3.connect(db_path)
    query = """
    SELECT 
        name AS Team,
        CASE WHEN tm = 1 THEN 'Home' ELSE 'Away' END AS Location,
        COUNT(game_id) AS Games_Played,
        AVG(p1_score + p2_score + p3_score + p4_score) AS Avg_Points,
        AVG(fouls_total) AS Avg_Fouls,
        AVG(free_throws_made) AS Avg_Free_Throws,
        AVG(field_goals_made) AS Avg_Field_Goals,
        AVG(assists) AS Avg_Assists,
        AVG(rebounds_total) AS Avg_Rebounds,
        AVG(steals) AS Avg_Steals,
        AVG(turnovers) AS Avg_Turnovers,
        AVG(blocks) AS Avg_Blocks
    FROM Teams
    GROUP BY name, tm
    ORDER BY Avg_Points DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ✅ Fetch Assists vs Turnovers
def fetch_assists_vs_turnovers():
    if not table_exists("Teams"):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    query = """
    SELECT name AS Team, AVG(assists) AS Avg_Assists, AVG(turnovers) AS Avg_Turnovers
    FROM Teams
    GROUP BY name
    ORDER BY Avg_Assists DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ✅ Fetch referee statistics
def fetch_referee_data():
    if not table_exists("Officials"):
        st.error("⚠️ Error: 'Officials' table not found in the database.")
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    query = """
    SELECT o.first_name || ' ' || o.last_name AS Referee,
           COUNT(t.game_id) AS Games_Officiated,
           AVG(t.fouls_total) AS Avg_Fouls_per_Game
    FROM Officials o
    JOIN Teams t ON o.game_id = t.game_id
    WHERE o.role NOT LIKE 'commissioner'
    GROUP BY Referee
    ORDER BY Avg_Fouls_per_Game DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ✅ Fetch Player Names for Dropdown
def fetch_players():
    if not table_exists("Shots"):
        return []

    conn = sqlite3.connect(db_path)
    query = "SELECT DISTINCT player_name FROM Shots ORDER BY player_name;"
    players = pd.read_sql(query, conn)["player_name"].tolist()
    conn.close()
    return players

def generate_shot_chart(player_name):
    """Generate a shot chart that correctly plots shots with proper scaling."""

    if not os.path.exists("fiba_courtonly.jpg"):
        st.error("⚠️ Court image file 'fiba_courtonly.jpg' is missing!")
        return

    conn = sqlite3.connect(db_path)
    query = """
    SELECT x AS x_coord, y AS y_coord, r AS shot_result
    FROM Shots 
    WHERE player = ?;
    """
    df_shots = pd.read_sql_query(query, conn, params=(player_name,))
    conn.close()

    if df_shots.empty:
        st.warning(f"❌ No shot data found for {player_name}.")
        return

    # ✅ Debug: Print first 5 rows to check correct values
    st.write("Raw Shot Data:", df_shots.head())

    # ✅ Fix shot result mapping (0 = Missed, 1 = Made)
    df_shots["shot_result"] = df_shots["shot_result"].astype(int)
    df_shots["shot_result"] = df_shots["shot_result"].replace({0: "missed", 1: "made"})

    # ✅ Correct coordinate scaling to match court image (28m x 15m full court)
    df_shots["x_coord"] = (df_shots["x_coord"] / 28) * 280  # Normalize width
    df_shots["y_coord"] = 150 - ((df_shots["y_coord"] / 15) * 150)  # Flip y-coordinates

    # ✅ Debug: Show transformed coordinates
    st.write("Transformed Coordinates:", df_shots.head())

    # ✅ Load court image
    court_img = mpimg.imread("fiba_courtonly.jpg")

    # ✅ Create figure
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_aspect("equal")

    # ✅ Display court background
    ax.imshow(court_img, extent=[0, 280, 0, 150], aspect="auto")

    # ✅ Separate made & missed shots
    made_shots = df_shots[df_shots["shot_result"] == "made"]
    missed_shots = df_shots[df_shots["shot_result"] == "missed"]

    # ✅ Plot individual shots with large visible markers
    ax.scatter(made_shots["x_coord"], made_shots["y_coord"], 
               c="lime", edgecolors="black", s=150, alpha=1, zorder=3, label="Made Shots")

    ax.scatter(missed_shots["x_coord"], missed_shots["y_coord"], 
               c="red", edgecolors="black", s=150, alpha=1, zorder=3, label="Missed Shots")

    # ✅ Remove all axis elements (clean chart)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.axis("off")  # Hide axis

    # ✅ Display chart in Streamlit
    st.pyplot(fig)



# ✅ Main Function
def main():
    st.title("🏀 Basketball Stats Viewer")

    # Sidebar navigation
    page = st.sidebar.selectbox("📌 Choose a page", ["Team Season Boxscore", "Head-to-Head Comparison", "Referee Stats", "Shot Chart"])

    if page == "Team Season Boxscore":
        df = fetch_team_data()

        if df.empty:
            st.warning("No team data available.")
        else:
            st.subheader("📊 Season Team Statistics (Averages Per Game)")
            numeric_cols = df.select_dtypes(include=['number']).columns
            st.dataframe(df.style.format({col: "{:.1f}" for col in numeric_cols}))

            # 📊 Assists vs Turnovers Graph
            st.subheader("📉 Assists vs. Turnovers (Lost Plays)")
            assists_turnovers_df = fetch_assists_vs_turnovers()

            if assists_turnovers_df.empty:
                st.warning("No data available for assists vs. turnovers.")
            else:
                fig_scatter = px.scatter(
                    assists_turnovers_df, x="Avg_Turnovers", y="Avg_Assists",
                    text="Team",
                    labels={"Avg_Turnovers": "Average Turnovers Per Game", "Avg_Assists": "Average Assists Per Game"},
                    title="Assists vs. Turnovers - Playmaking vs. Lost Plays",
                    color="Avg_Assists", size="Avg_Assists",
                )
                fig_scatter.update_traces(textposition='top center')
                st.plotly_chart(fig_scatter)

    elif page == "Shot Chart":
        st.subheader("🎯 Player Shot Chart")

        # Fetch available players
        players = fetch_players()

        if not players:
            st.warning("No player data available.")
        else:
            player_name = st.selectbox("Select a Player", players)
            generate_shot_chart(player_name)

if __name__ == "__main__":
    main()
