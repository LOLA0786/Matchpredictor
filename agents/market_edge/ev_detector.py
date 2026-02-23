from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

MIN_EDGE_PERCENT    = 4.0
STRONG_EDGE_PERCENT = 8.0

@dataclass
class EVSignal:
    market: str
    selection: str
    model_prob: float
    implied_prob: float
    edge_percent: float
    decimal_odds: float
    ev_per_1000: float
    strength: str
    reasoning: str

@dataclass
class MarketEdgeReport:
    match: str
    signals: list
    summary: str

def decimal_to_implied(odds):
    if odds <= 1:
        raise ValueError(f"Invalid odds: {odds}")
    return round(1.0 / odds, 4)

def implied_to_decimal(prob):
    if prob <= 0 or prob >= 1:
        raise ValueError(f"Invalid prob: {prob}")
    return round(1.0 / prob, 3)

def _compute_ev(market, selection, model_prob, decimal_odds, reasoning):
    implied_prob = 1.0 / decimal_odds
    edge_percent = (model_prob - implied_prob) * 100
    if edge_percent < MIN_EDGE_PERCENT:
        return None
    ev = model_prob * (decimal_odds - 1) * 1000 - (1 - model_prob) * 1000
    strength = "strong" if edge_percent >= STRONG_EDGE_PERCENT else "moderate"
    return EVSignal(
        market=market, selection=selection, model_prob=model_prob,
        implied_prob=implied_prob, edge_percent=round(edge_percent, 2),
        decimal_odds=decimal_odds, ev_per_1000=round(ev, 0),
        strength=strength, reasoning=reasoning,
    )

def detect_ev(sim_result, match_label, bookmaker_odds):
    signals = []
    mw = bookmaker_odds.get("match_winner", {})
    if mw:
        for team, prob, key in [
            (sim_result.team_batting_first,  sim_result.win_prob_batting_first,  "team_batting_first"),
            (sim_result.team_batting_second, sim_result.win_prob_batting_second, "team_batting_second"),
        ]:
            odds = mw.get(key, 0)
            if odds > 1:
                sig = _compute_ev(f"Match Winner — {team}", team, prob, odds,
                                  f"Model gives {team} {prob:.1%} win prob.")
                if sig:
                    signals.append(sig)

    for session in sim_result.sessions:
        over_odds = bookmaker_odds.get("session_runs", {}).get(session.over, {})
        for line, model_prob_over in session.prob_over_line.items():
            for direction, prob, key in [
                ("Over", model_prob_over,         "over"),
                ("Under", 1 - model_prob_over,    "under"),
            ]:
                odds = over_odds.get(key, 0)
                if odds > 1:
                    sig = _compute_ev(
                        "Session Runs",
                        f"Runs {direction} {line} at {session.over} overs",
                        prob, odds,
                        f"Model: {prob:.1%} vs implied {1/odds:.1%}",
                    )
                    if sig:
                        signals.append(sig)

    strong   = sum(1 for s in signals if s.strength == "strong")
    moderate = sum(1 for s in signals if s.strength == "moderate")
    summary  = (f"{strong} strong, {moderate} moderate EV signals for {match_label}."
                if signals else f"No +EV signals for {match_label}.")
    logger.info(summary)
    return MarketEdgeReport(match=match_label, signals=signals, summary=summary)
