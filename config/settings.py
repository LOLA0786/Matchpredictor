from pathlib import Path
import os
from dotenv import load_dotenv

ROOT_DIR        = Path(__file__).parent.parent
DATA_RAW        = ROOT_DIR / "data" / "raw"
DATA_PROCESSED  = ROOT_DIR / "data" / "processed"
DATA_MODELS     = ROOT_DIR / "data" / "models"
CRICSHEET_ZIP   = DATA_RAW / "ipl_all.zip"
CRICSHEET_URL   = "https://cricsheet.org/downloads/ipl_json.zip"

load_dotenv(ROOT_DIR / ".env")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

VENUES = {
    "Wankhede Stadium": {"city": "Mumbai", "lat": 18.9388, "lon": 72.8258, "dew_risk": 0.85, "chase_advantage": 0.58, "avg_first_innings_t20": 168, "avg_powerplay_runs": 52},
    "Eden Gardens": {"city": "Kolkata", "lat": 22.5645, "lon": 88.3433, "dew_risk": 0.80, "chase_advantage": 0.56, "avg_first_innings_t20": 162, "avg_powerplay_runs": 49},
    "M. Chinnaswamy Stadium": {"city": "Bengaluru", "lat": 12.9789, "lon": 77.5990, "dew_risk": 0.40, "chase_advantage": 0.54, "avg_first_innings_t20": 175, "avg_powerplay_runs": 55},
    "Arun Jaitley Stadium": {"city": "Delhi", "lat": 28.6364, "lon": 77.2167, "dew_risk": 0.50, "chase_advantage": 0.52, "avg_first_innings_t20": 161, "avg_powerplay_runs": 50},
    "MA Chidambaram Stadium": {"city": "Chennai", "lat": 13.0627, "lon": 80.2792, "dew_risk": 0.30, "chase_advantage": 0.48, "avg_first_innings_t20": 158, "avg_powerplay_runs": 47},
    "Rajiv Gandhi International Stadium": {"city": "Hyderabad", "lat": 17.4032, "lon": 78.4673, "dew_risk": 0.60, "chase_advantage": 0.55, "avg_first_innings_t20": 165, "avg_powerplay_runs": 51},
    "Narendra Modi Stadium": {"city": "Ahmedabad", "lat": 23.0902, "lon": 72.5958, "dew_risk": 0.35, "chase_advantage": 0.51, "avg_first_innings_t20": 163, "avg_powerplay_runs": 50},
    "Punjab Cricket Association Stadium": {"city": "Mohali", "lat": 30.6942, "lon": 76.7683, "dew_risk": 0.45, "chase_advantage": 0.53, "avg_first_innings_t20": 166, "avg_powerplay_runs": 52},
}

TOSS_FIELD_WIN_BOOST = {
    "Wankhede Stadium": 0.10, "Eden Gardens": 0.09, "M. Chinnaswamy Stadium": 0.05,
    "Arun Jaitley Stadium": 0.06, "MA Chidambaram Stadium": 0.02,
    "Rajiv Gandhi International Stadium": 0.07, "Narendra Modi Stadium": 0.04,
    "Punjab Cricket Association Stadium": 0.06, "default": 0.05,
}

TOURNAMENT_STAGE_RUN_MULTIPLIER = {
    "league_early": 1.05, "league_mid": 1.00, "league_late": 0.97,
    "qualifier": 0.96, "eliminator": 0.95, "final": 0.94,
}

SESSION_OVERS = [6, 10, 15, 20]
SESSION_BASELINE_RUNS = {
    6: {"mean": 50, "std": 9}, 10: {"mean": 84, "std": 12},
    15: {"mean": 120, "std": 15}, 20: {"mean": 158, "std": 20},
}

STAR_BATTER_ABSENCE_RUN_PENALTY  = 12
STAR_BOWLER_ABSENCE_WICKET_BOOST = 0.08
MONTE_CARLO_ITERATIONS = 10_000
RANDOM_SEED = 42
