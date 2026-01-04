# Tên file: git1/lottery_service.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA LỖI MISSING IMPORT DASHBOARD ANALYTICS)
#
"""
==================================================================================
LOTTERY SERVICE API (BỘ ĐIỀU PHỐI) - (V7.4 - FIXED EXPORTS)
==================================================================================
File này đóng vai trò là API trung tâm, import và phân phối logic từ
các file con trong thư mục /logic.
"""
# 1. LOGIC DB & REPO
try:
    from logic.data_repository import get_all_managed_bridges, load_data_ai_from_db, delete_managed_bridges_batch
    from logic.db_manager import (
        DB_NAME,
        delete_managed_bridge,
        delete_ky_from_db,
        get_all_kys_from_db,
        get_results_by_ky,
        setup_database,
        update_bridge_k2n_cache_batch,
        update_bridge_win_rate_batch,
        update_managed_bridge,
        upsert_managed_bridge,
    )

    print(">>> (V7.3) Loaded logic.db_manager & data_repository successfully.")
except ImportError as e_db:
    print(f"CRITICAL ERROR: Could not import logic DB/Repo: {e_db}")
    # Fallback for DB_NAME and functions if import fails
    DB_NAME = "data/xo_so_prizes_all_logic.db"
    def delete_managed_bridges_batch(names, db_name=None, transactional=False, chunk_size=500):
        return {"requested": len(names or []), "deleted": [], "missing": list(names or []), "failed": [{"error": "delete_managed_bridges_batch not available"}]}
    def upsert_managed_bridge(*args, **kwargs):
        return False, "Logic DB manager not available"

# 2. LOGIC PARSING (XỬ LÝ DỮ LIỆU)
try:
    from logic.data_parser import (
        parse_and_APPEND_data,
        parse_and_APPEND_data_TEXT,
        parse_and_insert_data,
        run_and_update_from_text,
    )

    print(">>> (V7.3) Loaded logic.data_parser successfully.")
except ImportError as e_parser:
    print(f"CRITICAL ERROR: Could not import logic.data_parser: {e_parser}")

# 3. LOGIC CẦU CỔ ĐIỂN & TIỆN ÍCH
try:
    from logic.bridges.bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5,
        calculate_loto_stats,
        getAllLoto_V30,
    )

    print(">>> (V7.3) Loaded logic.bridges.bridges_classic successfully.")
except ImportError as e_classic:
    print(
        f"CRITICAL ERROR: Could not import logic.bridges.bridges_classic: {e_classic}"
    )

# 4. LOGIC BACKTEST
try:
    from logic.backtester import (
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_15_CAU_N1_V31_AI_V8,
        BACKTEST_CUSTOM_CAU_V16,
        BACKTEST_MANAGED_BRIDGES_K2N,
        BACKTEST_MANAGED_BRIDGES_N1,
        BACKTEST_MEMORY_BRIDGES,
        TONGHOP_TOP_CAU_N1_V5,
        TONGHOP_TOP_CAU_RATE_V5,
        run_and_update_all_bridge_K2N_cache,
        run_and_update_all_bridge_rates,
    )

    print(">>> (V7.3) Loaded logic.backtester successfully.")
except ImportError as e_backtester:
    print(f"CRITICAL ERROR: Could not import logic.backtester: {e_backtester}")

# 5. LOGIC QUẢN LÝ CẦU (DÒ, LỌC)
try:
    # Import scanning functions from lo_bridge_scanner
    from logic.bridges.lo_bridge_scanner import (
        TIM_CAU_BAC_NHO_TOT_NHAT,
        TIM_CAU_TOT_NHAT_V16,
        update_fixed_lo_bridges,
    )
    # Import management functions from bridge_manager_core
    from logic.bridges.bridge_manager_core import (
        auto_manage_bridges,
        find_and_auto_manage_bridges,
        prune_bad_bridges,
    )
    from logic.bridges.bridge_manager_de import find_and_auto_manage_bridges_de

    print(">>> (V7.3) Loaded logic.bridges.bridge_manager_core & lo_bridge_scanner successfully.")
except ImportError as e_bridge_core:
    print(
        f"CRITICAL ERROR: Could not import logic.bridges modules: {e_bridge_core}"
    )

# 6. LOGIC DASHBOARD (CHẤM ĐIỂM)
try:
    from logic.dashboard_analytics import (
        get_high_win_rate_predictions,
        get_historical_dashboard_data,
        get_loto_gan_stats,
        get_loto_stats_last_n_days,
        get_prediction_consensus,
        get_top_memory_bridge_predictions,
        get_top_scored_pairs,
        # [FIXED] Thêm import để phục vụ AppController
        prepare_daily_features,
        calculate_score_from_features
    )

    print(">>> (V7.3) Loaded logic.dashboard_analytics successfully.")
except ImportError as e_dashboard:
    print(
        f"CRITICAL ERROR: Could not import logic.dashboard_analytics: {e_dashboard}"
    )


# 7. LOGIC AI (HUẤN LUYỆN, DỰ ĐOÁN, ĐA LUỒNG)
try:
    # (SỬA) Import các hàm AI đã được tách biệt
    from logic.ai_feature_extractor import (
        run_ai_prediction_for_dashboard,
        run_ai_training_threaded,
    )

    print(">>> (V7.3) Loaded logic.ai_feature_extractor (AI Wrappers) successfully.")
except ImportError as e_ai:
    error_msg = str(e_ai)
    print(f"CRITICAL ERROR: Could not import logic.ai_feature_extractor (AI): {error_msg}")

    # Giả lập hàm nếu lỗi
    def run_ai_training_threaded(callback=None):
        return False, "Lỗi: Không tìm thấy module ai_feature_extractor"

    def run_ai_prediction_for_dashboard():
        return None, "Lỗi: Không tìm thấy module ai_feature_extractor"


# Thêm __all__ để đánh dấu các hàm này là 'được sử dụng' (để export)
__all__ = [
    # DB & Repo (13)
    "get_all_managed_bridges",
    "load_data_ai_from_db",
    "DB_NAME",
    "add_managed_bridge",  # Service adapter (V11.4)
    "delete_managed_bridge",
    "delete_managed_bridges_batch",
    "get_all_kys_from_db",
    "get_results_by_ky",
    "setup_database",
    "update_bridge_k2n_cache_batch",
    "update_bridge_win_rate_batch",
    "update_managed_bridge",
    "upsert_managed_bridge",
    # Parsing (4)
    "parse_and_APPEND_data",
    "parse_and_APPEND_data_TEXT",
    "parse_and_insert_data",
    "run_and_update_from_text",
    # Bridges Classic (3)
    "ALL_15_BRIDGE_FUNCTIONS_V5",
    "calculate_loto_stats",
    "getAllLoto_V30",
    # Backtester (10)
    "BACKTEST_15_CAU_K2N_V30_AI_V8",
    "BACKTEST_15_CAU_N1_V31_AI_V8",
    "BACKTEST_CUSTOM_CAU_V16",
    "BACKTEST_MANAGED_BRIDGES_K2N",
    "BACKTEST_MANAGED_BRIDGES_N1",
    "BACKTEST_MEMORY_BRIDGES",
    "TONGHOP_TOP_CAU_N1_V5",
    "TONGHOP_TOP_CAU_RATE_V5",
    "run_and_update_all_bridge_K2N_cache",
    "run_and_update_all_bridge_rates",
    # Bridge Manager (5)
    "TIM_CAU_BAC_NHO_TOT_NHAT",
    "TIM_CAU_TOT_NHAT_V16",
    "auto_manage_bridges",
    "find_and_auto_manage_bridges",
    "prune_bad_bridges",
    "find_and_auto_manage_bridges_de",  # Thêm hàm của Đề
    # Dashboard (7)
    "get_high_win_rate_predictions",
    "get_historical_dashboard_data",
    "get_loto_gan_stats",
    "get_loto_stats_last_n_days",
    "get_prediction_consensus",
    "get_top_memory_bridge_predictions",
    "get_top_scored_pairs",
    # AI (2)
    "run_ai_prediction_for_dashboard",
    "run_ai_training_threaded",
    # Hàm Wrapper (1)
    "get_all_managed_bridges_wrapper",
    # Optimizer functions
    "prepare_daily_features",
    "calculate_score_from_features",
    # Service Layer Adapter (V11.4)
    "db_upsert_managed_bridge",  # Alias for backward compatibility
]


# ==========================================================================
# CÁC HÀM HỖ TRỢ CŨ (Đảm bảo chữ ký/logic đúng)
# ==========================================================================


# Wrapper cho get_all_managed_bridges để tương thích
def get_all_managed_bridges_wrapper(db_name=DB_NAME, only_enabled=False):
    """
    Wrapper (Giữ lại hàm này cho tương thích)
    """
    # Gọi hàm mới từ data_repository.py đã được import
    return get_all_managed_bridges(db_name, only_enabled)


# ==========================================================================
# SERVICE LAYER ADAPTER (V11.4 - Fix "Bridge name is required" error)
# ==========================================================================

def add_managed_bridge(
    bridge_name: str = None,
    description: str = None,
    bridge_type: str = None,
    win_rate_text: str = None,
    db_name: str = DB_NAME,
    **kwargs
) -> tuple:
    """
    Service-layer adapter for adding managed bridges with data normalization.
    
    This function sits between the UI and DB layers, ensuring proper data
    normalization before calling the database layer. It preserves backward
    compatibility by attempting kwargs first, then falling back to positional
    arguments.
    
    Args:
        bridge_name: Name of the bridge (required)
        description: Human-readable description
        bridge_type: Bridge type constant from logic.constants.BRIDGE_TYPES
        win_rate_text: Win rate as formatted string (e.g., "45.2%")
        db_name: Database path
        **kwargs: Additional bridge attributes (pos1_idx, pos2_idx, etc.)
    
    Returns:
        Tuple[bool, str]: (success, message)
        
    Example:
        >>> success, msg = add_managed_bridge(
        ...     bridge_name="DE_SET_01",
        ...     description="Test Bridge",
        ...     bridge_type="DE_SET",
        ...     win_rate_text="85.0%"
        ... )
    
    Notes:
        - Normalizes bridge name (strips whitespace, handles None)
        - Maps display types to DB types (e.g., "LÔ_V17" -> "LO_POS")
        - Falls back to positional upsert_managed_bridge signature if needed
        - Logs all operations for debugging
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Import constants for type mapping
    try:
        from logic.constants import BRIDGE_TYPES
    except ImportError:
        logger.warning("Could not import BRIDGE_TYPES from constants, using defaults")
        # Define minimal type mapping as fallback
        BRIDGE_TYPES = {
            "LO_V17": "LO_POS",
            "LO_BN": "LO_MEM",
            "LO_POS": "LO_POS",
            "LO_MEM": "LO_MEM",
            "LO_STL_FIXED": "LO_STL_FIXED",
            "DE_SET": "DE_SET",
            "DE_MEMORY": "DE_MEMORY",
            "DE_PASCAL": "DE_PASCAL",
            "DE_KILLER": "DE_KILLER",
            "DE_DYNAMIC_K": "DE_DYNAMIC_K",
            "DE_POS_SUM": "DE_POS_SUM",
            "DE_ALGO": "DE_ALGO",
        }
    
    # Normalize bridge name
    if not bridge_name or not str(bridge_name).strip():
        error_msg = "Bridge name is required and cannot be empty"
        logger.error(f"add_managed_bridge failed: {error_msg}")
        return False, error_msg
    
    normalized_name = str(bridge_name).strip()
    
    # Normalize description
    normalized_desc = str(description).strip() if description else ""
    
    # Normalize bridge type (map display types to DB types)
    if bridge_type:
        # Try to map display type to DB type
        normalized_type = BRIDGE_TYPES.get(bridge_type, bridge_type)
    else:
        normalized_type = "UNKNOWN"
    
    # Normalize win_rate_text
    normalized_win_rate = str(win_rate_text) if win_rate_text else "N/A"
    
    # Build bridge_data dict with all normalized values
    bridge_data = kwargs.copy() if kwargs else {}
    bridge_data.update({
        "name": normalized_name,
        "description": normalized_desc,
        "type": normalized_type,
        "win_rate_text": normalized_win_rate,
        "is_enabled": bridge_data.get("is_enabled", 1),
        "search_rate_text": bridge_data.get("search_rate_text", normalized_win_rate),
    })
    
    # Extract pos indices if provided
    pos1_idx = bridge_data.pop("pos1_idx", kwargs.get("pos1_idx"))
    pos2_idx = bridge_data.pop("pos2_idx", kwargs.get("pos2_idx"))
    
    logger.info(
        f"add_managed_bridge: name={normalized_name}, "
        f"type={normalized_type}, win_rate={normalized_win_rate}"
    )
    
    # Call upsert_managed_bridge with compatibility layer
    try:
        # Try with kwargs first (new signature)
        success, msg = upsert_managed_bridge(
            bridge_name=normalized_name,
            description=normalized_desc,
            win_rate=normalized_win_rate,
            db_name=db_name,
            pos1_idx=pos1_idx,
            pos2_idx=pos2_idx,
            bridge_data=bridge_data
        )
        logger.info(f"add_managed_bridge result: success={success}, msg={msg}")
        return success, msg
    except Exception as e:
        # Fallback to positional args if kwargs fail
        logger.warning(f"Kwargs approach failed, trying positional: {e}")
        try:
            success, msg = upsert_managed_bridge(
                normalized_name,
                normalized_desc,
                normalized_win_rate,
                db_name,
                pos1_idx,
                pos2_idx,
                bridge_data
            )
            logger.info(f"add_managed_bridge (fallback) result: success={success}, msg={msg}")
            return success, msg
        except Exception as e2:
            error_msg = f"Failed to add bridge: {str(e2)}"
            logger.error(f"add_managed_bridge failed completely: {error_msg}")
            return False, error_msg


# Keep db_upsert_managed_bridge as alias for compatibility
db_upsert_managed_bridge = upsert_managed_bridge


print("Lottery Service API (lottery_service.py) - Loaded successfully (V7.4).")