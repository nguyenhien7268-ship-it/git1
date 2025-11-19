"""
backtester_core.py - Core backtesting functions

Extracted from backtester.py (lines 351-1166) to reduce file size.
Contains the 6 main backtest functions that are stable and rarely change.

This module is imported by backtester.py for backward compatibility.
"""

# Import required dependencies
try:
    from .config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    except ImportError:
        try:
            from .constants import DEFAULT_SETTINGS
        except ImportError:
            from constants import DEFAULT_SETTINGS
        SETTINGS = type("obj", (object,), DEFAULT_SETTINGS)

try:
    from .db_manager import DB_NAME
except ImportError:
    DB_NAME = "data/xo_so_prizes_all_logic.db"

try:
    from .data_repository import get_all_managed_bridges
except ImportError:
    def get_all_managed_bridges(d, o):
        return []

try:
    from .bridges.bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5,
        checkHitSet_V30_K2N,
        getAllLoto_V30,
    )
except ImportError:
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
        get_27_loto_names,
        get_27_loto_positions,
    )
except ImportError:
    def getAllBridges_Memory_FAST(r):
        return []

    def checkHitBridge_V28(b, loto_set):
        return "Lỗi"

    def calculate_bridge_stl(b):
        return "Lỗi"

    def get_27_loto_names():
        return []

    def get_27_loto_positions(r):
        return []

# Import helper functions
from .backtester_helpers import validate_backtest_params as _validate_backtest_params

# ... (other backtest functions above omitted for brevity in this file snippet) ...

def BACKTEST_MEMORY_BRIDGES(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    """Backtest cho 756 Cầu Bạc Nhớ (N1)"""
    print("Bắt đầu Backtest 756 Cầu Bạc Nhớ...")

    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
        toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
    )
    if error:
        return error

    loto_names = get_27_loto_names()
    num_positions = len(loto_names)  # = 27

    algorithms = []
    headers = ["Kỳ (Cột A)"]

    for i in range(num_positions):
        for j in range(i, num_positions):
            name_sum = f"Tổng({loto_names[i]} + {loto_names[j]})"
            headers.append(name_sum)
            algorithms.append((i, j, "sum", name_sum))

            name_diff = f"Hiệu(|{loto_names[i]} - {loto_names[j]}|)"
            headers.append(name_diff)
            algorithms.append((i, j, "diff", name_diff))

    num_algorithms = len(algorithms)  # = 756
    results = [headers]

    print(f"Đã tạo {num_algorithms} thuật toán Bạc Nhớ. Bắt đầu tiền xử lý...")

    processedData = []
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]

        # Thay kiểm tra cứng bằng try/except khi lấy loto/vị trí
        if not prevRow or not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "":
            processedData.append({"soKy": actualRow[0] or k, "error": True})
            continue

        try:
            prev_lotos = get_27_loto_positions(prevRow)
            actual_loto_list = getAllLoto_V30(actualRow)
            if not actual_loto_list:
                raise ValueError("Không có loto hợp lệ trong hàng")
            actual_loto_set = set(actual_loto_list)
        except Exception:
            # chỉ mark lỗi nếu không thể parse loto / vị trí
            processedData.append({"soKy": actualRow[0] or k, "error": True})
            continue

        processedData.append(
            {
                "soKy": actualRow[0] or k,
                "error": False,
                "prevLotos": prev_lotos,
                "actualLotoSet": actual_loto_set,
            }
        )

    print(f"Tiền xử lý hoàn tất. Bắt đầu backtest {len(processedData)} ngày...")

    data_rows = []
    win_counts = [0] * num_algorithms
    totalTestDays = 0

    for dayData in processedData:
        if dayData["error"]:
            data_rows.append([dayData["soKy"], "Lỗi dữ liệu hàng"])
            continue

        actualSoKy = dayData["soKy"]
        actualLotoSet = dayData["actualLotoSet"]
        prevLotos = dayData["prevLotos"]
        daily_results_row = [actualSoKy]
        totalTestDays += 1

        for j in range(num_algorithms):
            alg = algorithms[j]
            idx1, idx2, alg_type = alg[0], alg[1], alg[2]

            loto1, loto2 = prevLotos[idx1], prevLotos[idx2]
            pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
            check_result = checkHitSet_V30_K2N(pred_stl, actualLotoSet)

            cell_output = f"{','.join(pred_stl)} {check_result}"
            if "✅" in check_result:
                win_counts[j] += 1

            daily_results_row.append(cell_output)

        data_rows.append(daily_results_row)

    data_rows.reverse()

    if totalTestDays > 0:
        rate_row = ["Tỷ Lệ %"]
        for count in win_counts:
            rate = (count / totalTestDays) * 100
            rate_row.append(f"{rate:.2f}%")
        results.insert(1, rate_row)

    try:
        last_data_row = allData[finalEndRow - offset]

        # Xử lý 'int' object has no attribute 'isdigit'
        # (Lỗi 6)
        try:
            ky_int = int(last_data_row[0])
            finalRowK = f"Kỳ {ky_int + 1}"
        except (ValueError, TypeError):
            finalRowK = f"Kỳ {last_data_row[0]} (Next)"
        # (Kết thúc sửa lỗi)

        finalRow = [finalRowK]
        last_lotos = get_27_loto_positions(last_data_row)

        for j in range(num_algorithms):
            alg = algorithms[j]
            idx1, idx2, alg_type = alg[0], alg[1], alg[2]
            loto1, loto2 = last_lotos[idx1], last_lotos[idx2]
            pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
            finalRow.append(f"{','.join(pred_stl)} (Dự đoán N1)")

        results.insert(2, finalRow)
        results.extend(data_rows)

    except Exception as e:
        print(f"Lỗi dự đoán Cầu Bạc Nhớ: {e}")
        results.append(["LỖI DỰ ĐOÁN"])

    print("Hoàn tất Backtest Cầu Bạc Nhớ.")
    return results

# (phần code còn lại unchanged)
