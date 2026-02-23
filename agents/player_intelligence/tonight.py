"""
Player-adjusted simulation for ZIM vs WI tonight.
Edit BAT_FIRST, TOSS_WINNER, TOSS_DEC after 6:30PM toss.
"""
import sys, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.context_engine.context import build_match_context
from agents.simulation.monte_carlo import simulate_match
from agents.market_edge.ev_detector import detect_ev
from config.settings import DATA_PROCESSED

# ── EDIT AFTER TOSS ───────────────────────────────────────────
BAT_FIRST   = "Zimbabwe"
BAT_SECOND  = "West Indies"
TOSS_WINNER = "West Indies"
TOSS_DEC    = "field"
# ─────────────────────────────────────────────────────────────

ODDS = {
    "match_winner": {
        "team_batting_first":  3.15,
        "team_batting_second": 1.35,
    },
    "session_runs": {
        20: {"over": 1.85, "under": 1.85},
        6:  {"over": 1.85, "under": 1.85},
        10: {"over": 1.85, "under": 1.85},
    },
}

# ── PLAYER PROFILES ───────────────────────────────────────────
# Cricsheet name | team | role | t20i_avg | t20i_sr | form(last5) | run_contribution
# form = weighted avg last 5 scores (most recent x2 weight)
# run_contribution = how many runs above/below team average this player adds

PLAYERS = {
    # WEST INDIES — Cricsheet exact names
    "R Powell":       {"team":"WI","role":"batter",     "avg":29.3,"sr":158.9,"form":[18,7,44,22,11], "contribution":+1.2},
    "SD Hope":        {"team":"WI","role":"wk-batter",  "avg":31.2,"sr":128.4,"form":[75,34,48,21,55],"contribution":+4.2},
    "SO Hetmyer":     {"team":"WI","role":"batter",     "avg":27.6,"sr":147.3,"form":[42,38,67,12,29],"contribution":+3.1},
    "JO Holder":      {"team":"WI","role":"allrounder", "avg":17.3,"sr":122.4,"form":[12,8,24,31,6],  "contribution":-2.1},
    "SE Rutherford":  {"team":"WI","role":"batter",     "avg":26.1,"sr":152.8,"form":[31,44,18,52,8], "contribution":+2.4},

    # ZIMBABWE — Cricsheet exact names
    "Sikandar Raza":  {"team":"ZIM","role":"allrounder","avg":34.4,"sr":141.2,"form":[44,28,61,18,35],"contribution":+5.1},
}

# Manual profiles for players NOT in Cricsheet (international only)
MANUAL_PLAYERS = {
    # WEST INDIES
    "B King":         {"team":"WI","role":"batter",     "avg":28.9,"sr":134.2,"form":[22,14,41,8,33], "contribution":+0.8},
    "R Chase":        {"team":"WI","role":"allrounder", "avg":19.4,"sr":118.9,"form":[28,15,33,9,21], "contribution":-1.8},
    "M Forde":        {"team":"WI","role":"bowler",     "avg":12.0,"sr":110.0,"form":[8,4,11,6,9],   "contribution":-3.0},
    "A Hosein":       {"team":"WI","role":"bowler",     "avg":10.0,"sr":105.0,"form":[],              "contribution":-3.5},
    "G Motie":        {"team":"WI","role":"bowler",     "avg":9.0, "sr":98.0, "form":[],              "contribution":-3.8},
    "S Joseph":       {"team":"WI","role":"bowler",     "avg":8.0, "sr":95.0, "form":[],              "contribution":-4.0},
    "J Charles":      {"team":"WI","role":"batter",     "avg":24.0,"sr":138.0,"form":[19,33,8,27,14],"contribution":+0.5},

    # ZIMBABWE
    "B Bennett":      {"team":"ZIM","role":"batter",    "avg":28.0,"sr":138.4,"form":[52,31,18,44,27],"contribution":+3.8},
    "TK Marumani":    {"team":"ZIM","role":"wk-batter", "avg":24.6,"sr":132.1,"form":[38,22,11,47,15],"contribution":+1.4},
    "R Burl":         {"team":"ZIM","role":"allrounder","avg":22.3,"sr":128.6,"form":[24,8,36,19,42], "contribution":+0.6},
    "B Curran":       {"team":"ZIM","role":"batter",    "avg":23.5,"sr":124.8,"form":[18,44,9,28,33], "contribution":+0.2},
    "D Myers":        {"team":"ZIM","role":"batter",    "avg":22.0,"sr":126.0,"form":[31,18,44,12,26],"contribution":+0.4},
    "C Madande":      {"team":"ZIM","role":"wk-batter", "avg":15.0,"sr":118.0,"form":[12,8,19,6,14],  "contribution":-1.2},
    "B Evans":        {"team":"ZIM","role":"allrounder","avg":14.0,"sr":112.0,"form":[11,6,18,4,9],   "contribution":-2.1},
    "T Munyonga":     {"team":"ZIM","role":"bowler",    "avg":8.0, "sr":95.0, "form":[],              "contribution":-3.5},
    "B Muzarabani":   {"team":"ZIM","role":"bowler",    "avg":8.0, "sr":90.0, "form":[],              "contribution":-3.2},
    "R Ngarava":      {"team":"ZIM","role":"bowler",    "avg":7.0, "sr":88.0, "form":[],              "contribution":-3.8},
    "T Maposa":       {"team":"ZIM","role":"batter",    "avg":19.0,"sr":122.0,"form":[14,22,8,31,17], "contribution":-0.5},
}

ALL_PLAYERS = {**PLAYERS, **MANUAL_PLAYERS}

ZIM_XI = ["TK Marumani","B Curran","B Bennett","Sikandar Raza",
          "D Myers","R Burl","C Madande","B Evans",
          "T Munyonga","B Muzarabani","R Ngarava"]

WI_XI  = ["B King","SD Hope","SO Hetmyer","R Chase",
          "SE Rutherford","R Powell","JO Holder",
          "M Forde","A Hosein","G Motie","S Joseph"]


def form_index(scores):
    if not scores: return 20.0   # default for bowlers
    weights = [2.0, 1.5, 1.2, 1.0, 0.8]
    total_w = sum(weights[:len(scores)])
    return round(sum(s*w for s,w in zip(scores, weights[:len(scores)])) / total_w, 1)


def analyze_xi(xi, team_code):
    profiles  = [ALL_PLAYERS[p] for p in xi if p in ALL_PLAYERS]
    missing   = [p for p in xi if p not in ALL_PLAYERS]
    batters   = [p for p in profiles if p["role"] in ("batter","wk-batter","allrounder")]
    top6      = sorted(batters, key=lambda x: x["avg"], reverse=True)[:6]
    net_runs  = sum(p["contribution"] for p in profiles)
    avg_form  = sum(form_index(p["form"]) for p in top6) / len(top6) if top6 else 0
    danger    = sorted(profiles, key=lambda x: form_index(x["form"]), reverse=True)[:2]
    in_form   = [p for p in top6 if form_index(p["form"]) > 35]
    out_form  = [p for p in top6 if form_index(p["form"]) < 18]
    return {
        "net_runs": round(net_runs, 1),
        "avg_form": round(avg_form, 1),
        "danger":   danger,
        "in_form":  in_form,
        "out_form": out_form,
        "missing":  missing,
    }


def main():
    # Also pull Wankhede IPL stats from our real data
    balls = pd.read_csv(DATA_PROCESSED / "balls.csv", low_memory=False)
    wank  = balls[balls["venue"].str.contains("Wankhede", na=False)]

    cricsheet_players = list(PLAYERS.keys())
    wank_stats = []
    for p in cricsheet_players:
        pb = wank[wank["batter"] == p]
        if len(pb) > 10:
            runs  = pb["runs_batter"].sum()
            balls_faced = len(pb)
            wank_stats.append((p, runs, balls_faced, round(runs/balls_faced*100,1)))

    print("=" * 65)
    print("  PLAYER-ADJUSTED SIMULATION | ZIM vs WI | Wankhede")
    print("=" * 65)

    if wank_stats:
        print("\n  WANKHEDE IPL RECORDS (from our 30,138 ball dataset):")
        print(f"  {'Player':20s} {'Runs':>6} {'Balls':>6} {'SR':>7}")
        print(f"  {'-'*20} {'-'*6} {'-'*6} {'-'*7}")
        for name, runs, b, sr in sorted(wank_stats, key=lambda x: x[1], reverse=True):
            print(f"  {name:20s} {runs:6d} {b:6d} {sr:7.1f}")

    zim_xi_analysis = analyze_xi(ZIM_XI, "ZIM")
    wi_xi_analysis  = analyze_xi(WI_XI,  "WI")

    for team, xi, analysis in [
        ("ZIMBABWE XI",    ZIM_XI, zim_xi_analysis),
        ("WEST INDIES XI", WI_XI,  wi_xi_analysis),
    ]:
        print(f"\n  {team}:")
        print(f"    Net run contribution : {analysis['net_runs']:+.1f} runs vs baseline")
        print(f"    Form index (top 6)   : {analysis['avg_form']}")
        print(f"    Danger men           :")
        for p in analysis["danger"]:
            fi = form_index(p["form"])
            print(f"      {p.get('name', ''):25s}  avg={p['avg']:.0f}  sr={p['sr']:.0f}  form={fi:.0f}  recent={p['form'][:3]}")
        if analysis["in_form"]:
            names = [p.get("name","?") for p in analysis["in_form"]]
            print(f"    In-form (form>35)    : {names}")
        if analysis["out_form"]:
            names = [p.get("name","?") for p in analysis["out_form"]]
            print(f"    Out-of-form (<18)    : {names}")
        if analysis["missing"]:
            print(f"    No profile for       : {analysis['missing']}")

    # Player-adjusted simulation
    bat_first_adj  = (zim_xi_analysis if BAT_FIRST == "Zimbabwe" else wi_xi_analysis)["net_runs"]

    ctx = build_match_context(
        venue="Wankhede Stadium, Mumbai",
        team_batting_first=BAT_FIRST,
        team_batting_second=BAT_SECOND,
        toss_winner=TOSS_WINNER,
        toss_decision=TOSS_DEC,
        match_time="night",
        tournament_stage="qualifier",
    )
    ctx.venue_avg_runs  = 160
    ctx.run_adjustment  = ctx.dew_risk * 8 + 160 * (ctx.stage_run_multiplier - 1) + bat_first_adj

    sim = simulate_match(ctx,
        lines={
            6:  [46.5, 51.0],
            10: [76.0, 82.0],
            15: [110.0, 116.0],
            20: [152.5, 158.5] if BAT_FIRST == "Zimbabwe" else [164.5, 170.5],
        },
        iterations=10000,
    )
    ev = detect_ev(sim, f"{BAT_FIRST} vs {BAT_SECOND}", ODDS)

    print(f"\n  FINAL PLAYER-ADJUSTED PROJECTION:")
    print(f"    Base venue avg     : 160")
    print(f"    Dew adjustment     : +{ctx.dew_risk * 8:.1f} (first innings must bat harder)")
    print(f"    Stage adjustment   : {160*(ctx.stage_run_multiplier-1):+.1f}")
    print(f"    XI adjustment      : {bat_first_adj:+.1f} runs")
    print(f"    ─────────────────────────────────────")
    print(f"    Adjusted mean      : {ctx.venue_avg_runs + ctx.run_adjustment:.0f} runs")
    print()
    print(f"    {BAT_FIRST:15s} (bat): {sim.innings1_mean:.0f} ± {sim.innings1_std:.0f}  WIN: {sim.win_prob_batting_first:.1%}")
    print(f"    {BAT_SECOND:15s} (chase): {sim.innings2_mean:.0f} ± {sim.innings2_std:.0f}  WIN: {sim.win_prob_batting_second:.1%}")

    print(f"\n  SESSIONS:")
    print(f"  {'Over':6s} {'Mean':>6} {'Lines & Probs':45s} {'Verdict'}")
    print(f"  {'─'*6} {'─'*6} {'─'*45} {'─'*20}")
    for s in sim.sessions:
        lines_str = "  ".join(f">{l:.0f}:{p:.0%}" for l,p in s.prob_over_line.items())
        best_verdict = ""
        for line, prob in s.prob_over_line.items():
            over_e  = prob*100 - 54.1
            under_e = (1-prob)*100 - 54.1
            if over_e > 8:   best_verdict = f"OVER  {line:.0f} +{over_e:.0f}%"
            elif under_e > 8: best_verdict = f"UNDER {line:.0f} +{under_e:.0f}%"
            elif over_e > 4:  best_verdict = f"lean OVER {line:.0f}"
            elif under_e > 4: best_verdict = f"lean UNDER {line:.0f}"
        print(f"  Ov {s.over:2d}  {s.mean_runs:6.0f}  {lines_str:45s} {best_verdict}")

    print(f"\n  EV SIGNALS:")
    if ev.signals:
        for sig in ev.signals:
            print(f"    [{sig.strength.upper():8s}] {sig.selection}")
            print(f"               Model:{sig.model_prob:.1%}  Implied:{sig.implied_prob:.1%}  Edge:+{sig.edge_percent:.1f}%  EV/1000:{sig.ev_per_1000:+.0f}")
    else:
        print("    No signals above threshold")
    print("=" * 65)


if __name__ == "__main__":
    main()
