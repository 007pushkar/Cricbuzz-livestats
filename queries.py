"""
Cricbuzz LiveStats — 25 SQL Practice Queries
Beginner (1-8) -> Intermediate (9-16) -> Advanced (17-25)
Every query is plain ANSI-ish SQL that runs on SQLite, and will also run
(with trivial syntax tweaks noted inline) on MySQL / PostgreSQL.
"""

QUERIES = {

# ---------------------------------------------------------------- BEGINNER
"Q1: Indian players (role, batting/bowling style)": """
SELECT full_name, playing_role, batting_style, bowling_style
FROM players
WHERE country = 'India';
""",

"Q2: Matches in the last 30 days": """
SELECT m.match_desc, t1.team_name AS team1, t2.team_name AS team2,
       v.venue_name, v.city, m.match_date
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
JOIN venues v ON m.venue_id = v.venue_id
WHERE m.match_date >= date((SELECT MAX(match_date) FROM matches), '-30 day')
ORDER BY m.match_date DESC;
""",

"Q3: Top 10 ODI run scorers": """
SELECT p.full_name,
       SUM(b.runs_scored) AS total_runs,
       ROUND(SUM(b.runs_scored) * 1.0 / NULLIF(SUM(b.is_out), 0), 2) AS batting_average,
       SUM(CASE WHEN b.runs_scored >= 100 THEN 1 ELSE 0 END) AS centuries
FROM batting_scorecard b
JOIN players p ON b.player_id = p.player_id
JOIN matches m ON b.match_id = m.match_id
WHERE m.match_format = 'ODI'
GROUP BY p.player_id
ORDER BY total_runs DESC
LIMIT 10;
""",

"Q4: Venues with capacity > 50,000": """
SELECT venue_name, city, country, capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC;
""",

"Q5: Total wins per team": """
SELECT t.team_name, COUNT(*) AS total_wins
FROM matches m
JOIN teams t ON m.winner_team_id = t.team_id
GROUP BY t.team_id
ORDER BY total_wins DESC;
""",

"Q6: Player count per playing role": """
SELECT playing_role, COUNT(*) AS player_count
FROM players
GROUP BY playing_role
ORDER BY player_count DESC;
""",

"Q7: Highest individual score per format": """
SELECT m.match_format, MAX(b.runs_scored) AS highest_score
FROM batting_scorecard b
JOIN matches m ON b.match_id = m.match_id
GROUP BY m.match_format;
""",

"Q8: Series started in 2024": """
SELECT series_name, host_country, match_type, start_date, total_matches
FROM series
WHERE strftime('%Y', start_date) = '2024';
""",

# ---------------------------------------------------------- INTERMEDIATE
"Q9: All-rounders with 1000+ runs and 50+ wickets": """
SELECT p.full_name,
       SUM(b.runs_scored) AS total_runs,
       SUM(w.wickets_taken) AS total_wickets,
       m.match_format
FROM players p
JOIN batting_scorecard b ON p.player_id = b.player_id
JOIN bowling_scorecard w ON p.player_id = w.player_id AND b.match_id = w.match_id
JOIN matches m ON b.match_id = m.match_id
WHERE p.playing_role = 'All-rounder'
GROUP BY p.player_id, m.match_format
HAVING SUM(b.runs_scored) > 1000 AND SUM(w.wickets_taken) > 50;
""",

"Q10: Last 20 completed matches": """
SELECT m.match_desc, t1.team_name AS team1, t2.team_name AS team2,
       tw.team_name AS winner, m.victory_margin, m.victory_type, v.venue_name
FROM matches m
JOIN teams t1 ON m.team1_id = t1.team_id
JOIN teams t2 ON m.team2_id = t2.team_id
LEFT JOIN teams tw ON m.winner_team_id = tw.team_id
JOIN venues v ON m.venue_id = v.venue_id
WHERE m.winner_team_id IS NOT NULL
ORDER BY m.match_date DESC
LIMIT 20;
""",

"Q11: Cross-format performance comparison (players in 2+ formats)": """
SELECT p.full_name,
       SUM(CASE WHEN m.match_format='Test' THEN b.runs_scored ELSE 0 END) AS test_runs,
       SUM(CASE WHEN m.match_format='ODI'  THEN b.runs_scored ELSE 0 END) AS odi_runs,
       SUM(CASE WHEN m.match_format='T20I' THEN b.runs_scored ELSE 0 END) AS t20i_runs,
       ROUND(SUM(b.runs_scored)*1.0 / NULLIF(SUM(b.is_out),0), 2) AS overall_average
FROM batting_scorecard b
JOIN players p ON b.player_id = p.player_id
JOIN matches m ON b.match_id = m.match_id
GROUP BY p.player_id
HAVING COUNT(DISTINCT m.match_format) >= 2
ORDER BY overall_average DESC;
""",

"Q12: Home vs away team performance": """
SELECT t.team_name,
       SUM(CASE WHEN v.country = t.country AND m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS home_wins,
       SUM(CASE WHEN v.country != t.country AND m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS away_wins
FROM matches m
JOIN teams t ON t.team_id IN (m.team1_id, m.team2_id)
JOIN venues v ON m.venue_id = v.venue_id
GROUP BY t.team_id
ORDER BY home_wins DESC;
""",

"Q13: Batting partnerships >= 100 runs (consecutive positions)": """
SELECT p1.full_name AS batsman_1, p2.full_name AS batsman_2,
       (b1.runs_scored + b2.runs_scored) AS partnership_runs,
       b1.match_id, b1.innings_no
FROM batting_scorecard b1
JOIN batting_scorecard b2
  ON b1.match_id = b2.match_id
 AND b1.innings_no = b2.innings_no
 AND b2.batting_position = b1.batting_position + 1
JOIN players p1 ON b1.player_id = p1.player_id
JOIN players p2 ON b2.player_id = p2.player_id
WHERE (b1.runs_scored + b2.runs_scored) >= 100
ORDER BY partnership_runs DESC
LIMIT 25;
""",

"Q14: Bowling performance by venue (>=3 matches at venue, >=4 overs/match)": """
SELECT p.full_name, v.venue_name,
       ROUND(AVG(w.economy_rate), 2) AS avg_economy,
       SUM(w.wickets_taken) AS total_wickets,
       COUNT(DISTINCT w.match_id) AS matches_played
FROM bowling_scorecard w
JOIN players p ON w.player_id = p.player_id
JOIN matches m ON w.match_id = m.match_id
JOIN venues v ON m.venue_id = v.venue_id
WHERE w.overs_bowled >= 4
GROUP BY p.player_id, v.venue_id
HAVING COUNT(DISTINCT w.match_id) >= 3
ORDER BY avg_economy ASC;
""",

"Q15: Player performance in close matches": """
WITH close_matches AS (
    SELECT match_id, winner_team_id
    FROM matches
    WHERE (victory_type = 'runs' AND victory_margin < 50)
       OR (victory_type = 'wickets' AND victory_margin < 5)
)
SELECT p.full_name,
       ROUND(AVG(b.runs_scored), 2) AS avg_runs_close_matches,
       COUNT(*) AS close_matches_played,
       SUM(CASE WHEN cm.winner_team_id = b.team_id THEN 1 ELSE 0 END) AS close_matches_won
FROM batting_scorecard b
JOIN close_matches cm ON b.match_id = cm.match_id
JOIN players p ON b.player_id = p.player_id
GROUP BY p.player_id
ORDER BY avg_runs_close_matches DESC
LIMIT 15;
""",

"Q16: Yearly batting trend since 2020 (>=5 matches/year)": """
SELECT p.full_name, strftime('%Y', m.match_date) AS year,
       ROUND(AVG(b.runs_scored), 2) AS avg_runs,
       ROUND(AVG(b.strike_rate), 2) AS avg_strike_rate,
       COUNT(*) AS matches_played
FROM batting_scorecard b
JOIN players p ON b.player_id = p.player_id
JOIN matches m ON b.match_id = m.match_id
WHERE m.match_date >= '2020-01-01'
GROUP BY p.player_id, year
HAVING COUNT(*) >= 5
ORDER BY p.full_name, year;
""",

# --------------------------------------------------------------- ADVANCED
"Q17: Toss advantage analysis": """
SELECT toss_decision,
       COUNT(*) AS total_matches,
       SUM(CASE WHEN toss_winner_team_id = winner_team_id THEN 1 ELSE 0 END) AS toss_winner_also_won,
       ROUND(100.0 * SUM(CASE WHEN toss_winner_team_id = winner_team_id THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM matches
WHERE winner_team_id IS NOT NULL AND toss_decision IS NOT NULL
GROUP BY toss_decision;
""",

"Q18: Most economical bowlers (limited-overs, >=10 matches, >=2 overs/match avg)": """
SELECT p.full_name,
       ROUND(SUM(w.runs_conceded) * 1.0 / SUM(w.overs_bowled), 2) AS overall_economy,
       SUM(w.wickets_taken) AS total_wickets,
       COUNT(DISTINCT w.match_id) AS matches_played
FROM bowling_scorecard w
JOIN players p ON w.player_id = p.player_id
JOIN matches m ON w.match_id = m.match_id
WHERE m.match_format IN ('ODI','T20I')
GROUP BY p.player_id
HAVING COUNT(DISTINCT w.match_id) >= 10
   AND (SUM(w.overs_bowled) * 1.0 / COUNT(DISTINCT w.match_id)) >= 2
ORDER BY overall_economy ASC
LIMIT 15;
""",

"Q19: Most consistent batsmen (avg runs & stddev, since 2022, >=10 balls/innings)": """
SELECT p.full_name,
       ROUND(AVG(b.runs_scored), 2) AS avg_runs,
       ROUND(
         SQRT(AVG(b.runs_scored * b.runs_scored) - AVG(b.runs_scored) * AVG(b.runs_scored))
       , 2) AS stddev_runs,
       COUNT(*) AS innings_played
FROM batting_scorecard b
JOIN players p ON b.player_id = p.player_id
JOIN matches m ON b.match_id = m.match_id
WHERE b.balls_faced >= 10 AND m.match_date >= '2022-01-01'
GROUP BY p.player_id
HAVING COUNT(*) >= 5
ORDER BY stddev_runs ASC
LIMIT 15;
""",

"Q20: Format-wise match count & batting average (>=20 total matches)": """
SELECT p.full_name,
       SUM(CASE WHEN m.match_format='Test' THEN 1 ELSE 0 END) AS test_matches,
       SUM(CASE WHEN m.match_format='ODI'  THEN 1 ELSE 0 END) AS odi_matches,
       SUM(CASE WHEN m.match_format='T20I' THEN 1 ELSE 0 END) AS t20i_matches,
       ROUND(SUM(CASE WHEN m.match_format='Test' THEN b.runs_scored ELSE 0 END) * 1.0 /
             NULLIF(SUM(CASE WHEN m.match_format='Test' THEN b.is_out ELSE 0 END),0), 2) AS test_avg,
       ROUND(SUM(CASE WHEN m.match_format='ODI' THEN b.runs_scored ELSE 0 END) * 1.0 /
             NULLIF(SUM(CASE WHEN m.match_format='ODI' THEN b.is_out ELSE 0 END),0), 2) AS odi_avg,
       ROUND(SUM(CASE WHEN m.match_format='T20I' THEN b.runs_scored ELSE 0 END) * 1.0 /
             NULLIF(SUM(CASE WHEN m.match_format='T20I' THEN b.is_out ELSE 0 END),0), 2) AS t20i_avg
FROM batting_scorecard b
JOIN players p ON b.player_id = p.player_id
JOIN matches m ON b.match_id = m.match_id
GROUP BY p.player_id
HAVING (test_matches + odi_matches + t20i_matches) >= 20
ORDER BY (test_matches + odi_matches + t20i_matches) DESC;
""",

"Q21: Composite player ranking (batting + bowling + fielding points)": """
WITH bat AS (
  SELECT b.player_id, m.match_format,
         SUM(b.runs_scored) AS runs, AVG(b.strike_rate) AS sr,
         SUM(b.runs_scored)*1.0/NULLIF(SUM(b.is_out),0) AS avg
  FROM batting_scorecard b JOIN matches m ON b.match_id = m.match_id
  GROUP BY b.player_id, m.match_format
),
bowl AS (
  SELECT w.player_id, m.match_format,
         SUM(w.wickets_taken) AS wkts,
         SUM(w.runs_conceded)*1.0/NULLIF(SUM(w.overs_bowled),0) AS econ,
         AVG(w.runs_conceded*1.0/NULLIF(w.wickets_taken,0)) AS bowl_avg
  FROM bowling_scorecard w JOIN matches m ON w.match_id = m.match_id
  GROUP BY w.player_id, m.match_format
),
field AS (
  SELECT player_id, SUM(catches) AS catches, SUM(stumpings) AS stumpings
  FROM fielding_scorecard GROUP BY player_id
)
SELECT p.full_name, COALESCE(bat.match_format, bowl.match_format) AS format,
   ROUND(COALESCE(bat.runs,0)*0.01 + COALESCE(bat.avg,0)*0.5 + COALESCE(bat.sr,0)*0.3, 2) AS batting_points,
   ROUND(COALESCE(bowl.wkts,0)*2 + (50 - COALESCE(bowl.bowl_avg,50))*0.5 + (6 - COALESCE(bowl.econ,6))*2, 2) AS bowling_points,
   ROUND(COALESCE(field.catches,0)*3 + COALESCE(field.stumpings,0)*5, 2) AS fielding_points
FROM players p
LEFT JOIN bat ON p.player_id = bat.player_id
LEFT JOIN bowl ON p.player_id = bowl.player_id AND bat.match_format = bowl.match_format
LEFT JOIN field ON p.player_id = field.player_id
WHERE bat.match_format IS NOT NULL OR bowl.match_format IS NOT NULL
ORDER BY (batting_points + bowling_points + fielding_points) DESC
LIMIT 20;
""",

"Q22: Head-to-head analysis (teams with >=5 matches in last 3 years)": """
WITH h2h AS (
    SELECT team1_id AS team_a, team2_id AS team_b, winner_team_id, victory_margin, match_date
    FROM matches
    WHERE match_date >= date((SELECT MAX(match_date) FROM matches), '-3 years')
)
SELECT t1.team_name AS team_a, t2.team_name AS team_b,
       COUNT(*) AS matches_played,
       SUM(CASE WHEN h2h.winner_team_id = h2h.team_a THEN 1 ELSE 0 END) AS team_a_wins,
       SUM(CASE WHEN h2h.winner_team_id = h2h.team_b THEN 1 ELSE 0 END) AS team_b_wins,
       ROUND(AVG(h2h.victory_margin), 2) AS avg_victory_margin,
       ROUND(100.0 * SUM(CASE WHEN h2h.winner_team_id = h2h.team_a THEN 1 ELSE 0 END) / COUNT(*), 2) AS team_a_win_pct
FROM h2h
JOIN teams t1 ON h2h.team_a = t1.team_id
JOIN teams t2 ON h2h.team_b = t2.team_id
GROUP BY h2h.team_a, h2h.team_b
HAVING COUNT(*) >= 5
ORDER BY matches_played DESC;
""",

"Q23: Recent form & momentum (last 10 innings per player)": """
WITH ranked AS (
    SELECT b.player_id, b.runs_scored, b.strike_rate,
           ROW_NUMBER() OVER (PARTITION BY b.player_id ORDER BY m.match_date DESC) AS rn
    FROM batting_scorecard b JOIN matches m ON b.match_id = m.match_id
)
SELECT p.full_name,
   ROUND(AVG(CASE WHEN rn <= 5  THEN runs_scored END), 2) AS avg_runs_last5,
   ROUND(AVG(CASE WHEN rn <= 10 THEN runs_scored END), 2) AS avg_runs_last10,
   ROUND(AVG(CASE WHEN rn <= 10 THEN strike_rate END), 2) AS recent_strike_rate,
   SUM(CASE WHEN rn <= 10 AND runs_scored >= 50 THEN 1 ELSE 0 END) AS scores_above_50,
   ROUND(
     SQRT(AVG(CASE WHEN rn<=10 THEN runs_scored*runs_scored END) -
          AVG(CASE WHEN rn<=10 THEN runs_scored END) * AVG(CASE WHEN rn<=10 THEN runs_scored END))
   , 2) AS consistency_stddev,
   CASE
       WHEN AVG(CASE WHEN rn <= 10 THEN runs_scored END) >= 45 THEN 'Excellent Form'
       WHEN AVG(CASE WHEN rn <= 10 THEN runs_scored END) >= 30 THEN 'Good Form'
       WHEN AVG(CASE WHEN rn <= 10 THEN runs_scored END) >= 15 THEN 'Average Form'
       ELSE 'Poor Form'
   END AS form_category
FROM ranked r
JOIN players p ON r.player_id = p.player_id
WHERE rn <= 10
GROUP BY p.player_id
HAVING COUNT(*) >= 5
ORDER BY avg_runs_last10 DESC;
""",

"Q24: Best batting partnerships (>=5 partnerships, consecutive positions)": """
WITH partnerships AS (
    SELECT b1.player_id AS p1_id, b2.player_id AS p2_id,
           (b1.runs_scored + b2.runs_scored) AS runs
    FROM batting_scorecard b1
    JOIN batting_scorecard b2
      ON b1.match_id = b2.match_id AND b1.innings_no = b2.innings_no
     AND b2.batting_position = b1.batting_position + 1
)
SELECT pl1.full_name AS player_1, pl2.full_name AS player_2,
       COUNT(*) AS partnerships_count,
       ROUND(AVG(runs), 2) AS avg_partnership_runs,
       SUM(CASE WHEN runs > 50 THEN 1 ELSE 0 END) AS partnerships_over_50,
       MAX(runs) AS highest_partnership,
       ROUND(100.0 * SUM(CASE WHEN runs > 50 THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct
FROM partnerships
JOIN players pl1 ON partnerships.p1_id = pl1.player_id
JOIN players pl2 ON partnerships.p2_id = pl2.player_id
GROUP BY p1_id, p2_id
HAVING COUNT(*) >= 5
ORDER BY avg_partnership_runs DESC
LIMIT 15;
""",

"Q25: Career trajectory — quarterly performance trend": """
WITH quarterly AS (
    SELECT b.player_id,
           strftime('%Y', m.match_date) || '-Q' ||
             ((CAST(strftime('%m', m.match_date) AS INTEGER) - 1) / 3 + 1) AS quarter,
           AVG(b.runs_scored) AS avg_runs,
           AVG(b.strike_rate) AS avg_sr,
           COUNT(*) AS matches_in_quarter
    FROM batting_scorecard b JOIN matches m ON b.match_id = m.match_id
    GROUP BY b.player_id, quarter
    HAVING COUNT(*) >= 3
),
trend AS (
    SELECT player_id, quarter, avg_runs, avg_sr,
           LAG(avg_runs) OVER (PARTITION BY player_id ORDER BY quarter) AS prev_avg_runs,
           COUNT(*) OVER (PARTITION BY player_id) AS quarters_count
    FROM quarterly
)
SELECT p.full_name, t.quarter, ROUND(t.avg_runs,2) AS avg_runs, ROUND(t.avg_sr,2) AS avg_sr,
       ROUND(t.avg_runs - t.prev_avg_runs, 2) AS change_vs_prev_quarter,
       CASE
           WHEN t.avg_runs > t.prev_avg_runs THEN 'Improving'
           WHEN t.avg_runs < t.prev_avg_runs THEN 'Declining'
           ELSE 'Stable'
       END AS trend_direction
FROM trend t
JOIN players p ON t.player_id = p.player_id
WHERE t.quarters_count >= 6 AND t.prev_avg_runs IS NOT NULL
ORDER BY p.full_name, t.quarter;
""",
}
