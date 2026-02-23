import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest
from agents.context_engine.context import build_match_context, PlayerAbsence
from agents.simulation.monte_carlo import simulate_match
from agents.market_edge.ev_detector import detect_ev, decimal_to_implied, implied_to_decimal

@pytest.fixture
def ctx():
    return build_match_context(
        venue="Wankhede Stadium", team_batting_first="Mumbai Indians",
        team_batting_second="Chennai Super Kings", toss_winner="Chennai Super Kings",
        toss_decision="field", match_time="night", tournament_stage="league_early",
    )

@pytest.fixture
def sim(ctx):
    return simulate_match(context=ctx, iterations=1000)

def test_win_probs_sum_to_one(sim):
    assert abs(sim.win_prob_batting_first + sim.win_prob_batting_second - 1.0) < 0.01

def test_win_probs_valid_range(sim):
    assert 0 < sim.win_prob_batting_first < 1
    assert 0 < sim.win_prob_batting_second < 1

def test_four_sessions(sim):
    assert len(sim.sessions) == 4

def test_session_means_increase(sim):
    means = [s.mean_runs for s in sim.sessions]
    assert means == sorted(means)

def test_innings_score_realistic(sim):
    assert 120 < sim.innings1_mean < 220

def test_dew_risk_wankhede(ctx):
    assert ctx.dew_risk >= 0.8

def test_toss_boost_when_fielding(ctx):
    assert ctx.toss_win_prob_boost > 0

def test_toss_no_boost_when_batting():
    ctx = build_match_context(
        venue="Wankhede Stadium", team_batting_first="MI", team_batting_second="CSK",
        toss_winner="MI", toss_decision="bat", match_time="night", tournament_stage="league_mid",
    )
    assert ctx.toss_win_prob_boost == 0.0

def test_player_absence_lowers_runs():
    ctx_full = build_match_context("Eden Gardens","KKR","RCB","KKR","bat","night","league_mid")
    ctx_miss = build_match_context("Eden Gardens","KKR","RCB","KKR","bat","night","league_mid",
        absent_players=[PlayerAbsence("Virat Kohli","batter","RCB")])
    assert ctx_miss.run_adjustment < ctx_full.run_adjustment

def test_no_ev_at_fair_odds(sim):
    odds = {
        "match_winner": {
            "team_batting_first":  1.0 / sim.win_prob_batting_first,
            "team_batting_second": 1.0 / sim.win_prob_batting_second,
        }
    }
    report = detect_ev(sim, "MI vs CSK", odds)
    assert len(report.signals) == 0

def test_strong_ev_on_mispriced_odds(sim):
    report = detect_ev(sim, "MI vs CSK", {
        "match_winner": {"team_batting_first": 4.0, "team_batting_second": 4.0}
    })
    assert any(s.strength == "strong" for s in report.signals)

def test_decimal_to_implied():
    assert abs(decimal_to_implied(2.0) - 0.50) < 0.001

def test_implied_to_decimal():
    assert abs(implied_to_decimal(0.5) - 2.0) < 0.001
