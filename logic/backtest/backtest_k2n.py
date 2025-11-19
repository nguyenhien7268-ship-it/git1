"""
backtest_k2n.py - K2N (Khung 2 Ngày) mode backtest functions

Contains K2N mode backtest logic extracted from backtester_core.py
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
    from ..bridges.bridges_v16 import (
        getPositionName_V16,
        taoSTL_V30_Bong,
    )
except ImportError:
    def getPositionName_V16(i):
        return "Lỗi"
    
    def taoSTL_V30_Bong(a, b):
        return ["00", "00"]

from ..backtester_helpers import validate_backtest_params as _validate_backtest_params

def BACKTEST_15_CAU_K2N_V30_AI_V8(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, history=True
):
    """Backtest 15 Cầu Cổ Điển K2N"""
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
        toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
    )
    if error:
        return error
    # ... (giữ nguyên logic backtest 15 cầu K2N) ...
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

    in_frame = [False] * 15
    prediction_in_frame = [None] * 15
    current_streak_k2n = [0] * 15

    current_lose_streak_k2n = [0] * 15
    max_lose_streak_k2n = [0] * 15

    cau_functions = ALL_15_BRIDGE_FUNCTIONS_V5

    data_rows = []
    totalTestDays = 0
    win_counts = [0] * 15

    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "":
            break

        if not prevRow or len(actualRow) < 10 or not actualRow[2] or not actualRow[9]:
            if history:
                data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"] + [""] * 15)
            continue

        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
        totalTestDays += 1

        daily_results_row, totalHits = [actualSoKy], 0

        try:
            for j in range(15):
                check_result = ""  # (Sửa V4) Khởi tạo
                cell_output = ""
                if in_frame[j]:
                    pred = prediction_in_frame[j]
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        if history:
                            cell_output = f"{','.join(pred)} ✅ (Ăn N2)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0
                    else:
                        if history:
                            cell_output = f"{','.join(pred)} ❌ (Trượt K2N)"
                        current_streak_k2n[j] = 0
                        current_lose_streak_k2n[j] += 1
                        if current_lose_streak_k2n[j] > max_lose_streak_k2n[j]:
                            max_lose_streak_k2n[j] = current_lose_streak_k2n[j]

                    in_frame[j], prediction_in_frame[j] = False, None
                else:
                    pred = cau_functions[j](prevRow)
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        if history:
                            cell_output = f"{','.join(pred)} ✅ (Ăn N1)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0
                    else:
                        if history:
                            cell_output = f"{','.join(pred)} (Trượt N1...)"
                        in_frame[j], prediction_in_frame[j] = True, pred

                if history:
                    daily_results_row.append(cell_output)
                    if "✅" in check_result:
                        totalHits += 1

            if history:
                daily_results_row.append(totalHits)
                data_rows.append(daily_results_row)

        except Exception as e:
            if history:
                data_rows.append([actualSoKy, f"Lỗi: {e}"] + [""] * 15)

    if history:
        data_rows.reverse()

    if totalTestDays > 0:
        rate_row, total_wins = ["Tỷ Lệ %"], 0
        for count in win_counts:
            rate = (count / totalTestDays) * 100
            rate_row.append(f"{rate:.2f}%")
            total_wins += count
        rate_row.append(f"TB: {(total_wins / totalTestDays):.2f}")
        results.insert(1, rate_row)

        streak_row = ["Chuỗi Thắng / Thua Max"]
        for i in range(15):
            streak_row.append(
                f"{current_streak_k2n[i]} thắng / {max_lose_streak_k2n[i]} thua"
            )
        streak_row.append("---")
        results.insert(2, streak_row)

    try:
        last_data_row_for_prediction = allData[finalEndRow - offset]
    except IndexError:
        results.append(["LỖI DỰ ĐOÁN", "Không có dữ liệu hàng cuối."])
        return results

    # Xử lý 'int' object has no attribute 'isdigit'
    # (Lỗi 1)
    try:
        ky_int = int(last_data_row_for_prediction[0])
        finalRowK = f"Kỳ {ky_int + 1}"
    except (ValueError, TypeError):
        finalRowK = f"Kỳ {last_data_row_for_prediction[0]} (Next)"
    # (Kết thúc sửa lỗi)

    finalRow, openFrames = [finalRowK], 0
    for j in range(15):
        if in_frame[j]:
            finalRow.append(f"{','.join(prediction_in_frame[j])} (Đang chờ N2)")
            openFrames += 1
        else:
            try:
                pred = cau_functions[j](last_data_row_for_prediction)
                finalRow.append(f"{','.join(pred)} (Khung mới N1)")
            except Exception:
                finalRow.append("LỖI PREDICT")
    finalRow.append(f"{openFrames} khung mở" if openFrames > 0 else "0")

    results.insert(3, finalRow)

    if history:
        results.extend(data_rows)

    return results



def BACKTEST_MANAGED_BRIDGES_K2N(
    toan_bo_A_I,
    ky_bat_dau_kiem_tra,
    ky_ket_thuc_kiem_tra,
    db_name=DB_NAME,
    history=True,
):
    """Backtest K2N cho Cầu Đã Lưu (V17 Shadow)"""
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

    num_bridges = len(bridges_to_test)
    headers = ["Kỳ (Cột A)"]
    for bridge in bridges_to_test:
        headers.append(f"{bridge['name']}")

    results = [headers]

    in_frame = [False] * num_bridges
    prediction_in_frame = [None] * num_bridges
    current_streak_k2n = [0] * num_bridges

    current_lose_streak_k2n = [0] * num_bridges
    max_lose_streak_k2n = [0] * num_bridges

    data_rows = []
    totalTestDays = 0
    win_counts = [0] * num_bridges

    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "":
            break

        if not prevRow or len(actualRow) < 10 or not actualRow[2] or not actualRow[9]:
            if history:
                data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"])
            continue

        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
        prevPositions = getAllPositions_V17_Shadow(prevRow)
        totalTestDays += 1

        daily_results_row = [actualSoKy]

        for j, bridge in enumerate(bridges_to_test):
            try:
                cell_output = ""
                if in_frame[j]:
                    pred = prediction_in_frame[j]
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        if history:
                            cell_output = f"{','.join(pred)} ✅ (Ăn N2)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0
                    else:
                        if history:
                            cell_output = f"{','.join(pred)} ❌ (Trượt K2N)"
                        current_streak_k2n[j] = 0
                        current_lose_streak_k2n[j] += 1
                        if current_lose_streak_k2n[j] > max_lose_streak_k2n[j]:
                            max_lose_streak_k2n[j] = current_lose_streak_k2n[j]

                    in_frame[j], prediction_in_frame[j] = False, None
                else:
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    a, b = prevPositions[idx1], prevPositions[idx2]
                    if a is None or b is None:
                        if history:
                            daily_results_row.append("Lỗi Vị Trí")
                        continue

                    pred = taoSTL_V30_Bong(a, b)
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)

                    if "✅" in check_result:
                        if history:
                            cell_output = f"{','.join(pred)} ✅ (Ăn N1)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0
                    else:
                        if history:
                            cell_output = f"{','.join(pred)} (Trượt N1...)"
                        in_frame[j], prediction_in_frame[j] = True, pred

                if history:
                    daily_results_row.append(cell_output)

            except Exception as e:
                if history:
                    daily_results_row.append(f"Lỗi: {e}")

        if history:
            data_rows.append(daily_results_row)

    if history:
        data_rows.reverse()

    if totalTestDays > 0:
        rate_row = ["Tỷ Lệ %"]
        for count in win_counts:
            rate = (count / totalTestDays) * 100
            rate_row.append(f"{rate:.2f}%")
        results.insert(1, rate_row)

        streak_row = ["Chuỗi Thắng / Thua Max"]
        for i in range(num_bridges):
            streak_row.append(
                f"{current_streak_k2n[i]} thắng / {max_lose_streak_k2n[i]} thua"
            )
        results.insert(2, streak_row)

    try:
        last_data_row = allData[finalEndRow - offset]

        # Xử lý 'int' object has no attribute 'isdigit'
        # (Lỗi 5)
        try:
            ky_int = int(last_data_row[0])
            finalRowK = f"Kỳ {ky_int + 1}"
        except (ValueError, TypeError):
            finalRowK = f"Kỳ {last_data_row[0]} (Next)"
        # (Kết thúc sửa lỗi)

        finalRow = [finalRowK]

        last_positions = getAllPositions_V17_Shadow(last_data_row)

        for j, bridge in enumerate(bridges_to_test):
            if in_frame[j]:
                finalRow.append(f"{','.join(prediction_in_frame[j])} (Đang chờ N2)")
            else:
                idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                a, b = last_positions[idx1], last_positions[idx2]
                if a is None or b is None:
                    finalRow.append("Lỗi Vị Trí")
                    continue
                pred = taoSTL_V30_Bong(a, b)
                finalRow.append(f"{','.join(pred)} (Khung mới N1)")

        results.insert(3, finalRow)

        if history:
            results.extend(data_rows)

    except Exception as e:
        print(f"Lỗi dự đoán Cầu Đã Lưu K2N: {e}")
        results.append(["LỖI DỰ ĐOÁN"])

    return results


