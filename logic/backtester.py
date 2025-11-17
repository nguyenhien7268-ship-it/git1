# Tên file: du-an-backup/logic/backtester.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA LỖI 'int' object has no attribute 'isdigit' (V4))
#
# (SỬA F401) Xóa 'import sqlite3' không dùng

# (V7.1) Chỉ giữ lại import Counter cho tiện ích chung
# (SỬA F401) Xóa 'from collections import Counter' không dùng

# (V7.1) Chỉ giữ lại import config_manager
try:
    from .config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    except ImportError:
        print(
            "LỖI: backtester.py không thể import config_manager. Sử dụng giá trị mặc định."
        )
        SETTINGS = type(
            "obj",
            (object,),
            {
                "STATS_DAYS": 7,
                "GAN_DAYS": 15,
                "HIGH_WIN_THRESHOLD": 47.0,
                "AUTO_ADD_MIN_RATE": 50.0,
                "AUTO_PRUNE_MIN_RATE": 40.0,
                "K2N_RISK_START_THRESHOLD": 4,
                "K2N_RISK_PENALTY_PER_FRAME": 0.5,
                "AI_PROB_THRESHOLD": 45.0,
                "AI_SCORE_WEIGHT": 0.2,
            },
        )


# (V7.1) Giữ lại các Import Cần Thiết cho Backtest
try:
    # (V7.1) Cần Import từ Repository cho các hàm cache
    from .data_repository import get_all_managed_bridges
    from .db_manager import (  # (V7.1) Xóa get_all_managed_bridges (Lấy từ Repository)
        DB_NAME,
        update_bridge_k2n_cache_batch,
        update_bridge_win_rate_batch,
    )
except ImportError:
    # Fallback cho db_manager
    print("Lỗi: Không thể import db_manager trong backtester.py")
    DB_NAME = "data/xo_so_prizes_all_logic.db"  # <--- ĐÃ SỬA

    def get_all_managed_bridges(d, o):
        return []

    def update_bridge_win_rate_batch(r, d):
        return False, "Lỗi Import"

    def update_bridge_k2n_cache_batch(r, d):
        return False, "Lỗi Import"


# Import các hàm cầu cổ điển
try:
    from .bridges.bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5,
        checkHitSet_V30_K2N,
        getAllLoto_V30,
    )
except ImportError:
    # Fallback
    print("Lỗi: Không thể import bridges_classic trong backtester.py")
    ALL_15_BRIDGE_FUNCTIONS_V5 = []

    def getAllLoto_V30(r):
        return []

    # (SỬA E741) Đổi tên 'l' thành 'loto_set'
    def checkHitSet_V30_K2N(p, loto_set):
        return "Lỗi"


# Import các hàm cầu V16 (VÀ V17 MỚI)
try:
    from .bridges.bridges_v16 import (
        get_index_from_name_V16,
        getAllPositions_V17_Shadow,
        getPositionName_V16,
        getPositionName_V17_Shadow,
        taoSTL_V30_Bong,
    )
except ImportError:
    # Fallback
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


# (V7.1) Import các hàm Bạc Nhớ (chỉ cần cho Backtest Memory)
try:
    from .bridges.bridges_memory import (
        calculate_bridge_stl,
        get_27_loto_names,
        get_27_loto_positions,
    )
except ImportError:
    print("Lỗi: Không thể import bridges_memory trong backtester.py")

    def get_27_loto_names():
        return []

    def get_27_loto_positions(r):
        return []

    def calculate_bridge_stl(l1, l2, type):
        return ["00", "00"]


# ===================================================================================
# I. HÀM HỖ TRỢ CHUNG (V7.1)
# ===================================================================================


def _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    if not all([toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra]):
        return None, None, None, None, [["LỖI:", "Cần đủ tham số."]]
    try:
        startRow, endRow = int(ky_bat_dau_kiem_tra), int(ky_ket_thuc_kiem_tra)
    except ValueError:
        return None, None, None, None, [["LỖI:", "Kỳ BĐ/KT phải là số."]]
    if not (startRow > 1 and startRow <= endRow):
        # (SỬA F541) Xóa f-string không cần thiết
        return None, None, None, None, [["LỖI:", "Kỳ BĐ/KT không hợp lệ."]]
    allData = toan_bo_A_I
    finalEndRow = min(endRow, (len(allData) + startRow - 1))
    startCheckRow = startRow + 1
    if startCheckRow > finalEndRow:
        return None, None, None, None, [["LỖI:", "Dữ liệu không đủ để chạy."]]
    offset = startRow
    return allData, finalEndRow, startCheckRow, offset, None


def _parse_k2n_results(results_data):
    """
    (Giữ lại) Hàm nội bộ: Phân tích kết quả 4 hàng từ backtest K2N.
    """
    cache_data_list = []
    pending_k2n_dict = {}

    if not results_data or len(results_data) < 4:
        print("Lỗi _parse_k2n_results: Dữ liệu backtest K2N không hợp lệ.")
        return cache_data_list, pending_k2n_dict

    try:
        headers = results_data[0]  # Hàng 0: Tên cầu
        rates = results_data[1]  # Hàng 1: Tỷ Lệ %
        streaks = results_data[2]  # Hàng 2: Chuỗi Thắng / Thua Max
        pending = results_data[3]  # Hàng 3: Dự đoán

        num_bridges = len(headers) - 1  # Trừ cột "Kỳ"

        for j in range(1, num_bridges + 1):
            bridge_name = str(headers[j]).split(" (")[0]  # Lấy tên gốc

            # 1. Lấy Tỷ lệ
            win_rate_text = str(rates[j])

            # 2. Lấy Chuỗi Thắng và Chuỗi Thua Max
            streak_text_full = str(streaks[j])  # "3 thắng / 5 thua"
            current_streak = 0
            max_lose_streak = 0
            try:
                parts = streak_text_full.split(" / ")
                current_streak = int(parts[0].split(" ")[0])
                max_lose_streak = int(parts[1].split(" ")[0])
            except Exception:
                pass

            # 3. Lấy Dự đoán
            pending_text = str(pending[j])
            next_prediction_stl = "LỖI"

            if "(Đang chờ N2)" in pending_text:
                next_prediction_stl = pending_text.split(" (")[0]
                pending_k2n_dict[bridge_name] = {
                    "stl": next_prediction_stl,
                    "streak": f"{current_streak} khung",
                    "max_lose": max_lose_streak,
                }
            elif "(Khung mới N1)" in pending_text:
                next_prediction_stl = pending_text.split(" (")[0]

            # 4. Thêm max_lose_streak vào danh sách cache
            cache_data_list.append(
                (
                    win_rate_text,
                    current_streak,
                    next_prediction_stl,
                    max_lose_streak,
                    bridge_name,
                )
            )

    except Exception as e:
        print(f"Lỗi _parse_k2n_results: {e}")

    return cache_data_list, pending_k2n_dict


# ===================================================================================
# II. TỔNG HỢP TOP CẦU (V7.1)
# ===================================================================================


def TONGHOP_TOP_CAU_CORE_V5(
    fullBacktestN1Range, lastDataRowForPrediction, topN, scoringFunction
):
    try:
        if not fullBacktestN1Range or len(fullBacktestN1Range) < 2:
            return [["LỖI: 'fullBacktestN1Range' không hợp lệ."]]
        if not lastDataRowForPrediction or len(lastDataRowForPrediction) < 10:
            return [["LỖI: 'lastDataRowForPrediction' không hợp lệ."]]

        lastKy = lastDataRowForPrediction[0]
        
        # (SỬA LỖI V4) Xử lý 'int' object
        try:
            ky_int = int(lastKy)
            nextKy = f"Kỳ {ky_int + 1}"
        except (ValueError, TypeError):
            nextKy = f"Kỳ {lastKy} (Next)"
        # (Kết thúc sửa lỗi)

        headers = fullBacktestN1Range[0]
        dataRows = [
            row
            for row in fullBacktestN1Range[1:]
            if "Tỷ Lệ %" not in str(row[0])
            and "HOÀN THÀNH" not in str(row[0])
            and not str(row[0]).startswith("Kỳ")
            # (SỬA E713) 'not ... in' được đổi thành '... not in'
            and "(Dự đoán N1)" not in str(row)
        ]

        numDataRows = len(dataRows)
        if numDataRows == 0:
            return [["LỖI: Không tìm thấy dữ liệu backtest hợp lệ."]]

        bridgeColumns = []
        for j, header in enumerate(headers):
            if str(header).startswith("Cầu "):
                bridgeColumns.append(
                    {"name": str(header).split(" (")[0], "colIndex": j}
                )

        if not bridgeColumns:
            return [["LỖI: Không tìm thấy cột 'Cầu ' nào trong tiêu đề."]]

        bridgeStats = []
        num_cau_functions = len(ALL_15_BRIDGE_FUNCTIONS_V5)

        for i, bridge in enumerate(bridgeColumns):
            if i >= num_cau_functions:
                break
            colIdx = bridge["colIndex"]
            wins, currentStreak = 0, 0

            for k in range(numDataRows):
                if "✅" in str(dataRows[k][colIdx]):
                    wins += 1
            for k in range(numDataRows - 1, -1, -1):
                if "✅" in str(dataRows[k][colIdx]):
                    currentStreak += 1
                else:
                    break

            winRate = (wins / numDataRows) if numDataRows > 0 else 0
            score = scoringFunction(winRate, currentStreak)

            bridgeStats.append(
                {
                    "name": bridge["name"],
                    "bridgeFuncIndex": i,
                    "rate": winRate,
                    "streak": currentStreak,
                    "score": score,
                }
            )

        bridgeStats.sort(key=lambda x: x["score"], reverse=True)

        topBridges = bridgeStats[:topN]
        outputParts, seenNumbers = [], set()

        for bridge in topBridges:
            try:
                stl = ALL_15_BRIDGE_FUNCTIONS_V5[bridge["bridgeFuncIndex"]](
                    lastDataRowForPrediction
                )
                bridgeNum = bridge["name"].replace("Cầu ", "")
                num1, num2 = stl[0], stl[1]
                pairPart1, pairPart2 = None, None

                if num1 not in seenNumbers:
                    pairPart1, seenNumbers = num1, seenNumbers | {num1}
                if num2 not in seenNumbers:
                    pairPart2, seenNumbers = f"{num2}({bridgeNum})", seenNumbers | {
                        num2
                    }
                elif pairPart1:
                    pairPart1 = f"{num1}({bridgeNum})"

                if pairPart1 and pairPart2:
                    outputParts.append(f"{pairPart1}, {pairPart2}")
                elif pairPart1:
                    outputParts.append(pairPart1)
                elif pairPart2:
                    outputParts.append(pairPart2)
            except Exception as e:
                print(f"Lỗi khi gọi hàm cầu {bridge['name']}: {e}")

        return [[f"{nextKy}: {', '.join(outputParts)}"]]
    except Exception as e:
        print(f"Lỗi TONGHOP_CORE_V5: {e}")
        return [[f"LỖI: {e}"]]


# (SỬA E731) Chuyển lambda thành def
def _scoreByStreak(rate, streak):
    return (streak * 1000) + (rate * 100)


def TONGHOP_TOP_CAU_N1_V5(fullBacktestN1Range, lastDataRowForPrediction, topN=3):
    return TONGHOP_TOP_CAU_CORE_V5(
        fullBacktestN1Range, lastDataRowForPrediction, topN, _scoreByStreak
    )


# (SỬA E731) Chuyển lambda thành def
def _scoreByRate(rate, streak):
    return (rate * 1000) + (streak * 100)


def TONGHOP_TOP_CAU_RATE_V5(fullBacktestN1Range, lastDataRowForPrediction, topN=3):
    return TONGHOP_TOP_CAU_CORE_V5(
        fullBacktestN1Range, lastDataRowForPrediction, topN, _scoreByRate
    )


# ===================================================================================
# III. HÀM BACKTEST CỐT LÕI (V7.1)
# ===================================================================================


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
                check_result = "" # (Sửa V4) Khởi tạo
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

    # (SỬA LỖI V4) Xử lý 'int' object has no attribute 'isdigit'
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

    # (SỬA LỖI V4) Xử lý 'int' object has no attribute 'isdigit'
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


# (V7.1) XÓA: TIM_CAU_TOT_NHAT_V16 (Đã chuyển sang bridge_manager_core.py)


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
            # (SỬA LỖI V4) Xử lý 'int' object has no attribute 'isdigit'
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


# (V7.1) XÓA: BACKTEST_MANAGED_BRIDGES_N1 (Đã giữ lại hàm dưới)
# (V7.1) XÓA: BACKTEST_MANAGED_BRIDGES_K2N (Đã giữ lại hàm dưới)


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
        
        # (SỬA LỖI V4) Xử lý 'int' object has no attribute 'isdigit'
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

        # (SỬA LỖI V4) Xử lý 'int' object has no attribute 'isdigit'
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
        
        # (SỬA LỖI V4) Xử lý 'int' object has no attribute 'isdigit'
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


# ===================================================================================
# IV. HÀM CẬP NHẬT CACHE/TỶ LỆ (V7.1)
# ===================================================================================


def run_and_update_all_bridge_rates(all_data_ai, db_name=DB_NAME):
    """Cập nhật Tỷ lệ (Win Rate) cho Cầu Đã Lưu"""
    try:
        if not all_data_ai:
            return 0, "Không có dữ liệu A:I để chạy backtest."

        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)

        # 1. Chạy backtest N1 (đã là V17)
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

        # 2. Cập nhật DB
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
    """Cập nhật Cache K2N cho Cầu Cổ Điển và Cầu Đã Lưu"""
    try:
        data_to_use = data_slice if data_slice else all_data_ai

        if not data_to_use:
            return {}, "Không có dữ liệu A:I để chạy backtest K2N cache."

        ky_bat_dau = 2
        ky_ket_thuc = len(data_to_use) + (ky_bat_dau - 1)

        full_cache_data_list = []
        full_pending_k2n_dict = {}

        # --- 1. Chạy 15 Cầu Cổ Điển K2N ---
        if write_to_db:
            print("... (Cache K2N) Đang chạy 15 Cầu Cổ Điển K2N (tối ưu)...")
        results_15_cau = BACKTEST_15_CAU_K2N_V30_AI_V8(
            data_to_use, ky_bat_dau, ky_ket_thuc, history=False
        )

        cache_list_15, pending_dict_15 = _parse_k2n_results(results_15_cau)
        full_cache_data_list.extend(cache_list_15)
        full_pending_k2n_dict.update(pending_dict_15)
        if write_to_db:
            print(f"... (Cache K2N) Đã phân tích {len(cache_list_15)} cầu CĐ.")

        # --- 2. Chạy Cầu Đã Lưu K2N ---
        if write_to_db:
            print("... (Cache K2N) Đang chạy Cầu Đã Lưu K2N (tối ưu)...")
        results_managed = BACKTEST_MANAGED_BRIDGES_K2N(
            data_to_use, ky_bat_dau, ky_ket_thuc, db_name, history=False
        )

        if results_managed and "LỖI" not in str(results_managed[0][0]):
            cache_list_managed, pending_dict_managed = _parse_k2n_results(
                results_managed
            )
            full_cache_data_list.extend(cache_list_managed)
            full_pending_k2n_dict.update(pending_dict_managed)
            if write_to_db:
                print(
                    f"... (Cache K2N) Đã phân tích {len(cache_list_managed)} cầu đã lưu."
                )
        else:
            if write_to_db:
                print(
                    "... (Cache K2N) Bỏ qua Cầu Đã Lưu (không có cầu nào hoặc bị lỗi)."
                )

        # --- 3. Cập nhật CSDL (Nếu được phép) ---
        if not full_cache_data_list:
            return {}, "Không có dữ liệu cache K2N nào để cập nhật."

        if write_to_db:
            print(
                f"... (Cache K2N) Đang cập nhật {len(full_cache_data_list)} bản ghi cache vào CSDL..."
            )
            success, message = update_bridge_k2n_cache_batch(
                full_cache_data_list, db_name
            )

            if success:
                return full_pending_k2n_dict, message
            else:
                return {}, message
        else:
            return (
                full_pending_k2n_dict,
                f"Mô phỏng Cache K2N hoàn tất ({len(full_cache_data_list)} cầu).",
            )

    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return {}, f"Lỗi nghiêm trọng trong run_and_update_all_bridge_K2N_cache: {e}"


# (V7.1) XÓA: find_and_auto_manage_bridges (Đã chuyển sang bridge_manager_core.py)
# (V7.1) XÓA: prune_bad_bridges (Đã chuyển sang bridge_manager_core.py)

# (V7.1) XÓA: Các hàm analytics (get_loto_stats_last_n_days, get_prediction_consensus, get_high_win_rate_predictions, get_top_scored_pairs, get_loto_gan_stats)
# (V7.1) ĐÃ CHUYỂN SANG dashboard_analytics.py

# (V7.1) XÓA: TIM_CAU_BAC_NHO_TOT_NHAT (Đã chuyển sang bridge_manager_core.py)
# (V7.1) XÓA: get_top_memory_bridge_predictions (Đã chuyển sang dashboard_analytics.py)

# (V7.1) XÓA: get_historical_dashboard_data (Đã chuyển sang dashboard_analytics.py)