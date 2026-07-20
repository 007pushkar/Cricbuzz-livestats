-- ============================================================
-- Cricbuzz LiveStats — Database Schema (SQLite, database-agnostic design)
-- ============================================================

DROP TABLE IF EXISTS fielding_scorecard;
DROP TABLE IF EXISTS bowling_scorecard;
DROP TABLE IF EXISTS batting_scorecard;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS series;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS venues;
DROP TABLE IF EXISTS teams;

CREATE TABLE teams (
    team_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name   TEXT NOT NULL UNIQUE,
    country     TEXT NOT NULL
);

CREATE TABLE players (
    player_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    team_id       INTEGER NOT NULL,
    playing_role  TEXT NOT NULL CHECK (playing_role IN ('Batsman','Bowler','All-rounder','Wicket-keeper')),
    batting_style TEXT NOT NULL CHECK (batting_style IN ('Right-hand bat','Left-hand bat')),
    bowling_style TEXT,
    country       TEXT NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE venues (
    venue_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_name  TEXT NOT NULL,
    city        TEXT NOT NULL,
    country     TEXT NOT NULL,
    capacity    INTEGER NOT NULL
);

CREATE TABLE series (
    series_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name    TEXT NOT NULL,
    host_country   TEXT NOT NULL,
    match_type     TEXT NOT NULL CHECK (match_type IN ('Test','ODI','T20I')),
    start_date     DATE NOT NULL,
    total_matches  INTEGER NOT NULL
);

CREATE TABLE matches (
    match_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id          INTEGER NOT NULL,
    match_desc         TEXT NOT NULL,
    team1_id           INTEGER NOT NULL,
    team2_id           INTEGER NOT NULL,
    venue_id           INTEGER NOT NULL,
    match_date         DATE NOT NULL,
    match_format       TEXT NOT NULL CHECK (match_format IN ('Test','ODI','T20I')),
    toss_winner_team_id INTEGER,
    toss_decision      TEXT CHECK (toss_decision IN ('bat','bowl')),
    winner_team_id     INTEGER,
    victory_margin     INTEGER,
    victory_type       TEXT CHECK (victory_type IN ('runs','wickets','N/A')),
    match_status        TEXT DEFAULT 'Completed',
    FOREIGN KEY (series_id) REFERENCES series(series_id),
    FOREIGN KEY (team1_id) REFERENCES teams(team_id),
    FOREIGN KEY (team2_id) REFERENCES teams(team_id),
    FOREIGN KEY (venue_id) REFERENCES venues(venue_id),
    FOREIGN KEY (toss_winner_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (winner_team_id) REFERENCES teams(team_id)
);

CREATE TABLE batting_scorecard (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id         INTEGER NOT NULL,
    player_id        INTEGER NOT NULL,
    team_id          INTEGER NOT NULL,
    innings_no       INTEGER NOT NULL,
    batting_position INTEGER NOT NULL,
    runs_scored      INTEGER NOT NULL DEFAULT 0,
    balls_faced      INTEGER NOT NULL DEFAULT 0,
    fours            INTEGER NOT NULL DEFAULT 0,
    sixes            INTEGER NOT NULL DEFAULT 0,
    strike_rate      REAL,
    is_out           INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE bowling_scorecard (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL,
    player_id       INTEGER NOT NULL,
    team_id         INTEGER NOT NULL,
    innings_no      INTEGER NOT NULL,
    overs_bowled    REAL NOT NULL,
    runs_conceded   INTEGER NOT NULL,
    wickets_taken   INTEGER NOT NULL,
    economy_rate    REAL,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE fielding_scorecard (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id    INTEGER NOT NULL,
    player_id   INTEGER NOT NULL,
    catches     INTEGER NOT NULL DEFAULT 0,
    stumpings   INTEGER NOT NULL DEFAULT 0,
    run_outs    INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

-- Indexes for frequently queried columns
CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_players_role ON players(playing_role);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_format ON matches(match_format);
CREATE INDEX idx_matches_series ON matches(series_id);
CREATE INDEX idx_batting_match ON batting_scorecard(match_id);
CREATE INDEX idx_batting_player ON batting_scorecard(player_id);
CREATE INDEX idx_bowling_match ON bowling_scorecard(match_id);
CREATE INDEX idx_bowling_player ON bowling_scorecard(player_id);
CREATE INDEX idx_fielding_player ON fielding_scorecard(player_id);
