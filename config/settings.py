from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT_DIR        = Path(__file__).parent.parent
DATA_RAW        = ROOT_DIR / "data" / "raw"
DATA_PROCESSED  = ROOT_DIR / "data" / "processed"
DATA_MODELS     = ROOT_DIR / "data" / "models"
CRICSHEET_ZIP   = DATA_RAW / "ipl_all.zip"
CRICSHEET_URL   = "https://cricsheet.org/downloads/ipl_json.zip"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# All averages from real Cricsheet data: 1169 matches, 278,205 deliveries
# chase_advantage = fraction of time chasing team wins (from toss model)
# dew_risk = 0.0 (none) to 1.0 (extreme) based on city + match conditions

VENUES = {
    "Wankhede Stadium, Mumbai":     {"city":"Mumbai",    "lat":18.9388,"lon":72.8258,"dew_risk":0.85,"chase_advantage":0.591,"avg_first_innings_t20":177,"avg_powerplay_runs":54},
    "Wankhede Stadium":             {"city":"Mumbai",    "lat":18.9388,"lon":72.8258,"dew_risk":0.85,"chase_advantage":0.510,"avg_first_innings_t20":166,"avg_powerplay_runs":51},
    "Eden Gardens, Kolkata":        {"city":"Kolkata",   "lat":22.5645,"lon":88.3433,"dew_risk":0.80,"chase_advantage":0.389,"avg_first_innings_t20":197,"avg_powerplay_runs":57},
    "Eden Gardens":                 {"city":"Kolkata",   "lat":22.5645,"lon":88.3433,"dew_risk":0.80,"chase_advantage":0.633,"avg_first_innings_t20":160,"avg_powerplay_runs":49},
    "M Chinnaswamy Stadium":        {"city":"Bengaluru", "lat":12.9789,"lon":77.5990,"dew_risk":0.40,"chase_advantage":0.544,"avg_first_innings_t20":168,"avg_powerplay_runs":52},
    "M Chinnaswamy Stadium, Bengaluru": {"city":"Bengaluru","lat":12.9789,"lon":77.5990,"dew_risk":0.40,"chase_advantage":0.474,"avg_first_innings_t20":168,"avg_powerplay_runs":52},
    "M.Chinnaswamy Stadium":        {"city":"Bengaluru", "lat":12.9789,"lon":77.5990,"dew_risk":0.40,"chase_advantage":0.500,"avg_first_innings_t20":168,"avg_powerplay_runs":52},
    "Feroz Shah Kotla":             {"city":"Delhi",     "lat":28.6364,"lon":77.2167,"dew_risk":0.50,"chase_advantage":0.559,"avg_first_innings_t20":162,"avg_powerplay_runs":50},
    "Arun Jaitley Stadium, Delhi":  {"city":"Delhi",     "lat":28.6364,"lon":77.2167,"dew_risk":0.50,"chase_advantage":0.444,"avg_first_innings_t20":200,"avg_powerplay_runs":58},
    "MA Chidambaram Stadium, Chepauk":          {"city":"Chennai","lat":13.0627,"lon":80.2792,"dew_risk":0.30,"chase_advantage":0.382,"avg_first_innings_t20":166,"avg_powerplay_runs":48},
    "MA Chidambaram Stadium, Chepauk, Chennai": {"city":"Chennai","lat":13.0627,"lon":80.2792,"dew_risk":0.30,"chase_advantage":0.385,"avg_first_innings_t20":164,"avg_powerplay_runs":48},
    "Rajiv Gandhi International Stadium, Uppal":                    {"city":"Hyderabad","lat":17.4032,"lon":78.4673,"dew_risk":0.60,"chase_advantage":0.217,"avg_first_innings_t20":156,"avg_powerplay_runs":48},
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad":        {"city":"Hyderabad","lat":17.4032,"lon":78.4673,"dew_risk":0.60,"chase_advantage":0.545,"avg_first_innings_t20":156,"avg_powerplay_runs":48},
    "Rajiv Gandhi International Stadium":                           {"city":"Hyderabad","lat":17.4032,"lon":78.4673,"dew_risk":0.60,"chase_advantage":0.300,"avg_first_innings_t20":156,"avg_powerplay_runs":48},
    "Narendra Modi Stadium, Ahmedabad": {"city":"Ahmedabad","lat":23.0902,"lon":72.5958,"dew_risk":0.35,"chase_advantage":0.481,"avg_first_innings_t20":187,"avg_powerplay_runs":55},
    "Punjab Cricket Association Stadium, Mohali": {"city":"Mohali","lat":30.6942,"lon":76.7683,"dew_risk":0.45,"chase_advantage":0.524,"avg_first_innings_t20":163,"avg_powerplay_runs":51},
    "Sawai Mansingh Stadium":       {"city":"Jaipur",   "lat":26.8926,"lon":75.8076,"dew_risk":0.45,"chase_advantage":0.678,"avg_first_innings_t20":158,"avg_powerplay_runs":49},
    "Maharashtra Cricket Association Stadium": {"city":"Pune","lat":18.6298,"lon":73.7997,"dew_risk":0.50,"chase_advantage":0.650,"avg_first_innings_t20":166,"avg_powerplay_runs":51},
    "Dr DY Patil Sports Academy, Mumbai": {"city":"Mumbai","lat":19.0438,"lon":73.0183,"dew_risk":0.75,"chase_advantage":0.529,"avg_first_innings_t20":171,"avg_powerplay_runs":53},
    "Dubai International Cricket Stadium": {"city":"Dubai","lat":25.0449,"lon":55.2373,"dew_risk":0.20,"chase_advantage":0.407,"avg_first_innings_t20":164,"avg_powerplay_runs":50},
    "Sharjah Cricket Stadium":      {"city":"Sharjah",  "lat":25.3311,"lon":55.3820,"dew_risk":0.15,"chase_advantage":0.650,"avg_first_innings_t20":159,"avg_powerplay_runs":49},
    "Sheikh Zayed Stadium":         {"city":"Abu Dhabi","lat":24.4186,"lon":54.4740,"dew_risk":0.15,"chase_advantage":0.429,"avg_first_innings_t20":159,"avg_powerplay_runs":49},
    "Brabourne Stadium, Mumbai":    {"city":"Mumbai",   "lat":18.9322,"lon":72.8264,"dew_risk":0.75,"chase_advantage":0.500,"avg_first_innings_t20":162,"avg_powerplay_runs":50},
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow": {"city":"Lucknow","lat":26.8920,"lon":80.9459,"dew_risk":0.55,"chase_advantage":0.625,"avg_first_innings_t20":175,"avg_powerplay_runs":54},
    "Subrata Roy Sahara Stadium":   {"city":"Pune",     "lat":18.5975,"lon":73.8075,"dew_risk":0.45,"chase_advantage":0.600,"avg_first_innings_t20":160,"avg_powerplay_runs":50},
}

# Field win boost = (field_win_rate - 0.50) from real toss model data
TOSS_FIELD_WIN_BOOST = {
    "Sawai Mansingh Stadium":                    0.179,
    "Sharjah Cricket Stadium":                   0.150,
    "Maharashtra Cricket Association Stadium":   0.150,
    "Eden Gardens":                              0.132,
    "Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium, Lucknow": 0.125,
    "Dr DY Patil Sports Academy, Mumbai":        0.100,
    "Wankhede Stadium, Mumbai":                  0.091,
    "Feroz Shah Kotla":                          0.059,
    "M Chinnaswamy Stadium":                     0.044,
    "Punjab Cricket Association Stadium, Mohali":0.024,
    "MA Chidambaram Stadium, Chepauk, Chennai":  0.024,
    "Wankhede Stadium":                          0.010,
    "Narendra Modi Stadium, Ahmedabad":         -0.019,
    "M Chinnaswamy Stadium, Bengaluru":         -0.026,
    "Rajiv Gandhi International Stadium, Uppal":-0.038,
    "Arun Jaitley Stadium, Delhi":              -0.056,
    "Dubai International Cricket Stadium":      -0.093,
    "Eden Gardens, Kolkata":                    -0.111,
    "Rajiv Gandhi International Stadium, Uppal, Hyderabad": 0.045,
    "default": 0.05,
}

TOURNAMENT_STAGE_RUN_MULTIPLIER = {
    "league_early": 1.05,
    "league_mid":   1.00,
    "league_late":  0.97,
    "qualifier":    0.96,
    "eliminator":   0.95,
    "final":        0.94,
}

SESSION_OVERS        = [6, 10, 15, 20]
SESSION_BASELINE_RUNS = {
    6:  {"mean": 50, "std": 9},
    10: {"mean": 84, "std": 12},
    15: {"mean": 120, "std": 15},
    20: {"mean": 158, "std": 20},
}

STAR_BATTER_ABSENCE_RUN_PENALTY  = 12
STAR_BOWLER_ABSENCE_WICKET_BOOST = 0.08
MONTE_CARLO_ITERATIONS           = 10_000
RANDOM_SEED                      = 42
