"""
Cricbuzz LiveStats — Sample Data Generator
--------------------------------------------
Generates realistic (synthetic) cricket data spanning 2018-2026 so that all
25 SQL practice questions have meaningful, non-empty results to work with.

Replace this with live Cricbuzz API pulls (see api/cricbuzz_api.py) once you
have a RapidAPI key — the schema and downstream SQL/Streamlit code do not
change either way.
"""
import sqlite3
import random
import datetime

random.seed(42)

DB_PATH = "cricbuzz_livestats.db"

TEAMS = [
    ("India", "India"), ("Australia", "Australia"), ("England", "England"),
    ("South Africa", "South Africa"), ("New Zealand", "New Zealand"),
    ("Pakistan", "Pakistan"), ("Sri Lanka", "Sri Lanka"),
    ("Bangladesh", "Bangladesh"), ("West Indies", "West Indies"),
    ("Afghanistan", "Afghanistan"),
]

FIRST_NAMES = ["Rohit","Virat","Shubman","Rishabh","Jasprit","Ravindra","Hardik","KL",
    "Steve","David","Pat","Mitchell","Marnus","Glenn","Travis","Josh",
    "Joe","Ben","Jos","Harry","Jofra","Moeen","Jonny","Chris",
    "Quinton","Kagiso","Aiden","Temba","David","Anrich","Rassie","Heinrich",
    "Kane","Tom","Trent","Devon","Daryl","Mitchell","Tim","Will",
    "Babar","Shaheen","Shadab","Mohammad","Fakhar","Imam","Naseem","Haris",
    "Kusal","Dimuth","Wanindu","Dhananjaya","Pathum","Dushmantha","Charith","Angelo",
    "Shakib","Litton","Mushfiqur","Mahmudullah","Taskin","Mustafizur","Najmul","Liton",
    "Nicholas","Shai","Jason","Kieron","Andre","Alzarri","Shimron","Rovman",
    "Rashid","Mohammad","Rahmanullah","Ibrahim","Najibullah","Mujeeb","Azmatullah","Gulbadin",
]
LAST_NAMES = ["Sharma","Kohli","Gill","Pant","Bumrah","Jadeja","Pandya","Rahul",
    "Smith","Warner","Cummins","Starc","Labuschagne","Maxwell","Head","Hazlewood",
    "Root","Stokes","Buttler","Brook","Archer","Ali","Bairstow","Woakes",
    "de Kock","Rabada","Markram","Bavuma","Miller","Nortje","van der Dussen","Klaasen",
    "Williamson","Latham","Boult","Conway","Mitchell","Santner","Southee","Young",
    "Azam","Afridi","Khan","Rizwan","Zaman","ul Haq","Shah","Rauf",
    "Mendis","Karunaratne","Fernando","de Silva","Nissanka","Chameera","Asalanka","Mathews",
    "Al Hasan","Das","Rahim","Riyad","Ahmed","Rahman","Sadman","Kumar",
    "Pooran","Hope","Holder","Pollard","Russell","Joseph","Hetmyer","Powell",
    "Khan","Nabi","Zadran","Zadran","Zadran","Rahman","Omarzai","Naib",
]

ROLES = ["Batsman","Bowler","All-rounder","Wicket-keeper"]
ROLE_WEIGHTS = [0.35, 0.35, 0.20, 0.10]
BAT_STYLES = ["Right-hand bat","Left-hand bat"]
BOWL_STYLES = ["Right-arm fast","Right-arm medium","Left-arm fast","Left-arm orthodox",
               "Right-arm off break","Leg break googly","Left-arm chinaman", None]

VENUES = [
    ("Melbourne Cricket Ground","Melbourne","Australia",100024),
    ("Eden Gardens","Kolkata","India",68000),
    ("Narendra Modi Stadium","Ahmedabad","India",132000),
    ("Lord's","London","England",30000),
    ("The Oval","London","England",25500),
    ("Wankhede Stadium","Mumbai","India",33108),
    ("Sydney Cricket Ground","Sydney","Australia",48000),
    ("Newlands","Cape Town","South Africa",25000),
    ("Wanderers Stadium","Johannesburg","South Africa",34000),
    ("Basin Reserve","Wellington","New Zealand",11600),
    ("Gaddafi Stadium","Lahore","Pakistan",27000),
    ("R Premadasa Stadium","Colombo","Sri Lanka",35000),
    ("Sher-e-Bangla Stadium","Dhaka","Bangladesh",26000),
    ("Kensington Oval","Bridgetown","West Indies",28000),
    ("Sharjah Cricket Stadium","Sharjah","United Arab Emirates",27000),
    ("Bay Oval","Mount Maunganui","New Zealand",7000),
]

FORMATS = ["Test","ODI","T20I"]


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def load_schema(conn):
    with open("schema.sql") as f:
        conn.executescript(f.read())
    conn.commit()


def gen_teams(conn):
    conn.executemany("INSERT INTO teams (team_name, country) VALUES (?,?)", TEAMS)
    conn.commit()
    return [r[0] for r in conn.execute("SELECT team_id FROM teams")]


def gen_venues(conn):
    conn.executemany(
        "INSERT INTO venues (venue_name, city, country, capacity) VALUES (?,?,?,?)",
        VENUES)
    conn.commit()
    return [r[0] for r in conn.execute("SELECT venue_id FROM venues")]


def gen_players(conn, team_ids):
    players = []
    used_names = set()
    for team_id in team_ids:
        country = conn.execute("SELECT country FROM teams WHERE team_id=?", (team_id,)).fetchone()[0]
        n_players = random.randint(9, 12)
        for _ in range(n_players):
            while True:
                name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                key = (team_id, name)
                if key not in used_names:
                    used_names.add(key)
                    break
            role = random.choices(ROLES, weights=ROLE_WEIGHTS)[0]
            bat_style = random.choice(BAT_STYLES)
            bowl_style = None if role == "Batsman" or role == "Wicket-keeper" else random.choice(BOWL_STYLES[:-1])
            if role == "All-rounder" and bowl_style is None:
                bowl_style = random.choice(BOWL_STYLES[:-1])
            players.append((name, team_id, role, bat_style, bowl_style, country))
    conn.executemany(
        "INSERT INTO players (full_name, team_id, playing_role, batting_style, bowling_style, country) "
        "VALUES (?,?,?,?,?,?)", players)
    conn.commit()
    return conn.execute("SELECT player_id, team_id, playing_role FROM players").fetchall()


def gen_series(conn):
    series = []
    for year in range(2018, 2027):
        n_series = random.randint(3, 5)
        for i in range(n_series):
            host = random.choice(TEAMS)[0]
            mtype = random.choice(FORMATS)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            start_date = f"{year}-{month:02d}-{day:02d}"
            total = random.randint(2, 5) if mtype != "Test" else random.randint(2, 3)
            series.append((f"{host} Tour {year} ({mtype})", host, mtype, start_date, total))
    conn.executemany(
        "INSERT INTO series (series_name, host_country, match_type, start_date, total_matches) "
        "VALUES (?,?,?,?,?)", series)
    conn.commit()
    return conn.execute("SELECT series_id, match_type, start_date FROM series").fetchall()


def random_date_near(start_date_str, spread_days=20):
    y, m, d = map(int, start_date_str.split("-"))
    base = datetime.date(y, m, d)
    return base + datetime.timedelta(days=random.randint(0, spread_days))


def gen_matches_and_scorecards(conn, team_ids, venue_ids, series_rows, players_by_team):
    match_rows = []
    matches_meta = []  # keep python-side info to generate scorecards after insert

    for series_id, mtype, start_date in series_rows:
        n_matches = random.randint(2, 4)
        t1, t2 = random.sample(team_ids, 2)
        for i in range(n_matches):
            venue_id = random.choice(venue_ids)
            mdate = random_date_near(start_date, spread_days=25 + i * 3)
            toss_winner = random.choice([t1, t2])
            toss_decision = random.choice(["bat", "bowl"])
            winner = random.choice([t1, t2, None]) if random.random() > 0.03 else None
            victory_type = random.choice(["runs", "wickets"]) if winner else "N/A"
            victory_margin = (random.randint(5, 250) if victory_type == "runs"
                               else random.randint(1, 10)) if winner else None
            desc = f"{['1st','2nd','3rd','4th','5th'][i % 5]} {mtype}"
            match_rows.append((series_id, desc, t1, t2, venue_id, mdate.isoformat(), mtype,
                                toss_winner, toss_decision, winner, victory_margin, victory_type))

    conn.executemany(
        "INSERT INTO matches (series_id, match_desc, team1_id, team2_id, venue_id, match_date, "
        "match_format, toss_winner_team_id, toss_decision, winner_team_id, victory_margin, victory_type) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", match_rows)
    conn.commit()

    matches = conn.execute(
        "SELECT match_id, team1_id, team2_id, match_format FROM matches").fetchall()

    bat_rows, bowl_rows, field_rows = [], [], []
    max_overs = {"Test": 90, "ODI": 50, "T20I": 20}

    for match_id, t1, t2, mfmt in matches:
        for innings_no, (bat_team, bowl_team) in enumerate([(t1, t2), (t2, t1)], start=1):
            bat_players = players_by_team.get(bat_team, [])
            bowl_players = players_by_team.get(bowl_team, [])
            if not bat_players or not bowl_players:
                continue
            order = bat_players[:]
            random.shuffle(order)
            order = order[:11] if len(order) >= 11 else order

            for pos, (pid, role) in enumerate(order, start=1):
                # role-influenced scoring
                if role == "Bowler":
                    runs = int(random.triangular(0, 15, 40))
                elif role == "All-rounder":
                    runs = int(random.triangular(0, 30, 90))
                elif role == "Wicket-keeper":
                    runs = int(random.triangular(0, 25, 80))
                else:
                    runs = int(random.triangular(0, 35, 130))
                # top order tends to face more balls
                position_factor = max(0.4, 1.2 - pos * 0.07)
                balls = max(1, int(runs / max(0.35, random.uniform(0.5, 1.3)) * position_factor) + random.randint(0, 15))
                fours = min(runs // 4, random.randint(0, runs // 4 + 1))
                sixes = min((runs - fours * 4) // 6 if runs > fours * 4 else 0, random.randint(0, 4))
                sr = round((runs / balls) * 100, 2) if balls > 0 else 0.0
                is_out = 0 if (pos > 7 and random.random() < 0.15) else 1
                bat_rows.append((match_id, pid, bat_team, innings_no, pos, runs, balls, fours, sixes, sr, is_out))

            bowl_order = bowl_players[:]
            random.shuffle(bowl_order)
            n_bowlers = min(len(bowl_order), random.randint(5, 7))
            overs_pool = max_overs[mfmt]
            remaining_overs = overs_pool
            for i, (pid, role) in enumerate(bowl_order[:n_bowlers]):
                if role == "Batsman" and random.random() < 0.6:
                    continue
                is_last = (i == n_bowlers - 1)
                if mfmt == "Test":
                    overs = round(random.uniform(5, 25), 1)
                else:
                    max_share = min(remaining_overs, overs_pool / n_bowlers * random.uniform(0.6, 1.4))
                    overs = round(max(1.0, max_share) if not is_last else max(1.0, remaining_overs), 1)
                remaining_overs = max(0, remaining_overs - overs)
                economy = round(random.triangular(2.5, 5.5, 12.0), 2)
                runs_conceded = int(overs * economy)
                wkts_weight = [0.25, 0.25, 0.2, 0.15, 0.08, 0.04, 0.02, 0.01]
                wickets = random.choices(range(8), weights=wkts_weight)[0]
                bowl_rows.append((match_id, pid, bowl_team, innings_no, overs, runs_conceded, wickets, economy))

            # fielding for the bowling side
            for pid, role in random.sample(bowl_players, k=min(len(bowl_players), 6)):
                catches = random.choices([0, 1, 2, 3], weights=[0.55, 0.3, 0.1, 0.05])[0]
                stumpings = random.choices([0, 1], weights=[0.92, 0.08])[0] if role == "Wicket-keeper" else 0
                run_outs = random.choices([0, 1], weights=[0.9, 0.1])[0]
                if catches or stumpings or run_outs:
                    field_rows.append((match_id, pid, catches, stumpings, run_outs))

    conn.executemany(
        "INSERT INTO batting_scorecard (match_id, player_id, team_id, innings_no, batting_position, "
        "runs_scored, balls_faced, fours, sixes, strike_rate, is_out) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        bat_rows)
    conn.executemany(
        "INSERT INTO bowling_scorecard (match_id, player_id, team_id, innings_no, overs_bowled, "
        "runs_conceded, wickets_taken, economy_rate) VALUES (?,?,?,?,?,?,?,?)", bowl_rows)
    conn.executemany(
        "INSERT INTO fielding_scorecard (match_id, player_id, catches, stumpings, run_outs) VALUES (?,?,?,?,?)",
        field_rows)
    conn.commit()
    print(f"Inserted {len(match_rows)} matches, {len(bat_rows)} batting rows, "
          f"{len(bowl_rows)} bowling rows, {len(field_rows)} fielding rows.")


def main():
    conn = connect()
    load_schema(conn)
    team_ids = gen_teams(conn)
    venue_ids = gen_venues(conn)
    player_rows = gen_players(conn, team_ids)

    players_by_team = {}
    for pid, tid, role in player_rows:
        players_by_team.setdefault(tid, []).append((pid, role))

    series_rows = gen_series(conn)
    gen_matches_and_scorecards(conn, team_ids, venue_ids, series_rows, players_by_team)

    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["teams", "players", "venues", "series", "matches",
                        "batting_scorecard", "bowling_scorecard", "fielding_scorecard"]}
    print("Row counts:", counts)
    conn.close()


if __name__ == "__main__":
    main()
