"""
dashboard/checkpoint_predictor.py
───────────────────────────────────
The punter's tool.

Given current score + overs, answers:
  → Will runs PASS X at over 6?
  → Will runs PASS X at over 10?
  → Will final score pass 170.5?

Compares vs bookmaker live odds and flags EV in real time.

Usage:
    python dashboard/checkpoint_predictor.py
"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── BOOKMAKER LINES — update each match ──────────────────────
LINES = {
    6:  [47.0, 51.0],       # 6 over session lines
    10: [76.0, 82.0, 86.0], # 10 over session lines
    15: [110.0, 116.0],     # 15 over session lines
    20: [158.5, 164.5, 170.5], # innings total lines
}

# Bookmaker odds for each line (over/under) — update live
BOOKIE_ODDS = {
    6:   {"over": 1.85, "under": 1.85},
    10:  {"over": 1.85, "under": 1.85},
    15:  {"over": 1.85, "under": 1.85},
    20:  {"over": 1.85, "under": 1.85},
}

TOTAL_OVERS = 20
ITERATIONS  = 8000


def balls_done(overs: float) -> int:
    complete = int(overs)
    partial  = round((overs - complete) * 10)
    return complete * 6 + partial


def simulate_from_here(
    runs:    int,
    wickets: int,
    overs:   float,
    rng:     np.random.Generator,
) -> np.ndarray:
    """
    Simulate ITERATIONS innings completions from current state.
    Returns array of (score_at_6, score_at_10, score_at_15, score_at_20).
    """
    bd       = balls_done(overs)
    balls_left = TOTAL_OVERS * 6 - bd
    current_rr = (runs / bd * 6) if bd > 0 else 8.0

    # Phase-based run rates (balls 1-120)
    # We only simulate from current ball onwards
    current_over = int(overs)

    results = np.zeros((ITERATIONS, 4))  # cols: ov6, ov10, ov15, ov20

    for i in range(ITERATIONS):
        score     = runs
        wkts      = wickets
        over_scores = []

        # Regress current RR toward phase mean
        # Powerplay mean: 9.0, Middle: 7.5, Death: 10.5
        for ov in range(current_over, TOTAL_OVERS):
            if ov < 6:
                phase_mean = 9.0
            elif ov < 15:
                phase_mean = 7.5
            else:
                phase_mean = 10.5

            # Blend current RR with phase mean (mean reversion)
            blend_rr = current_rr * 0.3 + phase_mean * 0.7
            wicket_penalty = 1.0 - (wkts * 0.045)
            effective_rr   = max(4.0, blend_rr * wicket_penalty)

            # Simulate this over
            over_runs = max(0, int(rng.normal(effective_rr, 2.8)))
            over_runs = min(over_runs, 36)  # cap at 6 sixes
            score    += over_runs

            # Wicket probability increases as game progresses
            wkt_prob = 0.10 + (wkts * 0.008)
            if rng.random() < wkt_prob:
                wkts = min(wkts + 1, 10)

            if wkts >= 10:
                # All out — pad remaining overs with 0
                for remaining in range(ov + 1, TOTAL_OVERS):
                    over_scores.append(0)
                break

            over_scores.append(over_runs)

        # Reconstruct cumulative at checkpoints
        cum = runs
        cum_by_over = {}
        for ov_idx, ov_runs in enumerate(over_scores):
            cum += ov_runs
            actual_over = current_over + ov_idx + 1
            cum_by_over[actual_over] = cum

        # Fill checkpoints
        for col_idx, checkpoint in enumerate([6, 10, 15, 20]):
            if checkpoint <= current_over:
                # Already passed — use actual score if we have it
                results[i][col_idx] = runs  # approximate
            else:
                results[i][col_idx] = cum_by_over.get(checkpoint, score)

    return results


def print_predictions(runs, wickets, overs, results):
    bd = balls_done(overs)
    rr = round(runs / bd * 6, 2) if bd > 0 else 0
    current_over = int(overs)

    print(f"\n{'═'*62}")
    print(f"  📊 CHECKPOINT PREDICTOR | {runs}/{wickets} after {overs} overs | RR {rr}")
    print(f"{'═'*62}")
    print(f"  {'Checkpoint':<12} {'Model Mean':>10} {'Bookie Line':>12} {'P(Over)':>9} {'P(Under)':>9} {'Edge':>8} {'BET'}")
    print(f"  {'-'*12} {'-'*10} {'-'*12} {'-'*9} {'-'*9} {'-'*8} {'-'*12}")

    checkpoint_cols = {6: 0, 10: 1, 15: 2, 20: 3}

    for checkpoint, col in checkpoint_cols.items():
        if checkpoint < current_over:
            continue  # Already passed

        col_data = results[:, col]
        model_mean = np.mean(col_data)

        bk_implied_over  = 1.0 / BOOKIE_ODDS[checkpoint]["over"]
        bk_implied_under = 1.0 / BOOKIE_ODDS[checkpoint]["under"]

        for line in LINES.get(checkpoint, []):
            p_over  = np.mean(col_data > line)
            p_under = 1.0 - p_over

            edge_over  = p_over  - bk_implied_over
            edge_under = p_under - bk_implied_under

            best_edge = max(edge_over, edge_under)
            if edge_over > edge_under:
                direction = f"OVER  {line:.0f}"
                edge_pct  = edge_over * 100
                ev        = edge_over * (BOOKIE_ODDS[checkpoint]["over"] - 1) * 1000 - (1 - p_over) * 1000 * (1 - edge_over)
            else:
                direction = f"UNDER {line:.0f}"
                edge_pct  = edge_under * 100
                ev        = edge_under * (BOOKIE_ODDS[checkpoint]["under"] - 1) * 1000 - (1 - p_under) * 1000 * (1 - edge_under)

            if edge_pct > 8:
                signal = f"🔥 STRONG"
            elif edge_pct > 4:
                signal = f"✅ LEAN"
            else:
                signal = f"— skip"

            print(f"  Ov {checkpoint:<8} {model_mean:>10.0f} {line:>12.1f} {p_over:>9.1%} {p_under:>9.1%} {edge_pct:>+7.1f}% {signal} {direction}")

    # Summary projection
    final_scores = results[:, 3]
    print(f"\n  FINAL INNINGS PROJECTION:")
    print(f"    Mean  : {np.mean(final_scores):.0f}")
    print(f"    Median: {np.median(final_scores):.0f}")
    print(f"    10th % : {np.percentile(final_scores, 10):.0f}  (bad day)")
    print(f"    90th % : {np.percentile(final_scores, 90):.0f}  (good day)")
    print(f"    P(>158): {np.mean(final_scores > 158):.1%}")
    print(f"    P(>170): {np.mean(final_scores > 170):.1%}")
    print(f"    P(>182): {np.mean(final_scores > 182):.1%}")
    print(f"{'═'*62}\n")


def main():
    rng = np.random.default_rng(42)

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║  MATCHPREDICTOR — CHECKPOINT PREDICTOR (Punter Mode)    ║")
    print("║  Format: runs/wickets overs  e.g.  54/1 6.0             ║")
    print("║  Type 'q' to quit                                        ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    while True:
        try:
            raw = input("  Score > ").strip()
            if raw.lower() == 'q':
                break

            parts = raw.split()
            if len(parts) != 2:
                print("  Format: 54/1 6.0")
                continue

            rw      = parts[0].split('/')
            runs    = int(rw[0])
            wickets = int(rw[1]) if len(rw) > 1 else 0
            overs   = float(parts[1])

            # Run simulation from current state
            rng2    = np.random.default_rng()
            results = simulate_from_here(runs, wickets, overs, rng2)
            print_predictions(runs, wickets, overs, results)

        except (ValueError, IndexError):
            print("  Format: runs/wickets overs  e.g.  4/0 1.0")
        except KeyboardInterrupt:
            print("\n  Stopped.")
            break


if __name__ == "__main__":
    main()
