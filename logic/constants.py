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
    "DATA_LIMIT_DASHBOARD": 1000, # 0 = All
    "DATA_LIMIT_RESEARCH": 0,     # 0 = All
    "DATA_LIMIT_SCANNER": 500,    # Giới hạn số kỳ khi Dò Cầu Mới (0 = Full)
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
