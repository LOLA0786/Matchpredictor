import sys, argparse, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.context_engine.context import build_match_context
from agents.simulation.monte_carlo import simulate_match
from agents.market_edge.ev_detector import detect_ev, implied_to_decimal

DEMO_MATCH = {
    "venue": "Wankhede Stadium",
    "team_batting_first": "Mumbai Indians",
    "team_batting_second": "Chennai Super Kings",
    "toss_winner": "Chennai Super Kings",
    "toss_decision": "field",
    "match_time": "night",
    "tournament_stage": "league_early",
}

DEMO_ODDS = {
    "match_winner": {"team_batting_first": 2.15, "team_batting_second": 1.78},
    "session_runs": {
        6:  {"over": 1.90, "under": 1.90},
        10: {"over": 1.85, "under": 1.95},
        20: {"over": 1.88, "under": 1.92},
    },
}

def run(match_config, odds):
    ctx = build_match_context(**match_config)
    session_lines = {}
    sim_pre = simulate_match(context=ctx, iterations=10000)
    for s in sim_pre.sessions:
        session_lines[s.over] = [round(s.mean_runs, 0)]

    sim = simulate_match(context=ctx, lines=session_lines, iterations=10000)
    label = f"{match_config['team_batting_first']} vs {match_config['team_batting_second']}"
    ev    = detect_ev(sim, label, odds)

    print("=" * 60)
    print(f"  MATCHPREDICTOR — {label}")
    print("=" * 60)
    print(f"  Venue      : {ctx.venue}")
    print(f"  Toss       : {ctx.toss_winner} chose to {ctx.toss_decision}")
    print(f"  Dew Risk   : {ctx.dew_risk:.0%}  |  Run Adj: {ctx.run_adjustment:+.1f}")
    print()
    print(f"  {sim.team_batting_first:30s}  WIN: {sim.win_prob_batting_first:.1%}  |  Score: {sim.innings1_mean:.0f} ± {sim.innings1_std:.0f}")
    print(f"  {sim.team_batting_second:30s}  WIN: {sim.win_prob_batting_second:.1%}  |  Score: {sim.innings2_mean:.0f} ± {sim.innings2_std:.0f}")
    print()
    print("  SESSION MARKETS (innings 1):")
    for s in sim.sessions:
        lines_str = "  ".join(f">{l:.0f}: {p:.1%}" for l, p in s.prob_over_line.items())
        print(f"    Over {s.over:2d}: mean={s.mean_runs:.0f} ± {s.std_runs:.0f}  |  {lines_str}")
    print()
    print(f"  EV: {ev.summary}")
    for sig in ev.signals:
        print(f"    [{sig.strength.upper():8s}] {sig.selection}")
        print(f"               Model: {sig.model_prob:.1%} | Implied: {sig.implied_prob:.1%} | Edge: +{sig.edge_percent:.1f}% | EV/1000: {sig.ev_per_1000:+.0f}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--odds", type=str, default=None)
    args = parser.parse_args()
    odds = json.loads(args.odds) if args.odds else DEMO_ODDS
    run(DEMO_MATCH, odds)
