# logic/constants.py
"""
Central location for all default settings and constants.
This file provides a single source of truth for configuration values.
"""

# Default Configuration Settings
DEFAULT_SETTINGS = {
    "STATS_DAYS": 7,
    "GAN_DAYS": 15,
    "HIGH_WIN_THRESHOLD": 47.0,
    "AUTO_ADD_MIN_RATE": 50.0,
    "AUTO_PRUNE_MIN_RATE": 40.0,
    "K2N_RISK_START_THRESHOLD": 4,
    "K2N_RISK_PENALTY_PER_FRAME": 0.5,
    "AI_PROB_THRESHOLD": 45.0,
    "AI_MAX_DEPTH": 6,
    "AI_N_ESTIMATORS": 200,
    "AI_LEARNING_RATE": 0.05,
    "AI_OBJECTIVE": "binary:logistic",
    "AI_SCORE_WEIGHT": 0.2,
    "RECENT_FORM_PERIODS": 10,
    "RECENT_FORM_BONUS_HIGH": 3.0,
    "RECENT_FORM_BONUS_MED": 2.0,
    "RECENT_FORM_BONUS_LOW": 1.0,
    "RECENT_FORM_MIN_HIGH": 8,
    "RECENT_FORM_MIN_MED": 6,
    "RECENT_FORM_MIN_LOW": 5,
}

# Database Paths
DB_PATH = "data/xo_so_prizes_all_logic.db"

# Machine Learning Model Paths
MODEL_PATH = "logic/ml_model_files/loto_model.joblib"
SCALER_PATH = "logic/ml_model_files/ai_scaler.joblib"

# Lottery Constants
ALL_LOTOS = [str(i).zfill(2) for i in range(100)]
MIN_DATA_TO_TRAIN = 50

# File Upload Limits
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_LINES = 100_000

# Allowed File Extensions
ALLOWED_FILE_EXTENSIONS = ['.txt', '.json']

# =============================================================================
# Bridge Management Constants (for normalization and defaulting)
# =============================================================================
import re
from typing import Tuple

# Bridge types (display / storage)
BRIDGE_TYPE_MANUAL_LO = "manual_lo"
BRIDGE_TYPE_MANUAL_DE = "manual_de"
BRIDGE_TYPE_ALGO_LO = "algo_lo"
BRIDGE_TYPE_ALGO_DE = "algo_de"

# Default numeric text values used in DB payloads
DEFAULT_WIN_RATE = "50"      # stored as text in existing DB schema
DEFAULT_SEARCH_RATE = "10"   # stored as text

# Mapping UI display types (or shorthand) to DB canonical types
# Example: UI might show "LO" or "LO_manual"; map to DB constants above.
WHITELIST_DISPLAY_TYPES: Tuple[Tuple[str, str], ...] = (
    ("lo_manual", BRIDGE_TYPE_MANUAL_LO),
    ("de_manual", BRIDGE_TYPE_MANUAL_DE),
    ("lo_algo", BRIDGE_TYPE_ALGO_LO),
    ("de_algo", BRIDGE_TYPE_ALGO_DE),
    ("manual_lo", BRIDGE_TYPE_MANUAL_LO),
    ("manual_de", BRIDGE_TYPE_MANUAL_DE),
    ("algo_lo", BRIDGE_TYPE_ALGO_LO),
    ("algo_de", BRIDGE_TYPE_ALGO_DE),
)

# Naming sanitation regex: keep unicode letters, numbers, hyphen, underscore, space
# Replace other chars with single space, then collapse whitespace.
# This constant is intentionally conservative to preserve user input while avoiding DB issues.
NAME_SANITIZE_REGEX = re.compile(r"[^\w\-\s\u00C0-\u024F\u1E00-\u1EFF]+", flags=re.UNICODE)

# Helper: allowed minimum length after strip
MIN_NAME_LENGTH = 1
