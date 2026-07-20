"""
Cricbuzz LiveStats — Live API Integration
Wraps the Cricbuzz Cricket API (via RapidAPI) with retries, error handling,
and JSON parsing. Requires a free RapidAPI key:
  1. Go to https://rapidapi.com/cricketapilive/api/cricbuzz-cricket/
  2. Subscribe to the free tier and copy your X-RapidAPI-Key
  3. In Colab: from google.colab import userdata; set a secret named
     CRICBUZZ_API_KEY, or just set the RAPIDAPI_KEY variable below.

If no key is configured, every function returns an empty result with a
clear message instead of raising — the rest of the app (SQL analytics,
CRUD, synthetic data) keeps working without live data.
"""
import os
import time
import requests

RAPIDAPI_HOST = "cricbuzz-cricket.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"


def _get_api_key():
    # Priority: explicit env var > Colab secret > empty
    key = os.environ.get("RAPIDAPI_KEY", "")
    if key:
        return key
    try:
        from google.colab import userdata  # type: ignore
        return userdata.get("CRICBUZZ_API_KEY") or ""
    except Exception:
        return ""


def _headers():
    return {
        "X-RapidAPI-Key": _get_api_key(),
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }


def _get(endpoint, params=None, max_retries=3, backoff=1.5):
    """GET with retry + exponential backoff. Returns (data, error)."""
    api_key = _get_api_key()
    if not api_key:
        return None, ("No RAPIDAPI_KEY configured. Set os.environ['RAPIDAPI_KEY'] = '<your key>' "
                       "or a Colab secret named CRICBUZZ_API_KEY to enable live data.")

    url = f"{BASE_URL}{endpoint}"
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=_headers(), params=params, timeout=10)
            if resp.status_code == 200:
                try:
                    return resp.json(), None
                except ValueError:
                    return None, "Received a non-JSON response from the API."
            elif resp.status_code == 429:
                last_err = "Rate limit exceeded (429)."
                time.sleep(backoff ** attempt)
            elif resp.status_code == 401:
                return None, "Unauthorized (401) — check your RapidAPI key."
            else:
                last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.exceptions.Timeout:
            last_err = "Request timed out."
        except requests.exceptions.ConnectionError:
            last_err = "Connection error — check your network."
        except requests.exceptions.RequestException as e:
            last_err = f"Request failed: {e}"
        time.sleep(backoff ** attempt)
    return None, f"Failed after {max_retries} attempts. Last error: {last_err}"


def get_live_matches():
    """Live/recent match summaries."""
    data, err = _get("/matches/v1/live")
    if err:
        return [], err
    matches = []
    for type_match in data.get("typeMatches", []):
        for series in type_match.get("seriesMatches", []):
            wrapper = series.get("seriesAdWrapper", {})
            for m in wrapper.get("matches", []):
                info = m.get("matchInfo", {})
                matches.append({
                    "match_id": info.get("matchId"),
                    "description": info.get("matchDesc"),
                    "team1": info.get("team1", {}).get("teamName"),
                    "team2": info.get("team2", {}).get("teamName"),
                    "venue": info.get("venueInfo", {}).get("ground"),
                    "status": info.get("status"),
                })
    return matches, None


def get_recent_matches():
    data, err = _get("/matches/v1/recent")
    return (data, None) if not err else ([], err)


def get_upcoming_matches():
    data, err = _get("/matches/v1/upcoming")
    return (data, None) if not err else ([], err)


def get_top_stats(stats_type="mostRuns"):
    """
    stats_type examples: mostRuns, mostWickets, highestScore, bestBowling
    (see the Cricbuzz API 'stats' endpoints for the exact list).
    """
    data, err = _get(f"/stats/v1/rankings/batsmen", params={"formatType": "test"})
    return (data, None) if not err else ({}, err)


def get_player_info(player_id):
    data, err = _get(f"/players/v1/{player_id}")
    return (data, None) if not err else ({}, err)


def get_series_list():
    data, err = _get("/series/v1/international")
    return (data, None) if not err else ({}, err)
