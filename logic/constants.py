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
    "DASHBOARD_MIN_RECENT_WINS": 9,  # Lo Dashboard filter: Show bridges with >= 9/10 recent wins
    "DE_DASHBOARD_MIN_RECENT_WINS": 9,  # De Dashboard filter: Show bridges with >= 9/10 recent wins
    "DATA_LIMIT_DASHBOARD": 1000, # 0 = All
    "DATA_LIMIT_RESEARCH": 0,     # 0 = All
    "DATA_LIMIT_SCANNER": 500,    # Giới hạn số kỳ khi Dò Cầu Mới (0 = Full)
    "DE_MAX_LOSE_THRESHOLD": 20,  # Ngưỡng chuỗi Gãy tối đa cho cầu Đề (Phase 4 - Pruning)
    
    # [NEW V10.5] Dan 65 Optimization Configuration
    "DAN65_TOP_SETS_COUNT": 5,        # Số lượng bộ top ưu tiên (default: 5)
    "DAN65_MIN_PER_TOP_SET": 1,       # Số tối thiểu từ mỗi bộ top (1-4, default: 1)
    "DAN65_SIZE": 65,                  # Kích thước dàn cuối cùng (default: 65)
    "DAN65_LOG_EXCLUDED_THRESHOLD": 30.0,  # Log số bị loại nếu điểm >= ngưỡng này
    
    # [NEW V11.3] DE Display Limits (Fixing low line count issue)
    "DE_CHOT_SO_CHAM_LIMIT": 8,        # Max number of top CHAM to display in summary
    "DE_CHOT_SO_BO_LIMIT": 8,          # Max number of top BO to display in summary
    
    # [NEW V10.7] DE Bridge Filtering & Control Configuration
    "ENABLE_DE_BRIDGES": True,         # Master switch for all DE bridges
    "ENABLE_DE_LO": True,              # Enable LO bridges scanning/display
    "ENABLE_DE_DE": True,              # Enable DE bridges scanning/display
    
    # DE_DYN Filtering (V10.7)
    "DE_DYN_MIN_WINRATE": 93.3,       # Minimum win rate for DE_DYN (28/30 = 93.3%)
    "DE_DYN_MAX_COUNT": 10,            # Maximum DE_DYN bridges to save
    
    # DE Visibility Policy (V11.0 - Hysteresis)
    "DE_WINDOW_KYS": 30,               # Window size for DE metrics (last N periods)
    "DE_DYN_ENABLE_RAW": 28,           # Enable threshold: wins >= 28 out of 30
    "DE_DYN_DISABLE_RAW": 26,          # Disable threshold: wins <= 26 out of 30
    
    # DE_KILLER Filtering (V10.7)
    "DE_KILLER_MAX_COUNT": 0,          # Maximum DE_KILLER bridges (0 = disabled)
    
    # DE_SET Priority (V10.7)
    "DE_SET_MIN_COUNT": 2,             # Minimum DE_SET bridges to guarantee
    
    # Chạm Thông Consecutive Requirement (V11.1)
    "CHAM_THONG_MIN_CONSEC": 8,        # Minimum consecutive matches at end for "chạm thông"
    
    # [NEW V8.0] Bridge Classification Indicators
    "DE_BRIDGE_INDICATORS": ["DE_", "Đề", "de_", "đề"],  # Indicators for De bridges
    
    # K2N Cache Control (V10.7)
    "K2N_CACHE_LO_ENABLED": True,      # Enable K2N cache refresh for LO bridges
    "K2N_CACHE_DE_ENABLED": True,      # Enable K2N cache refresh for DE bridges
    
    # Manager Rate Mode
    "MANAGER_RATE_MODE": "K1N",        # Backtest mode for bridge rate calculation (K1N/K2N)
    
    # [NEW V11.2] K1N-Primary Detection Flow Configuration
    "THRESHOLD_K1N_LO": 85.0,          # K1N threshold for LO bridges (%)
    "THRESHOLD_K1N_DE": 90.0,          # K1N threshold for DE bridges (%)
    "THRESHOLD_K2N_LO": 80.0,          # K2N threshold for LO bridges (%)
    "THRESHOLD_K2N_DE": 85.0,          # K2N threshold for DE bridges (%)
    "POLICY_TYPE": "k1n_primary",      # Import policy: 'k1n_primary', 'k2n_primary', 'combined'
    "FALLBACK_TO_K2N": True,           # Fallback to K2N when K1N is missing
    "AUTO_IMPORT_DEFAULT_ENABLE": False,   # Default enabled state for auto-imported bridges
    "AUTO_IMPORT_DEFAULT_PENDING": True,   # Default pending state for auto-imported bridges
    
    # Combined policy weights (when POLICY_TYPE='combined')
    "WEIGHT_K1N": 0.6,                 # Weight for K1N in combined score
    "WEIGHT_K2N": 0.4,                 # Weight for K2N in combined score
    
    # [NEW V8.0] Dual-Config Architecture (Lô/Đề)
    # Separate thresholds for Lo and De bridges
    "lo_config": {
        "remove_threshold": 43.0,      # Tắt cầu Lô khi tỷ lệ < 43%
        "add_threshold": 45.0,         # Bật lại cầu Lô khi tỷ lệ >= 45%
    },
    "de_config": {
        "remove_threshold": 80.0,      # Tắt cầu Đề khi tỷ lệ < 80%
        "add_threshold": 88.0,         # Bật lại cầu Đề khi tỷ lệ >= 88%
    },
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