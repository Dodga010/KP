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

# ✅ Generate Shot Chart
def generate_shot_chart(player_name):
    """Generate a shot chart with heatmap restricted within the court boundaries."""

    if not os.path.exists("fiba_courtonly.jpg"):
        st.error("⚠️ Court image file 'fiba_courtonly.jpg' is missing!")
        return

    conn = sqlite3.connect(db_path)
    query = """
    SELECT x_coord, y_coord, shot_result
    FROM Shots 
    WHERE player_name = ?;
    """
    df_shots = pd.read_sql_query(query, conn, params=(player_name,))
    conn.close()

    if df_shots.empty:
        st.warning(f"❌ No shot data found for {player_name}.")
        return

    # ✅ Convert shot_result to match 'made' or 'missed' conditions
    df_shots["shot_result"] = df_shots["shot_result"].astype(str)
    df_shots["shot_result"] = df_shots["shot_result"].replace({"1": "made", "0": "missed"})

    # ✅ Scale coordinates to match court image dimensions
    df_shots["x_coord"] = df_shots["x_coord"] * 2.8  
    df_shots["y_coord"] = 261 - (df_shots["y_coord"] * 2.61)

    # ✅ Load court image
    court_img = mpimg.imread("fiba_courtonly.jpg")

    # ✅ Create figure
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(court_img, extent=[0, 280, 0, 261], aspect="auto")

    # ✅ Heatmap (restrict to court area)
    sns.kdeplot(
        data=df_shots, 
        x="x_coord", y="y_coord", 
        cmap="coolwarm", fill=True, alpha=0.5, ax=ax, 
        bw_adjust=0.5, clip=[[0, 280], [0, 261]]  # 🔥 Restrict heatmap within the court
    )

    # ✅ Plot individual shots
    made_shots = df_shots[df_shots["shot_result"] == "made"]
    missed_shots = df_shots[df_shots["shot_result"] == "missed"]

    ax.scatter(made_shots["x_coord"], made_shots["y_coord"], 
               c="lime", edgecolors="black", s=35, alpha=1, zorder=3, label="Made Shots")

    ax.scatter(missed_shots["x_coord"], missed_shots["y_coord"], 
               c="red", edgecolors="black", s=35, alpha=1, zorder=3, label="Missed Shots")

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

elif page == "Head-to-Head Comparison":  
    df = fetch_team_data()

    if df.empty:
        st.warning("No team data available.")
    else:
        team_options = df["Team"].unique()

        # Team Selection
        st.subheader("🔄 Compare Two Teams Head-to-Head")
        team1 = st.selectbox("Select Team 1", team_options, key="team1")
        team2 = st.selectbox("Select Team 2", team_options, key="team2")

        if team1 and team2 and team1 != team2:
            st.subheader(f"📊 {team1} vs {team2} - Statistical Comparison")

            numeric_cols = df.columns[2:]  # Exclude 'Team' and 'Location'
            team1_stats = df[df["Team"] == team1][numeric_cols].reset_index(drop=True)
            team2_stats = df[df["Team"] == team2][numeric_cols].reset_index(drop=True)

            if team1_stats.empty or team2_stats.empty:
                st.error("⚠️ Error: One or both teams have no recorded stats.")
            else:
                # ✅ Ensure both teams have the same number of statistics
                team1_stats, team2_stats = team1_stats.align(team2_stats, join="outer", axis=1, fill_value=0)

                # ✅ Create a DataFrame for comparison
                comparison_df = pd.concat([team1_stats.T, team2_stats.T], axis=1)

                # ✅ Ensure the column count matches before renaming
                if comparison_df.shape[1] == 2:
                    comparison_df.columns = [team1, team2]
                    comparison_df["Stat"] = comparison_df.index

                    # 📊 Side-by-side Bar Chart
                    st.subheader("📉 Statistical Comparison")
                    fig = px.bar(comparison_df, x="Stat", y=[team1, team2],
                                 barmode="group", title=f"{team1} vs {team2} Performance",
                                 labels={"value": "Statistical Value", "Stat": "Statistic"})
                    st.plotly_chart(fig)

                    # 📈 Radar Chart for Overview (Optional)
                    radar_chart = px.line_polar(comparison_df, r=[team1, team2], theta="Stat",
                                                line_close=True, title="Radar Chart Comparison")
                    st.plotly_chart(radar_chart)
                else:
                    st.error("⚠️ Data inconsistency: The selected teams have mismatched statistics.")
        else:
            st.warning("Please select two different teams for comparison.")


    elif page == "Referee Stats":
        df_referee = fetch_referee_data()
        if df_referee.empty:
            st.warning("No referee data available.")
        else:
            st.subheader("🦺 Referee Statistics")
            st.dataframe(df_referee.style.format({"Avg_Fouls_per_Game": "{:.1f}"}))

    elif page == "Shot Chart":
        st.subheader("🎯 Player Shot Chart")
        players = fetch_players()
        if not players:
            st.warning("No player data available.")
        else:
            player_name = st.selectbox("Select a Player", players)
            generate_shot_chart(player_name)

if __name__ == "__main__":
    main()
