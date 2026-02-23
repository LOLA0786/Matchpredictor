"""
Parses Cricsheet IPL JSON files into clean DataFrames.
One row per match in matches_df, one row per delivery in balls_df.
"""
import json
from pathlib import Path
import pandas as pd
from tqdm import tqdm

def load_all_matches(json_dir: Path):
    json_files = sorted(json_dir.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(
            f"No JSON files in {json_dir}. Run: python scripts/download_cricsheet.py"
        )
    print(f"Parsing {len(json_files)} match files...")
    all_matches, all_balls = [], []
    for filepath in tqdm(json_files, desc="Parsing"):
        try:
            match_row, ball_rows = _parse_match(filepath)
            if match_row:
                all_matches.append(match_row)
                all_balls.extend(ball_rows)
        except Exception as e:
            print(f"  Skipping {filepath.name}: {e}")

    matches_df = pd.DataFrame(all_matches)
    balls_df   = pd.DataFrame(all_balls)
    print(f"Loaded {len(matches_df)} matches, {len(balls_df):,} deliveries.")
    return matches_df, balls_df

def _parse_match(filepath):
    with open(filepath, encoding="utf-8") as f:
        raw = json.load(f)
    info    = raw.get("info", {})
    teams   = info.get("teams", ["Unknown", "Unknown"])
    toss    = info.get("toss", {})
    outcome = info.get("outcome", {})
    match_row = {
        "match_id":       filepath.stem,
        "date":           info.get("dates", [""])[0],
        "season":         str(info.get("season", "")),
        "venue":          info.get("venue", "Unknown"),
        "team1":          teams[0] if len(teams) > 0 else "",
        "team2":          teams[1] if len(teams) > 1 else "",
        "toss_winner":    toss.get("winner", ""),
        "toss_decision":  toss.get("decision", ""),
        "winner":         outcome.get("winner", outcome.get("result", "")),
        "win_by_runs":    outcome.get("by", {}).get("runs", 0),
        "win_by_wickets": outcome.get("by", {}).get("wickets", 0),
    }
    ball_rows = []
    for inn_idx, innings in enumerate(raw.get("innings", [])):
        batting_team = innings.get("team", "")
        for over_obj in innings.get("overs", []):
            over_num = over_obj.get("over", 0)
            for ball_idx, delivery in enumerate(over_obj.get("deliveries", [])):
                runs_obj = delivery.get("runs", {})
                wickets  = delivery.get("wickets", [])
                ball_rows.append({
                    "match_id":     filepath.stem,
                    "date":         match_row["date"],
                    "season":       match_row["season"],
                    "venue":        match_row["venue"],
                    "innings":      inn_idx + 1,
                    "batting_team": batting_team,
                    "over":         over_num + 1,
                    "ball":         ball_idx + 1,
                    "batter":       delivery.get("batter", ""),
                    "bowler":       delivery.get("bowler", ""),
                    "runs_batter":  runs_obj.get("batter", 0),
                    "runs_extras":  runs_obj.get("extras", 0),
                    "runs_total":   runs_obj.get("total", 0),
                    "is_wicket":    1 if wickets else 0,
                    "wicket_kind":  wickets[0].get("kind", "") if wickets else "",
                })
    return match_row, ball_rows
