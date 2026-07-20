"""
Cricbuzz LiveStats — Streamlit Application
Run with: streamlit run app.py
"""
import sqlite3
import pandas as pd
import streamlit as st

import crud
from queries import QUERIES
import cricbuzz_api

DB_PATH = "cricbuzz_livestats.db"

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")


def run_query(sql, params=None):
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


# ---------------------------------------------------------------- SIDEBAR
st.sidebar.title("🏏 Cricbuzz LiveStats")
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "⚡ Live Matches", "🏆 Top Player Stats", "🔍 SQL Analytics", "🛠️ CRUD Operations", "⚙️ Settings"],
)

# ====================================================================
# HOME
# ====================================================================
if page == "🏠 Home":
    st.title("🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics")
    st.markdown("""
    A cricket analytics dashboard combining **live Cricbuzz API data** with a
    **SQL database** for interactive analysis.

    **Modules**
    - ⚡ **Live Matches** — live/recent match data from the Cricbuzz API
    - 🏆 **Top Player Stats** — leading batters/bowlers
    - 🔍 **SQL Analytics** — 25 SQL practice questions run against the database
    - 🛠️ **CRUD Operations** — manage player & match records
    - ⚙️ **Settings** — configure your RapidAPI key
    """)
    col1, col2, col3, col4 = st.columns(4)
    counts = {
        "Teams": run_query("SELECT COUNT(*) c FROM teams").iloc[0, 0],
        "Players": run_query("SELECT COUNT(*) c FROM players").iloc[0, 0],
        "Matches": run_query("SELECT COUNT(*) c FROM matches").iloc[0, 0],
        "Venues": run_query("SELECT COUNT(*) c FROM venues").iloc[0, 0],
    }
    for col, (label, val) in zip([col1, col2, col3, col4], counts.items()):
        col.metric(label, int(val))

    st.info("Sample data is synthetic (seeded generator) so every SQL query below returns "
            "meaningful results out of the box. Add your RapidAPI key in **Settings** to pull live data.")

# ====================================================================
# LIVE MATCHES
# ====================================================================
elif page == "⚡ Live Matches":
    st.title("⚡ Live Matches")
    st.caption("Pulled live from the Cricbuzz API (requires a RapidAPI key — see Settings).")

    if st.button("🔄 Refresh live matches"):
        with st.spinner("Fetching live matches..."):
            matches, err = cricbuzz_api.get_live_matches()
        if err:
            st.warning(err)
        elif not matches:
            st.info("No live matches right now.")
        else:
            for m in matches:
                with st.container(border=True):
                    st.subheader(m["description"] or f"{m['team1']} vs {m['team2']}")
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**{m['team1']}** vs **{m['team2']}**")
                    c2.write(f"📍 {m['venue']}")
                    c3.write(f"Status: {m['status']}")
    else:
        st.info("Click **Refresh live matches** to fetch current data from the Cricbuzz API.")

    st.divider()
    st.subheader("Sample: recent matches from local database")
    st.dataframe(run_query("""
        SELECT m.match_desc, t1.team_name AS team1, t2.team_name AS team2,
               v.venue_name, m.match_date, m.match_format
        FROM matches m
        JOIN teams t1 ON m.team1_id=t1.team_id
        JOIN teams t2 ON m.team2_id=t2.team_id
        JOIN venues v ON m.venue_id=v.venue_id
        ORDER BY m.match_date DESC LIMIT 15
    """), use_container_width=True)

# ====================================================================
# TOP PLAYER STATS
# ====================================================================
elif page == "🏆 Top Player Stats":
    st.title("🏆 Top Player Stats")
    tab1, tab2, tab3 = st.tabs(["Most Runs", "Most Wickets", "Highest Scores"])

    with tab1:
        st.dataframe(run_query("""
            SELECT p.full_name, t.team_name, SUM(b.runs_scored) AS total_runs,
                   ROUND(SUM(b.runs_scored)*1.0/NULLIF(SUM(b.is_out),0),2) AS batting_average
            FROM batting_scorecard b
            JOIN players p ON b.player_id=p.player_id
            JOIN teams t ON p.team_id=t.team_id
            GROUP BY p.player_id ORDER BY total_runs DESC LIMIT 15
        """), use_container_width=True)

    with tab2:
        st.dataframe(run_query("""
            SELECT p.full_name, t.team_name, SUM(w.wickets_taken) AS total_wickets,
                   ROUND(SUM(w.runs_conceded)*1.0/NULLIF(SUM(w.overs_bowled),0),2) AS economy
            FROM bowling_scorecard w
            JOIN players p ON w.player_id=p.player_id
            JOIN teams t ON p.team_id=t.team_id
            GROUP BY p.player_id ORDER BY total_wickets DESC LIMIT 15
        """), use_container_width=True)

    with tab3:
        st.dataframe(run_query("""
            SELECT p.full_name, t.team_name, m.match_format, MAX(b.runs_scored) AS highest_score
            FROM batting_scorecard b
            JOIN players p ON b.player_id=p.player_id
            JOIN teams t ON p.team_id=t.team_id
            JOIN matches m ON b.match_id=m.match_id
            GROUP BY p.player_id ORDER BY highest_score DESC LIMIT 15
        """), use_container_width=True)

    st.divider()
    st.caption("Live top stats via Cricbuzz API:")
    if st.button("🔄 Fetch live rankings"):
        data, err = cricbuzz_api.get_top_stats()
        if err:
            st.warning(err)
        else:
            st.json(data)

# ====================================================================
# SQL ANALYTICS
# ====================================================================
elif page == "🔍 SQL Analytics":
    st.title("🔍 SQL Queries & Analytics")
    st.caption("25 practice queries — Beginner → Intermediate → Advanced")

    question = st.selectbox("Choose a SQL question", list(QUERIES.keys()))
    sql = QUERIES[question]

    with st.expander("View SQL"):
        st.code(sql.strip(), language="sql")

    try:
        df = run_query(sql)
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(df)} row(s) returned.")
        if not df.empty and df.select_dtypes("number").shape[1] >= 1:
            numeric_cols = df.select_dtypes("number").columns.tolist()
            if len(numeric_cols) >= 1 and df.shape[0] <= 30:
                chart_col = st.selectbox("Visualize column (optional)", ["(none)"] + numeric_cols)
                if chart_col != "(none)":
                    st.bar_chart(df.set_index(df.columns[0])[chart_col])
    except Exception as e:
        st.error(f"Query failed: {e}")

# ====================================================================
# CRUD OPERATIONS
# ====================================================================
elif page == "🛠️ CRUD Operations":
    st.title("🛠️ CRUD Operations")
    entity = st.radio("Manage:", ["Players", "Matches"], horizontal=True)
    teams_df = run_query("SELECT team_id, team_name FROM teams ORDER BY team_name")

    if entity == "Players":
        tab_create, tab_read, tab_update, tab_delete = st.tabs(["➕ Create", "📋 Read", "✏️ Update", "🗑️ Delete"])

        with tab_create:
            with st.form("add_player_form"):
                full_name = st.text_input("Full name")
                team_name = st.selectbox("Team", teams_df["team_name"])
                role = st.selectbox("Playing role", ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"])
                bat_style = st.selectbox("Batting style", ["Right-hand bat", "Left-hand bat"])
                bowl_style = st.text_input("Bowling style (optional)")
                country = st.text_input("Country")
                submitted = st.form_submit_button("Add Player")
                if submitted:
                    team_id = int(teams_df.loc[teams_df.team_name == team_name, "team_id"].iloc[0])
                    ok, result = crud.add_player(full_name, team_id, role, bat_style, bowl_style or None, country)
                    if ok:
                        st.success(f"Player added successfully (player_id = {result}).")
                    else:
                        st.error(result)

        with tab_read:
            filt_team = st.selectbox("Filter by team (optional)", ["All"] + teams_df["team_name"].tolist())
            team_id_filter = None
            if filt_team != "All":
                team_id_filter = int(teams_df.loc[teams_df.team_name == filt_team, "team_id"].iloc[0])
            players = crud.get_players(team_id=team_id_filter)
            st.dataframe(pd.DataFrame(players), use_container_width=True)

        with tab_update:
            with st.form("update_player_form"):
                player_id = st.number_input("Player ID to update", min_value=1, step=1)
                new_role = st.selectbox("New playing role", ["(no change)", "Batsman", "Bowler", "All-rounder", "Wicket-keeper"])
                new_country = st.text_input("New country (leave blank for no change)")
                submitted = st.form_submit_button("Update Player")
                if submitted:
                    kwargs = {}
                    if new_role != "(no change)":
                        kwargs["playing_role"] = new_role
                    if new_country.strip():
                        kwargs["country"] = new_country.strip()
                    ok, msg = crud.update_player(int(player_id), **kwargs)
                    (st.success if ok else st.error)(msg)

        with tab_delete:
            with st.form("delete_player_form"):
                player_id = st.number_input("Player ID to delete", min_value=1, step=1, key="del_pid")
                submitted = st.form_submit_button("Delete Player", type="primary")
                if submitted:
                    ok, msg = crud.delete_player(int(player_id))
                    (st.success if ok else st.error)(msg)

    else:  # Matches
        tab_read, tab_update = st.tabs(["📋 Read", "✏️ Update Result"])
        with tab_read:
            st.dataframe(pd.DataFrame(crud.get_matches(limit=100)), use_container_width=True)
        with tab_update:
            with st.form("update_match_form"):
                match_id = st.number_input("Match ID", min_value=1, step=1)
                winner_team = st.selectbox("Winning team", teams_df["team_name"])
                margin = st.number_input("Victory margin", min_value=0, step=1)
                vtype = st.selectbox("Victory type", ["runs", "wickets"])
                submitted = st.form_submit_button("Update Result")
                if submitted:
                    team_id = int(teams_df.loc[teams_df.team_name == winner_team, "team_id"].iloc[0])
                    ok, msg = crud.update_match_result(int(match_id), team_id, int(margin), vtype)
                    (st.success if ok else st.error)(msg)

# ====================================================================
# SETTINGS
# ====================================================================
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.markdown("""
    ### Connecting live Cricbuzz API data
    1. Get a free key at [RapidAPI — Cricbuzz Cricket](https://rapidapi.com/cricketapilive/api/cricbuzz-cricket/)
    2. In Colab, set it as an environment variable **before** launching Streamlit:
       ```python
       import os
       os.environ["RAPIDAPI_KEY"] = "your_key_here"
       ```
       or store it as a Colab secret named `CRICBUZZ_API_KEY`.
    3. Restart the app — the Live Matches and Top Player Stats pages will
       automatically start using live data.

    ### Database
    - Engine: SQLite (file: `cricbuzz_livestats.db`) — swap the connection
      string in `crud.py` / `app.py` for MySQL/PostgreSQL without touching
      the SQL query logic.
    - Schema: `schema.sql`
    - Sample data: `generate_data.py` (synthetic, seeded, reproducible)
    """)
