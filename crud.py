"""
Cricbuzz LiveStats — CRUD Module
Centralized Create / Read / Update / Delete operations with validation,
error handling, and transaction safety for the `players` and `matches` tables.
"""
import sqlite3

DB_PATH = "cricbuzz_livestats.db"
VALID_ROLES = {"Batsman", "Bowler", "All-rounder", "Wicket-keeper"}
VALID_BAT_STYLES = {"Right-hand bat", "Left-hand bat"}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------- PLAYERS
def add_player(full_name, team_id, playing_role, batting_style, bowling_style, country):
    if not full_name or not full_name.strip():
        return False, "Player name cannot be empty."
    if playing_role not in VALID_ROLES:
        return False, f"playing_role must be one of {VALID_ROLES}"
    if batting_style not in VALID_BAT_STYLES:
        return False, f"batting_style must be one of {VALID_BAT_STYLES}"

    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO players (full_name, team_id, playing_role, batting_style, "
                "bowling_style, country) VALUES (?,?,?,?,?,?)",
                (full_name.strip(), team_id, playing_role, batting_style, bowling_style, country))
        return True, cur.lastrowid
    except sqlite3.IntegrityError as e:
        return False, f"Database integrity error: {e}"
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()


def get_players(team_id=None, playing_role=None):
    conn = get_connection()
    try:
        query = """SELECT p.player_id, p.full_name, t.team_name, p.playing_role,
                          p.batting_style, p.bowling_style, p.country
                   FROM players p JOIN teams t ON p.team_id = t.team_id WHERE 1=1"""
        params = []
        if team_id:
            query += " AND p.team_id = ?"
            params.append(team_id)
        if playing_role:
            query += " AND p.playing_role = ?"
            params.append(playing_role)
        query += " ORDER BY p.full_name"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_player(player_id, **fields):
    allowed = {"full_name", "team_id", "playing_role", "batting_style", "bowling_style", "country"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return False, "No valid fields provided to update."
    if "playing_role" in updates and updates["playing_role"] not in VALID_ROLES:
        return False, f"playing_role must be one of {VALID_ROLES}"

    conn = get_connection()
    try:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [player_id]
        with conn:
            cur = conn.execute(f"UPDATE players SET {set_clause} WHERE player_id = ?", params)
        if cur.rowcount == 0:
            return False, f"No player found with id {player_id}."
        return True, "Player updated successfully."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()


def delete_player(player_id):
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute("DELETE FROM players WHERE player_id = ?", (player_id,))
        if cur.rowcount == 0:
            return False, f"No player found with id {player_id}."
        return True, "Player deleted successfully."
    except sqlite3.IntegrityError:
        return False, "Cannot delete: player has existing scorecard records. Delete those first."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()


# ----------------------------------------------------------------- MATCHES
def add_match(series_id, match_desc, team1_id, team2_id, venue_id, match_date, match_format):
    if team1_id == team2_id:
        return False, "team1 and team2 must be different teams."
    if match_format not in {"Test", "ODI", "T20I"}:
        return False, "match_format must be Test, ODI, or T20I."

    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO matches (series_id, match_desc, team1_id, team2_id, venue_id, "
                "match_date, match_format) VALUES (?,?,?,?,?,?,?)",
                (series_id, match_desc, team1_id, team2_id, venue_id, match_date, match_format))
        return True, "Match added successfully."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()


def get_matches(limit=50):
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT m.match_id, m.match_desc, t1.team_name AS team1, t2.team_name AS team2,
                   v.venue_name, m.match_date, m.match_format, tw.team_name AS winner
            FROM matches m
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            JOIN venues v ON m.venue_id = v.venue_id
            LEFT JOIN teams tw ON m.winner_team_id = tw.team_id
            ORDER BY m.match_date DESC LIMIT ?""", (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_match_result(match_id, winner_team_id, victory_margin, victory_type):
    if victory_type not in {"runs", "wickets"}:
        return False, "victory_type must be 'runs' or 'wickets'."
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "UPDATE matches SET winner_team_id=?, victory_margin=?, victory_type=? WHERE match_id=?",
                (winner_team_id, victory_margin, victory_type, match_id))
        if cur.rowcount == 0:
            return False, f"No match found with id {match_id}."
        return True, "Match result updated successfully."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()


def delete_match(match_id):
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute("DELETE FROM matches WHERE match_id = ?", (match_id,))
        if cur.rowcount == 0:
            return False, f"No match found with id {match_id}."
        return True, "Match deleted successfully."
    except sqlite3.IntegrityError:
        return False, "Cannot delete: match has existing scorecard records. Delete those first."
    except sqlite3.Error as e:
        return False, f"Database error: {e}"
    finally:
        conn.close()
