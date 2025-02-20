def generate_shot_chart(player_name):
    """Generate a clean shot chart with only shots and the court background."""
    
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

    # Load court image
    court_img = mpimg.imread("fiba_courtonly.jpg")

    # ✅ Fix coordinate scaling for correct positioning
    df_shots["x_coord"] = (df_shots["x_coord"] / 28) * 280  
    df_shots["y_coord"] = 150 - ((df_shots["y_coord"] / 15) * 150)  # Flip y-coordinates

    # ✅ Debugging: Check transformed shot coordinates
    st.write(df_shots.head())

    # ✅ Create figure
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_aspect("equal")

    # ✅ Set court background with correct extent
    ax.imshow(court_img, extent=[0, 280, 0, 150], aspect="auto", zorder=0)

    # ✅ Separate made & missed shots
    made_shots = df_shots[df_shots["shot_result"] == "made"]
    missed_shots = df_shots[df_shots["shot_result"] == "missed"]

    # ✅ Plot individual shots with larger markers & visible edges
    ax.scatter(made_shots["x_coord"], made_shots["y_coord"], 
               c="lime", edgecolors="black", s=150, alpha=0.9, zorder=3, label="Made Shots")

    ax.scatter(missed_shots["x_coord"], missed_shots["y_coord"], 
               c="red", edgecolors="black", s=150, alpha=0.9, zorder=3, label="Missed Shots")

    # ✅ Remove all axis elements (clean chart)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.axis("off")  # Hide axis

    # ✅ Display chart in Streamlit
    st.pyplot(fig)
