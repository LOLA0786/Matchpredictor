"""
dashboard/odds_logger.py
─────────────────────────
Log odds + score at each checkpoint during live matches.
Run this during every IPL 2026 match.
After 74 matches = full pattern library validated.

Usage: python dashboard/odds_logger.py
"""
import csv, sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import DATA_PROCESSED

LOG_FILE = DATA_PROCESSED / "odds_log.csv"
FIELDS = [
    "date","match","venue","innings","over",
    "score","wickets","rr",
    "fav_team","fav_odds","nonfav_odds",
    "who_batting","notes"
]

def init_log():
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writeheader()
        print(f"  Created log: {LOG_FILE}")

def append_row(row: dict):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(row)

def get_input(prompt, default=""):
    val = input(f"  {prompt}").strip()
    return val if val else default

def main():
    init_log()
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║  MATCHPREDICTOR — LIVE ODDS LOGGER               ║")
    print("║  Log odds every over → build pattern dataset     ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  Checkpoints: Pre | Ov1 | Ov3 | Ov6 | Ov10      ║")
    print("║               Ov15 | Ov20 | Innings break        ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    # Match setup
    date  = datetime.now().strftime("%Y-%m-%d")
    match = get_input("Match (e.g. CSK vs MI): ")
    venue = get_input("Venue: ")
    print()
    print("  Log odds at each checkpoint.")
    print("  Format: score/wickets  fav_odds  nonfav_odds")
    print("  Example: 54/1  1.45  2.65")
    print("  Type 'q' to quit, 'skip' to skip checkpoint")
    print()

    checkpoints = [
        ("Pre-toss",   "0", "0/0"),
        ("Over 1",     "1", ""),
        ("Over 3",     "3", ""),
        ("Over 6",     "6", ""),
        ("Over 10",   "10", ""),
        ("Over 15",   "15", ""),
        ("Over 20",   "20", ""),
        ("Innings 2 start", "0", ""),
        ("Inns2 Over 3",  "3", ""),
        ("Inns2 Over 6",  "6", ""),
        ("Inns2 Over 10","10", ""),
        ("Inns2 Over 15","15", ""),
        ("Result",    "20", ""),
    ]

    fav_team   = get_input("Favourited team (pre-toss): ")
    innings    = 1

    for label, over, default_score in checkpoints:
        print(f"\n  ── {label} ──")

        if "Innings 2" in label or "Inns2" in label:
            innings = 2

        raw = get_input(f"Score/wkts fav_odds nonfav_odds (or skip/q): ")

        if raw.lower() == 'q':
            break
        if raw.lower() == 'skip':
            continue

        parts = raw.split()
        if len(parts) < 3:
            print("  Need: score/wkts fav_odds nonfav_odds")
            continue

        try:
            score_wkts = parts[0]
            score  = int(score_wkts.split("/")[0])
            wkts   = int(score_wkts.split("/")[1]) if "/" in score_wkts else 0
            fav_o  = float(parts[1])
            nfav_o = float(parts[2])
            over_n = int(over)
            rr     = round(score / over_n, 2) if over_n > 0 else 0
            notes  = get_input("Notes (optional): ")

            row = {
                "date":        date,
                "match":       match,
                "venue":       venue,
                "innings":     innings,
                "over":        over,
                "score":       score,
                "wickets":     wkts,
                "rr":          rr,
                "fav_team":    fav_team,
                "fav_odds":    fav_o,
                "nonfav_odds": nfav_o,
                "who_batting": get_input("Who batting (fav/nonfav): "),
                "notes":       notes,
            }

            append_row(row)

            # Pattern detection on the fly
            print(f"\n  Logged. Pattern check:")
            if 1.01 <= fav_o <= 1.06:
                print(f"  🚨 PATTERN 10: FAV at {fav_o} — 1.04 CURSE ZONE")
            if 1.01 <= nfav_o <= 1.06:
                print(f"  🚨 PATTERN 10: NON-FAV at {nfav_o} — 1.04 CURSE ZONE")
            if over == "3" and innings == 1 and fav_o < 1.07 and row["who_batting"] == "nonfav":
                print(f"  🚨 PATTERN 8: Fielding team {fav_o} after 3 overs — TRAP?")
            if over == "1" and fav_o < 1.07 and row["who_batting"] == "fav":
                print(f"  🚨 PATTERN 9: Batting team {fav_o} after over 1 — TRAP?")
            if fav_o > nfav_o and over != "0":
                print(f"  ⚡ PATTERN 3: Non-fav now favourite at {nfav_o}")

        except Exception as e:
            print(f"  Error: {e} — skipping")
            continue

    print()
    print("  Match logged. Run analysis:")
    print("  python scripts/analyze_patterns.py")
    print()

if __name__ == "__main__":
    main()
