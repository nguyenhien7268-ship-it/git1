# Tên file: logic/dashboard_analytics.py
# (PHASE 1 & 2 REFACTORING - WRAPPER MODULE)
# Logic đã được di chuyển sang logic/analytics/dashboard_scorer.py
# File này giữ lại để tương thích ngược với code cũ

"""
Wrapper module để tương thích ngược.
Toàn bộ logic đã được di chuyển sang logic.analytics.dashboard_scorer.
"""

# Import tất cả từ module mới
try:
    # Thử import tuyệt đối trước
    try:
        from logic.analytics.dashboard_scorer import (
            get_loto_stats_last_n_days,
            get_loto_gan_stats,
            get_top_memory_bridge_predictions,
            _standardize_pair,
            get_prediction_consensus,
            get_high_win_rate_predictions,
            get_pending_k2n_bridges,
            get_top_scored_pairs,
            get_consensus_simulation,
            get_high_win_simulation,
            prepare_daily_features,
            calculate_score_from_features,
            get_historical_dashboard_data,
        )
    except ImportError:
        # Fallback: thử import tương đối
        from .analytics.dashboard_scorer import (
            get_loto_stats_last_n_days,
            get_loto_gan_stats,
            get_top_memory_bridge_predictions,
            _standardize_pair,
            get_prediction_consensus,
            get_high_win_rate_predictions,
            get_pending_k2n_bridges,
            get_top_scored_pairs,
            get_consensus_simulation,
            get_high_win_simulation,
            prepare_daily_features,
            calculate_score_from_features,
            get_historical_dashboard_data,
        )
except ImportError:
    # Fallback: Nếu import lỗi, tạo các hàm dummy
    def get_loto_stats_last_n_days(*args, **kwargs): return []
    def get_loto_gan_stats(*args, **kwargs): return []
    def get_top_memory_bridge_predictions(*args, **kwargs): return []
    def _standardize_pair(*args, **kwargs): return None
    def get_prediction_consensus(*args, **kwargs): return []
    def get_high_win_rate_predictions(*args, **kwargs): return []
    def get_pending_k2n_bridges(*args, **kwargs): return []
    def get_top_scored_pairs(*args, **kwargs): return []
    def get_consensus_simulation(*args, **kwargs): return []
    def get_high_win_simulation(*args, **kwargs): return []
    def prepare_daily_features(*args, **kwargs): return None
    def calculate_score_from_features(*args, **kwargs): return []
    def get_historical_dashboard_data(*args, **kwargs): return None
    print("Cảnh báo: Không thể import từ logic.analytics.dashboard_scorer. Sử dụng fallback.")

__all__ = [
    'get_loto_stats_last_n_days',
    'get_loto_gan_stats',
    'get_top_memory_bridge_predictions',
    '_standardize_pair',
    'get_prediction_consensus',
    'get_high_win_rate_predictions',
    'get_pending_k2n_bridges',
    'get_top_scored_pairs',
    'get_consensus_simulation',
    'get_high_win_simulation',
    'prepare_daily_features',
    'calculate_score_from_features',
    'get_historical_dashboard_data',
]
