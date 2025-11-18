"""
backtester.py - Main backtesting interface (REFACTORED)

This module has been refactored from 1,303 LOC to ~200 LOC by extracting
functions into specialized modules:
- backtester_helpers.py: Validation and parsing utilities
- backtester_scoring.py: Scoring algorithms
- backtester_aggregation.py: Top bridge aggregation

The large backtest functions are kept in backtester_core.py for stability.
This file provides backward-compatible API by re-exporting all functions.
"""

# Import configuration
try:
    from .config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    except ImportError:
        print("LỖI: backtester.py không thể import config_manager.")
        try:
            from .constants import DEFAULT_SETTINGS
        except ImportError:
            from constants import DEFAULT_SETTINGS
        SETTINGS = type("obj", (object,), DEFAULT_SETTINGS)

# Import database functions
try:
    from .data_repository import get_all_managed_bridges
    from .db_manager import (
        DB_NAME,
        update_bridge_k2n_cache_batch,
        update_bridge_win_rate_batch,
    )
except ImportError:
    print("Lỗi: Không thể import db_manager trong backtester.py")
    DB_NAME = "data/xo_so_prizes_all_logic.db"
    
    def get_all_managed_bridges(d, o):
        return []
    
    def update_bridge_win_rate_batch(r, d):
        return False, "Lỗi Import"
    
    def update_bridge_k2n_cache_batch(r, d):
        return False, "Lỗi Import"

# Import bridge functions
try:
    from .bridges.bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5,
        checkHitSet_V30_K2N,
        getAllLoto_V30,
    )
except ImportError:
    print("Lỗi: Không thể import bridges_classic trong backtester.py")
    ALL_15_BRIDGE_FUNCTIONS_V5 = []
    
    def getAllLoto_V30(r):
        return []
    
    def checkHitSet_V30_K2N(p, loto_set):
        return "Lỗi"

try:
    from .bridges.bridges_v16 import (
        get_index_from_name_V16,
        getAllPositions_V17_Shadow,
        getPositionName_V16,
        getPositionName_V17_Shadow,
        taoSTL_V30_Bong,
    )
except ImportError:
    print("Lỗi: Không thể import bridges_v16 trong backtester.py")
    
    def getPositionName_V16(i):
        return "Lỗi"
    
    def get_index_from_name_V16(n):
        return None
    
    def taoSTL_V30_Bong(a, b):
        return ["00", "00"]
    
    def getAllPositions_V17_Shadow(r):
        return []
    
    def getPositionName_V17_Shadow(i):
        return "Lỗi V17"

try:
    from .bridges.bridges_memory import (
        calculate_bridge_stl,
        checkHitBridge_V28,
        getAllBridges_Memory_FAST,
    )
except ImportError:
    print("Lỗi: Không thể import bridges_memory trong backtester.py")
    
    def getAllBridges_Memory_FAST(r):
        return []
    
    def checkHitBridge_V28(b, loto_set):
        return "Lỗi"
    
    def calculate_bridge_stl(b):
        return "Lỗi"

# Import refactored modules
from .backtester_helpers import (
    parse_k2n_results as _parse_k2n_results,
)

from .backtester_aggregation import (
    tonghop_top_cau_n1 as TONGHOP_TOP_CAU_N1_V5,
    tonghop_top_cau_rate as TONGHOP_TOP_CAU_RATE_V5,
    tonghop_top_cau_core as TONGHOP_TOP_CAU_CORE_V5,
)

# Import large backtest functions from core module
# These are kept in a separate module to maintain stability
from .backtester_core import (
    BACKTEST_15_CAU_K2N_V30_AI_V8,
    BACKTEST_15_CAU_N1_V31_AI_V8,
    BACKTEST_CUSTOM_CAU_V16,
    BACKTEST_MANAGED_BRIDGES_N1,
    BACKTEST_MANAGED_BRIDGES_K2N,
    BACKTEST_MEMORY_BRIDGES,
)

# Update functions (kept here as they're relatively small)
def run_and_update_all_bridge_rates(all_data_ai, db_name=DB_NAME):
    """Cập nhật Tỷ lệ (Win Rate) cho Cầu Đã Lưu"""
    try:
        if not all_data_ai:
            return 0, "Không có dữ liệu A:I để chạy backtest."

        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)

        results_n1 = BACKTEST_MANAGED_BRIDGES_N1(
            all_data_ai, ky_bat_dau, ky_ket_thuc, db_name
        )

        if not results_n1 or len(results_n1) < 2 or "LỖI" in str(results_n1[0][0]):
            if not results_n1:
                return 0, "Backtest N1 không trả về kết quả."
            if "Không có cầu nào" in str(results_n1[0][1]):
                return 0, "Không có cầu nào được Bật để cập nhật."
            return 0, f"Lỗi khi chạy Backtest N1: {results_n1[0]}"

        headers = results_n1[0]
        rates = results_n1[1]

        rate_data_list = []
        num_bridges = len(headers) - 1

        if num_bridges == 0:
            return 0, "Không có cầu nào trong kết quả backtest."

        for i in range(1, num_bridges + 1):
            bridge_name = str(headers[i])
            win_rate_text = str(rates[i])
            rate_data_list.append((win_rate_text, bridge_name))

        if not rate_data_list:
            return 0, "Không trích xuất được dữ liệu tỷ lệ."

        success, message = update_bridge_win_rate_batch(rate_data_list, db_name)

        if success:
            return len(rate_data_list), message
        else:
            return 0, message

    except Exception as e:
        return 0, f"Lỗi nghiêm trọng trong run_and_update_all_bridge_rates: {e}"


def run_and_update_all_bridge_K2N_cache(
    all_data_ai, db_name=DB_NAME, data_slice=None, write_to_db=True
):
    """Cập nhật Cache K2N cho Cầu Cổ Điển và Cầu Đã Lưu
    
    Returns:
        tuple: (all_pending_dict, cache_count, message)
            - all_pending_dict: Dictionary of pending K2N predictions
            - cache_count: Number of cache entries written
            - message: Status message
    """
    try:
        if not all_data_ai:
            return {}, 0, "Không có dữ liệu A:I để chạy backtest."

        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)

        # Backtest K2N cổ điển
        results_k2n_classic = BACKTEST_15_CAU_K2N_V30_AI_V8(
            all_data_ai, ky_bat_dau, ky_ket_thuc, history=False
        )

        if not results_k2n_classic or len(results_k2n_classic) < 4:
            return {}, 0, "Backtest K2N cổ điển không trả về kết quả đầy đủ."

        cache_classic, pending_classic = _parse_k2n_results(results_k2n_classic)

        # Backtest K2N managed
        results_k2n_managed = BACKTEST_MANAGED_BRIDGES_K2N(
            all_data_ai, ky_bat_dau, ky_ket_thuc, db_name, data_slice=data_slice
        )

        if not results_k2n_managed or len(results_k2n_managed) < 4:
            cache_managed, pending_managed = [], {}
        else:
            cache_managed, pending_managed = _parse_k2n_results(results_k2n_managed)

        all_cache_data = cache_classic + cache_managed
        all_pending = {**pending_classic, **pending_managed}

        if not all_cache_data:
            return {}, 0, "Không trích xuất được dữ liệu cache K2N."

        if write_to_db:
            success, message = update_bridge_k2n_cache_batch(all_cache_data, db_name)
            if success:
                return all_pending, len(all_cache_data), message
            else:
                return {}, 0, message
        else:
            return all_pending, len(all_cache_data), "Không ghi vào DB (chế độ xem trước)."

    except Exception as e:
        return {}, 0, f"Lỗi nghiêm trọng trong run_and_update_all_bridge_K2N_cache: {e}"


# Export all functions for backward compatibility
__all__ = [
    'SETTINGS',
    'DB_NAME',
    'TONGHOP_TOP_CAU_N1_V5',
    'TONGHOP_TOP_CAU_RATE_V5',
    'TONGHOP_TOP_CAU_CORE_V5',
    'BACKTEST_15_CAU_K2N_V30_AI_V8',
    'BACKTEST_15_CAU_N1_V31_AI_V8',
    'BACKTEST_CUSTOM_CAU_V16',
    'BACKTEST_MANAGED_BRIDGES_N1',
    'BACKTEST_MANAGED_BRIDGES_K2N',
    'BACKTEST_MEMORY_BRIDGES',
    'run_and_update_all_bridge_rates',
    'run_and_update_all_bridge_K2N_cache',
]
