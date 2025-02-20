import sqlite3
import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ✅ Define SQLite database path (works locally and online)
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

# ✅ Fetch top 5 teams by assists per game
def fetch_top_assist_teams():
    if not table_exists("Teams"):
        return pd.DataFrame()  

    conn = sqlite3.connect(db_path)
    query = """
    SELECT name AS Team, AVG(assists) AS Avg_Assists
    FROM Teams
    GROUP BY name
    ORDER BY Avg_Assists DESC
    LIMIT 5;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ✅ Streamlit App
def main():
    st.title("🏀 Basketball Stats Viewer")

    # Sidebar navigation
    page = st.sidebar.selectbox("📌 Choose a page", ["Team Season Boxscore", "Head-to-Head Comparison", "Referee Stats"])

    if page == "Team Season Boxscore":
        df = fetch_team_data()

        if df.empty:
            st.warning("No team data available.")
        else:
            st.subheader("📊 Season Team Statistics (Averages Per Game)")
            numeric_cols = df.select_dtypes(include=['number']).columns
            st.dataframe(df.style.format({col: "{:.1f}" for col in numeric_cols}))

            # 📊 Bar Chart Comparing Teams
            st.subheader("🔎 Compare Key Team Stats")
            stat_choice = st.selectbox("Select a statistic to compare:", df.columns[3:])
            fig = px.bar(df, x="Team", y=stat_choice, color="Location",
                         labels={stat_choice: stat_choice}, 
                         title=f"{stat_choice} Comparison Between Teams (Per Game)",
                         barmode="group")
            st.plotly_chart(fig)

            # ✅ New Table: Top 5 Teams with Most Assists Per Game
            st.subheader("🏆 Top 5 Teams with Most Assists Per Game")
            top_assists_df = fetch_top_assist_teams()

            if top_assists_df.empty:
                st.warning("No data available for assists.")
            else:
                st.dataframe(top_assists_df.style.format({"Avg_Assists": "{:.1f}"}))

    elif page == "Head-to-Head Comparison":
        df = fetch_team_data()
        if df.empty:
            st.warning("No team data available.")
            return

        team_options = df["Team"].unique()

        # Select two teams to compare
        st.subheader("🔄 Compare Two Teams Head-to-Head")
        team1 = st.selectbox("Select Team 1", team_options)
        team2 = st.selectbox("Select Team 2", team_options)

        if team1 != team2:
            st.subheader(f"📊 Season Stats Comparison: {team1} vs {team2}")

            numeric_cols = df.columns[3:]  # Exclude 'Team', 'Location', 'Games_Played'
            team1_stats = df[df["Team"] == team1][numeric_cols]
            team2_stats = df[df["Team"] == team2][numeric_cols]

            if team1_stats.empty or team2_stats.empty:
                st.error("⚠️ Error: One or both teams have no recorded stats.")
            else:
                # Transpose and keep correct stat names
                team1_stats = team1_stats.T.rename(columns={team1_stats.index[0]: "Value"})
                team2_stats = team2_stats.T.rename(columns={team2_stats.index[0]: "Value"})

                # Ensure both teams have the same stats for comparison
                team1_stats, team2_stats = team1_stats.align(team2_stats, join='outer', axis=0, fill_value=0)
                team1_stats["Stat"] = team1_stats.index
                team2_stats["Stat"] = team2_stats.index

                # 📊 Separate bar charts for each team
                st.subheader(f"📉 {team1} Stats Per Game")
                fig1 = px.bar(team1_stats, x="Stat", y="Value", title=f"{team1} Stats Per Game", color="Stat")
                st.plotly_chart(fig1)

                st.subheader(f"📉 {team2} Stats Per Game")
                fig2 = px.bar(team2_stats, x="Stat", y="Value", title=f"{team2} Stats Per Game", color="Stat")
                st.plotly_chart(fig2)

    elif page == "Referee Stats":
        df_referee = fetch_referee_data()

        if df_referee.empty:
            st.warning("No referee data available.")
        else:
            st.subheader("🦺 Referee Statistics")
            st.dataframe(df_referee.style.format({"Avg_Fouls_per_Game": "{:.1f}"}))

            # 📊 Interactive bar chart for referees
            st.subheader("📉 Referee Stats: Average Fouls Called Per Game")
            fig_referee = px.bar(df_referee, x="Referee", y="Avg_Fouls_per_Game",
                                 labels={'Avg_Fouls_per_Game': 'Avg Fouls per Game'},
                                 title="Average Fouls Per Game by Referee",
                                 color="Referee")
            st.plotly_chart(fig_referee)

if __name__ == "__main__":
    main()
