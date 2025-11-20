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
        get_27_loto_names,
        get_27_loto_positions,
    )
except ImportError:
    print("Lỗi: Không thể import bridges_memory trong backtester_core.py")

    def calculate_bridge_stl(loto_str_1, loto_str_2, algorithm_type):
        """Fallback function for calculate_bridge_stl"""
        return ["00", "00"]

    def get_27_loto_names():
        """Fallback function for get_27_loto_names"""
        return []

    def get_27_loto_positions(r):
        """Fallback function for get_27_loto_positions"""
        return []

# Import helper functions
from .backtester_helpers import validate_backtest_params as _validate_backtest_params

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
            # [FIX] Luôn thêm vào data_rows để giữ cấu trúc, bất kể history=True/False
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
                        # [FIX] Luôn tạo string output để phục vụ đếm phong độ bên dưới
                        cell_output = f"{','.join(pred)} ✅ (Ăn N2)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0
                    else:
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
                        cell_output = f"{','.join(pred)} ✅ (Ăn N1)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0
                    else:
                        cell_output = f"{','.join(pred)} (Trượt N1...)"
                        in_frame[j], prediction_in_frame[j] = True, pred

                # [FIX] Luôn append kết quả chi tiết vào dòng
                daily_results_row.append(cell_output)
                if "✅" in check_result:
                    totalHits += 1

            # [FIX] Luôn thêm dòng vào data_rows (BỎ ĐIỀU KIỆN if history)
            daily_results_row.append(totalHits)
            data_rows.append(daily_results_row)

        except Exception as e:
            # [FIX] Luôn append lỗi
            data_rows.append([actualSoKy, f"Lỗi: {e}"] + [""] * 15)

    # [FIX] Luôn đảo ngược danh sách để tính 10 kỳ gần nhất chính xác
    data_rows.reverse()

    # Always insert rate, streak, and recent_form rows for consistent structure
    rate_row, total_wins = ["Tỷ Lệ %"], 0
    if totalTestDays > 0:
        for count in win_counts:
            rate = (count / totalTestDays) * 100
            rate_row.append(f"{rate:.2f}%")
            total_wins += count
        rate_row.append(f"TB: {(total_wins / totalTestDays):.2f}")
    else:
        for _ in range(15):
            rate_row.append("0.00%")
        rate_row.append("TB: 0.00")
    results.insert(1, rate_row)

    streak_row = ["Chuỗi Thắng / Thua Max"]
    for i in range(15):
        streak_row.append(
            f"{current_streak_k2n[i]} thắng / {max_lose_streak_k2n[i]} thua"
        )
    streak_row.append("---")
    results.insert(2, streak_row)

    # Calculate recent win count (last 10 periods)
    recent_win_row = ["Phong Độ 10 Kỳ"]
    for i in range(15):
        # Count wins in last 10 data rows (most recent periods)
        recent_wins = 0
        periods_to_check = min(10, len(data_rows))
        for row_idx in range(periods_to_check):
            if row_idx < len(data_rows):
                row = data_rows[row_idx]
                if i + 1 < len(row):
                    cell_value = str(row[i + 1])
                    if "✅" in cell_value:
                        recent_wins += 1
        recent_win_row.append(f"{recent_wins}/10")
    recent_win_row.append("---")
    results.insert(3, recent_win_row)

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

    results.insert(4, finalRow)

    if history:
        results.extend(data_rows)

    return results


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


def BACKTEST_CUSTOM_CAU_V16(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, custom_bridge_name, mode
):
    """Backtest một cầu tùy chỉnh N1/K2N (V17 Shadow)"""
    # ... (giữ nguyên logic backtest cầu tùy chỉnh) ...
    try:
        parts = custom_bridge_name.split("+")
        name1, name2 = parts[0].strip(), parts[1].strip()

        idx1, idx2 = get_index_from_name_V16(name1), get_index_from_name_V16(name2)

        if idx1 is None or idx2 is None:
            return [["LỖI:", f"Không thể dịch tên cầu '{custom_bridge_name}'."]]

        allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
            toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
        )
        if error:
            return error

        results = [["Kỳ (Cột A)", "Kết Quả"]]
        in_frame, prediction_in_frame = False, None
        totalTestDays, win_count = 0, 0

        data_rows = []

        for k in range(startCheckRow, finalEndRow + 1):
            prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
            if actualRow_idx >= len(allData) or prevRow_idx < 0:
                continue
            prevRow_data, actualRow = allData[prevRow_idx], allData[actualRow_idx]
            if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "":
                break
            if (
                not prevRow_data
                or len(actualRow) < 10
                or not actualRow[2]
                or not actualRow[9]
            ):
                data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"])
                continue

            actualSoKy, actualLotoSet = actualRow[0] or k, set(
                getAllLoto_V30(actualRow)
            )

            prevPositions = getAllPositions_V17_Shadow(prevRow_data)

            a, b = prevPositions[idx1], prevPositions[idx2]
            if a is None or b is None:
                data_rows.append([actualSoKy, "Lỗi (vị trí rỗng)"])
                continue

            totalTestDays += 1
            pred = taoSTL_V30_Bong(a, b)
            check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
            cell_output = ""

            if mode == "N1":
                cell_output = f"{','.join(pred)} {check_result}"
                if "✅" in check_result:
                    win_count += 1
            elif mode == "K2N":
                if in_frame:
                    check_result = checkHitSet_V30_K2N(
                        prediction_in_frame, actualLotoSet
                    )
                    if "✅" in check_result:
                        cell_output, win_count = (
                            f"{','.join(prediction_in_frame)} ✅ (Ăn N2)",
                            win_count + 1,
                        )
                    else:
                        cell_output = f"{','.join(prediction_in_frame)} ❌ (Trượt K2N)"
                    in_frame, prediction_in_frame = False, None
                else:
                    if "✅" in check_result:
                        cell_output, win_count = (
                            f"{','.join(pred)} ✅ (Ăn N1)",
                            win_count + 1,
                        )
                    else:
                        cell_output, in_frame, prediction_in_frame = (
                            f"{','.join(pred)} (Trượt N1...)",
                            True,
                            pred,
                        )
            data_rows.append([actualSoKy, cell_output])

        data_rows.reverse()
        results.extend(data_rows)

        if totalTestDays > 0:
            rate = (win_count / totalTestDays) * 100
            results.insert(1, ["Tỷ Lệ %", f"{rate:.2f}% ({win_count}/{totalTestDays})"])

        if mode == "K2N":
            # Xử lý 'int' object has no attribute 'isdigit'
            # (Lỗi 3)
            try:
                ky_int = int(allData[finalEndRow - offset][0])
                finalRowK = f"Kỳ {ky_int + 1}"
            except (ValueError, TypeError):
                finalRowK = f"Kỳ {allData[finalEndRow - offset][0]} (Next)"
            # (Kết thúc sửa lỗi)

            final_cell = "---"
            if in_frame:
                final_cell = f"{','.join(prediction_in_frame)} (Đang chờ N2)"
            results.insert(2, [finalRowK, final_cell])

        return results
    except Exception as e:
        print(f"Lỗi BACKTEST_CUSTOM_CAU_V16: {e}")
        return [["LỖI:", str(e)]]


# XÓA: BACKTEST_MANAGED_BRIDGES_N1 (Đã giữ lại hàm dưới)
# XÓA: BACKTEST_MANAGED_BRIDGES_K2N (Đã giữ lại hàm dưới)


def BACKTEST_MANAGED_BRIDGES_N1(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME
):
    """Backtest N1 cho Cầu Đã Lưu (V17 Shadow + Bạc Nhớ)"""
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
        prevLotos = get_27_loto_positions(prevRow)
        daily_results_row = [actualSoKy]

        for bridge in bridges_to_test:
            try:
                idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                
                # Check if this is a Memory Bridge (Cầu Bạc Nhớ)
                if idx1 == -1 and idx2 == -1:
                    # Parse bridge name to extract positions and algorithm
                    bridge_name = bridge["name"]
                    try:
                        import re
                        if "Tổng(" in bridge_name:
                            # Format: "Tổng(00+01)" or "Tổng(0+1)"
                            match = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                            if match:
                                pos1, pos2 = int(match.group(1)), int(match.group(2))
                                loto1, loto2 = prevLotos[pos1], prevLotos[pos2]
                                pred = calculate_bridge_stl(loto1, loto2, "sum")
                            else:
                                daily_results_row.append("Lỗi Parse Tổng")
                                continue
                        elif "Hiệu(" in bridge_name:
                            # Format: "Hiệu(00-01)" or "Hiệu(0-1)"
                            match = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                            if match:
                                pos1, pos2 = int(match.group(1)), int(match.group(2))
                                loto1, loto2 = prevLotos[pos1], prevLotos[pos2]
                                pred = calculate_bridge_stl(loto1, loto2, "diff")
                            else:
                                daily_results_row.append("Lỗi Parse Hiệu")
                                continue
                        else:
                            daily_results_row.append("Lỗi Format BN")
                            continue
                    except Exception as e_parse:
                        daily_results_row.append(f"Lỗi Parse: {e_parse}")
                        continue
                else:
                    # V17 Bridge (original logic)
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
        last_lotos = get_27_loto_positions(last_data_row)

        for bridge in bridges_to_test:
            idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
            
            # Check if this is a Memory Bridge
            if idx1 == -1 and idx2 == -1:
                bridge_name = bridge["name"]
                try:
                    import re
                    if "Tổng(" in bridge_name:
                        match = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                        if match:
                            pos1, pos2 = int(match.group(1)), int(match.group(2))
                            loto1, loto2 = last_lotos[pos1], last_lotos[pos2]
                            pred = calculate_bridge_stl(loto1, loto2, "sum")
                        else:
                            finalRow.append("Lỗi Parse")
                            continue
                    elif "Hiệu(" in bridge_name:
                        match = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                        if match:
                            pos1, pos2 = int(match.group(1)), int(match.group(2))
                            loto1, loto2 = last_lotos[pos1], last_lotos[pos2]
                            pred = calculate_bridge_stl(loto1, loto2, "diff")
                        else:
                            finalRow.append("Lỗi Parse")
                            continue
                    else:
                        finalRow.append("Lỗi Format")
                        continue
                except Exception:
                    finalRow.append("Lỗi")
                    continue
            else:
                # V17 Bridge
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


def BACKTEST_MANAGED_BRIDGES_K2N(
    toan_bo_A_I,
    ky_bat_dau_kiem_tra,
    ky_ket_thuc_kiem_tra,
    db_name=DB_NAME,
    history=True,
):
    """Backtest K2N cho Cầu Đã Lưu (V17 Shadow + Bạc Nhớ)"""
    try:
        # (V7.1) Dùng get_all_managed_bridges từ Repository
        bridges_to_test = get_all_managed_bridges(db_name, only_enabled=True)
    except Exception as e:
        # Return valid 5-row structure even on error
        return [
            ["Kỳ (Cột A)"],
            ["Tỷ Lệ %"],
            ["Chuỗi Thắng / Thua Max"],
            ["Phong Độ 10 Kỳ"],
            ["LỖI:", f"Không thể tải danh sách cầu: {e}"]
        ]
    if not bridges_to_test:
        # Return valid 5-row structure when no bridges enabled
        return [
            ["Kỳ (Cột A)"],
            ["Tỷ Lệ %"],
            ["Chuỗi Thắng / Thua Max"],
            ["Phong Độ 10 Kỳ"],
            ["Thông báo", "Không có cầu nào được Bật trong 'Quản lý Cầu'."]
        ]

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
            # [FIX] Luôn thêm vào data_rows, bất kể history=True/False
            data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"])
            continue

        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
        prevPositions = getAllPositions_V17_Shadow(prevRow)
        prevLotos = get_27_loto_positions(prevRow)
        totalTestDays += 1

        daily_results_row = [actualSoKy]

        for j, bridge in enumerate(bridges_to_test):
            try:
                cell_output = ""
                if in_frame[j]:
                    pred = prediction_in_frame[j]
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        # [FIX] Luôn tạo text cho output
                        cell_output = f"{','.join(pred)} ✅ (Ăn N2)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0
                    else:
                        cell_output = f"{','.join(pred)} ❌ (Trượt K2N)"
                        current_streak_k2n[j] = 0
                        current_lose_streak_k2n[j] += 1
                        if current_lose_streak_k2n[j] > max_lose_streak_k2n[j]:
                            max_lose_streak_k2n[j] = current_lose_streak_k2n[j]

                    in_frame[j], prediction_in_frame[j] = False, None
                else:
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    
                    # Check if this is a Memory Bridge
                    if idx1 == -1 and idx2 == -1:
                        bridge_name = bridge["name"]
                        try:
                            import re
                            if "Tổng(" in bridge_name:
                                match = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                                if match:
                                    pos1, pos2 = int(match.group(1)), int(match.group(2))
                                    loto1, loto2 = prevLotos[pos1], prevLotos[pos2]
                                    pred = calculate_bridge_stl(loto1, loto2, "sum")
                                else:
                                    daily_results_row.append("Lỗi Parse Tổng")
                                    continue
                            elif "Hiệu(" in bridge_name:
                                match = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                                if match:
                                    pos1, pos2 = int(match.group(1)), int(match.group(2))
                                    loto1, loto2 = prevLotos[pos1], prevLotos[pos2]
                                    pred = calculate_bridge_stl(loto1, loto2, "diff")
                                else:
                                    daily_results_row.append("Lỗi Parse Hiệu")
                                    continue
                            else:
                                daily_results_row.append("Lỗi Format BN")
                                continue
                        except Exception as e_parse:
                            daily_results_row.append(f"Lỗi Parse: {e_parse}")
                            continue
                    else:
                        # V17 Bridge (original logic)
                        a, b = prevPositions[idx1], prevPositions[idx2]
                        if a is None or b is None:
                            # [FIX] Luôn append vào daily_results_row
                            daily_results_row.append("Lỗi Vị Trí")
                            continue
                        pred = taoSTL_V30_Bong(a, b)
                    
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)

                    if "✅" in check_result:
                        cell_output = f"{','.join(pred)} ✅ (Ăn N1)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0
                    else:
                        cell_output = f"{','.join(pred)} (Trượt N1...)"
                        in_frame[j], prediction_in_frame[j] = True, pred

                # [FIX] Luôn append cell_output vào daily_results_row
                daily_results_row.append(cell_output)

            except Exception as e:
                # [FIX] Luôn append lỗi
                daily_results_row.append(f"Lỗi: {e}")

        # [FIX] Luôn thêm daily_results_row vào data_rows (BỎ điều kiện if history)
        data_rows.append(daily_results_row)

    # [FIX] Luôn đảo ngược data_rows để phục vụ tính toán 10 kỳ gần nhất
    data_rows.reverse()

    # Always insert rate, streak, and recent_form rows for consistent structure
    rate_row = ["Tỷ Lệ %"]
    if totalTestDays > 0:
        for count in win_counts:
            rate = (count / totalTestDays) * 100
            rate_row.append(f"{rate:.2f}%")
    else:
        for _ in range(num_bridges):
            rate_row.append("0.00%")
    results.insert(1, rate_row)

    streak_row = ["Chuỗi Thắng / Thua Max"]
    for i in range(num_bridges):
        streak_row.append(
            f"{current_streak_k2n[i]} thắng / {max_lose_streak_k2n[i]} thua"
        )
    results.insert(2, streak_row)

    # Calculate recent win count (last 10 periods)
    # [FIX] Vì data_rows giờ đã có dữ liệu (kể cả khi history=False), đoạn này sẽ tính đúng
    recent_win_row = ["Phong Độ 10 Kỳ"]
    for i in range(num_bridges):
        # Count wins in last 10 data rows (most recent periods)
        recent_wins = 0
        periods_to_check = min(10, len(data_rows))
        for row_idx in range(periods_to_check):
            if row_idx < len(data_rows):
                row = data_rows[row_idx]
                if i + 1 < len(row):
                    cell_value = str(row[i + 1])
                    if "✅" in cell_value:
                        recent_wins += 1
        recent_win_row.append(f"{recent_wins}/10")
    results.insert(3, recent_win_row)

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
        last_lotos = get_27_loto_positions(last_data_row)

        for j, bridge in enumerate(bridges_to_test):
            if in_frame[j]:
                finalRow.append(f"{','.join(prediction_in_frame[j])} (Đang chờ N2)")
            else:
                idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                
                # Check if this is a Memory Bridge
                if idx1 == -1 and idx2 == -1:
                    bridge_name = bridge["name"]
                    try:
                        import re
                        if "Tổng(" in bridge_name:
                            match = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                            if match:
                                pos1, pos2 = int(match.group(1)), int(match.group(2))
                                loto1, loto2 = last_lotos[pos1], last_lotos[pos2]
                                pred = calculate_bridge_stl(loto1, loto2, "sum")
                            else:
                                finalRow.append("Lỗi Parse")
                                continue
                        elif "Hiệu(" in bridge_name:
                            match = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                            if match:
                                pos1, pos2 = int(match.group(1)), int(match.group(2))
                                loto1, loto2 = last_lotos[pos1], last_lotos[pos2]
                                pred = calculate_bridge_stl(loto1, loto2, "diff")
                            else:
                                finalRow.append("Lỗi Parse")
                                continue
                        else:
                            finalRow.append("Lỗi Format")
                            continue
                    except Exception:
                        finalRow.append("Lỗi")
                        continue
                else:
                    # V17 Bridge
                    a, b = last_positions[idx1], last_positions[idx2]
                    if a is None or b is None:
                        finalRow.append("Lỗi Vị Trí")
                        continue
                    pred = taoSTL_V30_Bong(a, b)
                
                finalRow.append(f"{','.join(pred)} (Khung mới N1)")

        results.insert(4, finalRow)

        if history:
            results.extend(data_rows)

    except Exception as e:
        print(f"Lỗi dự đoán Cầu Đã Lưu K2N: {e}")
        results.append(["LỖI DỰ ĐOÁN"])

    return results


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
        if (
            not prevRow
            or not actualRow
            or not actualRow[0]
            or str(actualRow[0]).strip() == ""
            or len(actualRow) < 10
            or not actualRow[9]
        ):
            processedData.append({"soKy": actualRow[0] or k, "error": True})
            continue

        processedData.append(
            {
                "soKy": actualRow[0] or k,
                "error": False,
                "prevLotos": get_27_loto_positions(prevRow),
                "actualLotoSet": set(getAllLoto_V30(actualRow)),
            }
        )

    print(f"Tiền xử lý hoàn tất. Bắt đầu backtest {len(processedData)} ngày...")

    data_rows = []
    win_counts = [0] * num_algorithms
    totalTestDays = 0

    for dayData in processedData:
        if dayData["error"]:
            data_rows.append([dayData["soKy"], "Lỗi dữ liệu hàng"] + [""] * num_algorithms)
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


# XÓA: find_and_auto_manage_bridges (Đã chuyển sang bridge_manager_core.py)
# XÓA: prune_bad_bridges (Đã chuyển sang bridge_manager_core.py)

# XÓA: Các hàm analytics (get_loto_stats_last_n_days, get_prediction_consensus, get_high_win_rate_predictions, get_top_scored_pairs, get_loto_gan_stats)
# ĐÃ CHUYỂN SANG dashboard_analytics.py

# XÓA: TIM_CAU_BAC_NHO_TOT_NHAT (Đã chuyển sang bridge_manager_core.py)
# XÓA: get_top_memory_bridge_predictions (Đã chuyển sang dashboard_analytics.py)

# XÓA: get_historical_dashboard_data (Đã chuyển sang dashboard_analytics.py)