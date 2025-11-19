"""
backtest_n1.py - N1 (Ngày 1) mode backtest functions

Contains N1 mode backtest logic extracted from backtester_core.py
"""

# Import required dependencies
try:
    from ..config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    except ImportError:
        try:
            from ..constants import DEFAULT_SETTINGS
        except ImportError:
            from constants import DEFAULT_SETTINGS
        SETTINGS = type("obj", (object,), DEFAULT_SETTINGS)

try:
    from ..db_manager import DB_NAME
except ImportError:
    DB_NAME = "data/xo_so_prizes_all_logic.db"

try:
    from ..data_repository import get_all_managed_bridges
except ImportError:
    def get_all_managed_bridges(d, o):
        return []

try:
    from ..bridges.bridges_classic import (
    ALL_15_BRIDGE_FUNCTIONS_V5,
    getAllLoto_V30,
    checkHitSet_V30_K2N,
)
except ImportError:
    ALL_15_BRIDGE_FUNCTIONS_V5 = []
    
    def getAllLoto_V30(r):
        return []
    
    def checkHitSet_V30_K2N(p, loto_set):
        return "Lỗi"

try:
    from ..bridges.bridges_v16 import (
    getPositionName_V16,
    getAllPositions_V17_Shadow,
    taoSTL_V30_Bong,
)
except ImportError:
    def getPositionName_V16(i):
        return "Lỗi"
    
    def getAllPositions_V17_Shadow(r):
        return []
    
    def taoSTL_V30_Bong(a, b):
        return ["00", "00"]

from ..backtester_helpers import validate_backtest_params as _validate_backtest_params

def BACKTEST_15_CAU_N1_V31_AI_V8(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
):
    """Backtest 15 Cầu Lô N1"""
    # ... (giữ nguyên logic backtest 15 cầu N1) ...
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
        toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
    )
    if error:
        return error
    headers = [
        "Kỳ (Cột A)",
        "Cầu 1 (Đề+5)",
        "Cầu 2 (G6+G7)",
        "Cầu 3 (GĐB+G1)",
        "Cầu 4 (GĐB+G1)",
        "Cầu 5 (G7+G7)",
        "Cầu 6 (G7+G7)",
        "Cầu 7 (G5+G7)",
        "Cầu 8 (G3+G4)",
        "Cầu 9 (GĐB+G1)",
        "Cầu 10 (G2+G3)",
        "Cầu 11 (GĐB+G3)",
        "Cầu 12 (GĐB+G3)",
        "Cầu 13 (G7.3+8)",
        "Cầu 14 (G1+2)",
        "Cầu 15 (Đề+7)",
        "Tổng Trúng",
    ]
    results = [headers]
    cau_functions = ALL_15_BRIDGE_FUNCTIONS_V5

    data_rows = []

    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "":
            break
        if not prevRow or len(actualRow) < 10 or not actualRow[2] or not actualRow[9]:
            data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"] + [""] * 15)
            continue
        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
        daily_results_row, totalHits = [actualSoKy], 0
        try:
            for j in range(15):
                pred = cau_functions[j](prevRow)
                check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                cell_output = f"{','.join(pred)} {check_result}"
                if "✅" in check_result:
                    totalHits += 1
                daily_results_row.append(cell_output)
            daily_results_row.append(totalHits)
            data_rows.append(daily_results_row)
        except Exception as e:
            data_rows.append([actualSoKy, f"Lỗi: {e}"] + [""] * 15)

    data_rows.reverse()

    totalTestDays = len(data_rows)
    if totalTestDays > 0:
        win_counts = [0] * 15
        for row in data_rows:
            for j in range(15):
                if "✅" in str(row[j + 1]):
                    win_counts[j] += 1
        rate_row, total_wins = ["Tỷ Lệ %"], 0
        for count in win_counts:
            rate = (count / totalTestDays) * 100
            rate_row.append(f"{rate:.2f}%")
            total_wins += count
        rate_row.append(f"TB: {(total_wins / totalTestDays):.2f}")
        results.insert(1, rate_row)

    try:
        last_data_row_for_prediction = allData[finalEndRow - offset]
    except IndexError:
        results.append(["LỖI DỰ ĐOÁN", "Không có dữ liệu hàng cuối."])
        return results

    # Xử lý 'int' object has no attribute 'isdigit'
    # (Lỗi 2)
    try:
        ky_int = int(last_data_row_for_prediction[0])
        finalRowK = f"Kỳ {ky_int + 1}"
    except (ValueError, TypeError):
        finalRowK = f"Kỳ {last_data_row_for_prediction[0]} (Next)"
    # (Kết thúc sửa lỗi)

    finalRow = [finalRowK]
    for j in range(15):
        try:
            pred = cau_functions[j](last_data_row_for_prediction)
            finalRow.append(f"{','.join(pred)} (Dự đoán N1)")
        except Exception:
            finalRow.append("LỖI PREDICT")
    finalRow.append("---")

    results.insert(2, finalRow)
    results.extend(data_rows)

    return results


# XÓA: TIM_CAU_TOT_NHAT_V16 (Đã chuyển sang bridge_manager_core.py)



def BACKTEST_MANAGED_BRIDGES_N1(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME
):
    """Backtest N1 cho Cầu Đã Lưu (V17 Shadow)"""
    try:
        # (V7.1) Dùng get_all_managed_bridges từ Repository
        bridges_to_test = get_all_managed_bridges(db_name, only_enabled=True)
    except Exception as e:
        return [["LỖI:", f"Không thể tải danh sách cầu: {e}"]]
    if not bridges_to_test:
        return [["LỖI:", "Không có cầu nào được Bật trong 'Quản lý Cầu'."]]

    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
        toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
    )
    if error:
        return error

    headers = ["Kỳ (Cột A)"]
    for bridge in bridges_to_test:
        headers.append(f"{bridge['name']}")
    results = [headers]

    data_rows = []

    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "":
            break
        if not prevRow or len(actualRow) < 10 or not actualRow[2] or not actualRow[9]:
            data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"])
            continue

        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))

        prevPositions = getAllPositions_V17_Shadow(prevRow)
        daily_results_row = [actualSoKy]

        for bridge in bridges_to_test:
            try:
                idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                a, b = prevPositions[idx1], prevPositions[idx2]
                if a is None or b is None:
                    daily_results_row.append("Lỗi Vị Trí")
                    continue
                pred = taoSTL_V30_Bong(a, b)
                check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                daily_results_row.append(f"{','.join(pred)} {check_result}")
            except Exception as e:
                daily_results_row.append(f"Lỗi: {e}")
        data_rows.append(daily_results_row)

    data_rows.reverse()

    totalTestDays = len(data_rows)
    num_bridges = len(bridges_to_test)
    if totalTestDays > 0:
        win_counts = [0] * num_bridges
        for row in data_rows:
            for j in range(num_bridges):
                if "✅" in str(row[j + 1]):
                    win_counts[j] += 1
        rate_row = ["Tỷ Lệ %"]
        for count in win_counts:
            rate = (count / totalTestDays) * 100
            rate_row.append(f"{rate:.2f}%")
        results.insert(1, rate_row)

    try:
        last_data_row = allData[finalEndRow - offset]

        # Xử lý 'int' object has no attribute 'isdigit'
        # (Lỗi 4)
        try:
            ky_int = int(last_data_row[0])
            finalRowK = f"Kỳ {ky_int + 1}"
        except (ValueError, TypeError):
            finalRowK = f"Kỳ {last_data_row[0]} (Next)"
        # (Kết thúc sửa lỗi)

        finalRow = [finalRowK]

        last_positions = getAllPositions_V17_Shadow(last_data_row)

        for bridge in bridges_to_test:
            idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
            a, b = last_positions[idx1], last_positions[idx2]
            if a is None or b is None:
                finalRow.append("Lỗi Vị Trí")
                continue
            pred = taoSTL_V30_Bong(a, b)
            finalRow.append(f"{','.join(pred)} (Dự đoán N1)")

        results.insert(2, finalRow)
        results.extend(data_rows)

    except Exception as e:
        print(f"Lỗi dự đoán Cầu Đã Lưu: {e}")
        results.append(["LỖI DỰ ĐOÁN"])

    return results
