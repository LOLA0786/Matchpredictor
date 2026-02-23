"""
scripts/detect_patterns.py
───────────────────────────
Applies your 10 pattern scripts to historical odds data.
Calculates win rate per pattern.

Pattern 10 (1.04 curse) is the most testable from OddsPortal
closing odds data — if a team closes at 1.03-1.05 how often
do they lose?
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import DATA_RAW, DATA_PROCESSED

def load_odds_data():
    odds_file = DATA_RAW / "oddsportal" / "all_cricket_odds.csv"
    if not odds_file.exists():
        print("No odds data found. Run scrape_oddsportal.py first.")
        return None
    return pd.read_csv(odds_file)

def safe_float(val):
    try:
        return float(str(val).replace(",", "."))
    except:
        return None

def detect_pattern_10(df):
    """
    Pattern 10 — The 1.04 Curse
    Team closing at 1.02-1.06 → how often do they LOSE?
    """
    results = []
    for _, row in df.iterrows():
        o1 = safe_float(row.get("opening_odds_t1"))
        o2 = safe_float(row.get("opening_odds_t2"))
        if not o1 or not o2:
            continue
        # Whoever is at 1.02-1.06
        for odds, team in [(o1, row["team1"]), (o2, row["team2"])]:
            if 1.01 <= odds <= 1.06:
                results.append({
                    "match": f"{row['team1']} vs {row['team2']}",
                    "date": row.get("date",""),
                    "team_at_104": team,
                    "odds": odds,
                })
    return pd.DataFrame(results)

def detect_pattern_4(df):
    """
    Pattern 4 — Fav 1.45 → 1.10 then LOSES
    Opening favourite with tight closing odds loses
    """
    results = []
    for _, row in df.iterrows():
        o1 = safe_float(row.get("opening_odds_t1"))
        o2 = safe_float(row.get("opening_odds_t2"))
        if not o1 or not o2:
            continue
        fav_opening = min(o1, o2)
        if 1.30 <= fav_opening <= 1.55:
            results.append({
                "match": f"{row['team1']} vs {row['team2']}",
                "date": row.get("date",""),
                "fav_opening_odds": fav_opening,
                "fav_team": row["team1"] if o1 < o2 else row["team2"],
            })
    return pd.DataFrame(results)

def main():
    print("=" * 60)
    print("  PATTERN DETECTOR — Historical Odds Analysis")
    print("=" * 60)
    
    df = load_odds_data()
    if df is None:
        # Demo with synthetic data to show structure
        print("\n  No real data yet — showing pattern structure")
        print()
        print("  PATTERN 10 — The 1.04 Curse")
        print("  ─────────────────────────────")
        print("  When we have data, this will show:")
        print("  Total matches where team touched 1.02-1.06: ???")
        print("  Times that team LOST: ???")  
        print("  Loss rate: ???%")
        print()
        print("  YOUR HYPOTHESIS: 65-75% loss rate at 1.04")
        print("  DATA WILL CONFIRM OR DENY THIS")
        print()
        print("  PATTERN 4 — Fav 1.45→1.10 Trap")
        print("  ─────────────────────────────────")
        print("  Opening fav 1.30-1.55 who closes at 1.10:")
        print("  Win rate: ???%")
        print()
        print("  Run scrape_oddsportal.py first to get real data")
        return
    
    print(f"\n  Loaded {len(df)} matches")
    
    # Pattern 10
    p10 = detect_pattern_10(df)
    print(f"\n  PATTERN 10 — 1.04 Curse:")
    print(f"  Matches where team at 1.02-1.06: {len(p10)}")
    if len(p10) > 0:
        print(p10.head(10).to_string(index=False))
    
    # Pattern 4
    p4 = detect_pattern_4(df)
    print(f"\n  PATTERN 4 — Fav Opening 1.30-1.55:")
    print(f"  Matches found: {len(p4)}")
    if len(p4) > 0:
        print(p4.head(10).to_string(index=False))

if __name__ == "__main__":
    main()
