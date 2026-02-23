"""
dashboard/live_ball_tracker.py
───────────────────────────────
Live ball-by-ball win probability updater.
Polls Cricbuzz every 15 seconds, recalculates model,
flags EV shifts in real time.

Usage:
    python dashboard/live_ball_tracker.py

Stop with Ctrl+C
"""
import sys, time, re, requests
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup
from agents.simulation.monte_carlo import simulate_match
from agents.context_engine.context import build_match_context
from agents.market_edge.ev_detector import detect_ev

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── MATCH CONFIG — edit per match ────────────────────────────
MATCH_CONFIG = {
    "venue":               "Wankhede Stadium, Mumbai",
    "team_batting_first":  "West Indies",
    "team_batting_second": "Zimbabwe",
    "toss_winner":         "Zimbabwe",
    "toss_decision":       "field",
    "match_time":          "night",
    "tournament_stage":    "qualifier",
    "dew_risk_override":   0.30,
    "venue_avg_override":  160,
}

# Paste your live bookmaker odds here — update as market moves
LIVE_ODDS = {
    "match_winner": {
        "team_batting_first":  1.37,
        "team_batting_second": 3.00,
    }
}

# Cricbuzz match URL — find from cricbuzz.com/live-cricket-scores
CRICBUZZ_URL = "https://www.cricbuzz.com/live-cricket-scores/108021/wi-vs-zim-44th-match-super-eights-icc-mens-t20-world-cup-2026"

POLL_INTERVAL = 15   # seconds between updates


# ── Live state ────────────────────────────────────────────────

class MatchState:
    def __init__(self):
        self.innings        = 1
        self.runs           = 0
        self.wickets        = 0
        self.overs          = 0.0
        self.last_update    = ""
        self.prev_runs      = -1
        self.prev_wickets   = -1

state = MatchState()


def fetch_live_score(url: str) -> dict | None:
    """Scrape current score from Cricbuzz."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Cricbuzz score format varies — try multiple selectors
        score_text = ""
        for selector in [
            "div.cb-min-bat-rw",
            "div.cb-lv-scrs-col",
            "span.cb-run-rw",
        ]:
            el = soup.select_one(selector)
            if el:
                score_text = el.get_text(strip=True)
                break

        if not score_text:
            return None

        # Parse "134/3 (14.2 Ov)" format
        runs_wkts = re.search(r'(\d+)/(\d+)', score_text)
        overs_str = re.search(r'\((\d+\.?\d*)\s*Ov\)', score_text)

        if runs_wkts and overs_str:
            return {
                "runs":    int(runs_wkts.group(1)),
                "wickets": int(runs_wkts.group(2)),
                "overs":   float(overs_str.group(1)),
                "raw":     score_text,
            }
    except Exception as e:
        return None
    return None


def balls_remaining(overs_done: float, total_overs: int = 20) -> int:
    complete = int(overs_done)
    partial  = round((overs_done - complete) * 10)
    balls_done = complete * 6 + partial
    return total_overs * 6 - balls_done


def required_rate(runs_scored, wickets, overs_done, target=None):
    if target is None:
        return None
    needed = target - runs_scored
    balls  = balls_remaining(overs_done)
    return round(needed / balls * 6, 2) if balls > 0 else 99.9


def live_win_probability(runs, wickets, overs, innings=1):
    """
    Recalculate win probability given current match state.
    Uses projection: remaining_runs ~ N(projected_mean, std)
    """
    ctx = build_match_context(
        venue=MATCH_CONFIG["venue"],
        team_batting_first=MATCH_CONFIG["team_batting_first"],
        team_batting_second=MATCH_CONFIG["team_batting_second"],
        toss_winner=MATCH_CONFIG["toss_winner"],
        toss_decision=MATCH_CONFIG["toss_decision"],
        match_time=MATCH_CONFIG["match_time"],
        tournament_stage=MATCH_CONFIG["tournament_stage"],
    )
    ctx.venue_avg_runs    = MATCH_CONFIG["venue_avg_override"]
    ctx.dew_risk          = MATCH_CONFIG["dew_risk_override"]
    ctx.venue_chase_advantage = 0.45

    if innings == 1:
        # Project final score from current run rate
        balls_done = int(overs) * 6 + round((overs - int(overs)) * 10)
        if balls_done == 0:
            run_rate = 8.0
        else:
            run_rate = runs / balls_done * 6
        balls_left = 120 - balls_done

        # Wicket pressure factor — more wickets = slower scoring
        wicket_factor = 1.0 - (wickets * 0.04)
        projected_remaining = (balls_left / 6) * run_rate * wicket_factor
        projected_total = runs + projected_remaining

        ctx.run_adjustment = projected_total - ctx.venue_avg_runs + (ctx.dew_risk * 4)
    else:
        ctx.run_adjustment = ctx.dew_risk * 4 + 160 * (ctx.stage_run_multiplier - 1)

    sim = simulate_match(ctx, iterations=5000)
    return sim, ctx, runs + (ctx.venue_avg_runs + ctx.run_adjustment - runs)


def print_update(runs, wickets, overs, sim, projected_total):
    now = datetime.now().strftime("%H:%M:%S")
    rr  = round(runs / overs, 2) if overs > 0 else 0

    print(f"\n{'═'*60}")
    print(f"  🏏 LIVE | {now} | Over {overs:.1f}")
    print(f"  {MATCH_CONFIG['team_batting_first']}: {runs}/{wickets}  RR: {rr:.2f}")
    print(f"  Projected total: {projected_total:.0f}")
    print(f"  {'─'*56}")
    print(f"  {MATCH_CONFIG['team_batting_first']:20s} WIN: {sim.win_prob_batting_first:.1%}")
    print(f"  {MATCH_CONFIG['team_batting_second']:20s} WIN: {sim.win_prob_batting_second:.1%}")

    # EV vs live odds
    ev = detect_ev(sim, "Live", LIVE_ODDS)
    if ev.signals:
        print(f"  {'─'*56}")
        print(f"  ⚡ EV SIGNALS:")
        for sig in ev.signals:
            icon = "🔥" if sig.strength == "strong" else "✅"
            print(f"    {icon} {sig.selection}")
            print(f"       Edge: +{sig.edge_percent:.1f}%  EV/₹1000: {sig.ev_per_1000:+.0f}")
    else:
        print(f"  ✓ No EV signals at current odds")

    # Phase commentary
    overs_int = int(overs)
    if overs_int < 6:
        phase = "POWERPLAY"
        target_rr = 9.0
        status = "ahead" if rr > target_rr else "behind"
        print(f"  {'─'*56}")
        print(f"  Phase: {phase} | Model RR: {target_rr} | Actual: {rr:.1f} [{status}]")
    elif overs_int < 15:
        phase = "MIDDLE OVERS"
        print(f"  Phase: {phase} | Wickets key | {10-wickets} in hand")
    else:
        phase = "DEATH OVERS"
        print(f"  Phase: {phase} | Big hits expected | Projected: {projected_total:.0f}")

    print(f"{'═'*60}")


def manual_input_mode():
    """Fallback: manual score entry if scraper fails."""
    print("\n  Auto-scraping failed or not available.")
    print("  Enter score manually each over (format: runs/wickets overs)")
    print("  Example: 54/1 6.0  or  type 'q' to quit\n")

    while True:
        try:
            raw = input("  Score > ").strip()
            if raw.lower() == 'q':
                break
            parts = raw.split()
            if len(parts) == 2:
                rw = parts[0].split('/')
                runs    = int(rw[0])
                wickets = int(rw[1]) if len(rw) > 1 else 0
                overs   = float(parts[1])

                sim, ctx, projected = live_win_probability(runs, wickets, overs)
                print_update(runs, wickets, overs, sim, projected)
            else:
                print("  Format: runs/wickets overs  e.g. 54/1 6.0")
        except (ValueError, IndexError):
            print("  Invalid format. Try: 54/1 6.0")
        except KeyboardInterrupt:
            print("\n  Stopped.")
            break


def auto_mode():
    """Auto-poll Cricbuzz every 15 seconds."""
    print(f"\n  Auto-polling Cricbuzz every {POLL_INTERVAL}s")
    print(f"  URL: {CRICBUZZ_URL}")
    print(f"  Press Ctrl+C to stop\n")

    while True:
        score = fetch_live_score(CRICBUZZ_URL)
        if score:
            runs    = score["runs"]
            wickets = score["wickets"]
            overs   = score["overs"]

            # Only print if score has changed
            if runs != state.prev_runs or wickets != state.prev_wickets:
                sim, ctx, projected = live_win_probability(runs, wickets, overs)
                print_update(runs, wickets, overs, sim, projected)
                state.prev_runs    = runs
                state.prev_wickets = wickets
        else:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Waiting for score...")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  MATCHPREDICTOR — LIVE BALL TRACKER                     ║")
    print(f"║  {MATCH_CONFIG['team_batting_first']} vs {MATCH_CONFIG['team_batting_second']}".ljust(61) + "║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  Mode: 1 = Auto (Cricbuzz)  2 = Manual input            ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    mode = input("  Select mode (1/2): ").strip()

    if mode == "1":
        try:
            auto_mode()
        except KeyboardInterrupt:
            print("\n  Stopped.")
    else:
        manual_input_mode()
