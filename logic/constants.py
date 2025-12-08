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
    "DE_MAX_LOSE_THRESHOLD": 20,  # Ngưỡng chuỗi Gãy tối đa cho cầu Đề (Phase 4 - Pruning)
    
    # [NEW V10.5] Dan 65 Optimization Configuration
    "DAN65_TOP_SETS_COUNT": 5,        # Số lượng bộ top ưu tiên (default: 5)
    "DAN65_MIN_PER_TOP_SET": 1,       # Số tối thiểu từ mỗi bộ top (1-4, default: 1)
    "DAN65_SIZE": 65,                  # Kích thước dàn cuối cùng (default: 65)
    "DAN65_LOG_EXCLUDED_THRESHOLD": 30.0,  # Log số bị loại nếu điểm >= ngưỡng này
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

# [NEW V3.8] SCORING ENGINE WEIGHTS (TỐI ƯU HÓA ĐIỂM SỐ)
SCORING_WEIGHTS = {
    # --- LÔ SCORING ---
    'LO_STREAK_MULTIPLIER': 1.0,      # Hệ số nhân cho chuỗi thông (Attack)
    'LO_WINRATE_DIVISOR': 20.0,       # Hệ số chia cho WinRate (Attack) -> 100% / 20 = 5 điểm
    'LO_MEMORY_DIVISOR': 10.0,        # Hệ số chia cho Confidence Bạc nhớ
    
    # Phạt Lô Gan (Defense)
    'LO_GAN_PENALTY_LOW': 2.0,        # Gan > 10 ngày
    'LO_GAN_PENALTY_MED': 5.0,        # Gan > 15 ngày
    'LO_GAN_PENALTY_HIGH': 15.0,      # Gan > 25 ngày (Sát thủ)
    
    # Thưởng Tần Suất (Bonus)
    'LO_FREQ_BONUS_MAX': 3.0,         # Điểm thưởng tối đa cho Lô về nhiều

    # --- ĐỀ SCORING ---
    'DE_SET_MULTIPLIER': 2.0,         # Hệ số nhân cho Cầu Bộ (Ưu tiên cao nhất)
    'DE_NORMAL_MULTIPLIER': 1.0,      # Hệ số nhân cho Cầu Chạm/Tổng
    
    # Phạt Cầu Loại (Killer)
    'DE_KILLER_MULTIPLIER': 3.0,      # Hệ số phạt cực nặng để loại số
    
    # Thưởng Thị Trường
    'DE_MARKET_CHAM_BONUS': 2.0,      # Max bonus cho Chạm Hot
    'DE_MARKET_BO_BONUS': 1.0,        # Max bonus cho Bộ Hot
}