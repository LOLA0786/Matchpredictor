from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from config.settings import (
    VENUES, TOSS_FIELD_WIN_BOOST, TOURNAMENT_STAGE_RUN_MULTIPLIER,
    STAR_BATTER_ABSENCE_RUN_PENALTY, STAR_BOWLER_ABSENCE_WICKET_BOOST,
)

@dataclass
class PlayerAbsence:
    name: str
    role: str
    team: str

@dataclass
class MatchContext:
    venue: str
    team_batting_first: str
    team_batting_second: str
    toss_winner: str
    toss_decision: str
    match_time: str
    tournament_stage: str
    absent_players: list = field(default_factory=list)
    venue_avg_runs: float = 0.0
    venue_avg_powerplay: float = 0.0
    venue_chase_advantage: float = 0.5
    dew_risk: float = 0.0
    toss_win_prob_boost: float = 0.0
    stage_run_multiplier: float = 1.0
    run_adjustment: float = 0.0
    wicket_adjustment: float = 0.0

def build_match_context(venue, team_batting_first, team_batting_second,
                         toss_winner, toss_decision, match_time,
                         tournament_stage, absent_players=None):
    absent_players = absent_players or []
    ctx = MatchContext(
        venue=venue, team_batting_first=team_batting_first,
        team_batting_second=team_batting_second, toss_winner=toss_winner,
        toss_decision=toss_decision, match_time=match_time,
        tournament_stage=tournament_stage, absent_players=absent_players,
    )
    venue_data = VENUES.get(venue, {})
    if not venue_data:
        logger.warning(f"Venue '{venue}' not in registry. Using defaults.")

    ctx.venue_avg_runs      = venue_data.get("avg_first_innings_t20", 162.0)
    ctx.venue_avg_powerplay = venue_data.get("avg_powerplay_runs", 50.0)
    ctx.venue_chase_advantage = venue_data.get("chase_advantage", 0.50)
    ctx.dew_risk            = venue_data.get("dew_risk", 0.40)

    ctx.toss_win_prob_boost = (
        TOSS_FIELD_WIN_BOOST.get(venue, TOSS_FIELD_WIN_BOOST["default"])
        if toss_decision == "field" else 0.0
    )

    dew_run_adjustment = 0.0
    if match_time in ("day-night", "night"):
        dew_run_adjustment = ctx.dew_risk * 8
    ctx.run_adjustment += dew_run_adjustment

    ctx.stage_run_multiplier = TOURNAMENT_STAGE_RUN_MULTIPLIER.get(tournament_stage, 1.0)
    ctx.run_adjustment += ctx.venue_avg_runs * (ctx.stage_run_multiplier - 1.0)

    for player in absent_players:
        if player.role in ("batter", "allrounder"):
            ctx.run_adjustment    -= STAR_BATTER_ABSENCE_RUN_PENALTY
        if player.role in ("bowler", "allrounder"):
            ctx.wicket_adjustment += STAR_BOWLER_ABSENCE_WICKET_BOOST

    return ctx
