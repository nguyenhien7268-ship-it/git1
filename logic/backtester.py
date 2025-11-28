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
        get_27_loto_names,
        get_27_loto_positions,
    )
except ImportError:
    print("Lỗi: Không thể import bridges_memory trong backtester.py")
    
    def calculate_bridge_stl(loto_str_1, loto_str_2, algorithm_type):
        """Fallback function for calculate_bridge_stl"""
        return ["00", "00"]
    
    def get_27_loto_names():
        """Fallback function for get_27_loto_names"""
        return []
    
    def get_27_loto_positions(r):
        """Fallback function for get_27_loto_positions"""
        return []

# Import refactored modules (parse_k2n_results moved to backtester_core)
from .backtester_core import parse_k2n_results as _parse_k2n_results

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

        if not results_k2n_classic or len(results_k2n_classic) < 5:
            return {}, 0, "Backtest K2N cổ điển không trả về kết quả đầy đủ."

        cache_classic, pending_classic = _parse_k2n_results(results_k2n_classic)

        # Backtest K2N managed
        results_k2n_managed = BACKTEST_MANAGED_BRIDGES_K2N(
            all_data_ai, ky_bat_dau, ky_ket_thuc, db_name, history=False
        )

        if not results_k2n_managed or len(results_k2n_managed) < 5:
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


def run_backtest_lo_30_days(bridge_config, all_data):
    """
    Chạy backtest 30 ngày gần nhất cho một cầu cụ thể.
    
    Args:
        bridge_config: Dict chứa thông tin cầu từ DB (name, pos1_idx, pos2_idx, ...)
        all_data: Toàn bộ dữ liệu A:I (list các row)
    
    Returns:
        list: List các dict với format:
            [{'date': 'DD/MM/YYYY', 'pred': 'xx-yy', 'result': 'zz', 'is_win': True/False, 'status': 'Ăn/Gãy'}]
    """
    import re
    
    if not all_data or len(all_data) < 2:
        return []
    
    # Lấy 30 ngày gần nhất (hoặc tất cả nếu ít hơn 30)
    data_slice = all_data[-30:] if len(all_data) >= 30 else all_data
    results = []
    
    bridge_name = bridge_config.get("name", "")
    pos1_idx = bridge_config.get("pos1_idx")
    pos2_idx = bridge_config.get("pos2_idx")
    
    # Kiểm tra Memory Bridge (pos1_idx == -1 và pos2_idx == -1)
    is_memory_bridge = (pos1_idx == -1 and pos2_idx == -1)
    
    for i in range(len(data_slice) - 1):
        prev_row = data_slice[i]
        actual_row = data_slice[i + 1]
        
        try:
            # Lấy ngày từ actual_row (row[0] là kỳ)
            date_str = f"Kỳ {actual_row[0]}" if actual_row[0] else f"Ngày {i+1}"
            
            # Tính STL dự đoán
            pred_stl = None
            
            if is_memory_bridge:
                # Memory Bridge: Parse tên và tính STL
                try:
                    prev_lotos = get_27_loto_positions(prev_row)
                    
                    if "Tổng(" in bridge_name:
                        match = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                        if match:
                            pos1, pos2 = int(match.group(1)), int(match.group(2))
                            if pos1 < len(prev_lotos) and pos2 < len(prev_lotos):
                                loto1, loto2 = prev_lotos[pos1], prev_lotos[pos2]
                                pred_stl = calculate_bridge_stl(loto1, loto2, "sum")
                    elif "Hiệu(" in bridge_name:
                        match = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                        if match:
                            pos1, pos2 = int(match.group(1)), int(match.group(2))
                            if pos1 < len(prev_lotos) and pos2 < len(prev_lotos):
                                loto1, loto2 = prev_lotos[pos1], prev_lotos[pos2]
                                pred_stl = calculate_bridge_stl(loto1, loto2, "diff")
                except Exception:
                    pred_stl = None
            else:
                # V17 Bridge: Dùng pos1_idx và pos2_idx
                try:
                    positions = getAllPositions_V17_Shadow(prev_row)
                    if (pos1_idx is not None and pos2_idx is not None and 
                        pos1_idx < len(positions) and pos2_idx < len(positions)):
                        p1 = positions[pos1_idx]
                        p2 = positions[pos2_idx]
                        if p1 is not None and p2 is not None:
                            pred_stl = taoSTL_V30_Bong(int(p1), int(p2))
                except Exception:
                    pred_stl = None
            
            if not pred_stl:
                continue
            
            # Format pred_stl thành string "xx-yy"
            if isinstance(pred_stl, list) and len(pred_stl) >= 2:
                pred_str = f"{pred_stl[0]}-{pred_stl[1]}"
            else:
                pred_str = str(pred_stl)
            
            # Lấy kết quả thực tế
            actual_lotos = set(getAllLoto_V30(actual_row))
            
            # Kiểm tra thắng/thua
            check_result = checkHitSet_V30_K2N(pred_stl, actual_lotos)
            is_win = "✅" in str(check_result) or "Ăn" in str(check_result)
            status = "Ăn" if is_win else "Gãy"
            
            # Lấy số loto xuất hiện (format ngắn gọn)
            if actual_lotos:
                sorted_lotos = sorted(list(actual_lotos))
                if len(sorted_lotos) > 10:
                    result_str = ",".join(sorted_lotos[:10]) + "..."
                else:
                    result_str = ",".join(sorted_lotos)
            else:
                result_str = ""
            
            results.append({
                'date': date_str,
                'pred': pred_str,
                'result': result_str,
                'is_win': is_win,
                'status': status
            })
            
        except Exception:
            # Bỏ qua lỗi và tiếp tục
            continue
    
    return results


def run_backtest_de_30_days(bridge_config, all_data):
    """
    Chạy backtest 30 ngày cho một cầu Đề cụ thể.
    
    Args:
        bridge_config: Dict chứa cấu hình cầu (từ DB)
        all_data: Toàn bộ dữ liệu A:I
    
    Returns:
        list: List các dict với format:
            [{'date': 'DD/MM/YYYY', 'pred': 'Chạm X hoặc Bộ Y', 'result': 'GĐB', 'is_win': True/False, 'status': 'Ăn/Gãy'}]
    """
    from logic.de_backtester_core import DeBacktesterCore
    from logic.de_utils import get_gdb_last_2
    
    if not all_data or len(all_data) < 2:
        return []
    
    # Lấy 30 ngày gần nhất (hoặc tất cả nếu ít hơn 30)
    data_slice = all_data[-30:] if len(all_data) >= 30 else all_data
    results = []
    
    bridge_name = bridge_config.get("name", "")
    
    # Tạo DeBacktesterCore instance
    backtester = DeBacktesterCore(data_slice)
    
    # Chạy backtest với config
    stats = backtester.run_backtest(bridge_config, days_to_test=len(data_slice))
    
    # Kiểm tra lỗi
    if "error" in stats:
        return []
    
    # Format kết quả từ history_log
    history_log = stats.get("history_log", [])
    
    for log_item in history_log:
        try:
            date_str = log_item.get("date", "")
            gdb = log_item.get("gdb", "")
            desc = log_item.get("desc", "")
            is_win = log_item.get("is_win", False)
            
            # Format pred từ desc
            # VD: "(5+3)%2 -> Chạm [0, 2]" -> "Chạm 0,2"
            # VD: "(5) -> Chạm 5, 0" -> "Chạm 5,0"
            pred_str = desc
            if "-> Chạm" in desc:
                # Lấy phần sau "-> Chạm"
                cham_part = desc.split("-> Chạm")[-1].strip()
                # Xử lý nếu là list format [0, 2] hoặc string "5, 0"
                # Loại bỏ dấu ngoặc vuông và khoảng trắng
                cham_part = cham_part.replace("[", "").replace("]", "").replace(" ", "")
                pred_str = f"Chạm {cham_part}"
            elif "-> Bộ" in desc:
                pred_str = "Bộ " + desc.split("-> Bộ")[-1].strip()
            
            status = "Ăn" if is_win else "Gãy"
            
            results.append({
                'date': date_str,
                'pred': pred_str,
                'result': gdb,
                'is_win': is_win,
                'status': status
            })
        except Exception:
            continue
    
    return results


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
    'run_backtest_lo_30_days',
    'run_backtest_de_30_days',
]
