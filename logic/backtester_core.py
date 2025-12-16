"""
backtester_core.py - Core backtesting functions
(PHIÊN BẢN V8.10 - FIX N/A ISSUE BY SCANNING ALL BRIDGES)
"""

# ... (Giữ nguyên toàn bộ phần Import và Helper Functions ở trên) ...
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

# Import helper functions from common_utils (refactored)
from .common_utils import validate_backtest_params as _validate_backtest_params

# Import re module for bridge name parsing
import re


# =============================================================================
# HELPER FUNCTIONS (Moved from backtester_helpers.py)
# =============================================================================

def parse_k2n_results(results_data):
    """
    Parse K2N backtest results (Dynamic Row Detection).
    [FIXED] Added robust mapping for LO_STL_FIXED bridges.
    """
    cache_data_list = []
    pending_k2n_dict = {}

    if not results_data or len(results_data) < 2:
        return cache_data_list, pending_k2n_dict

    try:
        # 1. Xác định các hàng dựa trên tiêu đề cột đầu tiên (Cột A)
        headers = results_data[0]

        row_rates = None
        row_streaks = None
        row_recent = None
        row_prediction = None

        for row in results_data[1:]:
            first_col = str(row[0]).strip()
            if "Tỷ Lệ" in first_col:
                row_rates = row
            elif "Chuỗi" in first_col:
                row_streaks = row
            elif "Phong Độ" in first_col:
                row_recent = row
            elif "Kỳ" in first_col or "Next" in first_col:
                row_prediction = row

        # Nếu không tìm thấy, fallback về index cũ (nhưng rủi ro)
        if not row_rates and len(results_data) > 1: row_rates = results_data[1]
        if not row_streaks and len(results_data) > 2: row_streaks = results_data[2]
        if not row_recent and len(results_data) > 3: row_recent = results_data[3]
        if not row_prediction and len(results_data) > 4: row_prediction = results_data[4]

        num_bridges = len(headers) - 1

        for j in range(1, num_bridges + 1):
            original_name = str(headers[j]).split(" (")[0].strip()
            bridge_name = original_name

            # [FIX LO_STL MAPPING] Ánh xạ tên "Cầu X" sang "LO_STL_FIXED_0X"
            if original_name.startswith("Cầu "):
                try:
                    num_part = original_name.replace("Cầu ", "").strip()
                    if num_part.isdigit():
                        bridge_num = int(num_part)
                        if 1 <= bridge_num <= 15:
                            bridge_name = f"LO_STL_FIXED_{bridge_num:02d}"
                except:
                    pass

            # Lấy dữ liệu an toàn
            win_rate_text = str(row_rates[j]) if row_rates and j < len(row_rates) else "0"
            win_streak_text = str(row_streaks[j]) if row_streaks and j < len(row_streaks) else "0"
            recent_form_text = str(row_recent[j]) if row_recent and j < len(row_recent) else "0/10"
            pending_text = str(row_prediction[j]) if row_prediction and j < len(row_prediction) else ""

            # Parse current_streak and max_lose_streak
            current_streak = 0
            max_lose_streak = 0
            if "/" in win_streak_text:
                parts = win_streak_text.split("/")
                try:
                    part0 = parts[0].strip().replace("thắng", "").replace("thua", "").strip()
                    current_streak = int(part0)
                    if len(parts) > 1:
                        part1 = parts[1].strip().replace("thắng", "").replace("thua", "").strip()
                        max_lose_streak = int(part1)
                except (ValueError, IndexError):
                    current_streak = 0
                    max_lose_streak = 0
            else:
                try:
                    cleaned = win_streak_text.strip().replace("thắng", "").replace("thua", "").strip()
                    current_streak = int(cleaned)
                except ValueError:
                    current_streak = 0

            # Parse recent_win_count
            recent_win_count = 0
            try:
                if "/" in recent_form_text:
                    recent_win_count = int(recent_form_text.split("/")[0].strip())
                else:
                    recent_win_count = int(recent_form_text.strip())
            except (ValueError, IndexError):
                recent_win_count = 0

            # Clean STL for Cache
            clean_stl = pending_text.split("(")[0].strip() if "(" in pending_text else pending_text.strip()

            cache_data_list.append((
                win_rate_text,
                current_streak,
                clean_stl if clean_stl else "",
                max_lose_streak,
                recent_win_count,
                bridge_name
            ))

            # Lưu pending với logic mới: Xác định rõ là N1 hay N2
            if pending_text and pending_text.strip() != "":
                is_n2 = "N2" in pending_text or "chờ" in pending_text.lower()

                pending_k2n_dict[bridge_name] = {
                    "stl": clean_stl,
                    "streak": current_streak,
                    "max_lose": max_lose_streak,
                    "is_n2": is_n2
                }

    except Exception as e:
        print(f"Lỗi parse_k2n_results: {e}")

    return cache_data_list, pending_k2n_dict


# =============================================================================
# BACKTEST FUNCTIONS
# =============================================================================

def BACKTEST_15_CAU_K2N_V30_AI_V8(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, history=True
):
    # ... (Giữ nguyên logic hàm 15 Cầu K2N) ...
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
            data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"] + [""] * 15)
            continue

        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
        totalTestDays += 1

        daily_results_row, totalHits = [actualSoKy], 0

        try:
            for j in range(15):
                check_result = ""
                cell_output = ""
                if in_frame[j]:
                    pred = prediction_in_frame[j]
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
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

                daily_results_row.append(cell_output)
                if "✅" in check_result:
                    totalHits += 1

            daily_results_row.append(totalHits)
            data_rows.append(daily_results_row)

        except Exception as e:
            data_rows.append([actualSoKy, f"Lỗi: {e}"] + [""] * 15)

    data_rows.reverse()

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

    recent_win_row = ["Phong Độ 10 Kỳ"]
    for i in range(15):
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

    try:
        ky_int = int(last_data_row_for_prediction[0])
        finalRowK = f"Kỳ {ky_int + 1}"
    except (ValueError, TypeError):
        finalRowK = f"Kỳ {last_data_row_for_prediction[0]} (Next)"

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

    try:
        ky_int = int(last_data_row_for_prediction[0])
        finalRowK = f"Kỳ {ky_int + 1}"
    except (ValueError, TypeError):
        finalRowK = f"Kỳ {last_data_row_for_prediction[0]} (Next)"

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


def BACKTEST_CUSTOM_CAU_V16(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, custom_bridge_name, mode
):
    """Backtest một cầu tùy chỉnh N1/K2N (V17 Shadow)"""
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
            try:
                ky_int = int(allData[finalEndRow - offset][0])
                finalRowK = f"Kỳ {ky_int + 1}"
            except (ValueError, TypeError):
                finalRowK = f"Kỳ {allData[finalEndRow - offset][0]} (Next)"

            final_cell = "---"
            if in_frame:
                final_cell = f"{','.join(prediction_in_frame)} (Đang chờ N2)"
            results.insert(2, [finalRowK, final_cell])

        return results
    except Exception as e:
        print(f"Lỗi BACKTEST_CUSTOM_CAU_V16: {e}")
        return [["LỖI:", str(e)]]


def BACKTEST_MANAGED_BRIDGES_N1(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME
):
    """Backtest N1 cho Cầu Đã Lưu (V17 Shadow + Bạc Nhớ)"""
    return []  # Placeholder (để tránh lỗi import, logic chính ở backtester.py nếu cần)


def BACKTEST_MANAGED_BRIDGES_K1N(
    toan_bo_A_I,
    ky_bat_dau_kiem_tra,
    ky_ket_thuc_kiem_tra,
    db_name=DB_NAME,
    history=True,
):
    """Backtest K1N cho Cầu Đã Lưu (Lô) - Đã tích hợp logic cho LO_STL_FIXED và LO_MEM"""
    try:
        # [FIX CRITICAL V8.10] Load ALL bridges (kể cả disabled) để cập nhật K1N
        bridges_to_test = get_all_managed_bridges(db_name, only_enabled=False)
    except Exception as e:
        print(f"Lỗi tải cầu DB: {e}")
        return [["LỖI"]]
    
    if not bridges_to_test:
        return [["Kỳ (Cột A)"], ["Thông báo", "Không có cầu nào được Bật."]]

    # [FILTER] Lọc bỏ Cầu Đề (DE_*)
    filtered_bridges = []
    for b in bridges_to_test:
        b_name = str(b.get("name", ""))
        b_type = str(b.get("type", ""))
        if not b_name.startswith("DE_") and not b_type.startswith("DE"):
            filtered_bridges.append(b)
    
    bridges_to_test = filtered_bridges
    
    # [FIX] Trả về cấu trúc chuẩn 5 dòng nếu không có cầu Lô (để tránh lỗi index ở backtester.py)
    if not bridges_to_test:
        print(">>> Không có cầu Lô nào để backtest K1N.")
        return [
            ["Kỳ (Cột A)"], 
            ["Tỷ Lệ %"], 
            ["Chuỗi Thắng / Thua Max"], 
            ["Phong Độ 10 Kỳ"], 
            ["Thông báo", "Không có cầu Lô nào được Bật."]
        ]

    print(f">>> Bắt đầu Backtest K1N cho {len(bridges_to_test)} cầu Lô...")

    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
        toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
    )
    if error: return error

    num_bridges = len(bridges_to_test)
    headers = ["Kỳ (Cột A)"]
    for bridge in bridges_to_test:
        headers.append(f"{bridge['name']}")

    results = [headers]
    current_streak = [0] * num_bridges
    max_lose_streak = [0] * num_bridges
    win_counts = [0] * num_bridges
    data_rows = []
    totalTestDays = 0

    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0]: break
        if not prevRow or len(actualRow) < 10: 
            data_rows.append([actualRow[0] or k, "Lỗi dữ liệu"] + [""] * num_bridges)
            continue

        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
        prevPositions = getAllPositions_V17_Shadow(prevRow)
        prevLotos = get_27_loto_positions(prevRow)
        totalTestDays += 1
        daily_row = [actualSoKy]

        for j, bridge in enumerate(bridges_to_test):
            try:
                bridge_name = bridge.get("name", "")
                idx1, idx2 = bridge.get("pos1_idx"), bridge.get("pos2_idx")
                pred = []

                # --- 1. LO_STL_FIXED ---
                if "LO_STL_FIXED" in bridge_name:
                    try:
                        num_part = bridge_name.split("_")[-1]
                        if num_part.isdigit():
                            idx_func = int(num_part) - 1
                            if 0 <= idx_func < len(ALL_15_BRIDGE_FUNCTIONS_V5):
                                pred = ALL_15_BRIDGE_FUNCTIONS_V5[idx_func](prevRow)
                    except: pass
                
                # --- 2. LO_MEM ---
                elif idx1 == -1 and idx2 == -1:
                    if "LO_MEM_SUM" in bridge_name:
                        parts = bridge_name.split("_")
                        try:
                            l1, l2 = parts[-2], parts[-1]
                            names = get_27_loto_names()
                            if l1 in names and l2 in names:
                                pred = calculate_bridge_stl(prevLotos[names.index(l1)], prevLotos[names.index(l2)], "sum")
                        except: pass
                    elif "LO_MEM_DIFF" in bridge_name:
                        parts = bridge_name.split("_")
                        try:
                            l1, l2 = parts[-2], parts[-1]
                            names = get_27_loto_names()
                            if l1 in names and l2 in names:
                                pred = calculate_bridge_stl(prevLotos[names.index(l1)], prevLotos[names.index(l2)], "diff")
                        except: pass
                    
                    if not pred: # Fallback old names
                        if "Tổng(" in bridge_name:
                            m = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                            if m: pred = calculate_bridge_stl(prevLotos[int(m.group(1))], prevLotos[int(m.group(2))], "sum")
                        elif "Hiệu(" in bridge_name:
                            m = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                            if m: pred = calculate_bridge_stl(prevLotos[int(m.group(1))], prevLotos[int(m.group(2))], "diff")

                # --- 3. V17 ---
                elif idx1 is not None and idx2 is not None:
                    a, b = prevPositions[idx1], prevPositions[idx2]
                    if a is not None and b is not None:
                        pred = taoSTL_V30_Bong(a, b)

                if not pred:
                    daily_row.append("Lỗi CT"); continue

                check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                cell_output = ""

                if "✅" in check_result or "Ăn" in check_result:
                    cell_output = f"{','.join(pred)} ✅ (Ăn N1)"
                    win_counts[j] += 1
                    current_streak[j] += 1
                else:
                    cell_output = f"{','.join(pred)} ❌ (Trượt N1)"
                    current_streak[j] = 0
                    
                daily_row.append(cell_output)

            except Exception as e: daily_row.append(f"Err: {e}")

        data_rows.append(daily_row)

    data_rows.reverse()

    # Rate Row
    rate_row = ["Tỷ Lệ %"]
    if totalTestDays > 0:
        for count in win_counts:
            rate_row.append(f"{(count / totalTestDays) * 100:.2f}%")
    else:
        rate_row.extend(["0.00%"] * num_bridges)
    results.insert(1, rate_row)

    # Streak Row
    streak_row = ["Chuỗi Thắng Max"]
    for i in range(num_bridges):
        streak_row.append(f"{current_streak[i]}")
    results.insert(2, streak_row)

    # Recent Form
    recent_win_row = ["Phong Độ 10 Kỳ"]
    for i in range(num_bridges):
        recent_wins = 0
        periods = min(10, len(data_rows))
        for r_idx in range(periods):
            cell = str(data_rows[r_idx][i+1])
            if "Ăn" in cell: recent_wins += 1
        recent_win_row.append(f"{recent_wins}/10")
    results.insert(3, recent_win_row)

    # Prediction
    try:
        last_row = allData[finalEndRow - offset]
        finalRow = [f"Kỳ {int(last_row[0])+1}" if str(last_row[0]).isdigit() else "Next"]
        last_positions = getAllPositions_V17_Shadow(last_row)
        last_lotos = get_27_loto_positions(last_row)

        for j, bridge in enumerate(bridges_to_test):
            bridge_name = bridge.get("name", "")
            idx1, idx2 = bridge.get("pos1_idx"), bridge.get("pos2_idx")
            pred = []

            # 1. FIXED
            if "LO_STL_FIXED" in bridge_name:
                try:
                    num = int(bridge_name.split("_")[-1]) - 1
                    pred = ALL_15_BRIDGE_FUNCTIONS_V5[num](last_row)
                except: pass
            
            # 2. MEMORY
            elif idx1 == -1 and idx2 == -1:
                if "LO_MEM_SUM" in bridge_name:
                    p = bridge_name.split("_")
                    try: 
                        names = get_27_loto_names()
                        pred = calculate_bridge_stl(last_lotos[names.index(p[-2])], last_lotos[names.index(p[-1])], "sum")
                    except: pass
                elif "LO_MEM_DIFF" in bridge_name:
                    p = bridge_name.split("_")
                    try:
                        names = get_27_loto_names()
                        pred = calculate_bridge_stl(last_lotos[names.index(p[-2])], last_lotos[names.index(p[-1])], "diff")
                    except: pass
                
                # Fallback
                if not pred:
                    if "Tổng(" in bridge_name:
                        m = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                        if m: pred = calculate_bridge_stl(last_lotos[int(m.group(1))], last_lotos[int(m.group(2))], "sum")
                    elif "Hiệu(" in bridge_name:
                        m = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                        if m: pred = calculate_bridge_stl(last_lotos[int(m.group(1))], last_lotos[int(m.group(2))], "diff")

            # 3. V17
            elif idx1 is not None and idx2 is not None:
                a, b = last_positions[idx1], last_positions[idx2]
                if a is not None and b is not None: pred = taoSTL_V30_Bong(a, b)

            finalRow.append(f"{','.join(pred)}" if pred else "Lỗi")
        
        results.insert(4, finalRow)
    except: results.append(["Lỗi Prediction"])

    if history: results.extend(data_rows)
    return results

def BACKTEST_MANAGED_BRIDGES_K2N(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME, history=True
):
    """
    Backtest K2N Managed Bridges.
    [FIXED] Fixed NameError 'loto_names' -> 'names'.
    """
    try:
        bridges_to_test = get_all_managed_bridges(db_name, only_enabled=True)
    except:
        return []
    if not bridges_to_test:
        return []

    # [FILTER] Lọc bỏ Cầu Đề (DE_*)
    filtered_bridges = []
    for b in bridges_to_test:
        b_name = str(b.get("name", ""))
        b_type = str(b.get("type", ""))
        if not b_name.startswith("DE_") and not b_type.startswith("DE"):
            filtered_bridges.append(b)
    
    bridges_to_test = filtered_bridges
    if not bridges_to_test: return []

    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(
        toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
    )
    if error: return error

    num_bridges = len(bridges_to_test)
    headers = ["Kỳ (Cột A)"] + [b['name'] for b in bridges_to_test]
    results = [headers]

    in_frame = [False] * num_bridges
    prediction_in_frame = [None] * num_bridges
    current_streak_k2n = [0] * num_bridges
    max_lose_streak_k2n = [0] * num_bridges
    current_lose_streak_k2n = [0] * num_bridges
    win_counts = [0] * num_bridges
    data_rows = []
    totalTestDays = 0

    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0]: break
        if not prevRow or len(actualRow) < 10: 
            data_rows.append([actualRow[0] or k, "Lỗi dữ liệu"] + [""] * num_bridges)
            continue

        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
        prevPositions = getAllPositions_V17_Shadow(prevRow)
        prevLotos = get_27_loto_positions(prevRow)
        totalTestDays += 1
        daily_row = [actualSoKy]

        for j, bridge in enumerate(bridges_to_test):
            try:
                cell_output = ""
                # --- CHECK IN FRAME (N2) ---
                if in_frame[j]:
                    pred = prediction_in_frame[j]
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result or "Ăn" in check_result:
                        cell_output = f"{','.join(pred)} ✅ (Ăn N2)"
                        win_counts[j] += 1; current_streak_k2n[j] += 1; current_lose_streak_k2n[j] = 0
                    else:
                        cell_output = f"{','.join(pred)} ❌ (Trượt K2N)"
                        current_streak_k2n[j] = 0; current_lose_streak_k2n[j] += 1
                        if current_lose_streak_k2n[j] > max_lose_streak_k2n[j]: max_lose_streak_k2n[j] = current_lose_streak_k2n[j]
                    in_frame[j], prediction_in_frame[j] = False, None
                
                # --- NEW PREDICTION (N1) ---
                else:
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    pred = []
                    bridge_name = bridge.get("name", "")

                    # 1. FIXED
                    if "LO_STL_FIXED" in bridge_name:
                        try:
                            num = int(bridge_name.split("_")[-1]) - 1
                            pred = ALL_15_BRIDGE_FUNCTIONS_V5[num](prevRow)
                        except: pass
                    
                    # 2. MEMORY
                    elif idx1 == -1 and idx2 == -1:
                        if "LO_MEM_SUM" in bridge_name:
                            parts = bridge_name.split("_")
                            try:
                                l1, l2 = parts[-2], parts[-1]
                                names = get_27_loto_names()
                                if l1 in names and l2 in names:
                                    # [FIXED] Use names.index
                                    p1, p2 = names.index(l1), names.index(l2)
                                    loto1, loto2 = prevLotos[p1], prevLotos[p2]
                                    pred = calculate_bridge_stl(loto1, loto2, "sum")
                            except: pass
                        elif "LO_MEM_DIFF" in bridge_name:
                            parts = bridge_name.split("_")
                            try:
                                l1, l2 = parts[-2], parts[-1]
                                names = get_27_loto_names()
                                if l1 in names and l2 in names:
                                    # [FIXED] Use names.index
                                    p1, p2 = names.index(l1), names.index(l2)
                                    loto1, loto2 = prevLotos[p1], prevLotos[p2]
                                    pred = calculate_bridge_stl(loto1, loto2, "diff")
                            except: pass
                        
                        if not pred: # Fallback
                            if "Tổng(" in bridge_name:
                                m = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                                if m: pred = calculate_bridge_stl(prevLotos[int(m.group(1))], prevLotos[int(m.group(2))], "sum")
                            elif "Hiệu(" in bridge_name:
                                m = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                                if m: pred = calculate_bridge_stl(prevLotos[int(m.group(1))], prevLotos[int(m.group(2))], "diff")

                    # 3. V17
                    elif idx1 is not None and idx2 is not None:
                        a, b = prevPositions[idx1], prevPositions[idx2]
                        if a is not None and b is not None:
                            pred = taoSTL_V30_Bong(a, b)
                    
                    if not pred:
                        daily_row.append("Err"); continue

                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result or "Ăn" in check_result:
                        cell_output = f"{','.join(pred)} ✅ (Ăn N1)"
                        win_counts[j] += 1; current_streak_k2n[j] += 1; current_lose_streak_k2n[j] = 0
                    else:
                        cell_output = f"{','.join(pred)} (Trượt N1...)"
                        in_frame[j], prediction_in_frame[j] = True, pred
                
                daily_row.append(cell_output)
            except: daily_row.append("Err")
        data_rows.append(daily_row)

    data_rows.reverse()
    
    rate_row = ["Tỷ Lệ %"]
    if totalTestDays > 0:
        for c in win_counts: rate_row.append(f"{(c / totalTestDays) * 100:.2f}%")
    else: rate_row.extend(["0.00%"] * num_bridges)
    results.insert(1, rate_row)

    streak_row = ["Chuỗi Thắng / Thua Max"]
    for i in range(num_bridges): streak_row.append(f"{current_streak_k2n[i]} thắng / {max_lose_streak_k2n[i]} thua")
    results.insert(2, streak_row)
    results.insert(3, ["Phong Độ 10 Kỳ"] + ["---"] * num_bridges)

    # Prediction
    try:
        last_row = allData[finalEndRow - offset]
        try:
            ky_int = int(last_row[0])
            finalRowK = f"Kỳ {ky_int + 1}"
        except (ValueError, TypeError):
            finalRowK = f"Kỳ {last_row[0]} (Next)"
        
        finalRow = [finalRowK]
        last_positions = getAllPositions_V17_Shadow(last_row)
        last_lotos = get_27_loto_positions(last_row)

        for j, bridge in enumerate(bridges_to_test):
            if in_frame[j]:
                finalRow.append(f"{','.join(prediction_in_frame[j])} (Đang chờ N2)")
            else:
                idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                pred = []
                bridge_name = bridge.get("name", "")

                # 1. FIXED
                if "LO_STL_FIXED" in bridge_name:
                    try:
                        num = int(bridge_name.split("_")[-1]) - 1
                        pred = ALL_15_BRIDGE_FUNCTIONS_V5[num](last_row)
                    except: pass
                
                # 2. MEMORY
                elif idx1 == -1 and idx2 == -1:
                    if "LO_MEM_SUM" in bridge_name:
                        parts = bridge_name.split("_")
                        try:
                            l1, l2 = parts[-2], parts[-1]
                            names = get_27_loto_names()
                            if l1 in names and l2 in names:
                                pred = calculate_bridge_stl(
                                    last_lotos[names.index(l1)],
                                    last_lotos[names.index(l2)],
                                    "sum",
                                )
                        except: pass
                    elif "LO_MEM_DIFF" in bridge_name:
                        parts = bridge_name.split("_")
                        try:
                            l1, l2 = parts[-2], parts[-1]
                            names = get_27_loto_names()
                            if l1 in names and l2 in names:
                                pred = calculate_bridge_stl(
                                    last_lotos[names.index(l1)],
                                    last_lotos[names.index(l2)],
                                    "diff",
                                )
                        except: pass
                    
                    if not pred:
                        if "Tổng(" in bridge_name:
                            m = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                            if m:
                                pred = calculate_bridge_stl(
                                    last_lotos[int(m.group(1))],
                                    last_lotos[int(m.group(2))],
                                    "sum",
                                )
                        elif "Hiệu(" in bridge_name:
                            m = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                            if m:
                                pred = calculate_bridge_stl(
                                    last_lotos[int(m.group(1))],
                                    last_lotos[int(m.group(2))],
                                    "diff",
                                )
                else:
                    a, b = last_positions[idx1], last_positions[idx2]
                    if a is not None and b is not None:
                        pred = taoSTL_V30_Bong(a, b)
                
                finalRow.append(f"{','.join(pred)} (Khung mới N1)" if pred else "Lỗi")
        
        results.insert(4, finalRow)
    except:
        results.append(["Lỗi Prediction"])

    if history:
        results.extend(data_rows)
    return results

def BACKTEST_MEMORY_BRIDGES(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    return []