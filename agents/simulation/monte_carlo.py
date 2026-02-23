import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from config.settings import MONTE_CARLO_ITERATIONS, RANDOM_SEED, SESSION_OVERS

@dataclass
class SessionResult:
    over: int
    mean_runs: float
    std_runs: float
    prob_over_line: dict = field(default_factory=dict)

@dataclass
class SimulationResult:
    team_batting_first: str
    team_batting_second: str
    win_prob_batting_first: float
    win_prob_batting_second: float
    innings1_mean: float
    innings1_std: float
    innings2_mean: float
    innings2_std: float
    sessions: list = field(default_factory=list)
    iterations: int = MONTE_CARLO_ITERATIONS

def _simulate_innings(rng, iterations, mean_total, std_total, powerplay_mean, wicket_rate_boost):
    phases = [
        (6,  powerplay_mean / 36,          0.028 + wicket_rate_boost),
        (9,  (mean_total * 0.32) / 54,     0.038 + wicket_rate_boost),
        (5,  (mean_total * 0.35) / 30,     0.045 + wicket_rate_boost),
    ]
    run_means, wicket_probs = [], []
    for overs_in_phase, run_mean_pb, wkt_prob_pb in phases:
        balls = overs_in_phase * 6
        run_means.extend([run_mean_pb] * balls)
        wicket_probs.extend([wkt_prob_pb] * balls)

    run_means_arr    = np.array(run_means)
    wicket_probs_arr = np.array(wicket_probs)
    ball_runs        = np.clip(rng.poisson(lam=run_means_arr, size=(iterations, 120)), 0, 6)
    cumulative_runs  = np.cumsum(ball_runs, axis=1)
    cumulative_at_over = {over: cumulative_runs[:, over * 6 - 1] for over in SESSION_OVERS}
    return cumulative_runs[:, -1], cumulative_at_over

def simulate_match(context, lines=None, iterations=MONTE_CARLO_ITERATIONS, seed=RANDOM_SEED):
    rng   = np.random.default_rng(seed)
    lines = lines or {}

    innings1_mean = context.venue_avg_runs + context.run_adjustment
    innings1_std  = innings1_mean * 0.12

    innings1_scores, innings1_session_runs = _simulate_innings(
        rng=rng, iterations=iterations, mean_total=innings1_mean,
        std_total=innings1_std, powerplay_mean=context.venue_avg_powerplay,
        wicket_rate_boost=context.wicket_adjustment,
    )

    dew_boost  = context.dew_risk * 6 if context.match_time in ("day-night", "night") else 0.0
    toss_boost = (context.toss_win_prob_boost * innings1_mean
                  if context.toss_winner == context.team_batting_second else 0.0)
    innings2_mean = innings1_mean * context.venue_chase_advantage * 2 + dew_boost + toss_boost
    innings2_std  = innings2_mean * 0.12

    innings2_scores, _ = _simulate_innings(
        rng=rng, iterations=iterations, mean_total=innings2_mean,
        std_total=innings2_std, powerplay_mean=context.venue_avg_powerplay,
        wicket_rate_boost=0.0,
    )

    win_prob_second = float(np.sum(innings2_scores >= innings1_scores)) / iterations
    win_prob_first  = 1.0 - win_prob_second

    sessions = []
    for over in SESSION_OVERS:
        session_runs = innings1_session_runs[over]
        prob_map = {line: float(np.mean(session_runs > line)) for line in lines.get(over, [])}
        sessions.append(SessionResult(
            over=over,
            mean_runs=round(float(np.mean(session_runs)), 1),
            std_runs=round(float(np.std(session_runs)), 1),
            prob_over_line=prob_map,
        ))

    return SimulationResult(
        team_batting_first=context.team_batting_first,
        team_batting_second=context.team_batting_second,
        win_prob_batting_first=round(win_prob_first, 4),
        win_prob_batting_second=round(win_prob_second, 4),
        innings1_mean=round(float(np.mean(innings1_scores)), 1),
        innings1_std=round(float(np.std(innings1_scores)), 1),
        innings2_mean=round(float(np.mean(innings2_scores)), 1),
        innings2_std=round(float(np.std(innings2_scores)), 1),
        sessions=sessions,
        iterations=iterations,
    )
