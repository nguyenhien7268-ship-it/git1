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

def _determine_de_dyn_visibility(bridge, enable_threshold_raw, disable_threshold_raw):
    """
    Determine if a DE_DYN bridge should be visible based on visibility policy.
    
    Precedence:
    1. Manual override (de_manual_override == 1): use de_manual_override_value
    2. Auto enabled (de_auto_enabled == 1): show
    3. Computed metrics with hysteresis: check de_win_count_last30
    
    Args:
        bridge: Bridge dict from DB
        enable_threshold_raw: Threshold to enable (e.g., 28)
        disable_threshold_raw: Threshold to disable (e.g., 26)
    
    Returns:
        (visible: bool, reason: str)
    """
    bridge_name = bridge.get("name", "N/A")
    
    # Priority 1: Manual override
    de_manual_override = bridge.get("de_manual_override", 0)
    if de_manual_override == 1:
        de_manual_override_value = bridge.get("de_manual_override_value", 0)
        visible = bool(de_manual_override_value)
        reason = f"manual override (value={de_manual_override_value})"
        return visible, reason
    
    # Priority 2: Auto enabled flag
    de_auto_enabled = bridge.get("de_auto_enabled", 0)
    if de_auto_enabled == 1:
        return True, "auto flag true"
    
    # Priority 3: Computed metrics with hysteresis
    de_win_count_last30 = bridge.get("de_win_count_last30")
    
    if de_win_count_last30 is None:
        # Try legacy fields as fallback
        current_streak = bridge.get("current_streak")
        streak = bridge.get("streak")
        
        if current_streak is not None:
            wins_last30 = int(current_streak) if current_streak <= 30 else int((current_streak / 100.0) * 30)
        elif streak is not None:
            wins_last30 = int(streak) if streak <= 30 else int((streak / 100.0) * 30)
        else:
            # No metrics available - mark for evaluation and hide
            bridge["needs_evaluation"] = True
            return False, "no metrics available (needs evaluation)"
    else:
        wins_last30 = int(de_win_count_last30)
    
    # Apply hysteresis thresholds
    if wins_last30 >= enable_threshold_raw:
        return True, f"wins30={wins_last30} >= enable_threshold={enable_threshold_raw}"
    elif wins_last30 <= disable_threshold_raw:
        return False, f"wins30={wins_last30} <= disable_threshold={disable_threshold_raw}"
    else:
        # In hysteresis zone: check previous auto_enabled state
        prev_auto_enabled = bridge.get("de_auto_enabled", 0)
        if prev_auto_enabled == 1:
            return True, f"wins30={wins_last30} in hysteresis zone, prev_auto=1"
        else:
            return False, f"wins30={wins_last30} in hysteresis zone, prev_auto=0"


# def get_cau_dong_for_tab_soi_cau_de(db_name=None, threshold_thong=None):
#     """
#     V11.0: Lấy danh sách cầu động đã lọc từ DB cho Tab Soi Cầu Đề.
    
#     Implements strict visibility policy with auto/manual/hysteresis rules:
#     - Only DE_* bridges are included
#     - DE_KILLER always excluded
#     - DE_DYN visibility determined by: manual override > auto_enabled > computed metrics with hysteresis
    
#     Args:
#         db_name: Đường dẫn database (None = mặc định)
#         threshold_thong: Legacy parameter (kept for compatibility, not used in new policy)
    
#     Returns:
#         List[Dict]: Danh sách các bridge dict đã lọc, với needs_evaluation flag nếu thiếu metrics
#     """
#     # Import DB_NAME locally to avoid circular dependencies
#     if db_name is None:
#         try:
#             from logic.db_manager import DB_NAME
#             db_name = DB_NAME
#         except ImportError:
#             db_name = "data/xo_so_prizes_all_logic.db"
    
#     # Load configuration from constants
#     try:
#         from logic.constants import DEFAULT_SETTINGS
#         window_kys = DEFAULT_SETTINGS.get("DE_WINDOW_KYS", 30)
#         enable_threshold_raw = DEFAULT_SETTINGS.get("DE_DYN_ENABLE_RAW", 28)
#         disable_threshold_raw = DEFAULT_SETTINGS.get("DE_DYN_DISABLE_RAW", 26)
#     except ImportError:
#         # Fallback defaults
#         window_kys = 30
#         enable_threshold_raw = 28
#         disable_threshold_raw = 26
    
#     print(f"[get_cau_dong_for_tab_soi_cau_de] DE Visibility Policy:")
#     print(f"  - Window: {window_kys} periods")
#     print(f"  - Enable threshold: {enable_threshold_raw}/{window_kys}")
#     print(f"  - Disable threshold: {disable_threshold_raw}/{window_kys}")
#     print(f"  - Hysteresis zone: {disable_threshold_raw+1} to {enable_threshold_raw-1}")
    
#     # Get all enabled bridges from DB
#     all_bridges = get_all_managed_bridges(db_name, only_enabled=True)
    
#     filtered_bridges = []
#     filtered_count = {
#         "NON_DE": 0,
#         "DE_KILLER": 0, 
#         "DE_DYN_HIDDEN": 0,
#         "NEEDS_EVAL": 0
#     }
    
#     for bridge in all_bridges:
#         bridge_type = (bridge.get("type", "") or "").upper()
#         bridge_name = bridge.get("name", "N/A")
#         bridge_id = bridge.get("id", "?")
        
#         # Rule 0: Only include DE_* bridges in this tab
#         if not bridge_type.startswith("DE_"):
#             filtered_count["NON_DE"] += 1
#             print(f"  [FILTERED] Non-DE bridge: {bridge_name} ({bridge_type})")
#             continue
        
#         # Rule 1: Always exclude DE_KILLER
#         if bridge_type == "DE_KILLER":
#             filtered_count["DE_KILLER"] += 1
#             print(f"  [FILTERED] DE_KILLER: {bridge_name}")
#             continue
        
#         # Rule 2: Dynamic bridge visibility with auto/manual/hysteresis policy
#         # Auto-detect dynamic variants (DE_DYN, DE_DYNAMIC, DE_DYNAMIC_K, etc.)
#         from logic.bridges.de_performance import is_dynamic_bridge_type
        
#         if is_dynamic_bridge_type(bridge_type):
#             visible, reason = _determine_de_dyn_visibility(
#                 bridge, 
#                 enable_threshold_raw, 
#                 disable_threshold_raw
#             )
            
#             if not visible:
#                 filtered_count["DE_DYN_HIDDEN"] += 1
#                 print(f"  [FILTERED] Dynamic bridge hidden: {bridge_name} ({bridge_type}) - {reason}")
                
#                 # Check if it needs evaluation
#                 if bridge.get("needs_evaluation", False):
#                     filtered_count["NEEDS_EVAL"] += 1
                
#                 continue
#             else:
#                 print(f"  [VISIBLE] Dynamic bridge: {bridge_name} ({bridge_type}) - {reason}")
        
#         # Normalize field names for UI compatibility
#         if "current_streak" in bridge and "streak" not in bridge:
#             bridge["streak"] = bridge["current_streak"]
#         if "next_prediction_stl" in bridge and "predicted_value" not in bridge:
#             bridge["predicted_value"] = bridge["next_prediction_stl"]
        
#         filtered_bridges.append(bridge)
    
#     # Summary log
#     print(f"\n[get_cau_dong_for_tab_soi_cau_de] Summary:")
#     print(f"  - Total from DB: {len(all_bridges)}")
#     print(f"  - Filtered Non-DE (LO_*, etc.): {filtered_count['NON_DE']}")
#     print(f"  - Filtered DE_KILLER: {filtered_count['DE_KILLER']}")
#     print(f"  - Filtered DE_DYN (hidden): {filtered_count['DE_DYN_HIDDEN']}")
#     print(f"  - Needs evaluation: {filtered_count['NEEDS_EVAL']}")
#     print(f"  - Final result: {len(filtered_bridges)}")
    
#     return filtered_bridges

def get_cau_dong_for_tab_soi_cau_de(db_name=None, threshold_thong=None):
    """
    Simplified visibility: only apply DE_KILLER exclusion. All other bridges
    (including DE_*, non-DE, dynamic variants, etc.) will be returned as-is,
    except those explicitly of type 'DE_KILLER' which are always excluded.

    Args:
        db_name: Đường dẫn database (None = mặc định)
        threshold_thong: Legacy parameter (kept for compatibility, not used)

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

    # Get all enabled bridges from DB (preserve existing behaviour)
    all_bridges = get_all_managed_bridges(db_name, only_enabled=True)

    filtered_bridges = []
    filtered_count = {
        "DE_KILLER": 0,
    }

    for bridge in all_bridges:
        bridge_type = (bridge.get("type", "") or "").upper()
        bridge_name = bridge.get("name", "N/A")

        # Only apply Rule 1: exclude DE_KILLER
        if bridge_type == "DE_KILLER":
            filtered_count["DE_KILLER"] += 1
            # Keep a debug print for visibility
            print(f"  [FILTERED] DE_KILLER: {bridge_name}")
            continue

        # No other filtering: include the bridge
        # Normalize field names for UI compatibility (keep existing normalizations)
        if "current_streak" in bridge and "streak" not in bridge:
            bridge["streak"] = bridge["current_streak"]
        if "next_prediction_stl" in bridge and "predicted_value" not in bridge:
            bridge["predicted_value"] = bridge["next_prediction_stl"]

        filtered_bridges.append(bridge)

    # Summary log
    print(f"\n[get_cau_dong_for_tab_soi_cau_de] Summary:")
    print(f"  - Total from DB: {len(all_bridges)}")
    print(f"  - Filtered DE_KILLER: {filtered_count['DE_KILLER']}")
    print(f"  - Final result: {len(filtered_bridges)}")

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
