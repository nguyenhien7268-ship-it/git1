# Tên file: git3/lottery_service.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA F821)
#
"""
==================================================================================
LOTTERY SERVICE API (BỘ ĐIỀU PHỐI) - (V7.3 - TÁCH LOGIC AI FEATURE)
==================================================================================
File này đóng vai trò là API trung tâm, import và phân phối logic từ
các file con trong thư mục /logic.
"""
import logging
import re
from typing import Tuple, Optional
# 1. LOGIC DB & REPO
try:
    from logic.data_repository import get_all_managed_bridges, load_data_ai_from_db
    from logic.db_manager import (
        DB_NAME,
        add_managed_bridge,
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

    print(">>> (V7.3) Tải logic.db_manager & data_repository thành công.")
except ImportError as e_db:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic DB/Repo: {e_db}")

# Import bridge normalization constants
try:
    from logic.constants import (
        NAME_SANITIZE_REGEX,
        MIN_NAME_LENGTH,
        DEFAULT_WIN_RATE,
        WHITELIST_DISPLAY_TYPES,
    )
    print(">>> (V7.3) Tải logic.constants (bridge normalization) thành công.")
except ImportError as e_const:
    print(f"LỖI: Không thể import logic.constants: {e_const}")
    # Provide fallback values
    NAME_SANITIZE_REGEX = re.compile(r"[^\w\-\s\u00C0-\u024F\u1E00-\u1EFF]+", flags=re.UNICODE)
    MIN_NAME_LENGTH = 1
    DEFAULT_WIN_RATE = "50"
    WHITELIST_DISPLAY_TYPES = ()

# 2. LOGIC PARSING (XỬ LÝ DỮ LIỆU)
try:
    from logic.data_parser import (
        parse_and_APPEND_data,
        parse_and_APPEND_data_TEXT,
        parse_and_insert_data,
        run_and_update_from_text,
    )

    print(">>> (V7.3) Tải logic.data_parser thành công.")
except ImportError as e_parser:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.data_parser: {e_parser}")

# 3. LOGIC CẦU CỔ ĐIỂN & TIỆN ÍCH
try:
    from logic.bridges.bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5,
        calculate_loto_stats,
        getAllLoto_V30,
    )

    print(">>> (V7.3) Tải logic.bridges.bridges_classic thành công.")
except ImportError as e_classic:
    print(
        f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridges.bridges_classic: {e_classic}"
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

    print(">>> (V7.3) Tải logic.backtester thành công.")
except ImportError as e_backtester:
    print(f"LỖĨ NGHIÊM TRỌNG: Không thể import logic.backtester: {e_backtester}")

# 5. LOGIC QUẢN LÝ CẦU (DÒ, LỌC)
try:
    from logic.bridges.bridge_manager_core import (
        TIM_CAU_BAC_NHO_TOT_NHAT,
        TIM_CAU_TOT_NHAT_V16,
        auto_manage_bridges,
        find_and_auto_manage_bridges,
        prune_bad_bridges,
    )

    print(">>> (V7.3) Tải logic.bridges.bridge_manager_core thành công.")
except ImportError as e_bridge_core:
    print(
        f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridges.bridge_manager_core: {e_bridge_core}"
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
    )

    print(">>> (V7.3) Tải logic.dashboard_analytics thành công.")
except ImportError as e_dashboard:
    print(
        f"LỖI NGHIÊM TRỌNG: Không thể import logic.dashboard_analytics: {e_dashboard}"
    )


# 7. LOGIC AI (HUẤN LUYỆN, DỰ ĐOÁN, ĐA LUỒNG)
try:
    # (SỬA) Import các hàm AI đã được tách biệt
    from logic.ai_feature_extractor import (
        run_ai_prediction_for_dashboard,
        run_ai_training_threaded,
    )

    print(">>> (V7.3) Tải logic.ai_feature_extractor (AI Wrappers) thành công.")
except ImportError as e_ai:
    error_msg = str(e_ai)
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.ai_feature_extractor (AI): {error_msg}")

    # Giả lập hàm nếu lỗi
    def run_ai_training_threaded(callback=None):
        return False, "Lỗi: Không tìm thấy module ai_feature_extractor"

    def run_ai_prediction_for_dashboard():
        return None, "Lỗi: Không tìm thấy module ai_feature_extractor"


# Thêm __all__ để đánh dấu các hàm này là 'được sử dụng' (để export)
__all__ = [
    # DB & Repo (11)
    "get_all_managed_bridges",
    "load_data_ai_from_db",
    "DB_NAME",
    "add_managed_bridge",
    "delete_managed_bridge",
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
    # Hàm Wrapper (2)
    "get_all_managed_bridges_wrapper",
    "add_managed_bridge_adapter",
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
# ADAPTER: add_managed_bridge with normalization
# ==========================================================================
def add_managed_bridge_adapter(
    bridge_name: str,
    description: str = "",
    bridge_type: Optional[str] = None,
    win_rate: Optional[str] = None,
    db_name: str = DB_NAME,
    **kwargs
) -> Tuple[bool, str]:
    """
    Service-layer adapter for adding a managed bridge with normalization.
    
    This function acts as a bridge between UI/high-level code and the database layer,
    performing validation, normalization, and defaulting before calling the DB function.
    
    Args:
        bridge_name: The name of the bridge to add (will be normalized)
        description: Optional description for the bridge
        bridge_type: Optional bridge type (e.g., 'manual_lo', 'algo_de')
        win_rate: Optional win rate as text (defaults to DEFAULT_WIN_RATE)
        db_name: Database name (defaults to DB_NAME)
        **kwargs: Additional keyword arguments for future compatibility
    
    Returns:
        Tuple[bool, str]: (success, message) indicating operation result
    
    Raises:
        None - all errors are caught and returned as (False, error_message)
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Step 1: Normalize bridge name
        if not bridge_name or not isinstance(bridge_name, str):
            logger.warning(f"Invalid bridge_name type or empty: {bridge_name}")
            return False, "Bridge name is required"
        
        # Strip whitespace
        normalized_name = bridge_name.strip()
        
        # Apply sanitization regex
        try:
            normalized_name = NAME_SANITIZE_REGEX.sub(" ", normalized_name)
            # Collapse multiple spaces
            normalized_name = re.sub(r"\s+", " ", normalized_name).strip()
        except Exception as e:
            logger.error(f"Error sanitizing bridge name: {e}")
            return False, f"Error sanitizing bridge name: {e}"
        
        # Check minimum length
        if len(normalized_name) < MIN_NAME_LENGTH:
            logger.warning(f"Bridge name too short after normalization: '{normalized_name}'")
            return False, "Bridge name is required (too short after normalization)"
        
        # Step 2: Normalize bridge_type if provided
        if bridge_type:
            bridge_type_lower = bridge_type.lower().strip()
            # Map display types to canonical types
            type_mapping = dict(WHITELIST_DISPLAY_TYPES)
            bridge_type = type_mapping.get(bridge_type_lower, bridge_type)
        
        # Step 3: Default win_rate if not provided
        if win_rate is None or win_rate == "":
            win_rate = DEFAULT_WIN_RATE
            logger.debug(f"Using default win_rate: {win_rate}")
        
        # Step 4: Normalize description
        if description is None:
            description = ""
        description = str(description).strip()
        
        # Step 5: Attempt to call underlying DB function with kwargs first (new signature)
        logger.info(f"Adding managed bridge: '{normalized_name}' with type={bridge_type}, win_rate={win_rate}")
        
        try:
            # Try new signature with kwargs
            result = add_managed_bridge(
                bridge_name=normalized_name,
                description=description,
                db_name=db_name,
                **kwargs
            )
            return result
        except TypeError as e:
            # Fallback to positional arguments (old signature)
            logger.debug(f"Falling back to positional args for add_managed_bridge: {e}")
            result = add_managed_bridge(normalized_name, description, db_name)
            return result
            
    except Exception as e:
        logger.error(f"Unexpected error in add_managed_bridge_adapter: {e}", exc_info=True)
        return False, f"Error adding bridge: {e}"


# Alias for backward compatibility
db_upsert_managed_bridge = upsert_managed_bridge


print("Lottery Service API (lottery_service.py) đã tải thành công (V7.3).")
