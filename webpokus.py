import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px

# Function to fetch team **average stats per game**
def fetch_team_data():
    db_path = "C:\\Users\\dolez\\Desktop\\KP_Brno\\database.db"
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

# Function to fetch referee stats
def fetch_referee_data():
    db_path = "C:\\Users\\dolez\\Desktop\\KP_Brno\\database.db"
    conn = sqlite3.connect(db_path)

    query = """
    SELECT o.first_name || ' ' || o.last_name AS Referee,
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

# Streamlit app
def main():
    st.title("🏀 Basketball Stats Viewer")

    # Sidebar navigation
    page = st.sidebar.selectbox("📌 Choose a page", ["Team Season Boxscore", "Head-to-Head Comparison", "Referee Stats"])

    if page == "Team Season Boxscore":
        df = fetch_team_data()

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

    elif page == "Head-to-Head Comparison":
        df = fetch_team_data()
        team_options = df["Team"].unique()

        # Select two teams to compare
        st.subheader("🔄 Compare Two Teams Head-to-Head")
        team1 = st.selectbox("Select Team 1", team_options)
        team2 = st.selectbox("Select Team 2", team_options)

        if team1 != team2:
            st.subheader(f"📊 Season Stats Comparison: {team1} vs {team2}")

            # **Fix: Ensure teams exist in dataset before comparing**
            if team1 not in df["Team"].values or team2 not in df["Team"].values:
                st.error("⚠️ Error: One or both teams do not exist in the dataset.")
            else:
                # **Fix: Select only numeric columns for comparison**
                numeric_cols = df.columns[3:]  # Exclude 'Team', 'Location', 'Games_Played'
                team1_stats = df[df["Team"] == team1][numeric_cols]
                team2_stats = df[df["Team"] == team2][numeric_cols]

                # **Fix: Transpose and keep correct stat names**
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
