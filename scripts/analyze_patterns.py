"""
scripts/analyze_patterns.py
─────────────────────────────
Reads odds_log.csv and validates your pattern library.
Run after each match. After 50+ matches = statistical proof.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import DATA_PROCESSED

LOG_FILE = DATA_PROCESSED / "odds_log.csv"

def main():
    if not LOG_FILE.exists():
        print("No log yet. Run odds_logger.py during matches first.")
        return

    df = pd.read_csv(LOG_FILE)
    matches = df["match"].unique()

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║  PATTERN ANALYSIS — Your 10 Scripts                 ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"  Matches logged: {len(matches)}")
    print(f"  Total entries:  {len(df)}")
    print()

    # Pattern 10 — 1.04 curse
    p10_fav   = df[(df["fav_odds"] >= 1.01) & (df["fav_odds"] <= 1.06)]
    p10_nonfav = df[(df["nonfav_odds"] >= 1.01) & (df["nonfav_odds"] <= 1.06)]

    print("  PATTERN 10 — The 1.04 Curse")
    print("  ─────────────────────────────")
    print(f"  Times fav reached 1.01-1.06:    {len(p10_fav)}")
    print(f"  Times non-fav reached 1.01-1.06: {len(p10_nonfav)}")
    print(f"  Your hypothesis: whoever touches 1.04 LOSES")
    print(f"  Need match outcomes to calculate win rate")
    print(f"  Add 'result' column (fav_won/nonfav_won) to validate")
    print()

    # Pattern 8 — fielding team sub 1.06 after 3 overs
    p8 = df[
        (df["over"] == 3) &
        (df["innings"] == 1) &
        (df["fav_odds"] < 1.07) &
        (df["who_batting"] == "nonfav")
    ]
    print("  PATTERN 8 — Fielding team sub 1.06 after 3 overs")
    print("  ───────────────────────────────────────────────────")
    print(f"  Occurrences: {len(p8)}")
    if len(p8) > 0:
        print(p8[["match","date","fav_odds","score"]].to_string(index=False))
    print()

    # Pattern 9 — batting team 1.05 after over 1
    p9 = df[
        (df["over"] == 1) &
        (df["fav_odds"] < 1.07) &
        (df["who_batting"] == "fav")
    ]
    print("  PATTERN 9 — Batting team sub 1.07 after over 1")
    print("  ─────────────────────────────────────────────────")
    print(f"  Occurrences: {len(p9)}")
    print()

    # Odds movement — fav drift then recovery (Pattern 5)
    print("  PATTERN 5 — Fav drift then recovery")
    print("  ─────────────────────────────────────")
    drift_matches = []
    for match in matches:
        m = df[df["match"] == match].sort_values("over")
        if len(m) < 4:
            continue
        fav_odds = m["fav_odds"].values
        min_idx  = np.argmin(fav_odds)
        if min_idx > 0 and min_idx < len(fav_odds)-1:
            if fav_odds[min_idx] > fav_odds[0] * 1.10:
                drift_matches.append(match)
    print(f"  Matches where fav drifted 10%+ then recovered: {len(drift_matches)}")
    if drift_matches:
        for m in drift_matches[:5]:
            print(f"    {m}")
    print()

    print("  ── AFTER 50 MATCHES ──────────────────────────────")
    print("  Each pattern gets:")
    print("    Trigger count | Win rate | Avg odds at entry")
    print("    EV calculation | Recommended stake size")
    print()
    print("  IPL 2026: 74 matches starting late March")
    print("  Log every match → pattern library validated by May")
    print("╚══════════════════════════════════════════════════════╝")

if __name__ == "__main__":
    main()
