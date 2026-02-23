#!/usr/bin/env python3
"""
Reads Cricsheet data and builds venue/toss/session models.
Run after download_cricsheet.py.

Usage: python scripts/build_models.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from agents.data_scout.parser import load_all_matches
from config.settings import DATA_RAW, DATA_PROCESSED

def main():
    print("=" * 60)
    print("Matchpredictor — Model Builder")
    print("=" * 60)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    json_dir = DATA_RAW / "ipl_json"
    matches_df, balls_df = load_all_matches(json_dir)

    matches_df.to_csv(DATA_PROCESSED / "matches.csv", index=False)
    balls_df.to_csv(DATA_PROCESSED / "balls.csv", index=False)
    print(f"Saved {len(matches_df)} matches and {len(balls_df):,} balls to data/processed/")

    # Venue run model
    innings1 = balls_df[balls_df["innings"] == 1].copy()
    venue_runs = (
        innings1.groupby(["match_id", "venue"])["runs_total"].sum()
        .reset_index().rename(columns={"runs_total": "innings1_total"})
    )
    venue_model = (
        venue_runs.groupby("venue")["innings1_total"]
        .agg(avg_runs="mean", std_runs="std", match_count="count")
        .reset_index().sort_values("match_count", ascending=False)
    )
    venue_model.to_csv(DATA_PROCESSED / "venue_model.csv", index=False)
    print("\nVenue model (top 8):")
    print(venue_model.head(8).to_string(index=False))

    # Session checkpoint model
    rows = []
    for match_id, group in balls_df[balls_df["innings"] == 1].groupby("match_id"):
        venue = group["venue"].iloc[0]
        for cp in [6, 10, 15, 20]:
            runs_at = group[group["over"] <= cp]["runs_total"].sum()
            rows.append({"match_id": match_id, "venue": venue, "over": cp, "runs": runs_at})
    sessions_df = pd.DataFrame(rows)
    session_model = (
        sessions_df.groupby(["venue", "over"])["runs"]
        .agg(mean_runs="mean", std_runs="std").reset_index()
    )
    session_model.to_csv(DATA_PROCESSED / "session_model.csv", index=False)
    print("\nSession model saved.")

    # Toss advantage model
    toss_df = matches_df[
        matches_df["toss_decision"].isin(["bat", "field"]) &
        matches_df["winner"].notna() & (matches_df["winner"] != "")
    ].copy()
    toss_df["toss_winner_won"] = toss_df["toss_winner"] == toss_df["winner"]
    toss_model = (
        toss_df.groupby(["venue", "toss_decision"])["toss_winner_won"]
        .agg(win_rate="mean", match_count="count").reset_index()
        .sort_values("win_rate", ascending=False)
    )
    toss_model.to_csv(DATA_PROCESSED / "toss_model.csv", index=False)
    print("\nToss model (top 8):")
    print(toss_model.head(8).to_string(index=False))
    print("\nDone. Run: python dashboard/live_dashboard.py")

if __name__ == "__main__":
    main()
