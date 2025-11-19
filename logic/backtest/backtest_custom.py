"""
backtest_custom.py - Custom bridge and memory bridge backtest functions

Contains custom bridge backtest logic extracted from backtester_core.py
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
    from ..bridges.bridges_classic import (
        getAllLoto_V30,
        checkHitSet_V30_K2N,
    )
except ImportError:
    def getAllLoto_V30(r):
        return []
    
    def checkHitSet_V30_K2N(p, loto_set):
        return "Lỗi"

try:
    from ..bridges.bridges_v16 import (
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
    from ..bridges.bridges_memory import (
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

from ..backtester_helpers import validate_backtest_params as _validate_backtest_params

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
