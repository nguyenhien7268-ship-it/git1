# Tên file: logic/dashboard_analytics.py
# (PHASE 1 & 2 REFACTORING - WRAPPER MODULE)
# Logic đã được di chuyển sang logic/analytics/dashboard_scorer.py
# File này giữ lại để tương thích ngược với code cũ

"""
Wrapper module để tương thích ngược.
Toàn bộ logic đã được di chuyển sang logic.analytics.dashboard_scorer.
"""

# Import data repository for new function
try:
    from logic.data_repository import get_all_managed_bridges
except ImportError:
    def get_all_managed_bridges(*args, **kwargs): return []

# Import constants for threshold
try:
    from logic.constants import DEFAULT_SETTINGS
    DE_DYN_MIN_WINRATE = DEFAULT_SETTINGS.get("DE_DYN_MIN_WINRATE", 93.3)
except ImportError:
    DE_DYN_MIN_WINRATE = 93.3

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

def get_cau_dong_for_tab_soi_cau_de(db_name=None, threshold_thong=None):
    """
    PR1: Lấy danh sách cầu động đã lọc từ DB cho Tab Soi Cầu Đề.
    
    Lọc theo quy tắc:
    - Loại bỏ hoàn toàn DE_KILLER
    - Nếu type == 'DE_DYN', chỉ giữ khi win_rate >= threshold_thong
    
    Args:
        db_name: Đường dẫn database (None = mặc định)
        threshold_thong: Ngưỡng win_rate cho DE_DYN (None = dùng config)
    
    Returns:
        List[Dict]: Danh sách các bridge dict đã lọc
    """
    # Import DB_NAME locally to avoid circular dependencies
    if db_name is None:
        try:
            from logic.db_manager import DB_NAME
            db_name = DB_NAME
        except ImportError:
            db_name = "data/xo_so_prizes_all_logic.db"
    
    # Use configured threshold if not provided
    if threshold_thong is None:
        threshold_thong = DE_DYN_MIN_WINRATE
    
    # Normalize threshold to raw count (out of 30 periods)
    # Input can be:
    # - Raw count: 1-30 (e.g., 28 meaning 28 out of 30)
    # - Percentage: 50-100 (e.g., 93.3 meaning 93.3%)
    # - Decimal: 0.0-1.0 (e.g., 0.933 meaning 93.3%)
    
    if threshold_thong <= 1.0:
        # Decimal format (0.0-1.0) -> convert to raw count
        threshold_raw = int(threshold_thong * 30)
    elif 1.0 < threshold_thong <= 30:
        # Already in raw count format (1-30)
        threshold_raw = int(threshold_thong)
    elif 30 < threshold_thong <= 100:
        # Percentage format (30.1-100%) -> convert to raw count
        threshold_raw = int((threshold_thong / 100.0) * 30)
    else:
        # Invalid range (>100 or negative), use default 28
        print(f"  [WARNING] Invalid threshold {threshold_thong}, using default 28")
        threshold_raw = 28
    
    print(f"[get_cau_dong_for_tab_soi_cau_de] Ngưỡng lọc DE_DYN: {threshold_raw}/30 ({threshold_raw/30.0*100:.1f}%)")
    
    # Get all enabled bridges from DB
    all_bridges = get_all_managed_bridges(db_name, only_enabled=True)
    
    filtered_bridges = []
    filtered_count = {"DE_KILLER": 0, "DE_DYN_LOW": 0}
    
    for bridge in all_bridges:
        bridge_type = bridge.get("type", "")
        bridge_name = bridge.get("name", "N/A")
        win_rate = bridge.get("win_rate", 0) or 0  # Handle None
        
        # Rule 1: Loại bỏ hoàn toàn DE_KILLER
        if bridge_type == "DE_KILLER":
            filtered_count["DE_KILLER"] += 1
            print(f"  [FILTERED] DE_KILLER: {bridge_name}")
            continue
        
        # Rule 2: Lọc DE_DYN theo win_rate/streak
        if bridge_type == "DE_DYN":
            # Get the streak/win count value from DB
            # DB stores: current_streak (raw count) or win_rate (could be text or number)
            streak_value = bridge.get("current_streak", 0) or bridge.get("streak", 0)
            
            # Normalize to raw count based on value range
            if streak_value <= 0:
                streak_raw = 0
            elif streak_value <= 30:
                # It's already a raw count (1-30)
                streak_raw = int(streak_value)
            elif 30 < streak_value <= 100:
                # It's a percentage (30.1-100%) -> convert to raw count
                streak_raw = int((streak_value / 100.0) * 30)
            else:
                # Invalid value (>100), treat as 0
                print(f"  [WARNING] Invalid streak value {streak_value} for {bridge_name}, treating as 0")
                streak_raw = 0
            
            if streak_raw < threshold_raw:
                filtered_count["DE_DYN_LOW"] += 1
                print(f"  [FILTERED] DE_DYN (thông={streak_raw}/30 < {threshold_raw}/30): {bridge_name}")
                continue
        
        # Keep this bridge and normalize field names for UI compatibility
        # UI expects: name, type, streak, predicted_value
        # DB has: name, type, current_streak, next_prediction_stl
        if "current_streak" in bridge and "streak" not in bridge:
            bridge["streak"] = bridge["current_streak"]
        if "next_prediction_stl" in bridge and "predicted_value" not in bridge:
            bridge["predicted_value"] = bridge["next_prediction_stl"]
        
        filtered_bridges.append(bridge)
    
    # Summary log
    print(f"[get_cau_dong_for_tab_soi_cau_de] Kết quả:")
    print(f"  - Tổng cầu từ DB: {len(all_bridges)}")
    print(f"  - Đã lọc DE_KILLER: {filtered_count['DE_KILLER']}")
    print(f"  - Đã lọc DE_DYN (thấp): {filtered_count['DE_DYN_LOW']}")
    print(f"  - Còn lại: {len(filtered_bridges)}")
    
    return filtered_bridges


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
    'get_cau_dong_for_tab_soi_cau_de',
]
