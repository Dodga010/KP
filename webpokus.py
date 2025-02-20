def generate_shot_chart(player_name):
    """Generate a shot chart for a specific player and display it in Streamlit."""
    
    # ✅ Check if court image exists
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

    # ✅ Check if data exists for the player
    if df_shots.empty:
        st.warning(f"❌ No shot data found for {player_name}.")
        return

    # ✅ Debugging: Check unique values in shot_result
    st.write("Unique shot_result values:", df_shots["shot_result"].unique())

    # ✅ Fix issue where shot_result might be stored as 1/0 instead of "made"/"missed"
    if df_shots["shot_result"].dtype != object:
        df_shots["shot_result"] = df_shots["shot_result"].astype(str)
    
    df_shots["shot_result"] = df_shots["shot_result"].replace({"1": "made", "0": "missed"})

    # ✅ Debugging: Check if made/missed shots exist
    made_shots = df_shots[df_shots["shot_result"] == "made"]
    missed_shots = df_shots[df_shots["shot_result"] == "missed"]
    st.write(f"Total Shots: {len(df_shots)} | Made: {len(made_shots)} | Missed: {len(missed_shots)}")

    # ✅ Ensure x/y coordinates are scaled correctly
    df_shots["x_coord"] = df_shots["x_coord"] * 2.7  
    df_shots["y_coord"] = 261 - (df_shots["y_coord"] * 2.6)

    # ✅ Load court image
    court_img = mpimg.imread("fiba_courtonly.jpg")

    # ✅ Create figure
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(court_img, extent=[0, 280, 0, 261], aspect="auto", alpha=0.8)  # Make court slightly transparent

    # ✅ Heatmap (density plot for shooting zones)
    sns.kdeplot(data=df_shots, x="x_coord", y="y_coord", cmap="coolwarm", fill=True, alpha=0.6, ax=ax, bw_adjust=0.5)

    # ✅ Plot individual shots (Made & Missed)
    ax.scatter(made_shots["x_coord"], made_shots["y_coord"], 
               c="lime", edgecolors="black", s=80, label="Made Shots", alpha=0.9, zorder=3)

    ax.scatter(missed_shots["x_coord"], missed_shots["y_coord"], 
               c="red", edgecolors="black", s=80, label="Missed Shots", alpha=0.9, zorder=3)

    # ✅ Remove axis labels
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])

    # ✅ Title
    ax.text(140, 270, f"Shot Chart - {player_name}", fontsize=14, color="white", ha="center", fontweight="bold",
            bbox=dict(facecolor='black', alpha=0.6))

    plt.legend()
    st.pyplot(fig)
