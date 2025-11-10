import sqlite3
from collections import Counter # (MỚI) Thêm import Counter cho các hàm analytics

# (MỚI GĐ 8) Import file Cài đặt
try:
    from .config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    except ImportError:
        print("LỖI: backtester.py không thể import config_manager. Sử dụng giá trị mặc định.")
        SETTINGS = type('obj', (object,), {
            'STATS_DAYS': 7, 'GAN_DAYS': 15, 'HIGH_WIN_THRESHOLD': 47.0,
            'AUTO_ADD_MIN_RATE': 50.0, 'AUTO_PRUNE_MIN_RATE': 40.0,
            'K2N_RISK_START_THRESHOLD': 4, 'K2N_RISK_PENALTY_PER_FRAME': 0.5
        })


# Import các hàm DB
try:
    from .db_manager import (
        DB_NAME, 
        get_all_managed_bridges, 
        update_bridge_win_rate_batch,
        # (MỚI GĐ 1) Thêm hàm cập nhật K2N cache
        update_bridge_k2n_cache_batch
    )
except ImportError:
    try:
        from db_manager import (
            DB_NAME, 
            get_all_managed_bridges, 
            update_bridge_win_rate_batch,
            # (MỚI GĐ 1) Thêm hàm cập nhật K2N cache
            update_bridge_k2n_cache_batch
        )
    except ImportError:
        print("Lỗi: Không thể import db_manager trong backtester.py")
        DB_NAME = 'xo_so_prizes_all_logic.db'
        def get_all_managed_bridges(d, o): return []
        def update_bridge_win_rate_batch(r, d): return False, "Lỗi Import"
        # (MỚI GĐ 1) Giả lập
        def update_bridge_k2n_cache_batch(r, d): return False, "Lỗi Import"

# Import các hàm cầu cổ điển
try:
    from .bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5, 
        getAllLoto_V30, 
        checkHitSet_V30_K2N
    )
except ImportError:
    try:
        from bridges_classic import (
            ALL_15_BRIDGE_FUNCTIONS_V5, 
            getAllLoto_V30, 
            checkHitSet_V30_K2N
        )
    except ImportError:
        print("Lỗi: Không thể import bridges_classic trong backtester.py")
        ALL_15_BRIDGE_FUNCTIONS_V5 = []
        def getAllLoto_V30(r): return []
        def checkHitSet_V30_K2N(p, l): return "Lỗi"

# Import các hàm cầu V16 (VÀ V17 MỚI)
try:
    from .bridges_v16 import (
        getAllPositions_V16, 
        getPositionName_V16, 
        get_index_from_name_V16,
        taoSTL_V30_Bong,
        # (MỚI) Thêm hàm V17
        getAllPositions_V17_Shadow,
        getPositionName_V17_Shadow
    )
except ImportError:
    try:
        from bridges_v16 import (
            getAllPositions_V16, 
            getPositionName_V16, 
            get_index_from_name_V16,
            taoSTL_V30_Bong,
            # (MỚI) Thêm hàm V17
            getAllPositions_V17_Shadow,
            getPositionName_V17_Shadow
        )
    except ImportError:
        print("Lỗi: Không thể import bridges_v16 trong backtester.py")
        def getAllPositions_V16(r): return []
        def getPositionName_V16(i): return "Lỗi"
        def get_index_from_name_V16(n): return None
        def taoSTL_V30_Bong(a, b): return ['00', '00']
        # Giả lập V17
        def getAllPositions_V17_Shadow(r): return []
        def getPositionName_V17_Shadow(i): return "Lỗi V17"


# ===================================================================================
# III. HÀM CÔNG KHAI: TỔNG HỢP (V25)
# ===================================================================================

def TONGHOP_TOP_CAU_CORE_V5(fullBacktestN1Range, lastDataRowForPrediction, topN, scoringFunction):
    try:
        if not fullBacktestN1Range or len(fullBacktestN1Range) < 2:
            return [["LỖI: 'fullBacktestN1Range' không hợp lệ."]]
        if not lastDataRowForPrediction or len(lastDataRowForPrediction) < 10:
            return [["LỖI: 'lastDataRowForPrediction' không hợp lệ."]]
        
        lastKy = lastDataRowForPrediction[0]
        nextKy = f"Kỳ {int(lastKy) + 1}" if lastKy.isdigit() else f"Kỳ {lastKy} (Next)"

        headers = fullBacktestN1Range[0]
        dataRows = [row for row in fullBacktestN1Range[1:] if "Tỷ Lệ %" not in str(row[0]) and "HOÀN THÀNH" not in str(row[0]) and not str(row[0]).startswith("Kỳ") and not "(Dự đoán N1)" in str(row)]
        
        numDataRows = len(dataRows)
        if numDataRows == 0:
            return [["LỖI: Không tìm thấy dữ liệu backtest hợp lệ."]]
            
        bridgeColumns = []
        for j, header in enumerate(headers):
            if str(header).startswith("Cầu "):
                bridgeColumns.append({"name": str(header).split(' (')[0], "colIndex": j})
        
        if not bridgeColumns:
            return [["LỖI: Không tìm thấy cột 'Cầu ' nào trong tiêu đề."]]
        
        bridgeStats = []
        num_cau_functions = len(ALL_15_BRIDGE_FUNCTIONS_V5)
        
        for i, bridge in enumerate(bridgeColumns):
            if i >= num_cau_functions: break
            colIdx = bridge["colIndex"]
            wins, currentStreak = 0, 0
            
            for k in range(numDataRows):
                if "✅" in str(dataRows[k][colIdx]): wins += 1
            for k in range(numDataRows - 1, -1, -1):
                if "✅" in str(dataRows[k][colIdx]): currentStreak += 1
                else: break
            
            winRate = (wins / numDataRows) if numDataRows > 0 else 0
            score = scoringFunction(winRate, currentStreak)
            
            bridgeStats.append({
                "name": bridge["name"], "bridgeFuncIndex": i,
                "rate": winRate, "streak": currentStreak, "score": score
            })

        bridgeStats.sort(key=lambda x: x["score"], reverse=True)
        
        topBridges = bridgeStats[:topN]
        outputParts, seenNumbers = [], set()
        
        for bridge in topBridges:
            try:
                stl = ALL_15_BRIDGE_FUNCTIONS_V5[bridge["bridgeFuncIndex"]](lastDataRowForPrediction)
                bridgeNum = bridge["name"].replace('Cầu ', '')
                num1, num2 = stl[0], stl[1]
                pairPart1, pairPart2 = None, None

                if num1 not in seenNumbers:
                    pairPart1, seenNumbers = num1, seenNumbers | {num1}
                if num2 not in seenNumbers:
                    pairPart2, seenNumbers = f"{num2}({bridgeNum})", seenNumbers | {num2}
                elif pairPart1:
                    pairPart1 = f"{num1}({bridgeNum})"
                
                if pairPart1 and pairPart2: outputParts.append(f"{pairPart1}, {pairPart2}")
                elif pairPart1: outputParts.append(pairPart1)
                elif pairPart2: outputParts.append(pairPart2)
            except Exception as e:
                print(f"Lỗi khi gọi hàm cầu {bridge['name']}: {e}")
        
        return [[f"{nextKy}: {', '.join(outputParts)}"]]
    except Exception as e:
        print(f"Lỗi TONGHOP_CORE_V5: {e}")
        return [[f"LỖI: {e}"]]

def TONGHOP_TOP_CAU_N1_V5(fullBacktestN1Range, lastDataRowForPrediction, topN = 3):
    scoreByStreak = lambda rate, streak: (streak * 1000) + (rate * 100)
    return TONGHOP_TOP_CAU_CORE_V5(
        fullBacktestN1Range, lastDataRowForPrediction, topN, scoreByStreak
    )

def TONGHOP_TOP_CAU_RATE_V5(fullBacktestN1Range, lastDataRowForPrediction, topN = 3):
    scoreByRate = lambda rate, streak: (rate * 1000) + (streak * 100)
    return TONGHOP_TOP_CAU_CORE_V5(
        fullBacktestN1Range, lastDataRowForPrediction, topN, scoreByRate
    )

# ===================================================================================
# IV. HÀM CÔNG KHAI: BACKTEST (V25)
# ===================================================================================

def _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    if not all([toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra]):
        return None, None, None, None, [["LỖI:", "Cần đủ tham số."]]
    try:
        startRow, endRow = int(ky_bat_dau_kiem_tra), int(ky_ket_thuc_kiem_tra)
    except ValueError:
        return None, None, None, None, [["LỖI:", "Kỳ BĐ/KT phải là số."]]
    if not (startRow > 1 and startRow <= endRow):
        return None, None, None, None, [["LỖI:", f"Kỳ BĐ/KT không hợp lệ."]]
    allData = toan_bo_A_I
    finalEndRow = min(endRow, (len(allData) + startRow - 1))
    startCheckRow = startRow + 1
    if startCheckRow > finalEndRow:
        return None, None, None, None, [["LỖI:", "Dữ liệu không đủ để chạy."]]
    offset = startRow
    return allData, finalEndRow, startCheckRow, offset, None

def BACKTEST_15_CAU_K2N_V30_AI_V8(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, history=True):
    """
    (CẬP NHẬT GĐ 4) Thêm tính toán 'Chuỗi thua K2N dài nhất'.
    """
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error
    headers = ["Kỳ (Cột A)", "Cầu 1 (Đề+5)", "Cầu 2 (G6+G7)", "Cầu 3 (GĐB+G1)", 
               "Cầu 4 (GĐB+G1)", "Cầu 5 (G7+G7)", "Cầu 6 (G7+G7)", 
               "Cầu 7 (G5+G7)", "Cầu 8 (G3+G4)", "Cầu 9 (GĐB+G1)",
               "Cầu 10 (G2+G3)", "Cầu 11 (GĐB+G3)", "Cầu 12 (GĐB+G3)",
               "Cầu 13 (G7.3+8)", "Cầu 14 (G1+2)", "Cầu 15 (Đề+7)", "Tổng Trúng"]
    results = [headers]
    
    # Biến theo dõi K2N
    in_frame = [False] * 15
    prediction_in_frame = [None] * 15
    current_streak_k2n = [0] * 15 # Đếm chuỗi K2N
    
    # (MỚI GĐ 4) Biến theo dõi chuỗi thua
    current_lose_streak_k2n = [0] * 15
    max_lose_streak_k2n = [0] * 15
    
    cau_functions = ALL_15_BRIDGE_FUNCTIONS_V5
    
    data_rows = []
    totalTestDays = 0
    win_counts = [0] * 15
    
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "": break
        
        if not prevRow or len(actualRow) < 10 or not actualRow[2] or not actualRow[9]:
            if history:
                data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"] + [""] * 15)
            continue
            
        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
        totalTestDays += 1
        
        daily_results_row, totalHits = [actualSoKy], 0
        
        try:
            for j in range(15):
                cell_output = "" 
                if in_frame[j]:
                    # --- Đang ở Ngày 2 (N2) ---
                    pred = prediction_in_frame[j]
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        if history: cell_output = f"{','.join(pred)} ✅ (Ăn N2)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1 
                        current_lose_streak_k2n[j] = 0 # (MỚI GĐ 4) Reset chuỗi thua
                    else:
                        if history: cell_output = f"{','.join(pred)} ❌ (Trượt K2N)"
                        current_streak_k2n[j] = 0 
                        # (MỚI GĐ 4) Cập nhật chuỗi thua
                        current_lose_streak_k2n[j] += 1
                        if current_lose_streak_k2n[j] > max_lose_streak_k2n[j]:
                            max_lose_streak_k2n[j] = current_lose_streak_k2n[j]
                            
                    in_frame[j], prediction_in_frame[j] = False, None
                else:
                    # --- Đang ở Ngày 1 (N1) ---
                    pred = cau_functions[j](prevRow)
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        if history: cell_output = f"{','.join(pred)} ✅ (Ăn N1)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0 # (MỚI GĐ 4) Reset chuỗi thua
                    else:
                        if history: cell_output = f"{','.join(pred)} (Trượt N1...)"
                        # (MỚI GĐ 4) Chuỗi thua chưa bắt đầu, chờ N2
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
        
        # (SỬA GĐ 4) Đổi tên hàng và thêm Max Lose
        streak_row = ["Chuỗi Thắng / Thua Max"]
        for i in range(15):
            streak_row.append(f"{current_streak_k2n[i]} thắng / {max_lose_streak_k2n[i]} thua")
        streak_row.append("---")
        results.insert(2, streak_row) # Chèn Chuỗi

    try:
        last_data_row_for_prediction = allData[finalEndRow - offset]
    except IndexError:
        results.append(["LỖI DỰ ĐOÁN", "Không có dữ liệu hàng cuối."])
        return results
        
    finalRowK = f"Kỳ {int(last_data_row_for_prediction[0]) + 1}" if last_data_row_for_prediction[0].isdigit() else f"Kỳ {finalEndRow + 1}"
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

def BACKTEST_15_CAU_N1_V31_AI_V8(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    """ (Giữ nguyên) Backtest 15 Cầu Lô N1 (Sắp xếp giảm dần) """
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error
    headers = ["Kỳ (Cột A)", "Cầu 1 (Đề+5)", "Cầu 2 (G6+G7)", "Cầu 3 (GĐB+G1)", 
               "Cầu 4 (GĐB+G1)", "Cầu 5 (G7+G7)", "Cầu 6 (G7+G7)", 
               "Cầu 7 (G5+G7)", "Cầu 8 (G3+G4)", "Cầu 9 (GĐB+G1)",
               "Cầu 10 (G2+G3)", "Cầu 11 (GĐB+G3)", "Cầu 12 (GĐB+G3)",
               "Cầu 13 (G7.3+8)", "Cầu 14 (G1+2)", "Cầu 15 (Đề+7)", "Tổng Trúng"]
    results = [headers]
    cau_functions = ALL_15_BRIDGE_FUNCTIONS_V5
    
    data_rows = [] 
    
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "": break
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
                if "✅" in check_result: totalHits += 1
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
                if "✅" in str(row[j+1]): win_counts[j] += 1
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

    finalRowK = f"Kỳ {int(last_data_row_for_prediction[0]) + 1}" if last_data_row_for_prediction[0].isdigit() else f"Kỳ {finalEndRow + 1}"
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

def TIM_CAU_TOT_NHAT_V16(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """(Giữ nguyên) Lọc ra các cầu đã lưu. Đã nâng cấp lên V17 (23.005 cầu)."""
    print("Bắt đầu Dò Cầu Tốt Nhất V17 (Shadow)...") 
    
    saved_bridge_names = set()
    try:
        conn_managed = sqlite3.connect(db_name)
        cursor_managed = conn_managed.cursor()
        cursor_managed.execute('SELECT name FROM ManagedBridges')
        saved_rows = cursor_managed.fetchall()
        conn_managed.close()
        saved_bridge_names = {row[0] for row in saved_rows}
        print(f"Đã tìm thấy {len(saved_bridge_names)} cầu đã lưu để lọc.")
    except Exception as e:
        print(f"Lỗi khi tải cầu đã lưu (vẫn tiếp tục): {e}")
    
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error
    
    processedData = []
    print("Đang tiền xử lý dữ liệu...")
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not prevRow or not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "" or len(actualRow) < 10 or not actualRow[9]:
            continue
        processedData.append({
          "prevPositions": getAllPositions_V17_Shadow(prevRow),
          "actualLotoSet": set(getAllLoto_V30(actualRow))
        })
    
    totalTestDays = len(processedData)
    if totalTestDays == 0: 
        return [["LỖI:", "Không có dữ liệu hợp lệ để backtest."]]

    print(f"Tiền xử lý hoàn tất. {totalTestDays} ngày test. Bắt đầu dò 23005 cầu (V17)...")
    
    allPositions = getAllPositions_V17_Shadow(allData[0])
    numPositions = len(allPositions) # Sẽ là 214
    results = []
    combinationCount = 0
    
    for i in range(numPositions):
        for j in range(i, numPositions):
            pos1_idx, pos2_idx, hits = i, j, 0
            for dayData in processedData:
                a, b = dayData["prevPositions"][pos1_idx], dayData["prevPositions"][pos2_idx]
                if a is None or b is None: continue
                stl = taoSTL_V30_Bong(a, b)
                if stl[0] in dayData["actualLotoSet"] or stl[1] in dayData["actualLotoSet"]:
                    hits += 1
            
            pos1_name, pos2_name = getPositionName_V17_Shadow(pos1_idx), getPositionName_V17_Shadow(pos2_idx)
            
            results.append({"name": f"{pos1_name} + {pos2_name}", "hits": hits})
            combinationCount += 1
            
            if combinationCount % 500 == 0:
                print(f"Đã dò {combinationCount} / 23005 cầu...")
    
    print(f"Dò cầu hoàn tất. Đã chạy {combinationCount} cầu. Đang lọc {len(saved_bridge_names)} cầu đã lưu...")
    
    filtered_results = [res for res in results if res["name"] not in saved_bridge_names]
    
    print(f"Đã lọc. Sắp xếp {len(filtered_results)} cầu còn lại...")
    
    filtered_results.sort(key=lambda x: x["hits"], reverse=True)
    top20 = filtered_results[:20]
              
    output = [["Hạng", "Tên Cầu", "Trúng/Tổng", "Tỷ lệ"]]
    for index, res in enumerate(top20):
        rate = (res["hits"] / totalTestDays) * 100 if totalTestDays > 0 else 0
        output.append([
            index + 1,
            res["name"],
            f"{res['hits']}/{totalTestDays}",
            f"{rate:.2f}%"
        ])
    output.append(["---", "---", "---", "---"])
    output.append([f"HOÀN THÀNH: Đã chạy tất cả {combinationCount} cầu (V17).", "", "", ""])
    print("Hoàn thành Dò Cầu V17.")
    return output

def BACKTEST_CUSTOM_CAU_V16(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, custom_bridge_name, mode):
    """ (Giữ nguyên) Sắp xếp giảm dần. Đã nâng cấp lên V17 (Shadow). """
    try:
        parts = custom_bridge_name.split('+')
        name1, name2 = parts[0].strip(), parts[1].strip()
        
        idx1, idx2 = get_index_from_name_V16(name1), get_index_from_name_V16(name2)
        
        if idx1 is None or idx2 is None:
            return [["LỖI:", f"Không thể dịch tên cầu '{custom_bridge_name}'."]]

        allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        if error: return error

        results = [ ["Kỳ (Cột A)", "Kết Quả"] ]
        in_frame, prediction_in_frame = False, None
        totalTestDays, win_count = 0, 0
        
        data_rows = [] 

        for k in range(startCheckRow, finalEndRow + 1):
            prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
            if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
            prevRow_data, actualRow = allData[prevRow_idx], allData[actualRow_idx]
            if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "": break
            if not prevRow_data or len(actualRow) < 10 or not actualRow[2] or not actualRow[9]:
                data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"])
                continue
            
            actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
            
            prevPositions = getAllPositions_V17_Shadow(prevRow_data)
            
            a, b = prevPositions[idx1], prevPositions[idx2]
            if a is None or b is None:
                data_rows.append([actualSoKy, "Lỗi (vị trí rỗng)"])
                continue
            
            totalTestDays += 1
            pred = taoSTL_V30_Bong(a, b)
            check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
            cell_output = ""

            if mode == 'N1':
                cell_output = f"{','.join(pred)} {check_result}"
                if "✅" in check_result: win_count += 1
            elif mode == 'K2N':
                if in_frame:
                    check_result = checkHitSet_V30_K2N(prediction_in_frame, actualLotoSet)
                    if "✅" in check_result:
                        cell_output, win_count = f"{','.join(prediction_in_frame)} ✅ (Ăn N2)", win_count + 1
                    else:
                        cell_output = f"{','.join(prediction_in_frame)} ❌ (Trượt K2N)"
                    in_frame, prediction_in_frame = False, None
                else:
                    if "✅" in check_result:
                        cell_output, win_count = f"{','.join(pred)} ✅ (Ăn N1)", win_count + 1
                    else:
                        cell_output, in_frame, prediction_in_frame = f"{','.join(pred)} (Trượt N1...)", True, pred
            data_rows.append([actualSoKy, cell_output])
        
        data_rows.reverse() 
        results.extend(data_rows) 

        if totalTestDays > 0:
            rate = (win_count / totalTestDays) * 100
            results.insert(1, ["Tỷ Lệ %", f"{rate:.2f}% ({win_count}/{totalTestDays})"])
        
        if mode == 'K2N':
            finalRowK = f"Kỳ {int(allData[finalEndRow - offset][0]) + 1}" if allData[finalEndRow - offset][0].isdigit() else f"Kỳ {finalEndRow + 1}"
            final_cell = "---"
            if in_frame: final_cell = f"{','.join(prediction_in_frame)} (Đang chờ N2)"
            results.insert(2, [finalRowK, final_cell]) 
        
        return results
    except Exception as e:
        print(f"Lỗi BACKTEST_CUSTOM_CAU_V16: {e}")
        return [["LỖI:", str(e)]]

# (HÀM NÀY GIỮ NGUYÊN)
def BACKTEST_MANAGED_BRIDGES_N1(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """(Giữ nguyên) Chạy backtest N1 cho Cầu Đã Lưu (Sắp xếp giảm dần). Nâng cấp V17."""
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ManagedBridges WHERE is_enabled = 1 ORDER BY id')
        bridges_to_test = [dict(row) for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        return [["LỖI:", f"Không thể tải danh sách cầu: {e}"]]
    if not bridges_to_test:
        return [["LỖI:", "Không có cầu nào được Bật trong 'Quản lý Cầu'."]]

    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error

    headers = ["Kỳ (Cột A)"]
    for bridge in bridges_to_test:
        headers.append(f"{bridge['name']}")
    results = [headers]
    
    data_rows = [] 
    
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "": break
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
                if "✅" in str(row[j+1]): win_counts[j] += 1
        rate_row = ["Tỷ Lệ %"]
        for count in win_counts:
            rate = (count / totalTestDays) * 100
            rate_row.append(f"{rate:.2f}%")
        results.insert(1, rate_row)
            
    try:
        last_data_row = allData[finalEndRow - offset]
        finalRowK = f"Kỳ {int(last_data_row[0]) + 1}" if last_data_row[0].isdigit() else f"Kỳ {finalEndRow + 1}"
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

# (MỚI) HÀM K2N CHO CẦU ĐÃ LƯU (VỚI STREAK)
def BACKTEST_MANAGED_BRIDGES_K2N(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME, history=True):
    """
    (CẬP NHẬT GĐ 4) Thêm tính toán 'Chuỗi thua K2N dài nhất'.
    """
    try:
        conn = sqlite3.connect(db_name)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ManagedBridges WHERE is_enabled = 1 ORDER BY id')
        bridges_to_test = [dict(row) for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        return [["LỖI:", f"Không thể tải danh sách cầu: {e}"]]
    if not bridges_to_test:
        return [["LỖI:", "Không có cầu nào được Bật trong 'Quản lý Cầu'."]]

    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error

    num_bridges = len(bridges_to_test)
    headers = ["Kỳ (Cột A)"]
    for bridge in bridges_to_test:
        headers.append(f"{bridge['name']}")
        
    results = [headers] 
    
    # Biến theo dõi K2N
    in_frame = [False] * num_bridges
    prediction_in_frame = [None] * num_bridges
    current_streak_k2n = [0] * num_bridges 
    
    # (MỚI GĐ 4) Biến theo dõi chuỗi thua
    current_lose_streak_k2n = [0] * num_bridges
    max_lose_streak_k2n = [0] * num_bridges
    
    data_rows = []
    totalTestDays = 0
    win_counts = [0] * num_bridges
    
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "": break
        
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
                    # --- Đang ở Ngày 2 (N2) ---
                    pred = prediction_in_frame[j]
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        if history: cell_output = f"{','.join(pred)} ✅ (Ăn N2)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0 # (MỚI GĐ 4) Reset
                    else:
                        if history: cell_output = f"{','.join(pred)} ❌ (Trượt K2N)"
                        current_streak_k2n[j] = 0
                        # (MỚI GĐ 4) Cập nhật chuỗi thua
                        current_lose_streak_k2n[j] += 1
                        if current_lose_streak_k2n[j] > max_lose_streak_k2n[j]:
                            max_lose_streak_k2n[j] = current_lose_streak_k2n[j]
                            
                    in_frame[j], prediction_in_frame[j] = False, None
                else:
                    # --- Đang ở Ngày 1 (N1) ---
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    a, b = prevPositions[idx1], prevPositions[idx2]
                    if a is None or b is None:
                        if history: daily_results_row.append("Lỗi Vị Trí")
                        continue
                    
                    pred = taoSTL_V30_Bong(a, b)
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    
                    if "✅" in check_result:
                        if history: cell_output = f"{','.join(pred)} ✅ (Ăn N1)"
                        win_counts[j] += 1
                        current_streak_k2n[j] += 1
                        current_lose_streak_k2n[j] = 0 # (MỚI GĐ 4) Reset
                    else:
                        if history: cell_output = f"{','.join(pred)} (Trượt N1...)"
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
        
        # (SỬA GĐ 4) Đổi tên hàng và thêm Max Lose
        streak_row = ["Chuỗi Thắng / Thua Max"]
        for i in range(num_bridges):
            streak_row.append(f"{current_streak_k2n[i]} thắng / {max_lose_streak_k2n[i]} thua")
        results.insert(2, streak_row) # Chèn Chuỗi
            
    try:
        last_data_row = allData[finalEndRow - offset]
        finalRowK = f"Kỳ {int(last_data_row[0]) + 1}" if last_data_row[0].isdigit() else f"Kỳ {finalEndRow + 1}"
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

# ===================================================================================
# (MỚI) HÀM NGHIỆP VỤ CẬP NHẬT TỶ LỆ CẦU
# ===================================================================================

def run_and_update_all_bridge_rates(all_data_ai, db_name=DB_NAME):
    """
    (MỚI) Chạy backtest N1 cho tất cả cầu đã lưu và cập nhật tỷ lệ vào DB.
    """
    try:
        if not all_data_ai:
            return 0, "Không có dữ liệu A:I để chạy backtest."
            
        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
        
        # 1. Chạy backtest N1 (giờ đã là V17)
        results_n1 = BACKTEST_MANAGED_BRIDGES_N1(all_data_ai, ky_bat_dau, ky_ket_thuc, db_name)
        
        if not results_n1 or len(results_n1) < 2 or "LỖI" in str(results_n1[0][0]):
            if not results_n1:
                return 0, "Backtest N1 không trả về kết quả."
            # Kiểm tra trường hợp không có cầu nào
            if "Không có cầu nào" in str(results_n1[0][1]):
                return 0, "Không có cầu nào được Bật để cập nhật."
            return 0, f"Lỗi khi chạy Backtest N1: {results_n1[0]}"
            
        headers = results_n1[0] # Hàng 0 là Tiêu đề (Tên cầu)
        rates = results_n1[1]   # Hàng 1 là Tỷ Lệ %
        
        rate_data_list = []
        num_bridges = len(headers) - 1 # Trừ cột "Kỳ"
        
        if num_bridges == 0:
            return 0, "Không có cầu nào trong kết quả backtest."
            
        for i in range(1, num_bridges + 1):
            bridge_name = str(headers[i])
            win_rate_text = str(rates[i])
            # Tạo tuple (tỷ_lệ, tên_cầu) cho hàm SQL
            rate_data_list.append((win_rate_text, bridge_name))
            
        if not rate_data_list:
            return 0, "Không trích xuất được dữ liệu tỷ lệ."
            
        # 2. Import hàm DB và cập nhật
        # (Import ở đây để tránh lỗi circular import)
        try:
            from .db_manager import update_bridge_win_rate_batch
        except ImportError:
            from db_manager import update_bridge_win_rate_batch
            
        success, message = update_bridge_win_rate_batch(rate_data_list, db_name)
        
        if success:
            return len(rate_data_list), message
        else:
            return 0, message

    except Exception as e:
        return 0, f"Lỗi nghiêm trọng trong run_and_update_all_bridge_rates: {e}"

# ===================================================================================
# (MỚI GĐ 1) HÀM NGHIỆP VỤ CẬP NHẬT K2N CACHE
# ===================================================================================

def _parse_k2n_results(results_data):
    """
    (CẬP NHẬT GĐ 4) Hàm nội bộ: Phân tích kết quả 4 hàng từ backtest K2N.
    Trả về: 
    - list các tuple: [(win_rate, streak, prediction, max_lose_streak, bridge_name), ...]
    - dict (chỉ cho Bảng Tổng Hợp): { 'Cầu 1': {'stl': '01,10', 'streak': '3 khung', 'max_lose': 5} }
    """
    cache_data_list = []
    pending_k2n_dict = {}
    
    if not results_data or len(results_data) < 4:
        print("Lỗi _parse_k2n_results: Dữ liệu backtest K2N không hợp lệ.")
        return cache_data_list, pending_k2n_dict
        
    try:
        headers = results_data[0] # Hàng 0: Tên cầu
        rates = results_data[1]   # Hàng 1: Tỷ Lệ %
        streaks = results_data[2] # Hàng 2: Chuỗi Thắng / Thua Max
        pending = results_data[3] # Hàng 3: Dự đoán
        
        num_bridges = len(headers) - 1 # Trừ cột "Kỳ"
        
        for j in range(1, num_bridges + 1):
            bridge_name = str(headers[j]).split(' (')[0] # Lấy tên gốc
            
            # 1. Lấy Tỷ lệ
            win_rate_text = str(rates[j])
            
            # 2. (SỬA GĐ 4) Lấy Chuỗi Thắng và Chuỗi Thua Max
            streak_text_full = str(streaks[j]) # "3 thắng / 5 thua"
            current_streak = 0
            max_lose_streak = 0
            try:
                parts = streak_text_full.split(' / ')
                current_streak = int(parts[0].split(' ')[0])
                max_lose_streak = int(parts[1].split(' ')[0])
            except Exception:
                pass # Giữ giá trị 0
                
            # 3. Lấy Dự đoán
            pending_text = str(pending[j])
            next_prediction_stl = "LỖI"
            
            if "(Đang chờ N2)" in pending_text:
                next_prediction_stl = pending_text.split(' (')[0]
                # (SỬA GĐ 4) Thêm max_lose vào dict cho Bảng Tổng Hợp
                pending_k2n_dict[bridge_name] = {
                    'stl': next_prediction_stl,
                    'streak': f"{current_streak} khung",
                    'max_lose': max_lose_streak
                }
            elif "(Khung mới N1)" in pending_text:
                next_prediction_stl = pending_text.split(' (')[0]
            
            # 4. (SỬA GĐ 4) Thêm max_lose_streak vào danh sách cache
            cache_data_list.append((
                win_rate_text,
                current_streak,
                next_prediction_stl,
                max_lose_streak, # Thêm cột mới
                bridge_name
            ))
            
    except Exception as e:
        print(f"Lỗi _parse_k2n_results: {e}")
        
    return cache_data_list, pending_k2n_dict

def run_and_update_all_bridge_K2N_cache(all_data_ai, db_name=DB_NAME, data_slice=None, write_to_db=True):
    """
    (CẬP NHẬT GĐ 10) Chạy backtest K2N (đã tối ưu).
    - data_slice: (MỚI) Cho phép chạy trên một phần dữ liệu (dùng cho Tối ưu hóa)
    - write_to_db: (MỚI) Cho phép không ghi vào CSDL (dùng cho Tối ưu hóa)
    """
    try:
        # (MỚI GĐ 10) Quyết định dùng data_slice hay all_data_ai
        data_to_use = data_slice if data_slice else all_data_ai
        
        if not data_to_use:
            return {}, "Không có dữ liệu A:I để chạy backtest K2N cache."
            
        ky_bat_dau = 2
        ky_ket_thuc = len(data_to_use) + (ky_bat_dau - 1)
        
        full_cache_data_list = []
        full_pending_k2n_dict = {}
        
        # --- 1. Chạy 15 Cầu Cổ Điển K2N (Tối ưu) ---
        if write_to_db: # Chỉ log khi chạy thực
            print("... (Cache K2N) Đang chạy 15 Cầu Cổ Điển K2N (tối ưu)...")
        results_15_cau = BACKTEST_15_CAU_K2N_V30_AI_V8(data_to_use, ky_bat_dau, ky_ket_thuc, history=False)
        
        cache_list_15, pending_dict_15 = _parse_k2n_results(results_15_cau)
        full_cache_data_list.extend(cache_list_15)
        full_pending_k2n_dict.update(pending_dict_15)
        if write_to_db:
            print(f"... (Cache K2N) Đã phân tích {len(cache_list_15)} cầu CĐ.")

        # --- 2. Chạy Cầu Đã Lưu K2N (Tối ưu) ---
        if write_to_db:
            print("... (Cache K2N) Đang chạy Cầu Đã Lưu K2N (tối ưu)...")
        results_managed = BACKTEST_MANAGED_BRIDGES_K2N(data_to_use, ky_bat_dau, ky_ket_thuc, db_name, history=False)
        
        if results_managed and "LỖI" not in str(results_managed[0][0]):
            cache_list_managed, pending_dict_managed = _parse_k2n_results(results_managed)
            full_cache_data_list.extend(cache_list_managed)
            full_pending_k2n_dict.update(pending_dict_managed)
            if write_to_db:
                print(f"... (Cache K2N) Đã phân tích {len(cache_list_managed)} cầu đã lưu.")
        else:
            if write_to_db:
                print("... (Cache K2N) Bỏ qua Cầu Đã Lưu (không có cầu nào hoặc bị lỗi).")

        # --- 3. Cập nhật CSDL (Nếu được phép) ---
        if not full_cache_data_list:
            return {}, "Không có dữ liệu cache K2N nào để cập nhật."
        
        if write_to_db:
            print(f"... (Cache K2N) Đang cập nhật {len(full_cache_data_list)} bản ghi cache vào CSDL...")
            success, message = update_bridge_k2n_cache_batch(full_cache_data_list, db_name)
            
            if success:
                return full_pending_k2n_dict, message 
            else:
                return {}, message
        else:
            # (MỚI GĐ 10) Chỉ trả về kết quả, không ghi DB
            return full_pending_k2n_dict, f"Mô phỏng Cache K2N hoàn tất ({len(full_cache_data_list)} cầu)."

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {}, f"Lỗi nghiêm trọng trong run_and_update_all_bridge_K2N_cache: {e}"


# ===================================================================================
# (MỚI) CÁC HÀM TỰ ĐỘNG HÓA DÒ CẦU (Đã sửa lỗi index)
# ===================================================================================

def find_and_auto_manage_bridges(all_data_ai, db_name):
    """
    (NÂNG CẤP GĐ 2) Chạy dò cầu V17 + Bạc Nhớ và tự động cập nhật CSDL.
    """
    # Import nội bộ
    try:
        from .db_manager import upsert_managed_bridge, get_all_managed_bridges
    except ImportError:
        from db_manager import upsert_managed_bridge, get_all_managed_bridges
        
    # (MỚI GĐ 8) Đọc ngưỡng từ SETTINGS
    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE

    added_count = 0
    updated_count = 0
    
    try:
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(all_data_ai) + (ky_bat_dau_kiem_tra - 1)
        
        # --- (MỚI GĐ 2) Bước 1: Chạy cả hai hệ thống dò cầu ---
        
        # 1a. Dò cầu V17 (23k cầu)
        results_v17 = TIM_CAU_TOT_NHAT_V16(all_data_ai, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name)
        
        # 1b. Dò cầu Bạc Nhớ (756 cầu)
        results_memory = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)

        # 1c. Gộp kết quả (Bỏ qua hàng tiêu đề [0] của mỗi hàm)
        combined_results_data = []
        if results_v17 and len(results_v17) > 1:
            # Bỏ qua hàng '---' và 'HOÀN THÀNH' ở cuối
            combined_results_data.extend([row for row in results_v17[1:] if "---" not in str(row[0])])
        else:
            print("Cảnh báo: Dò cầu V17 không trả về dữ liệu.")
            
        if results_memory and len(results_memory) > 1:
            combined_results_data.extend([row for row in results_memory[1:] if "---" not in str(row[0])])
        else:
             print("Cảnh báo: Dò cầu Bạc Nhớ không trả về dữ liệu.")

        if not combined_results_data:
            return "Lỗi: Cả hai hệ thống dò cầu (V17 & Bạc Nhớ) đều không trả về dữ liệu."
            
        # Lấy danh sách cầu đã có để so sánh
        existing_bridges = {b['name'] for b in get_all_managed_bridges(db_name)}
        
        # --- (MỚI GĐ 2) Bước 2: Duyệt kết quả TỔNG HỢP và "Upsert" ---
        print(f"... (Dò Cầu Tự Động) Đã gộp {len(combined_results_data)} cầu. Bắt đầu lọc và lưu...")
        
        for row in combined_results_data: 
            try:
                if len(row) < 4:
                    continue

                bridge_name = str(row[1])
                win_rate_str = str(row[3]).replace('%', '')

                try:
                    win_rate = float(win_rate_str)
                except ValueError:
                    continue 

                # Áp dụng bộ lọc Tỷ lệ
                if win_rate >= AUTO_ADD_MIN_RATE:
                    
                    # (SỬA GĐ 2) Thêm loại cầu vào mô tả
                    desc_prefix = "Tự động (V17)"
                    if "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
                        desc_prefix = "Tự động (BN)"
                        
                    desc = f"{desc_prefix} (Tỷ lệ: {win_rate_str}%)"
                    
                    # Gọi hàm Upsert (chỉ lưu tỷ lệ N1)
                    success, msg = upsert_managed_bridge(bridge_name, desc, f"{win_rate_str}%", db_name)
                    
                    if success:
                        if bridge_name in existing_bridges:
                            updated_count += 1
                        else:
                            added_count += 1
                            
            except Exception as e_row:
                import traceback
                print(f"Lỗi xử lý hàng: {row}, Lỗi: {e_row}")
                print(traceback.format_exc())
                
        return f"Hoàn tất Dò Cầu Tổng Hợp: Thêm {added_count} cầu mới và cập nhật {updated_count} cầu (V17 + BN)."

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return f"LỖI find_and_auto_manage_bridges: {e}"

def prune_bad_bridges(all_data_ai, db_name):
    """
    (NÂNG CẤP GĐ 2) Chạy backtest Cầu Đã Lưu và tự động TẮT các cầu kém hiệu quả
    (Sử dụng cache K2N thay vì chạy lại N1)
    """
    # Import nội bộ
    try:
        from .db_manager import get_all_managed_bridges, update_managed_bridge
    except ImportError:
        from db_manager import get_all_managed_bridges, update_managed_bridge
        
    # (MỚI GĐ 8) Đọc ngưỡng từ SETTINGS
    AUTO_PRUNE_MIN_RATE = SETTINGS.AUTO_PRUNE_MIN_RATE
        
    disabled_count = 0
    try:
        # (SỬA GĐ 2) Dùng Cache K2N thay vì chạy lại N1
        # Lấy danh sách cầu đã lưu (bao gồm cả ID và mô tả)
        managed_bridges_map = {b['name']: b for b in get_all_managed_bridges(db_name, only_enabled=True)}

        if not managed_bridges_map:
             return "Lỗi: Không có cầu nào được Bật để lọc."

        print(f"... (Lọc Cầu Yếu) Đang kiểm tra {len(managed_bridges_map)} cầu đã bật...")
        
        # Bước 2: Duyệt các cầu đã cache và lọc
        for bridge_name, bridge_data in managed_bridges_map.items():
            try:
                # (SỬA GĐ 2) Đọc tỷ lệ từ cache K2N
                win_rate_str = str(bridge_data.get('win_rate_text', '0%')).replace('%', '')
                
                # Bỏ qua nếu không có tỷ lệ (chưa chạy cache)
                if not win_rate_str or win_rate_str == "N/A":
                    continue
                    
                win_rate = float(win_rate_str)
                
                # Nếu cầu còn được bật (enabled) VÀ tỷ lệ thấp
                if win_rate < AUTO_PRUNE_MIN_RATE:
                    
                    bridge_id = bridge_data['id']
                    old_desc = bridge_data['description']
                    
                    # Gọi hàm update, set is_enabled = 0
                    update_managed_bridge(bridge_id, old_desc, 0, db_name)
                    disabled_count += 1
                    
            except Exception as e_row:
                print(f"Lỗi xử lý lọc cầu: {bridge_name}, Lỗi: {e_row}")

        return f"Hoàn tất: Đã tự động vô hiệu hóa {disabled_count} cầu kém hiệu quả (dựa trên cache K2N)."
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return f"LỖI prune_bad_bridges: {e}"

# ===================================================================================
# (MỚI) CÁC HÀM CHO BẢNG TỔNG HỢP QUYẾT ĐỊNH
# ===================================================================================

def get_loto_stats_last_n_days(all_data_ai, n=None):
    """
    (CẬP NHẬT GĐ 8) Lấy thống kê tần suất loto.
    Đọc 'n' từ SETTINGS nếu không được cung cấp.
    """
    try:
        # (MỚI GĐ 8) Đọc từ SETTINGS
        if n is None:
            n = SETTINGS.STATS_DAYS
            
        if not all_data_ai or len(all_data_ai) == 0:
            return []
            
        if len(all_data_ai) < n:
            n = len(all_data_ai)
        
        last_n_rows = all_data_ai[-n:]
        
        all_lotos_hits = [] 
        day_appearance_counter = Counter() 
        
        for row in last_n_rows:
            lotos_in_this_row = getAllLoto_V30(row)
            all_lotos_hits.extend(lotos_in_this_row)
            unique_lotos_in_this_row = set(lotos_in_this_row)
            day_appearance_counter.update(unique_lotos_in_this_row) 
        
        loto_hit_counts = Counter(all_lotos_hits)
        sorted_lotos_by_hits = sorted(loto_hit_counts.items(), key=lambda item: item[1], reverse=True)
        
        final_stats = []
        for loto, hit_count in sorted_lotos_by_hits:
            day_count = day_appearance_counter.get(loto, 0) 
            final_stats.append((loto, hit_count, day_count)) 
            
        return final_stats
        
    except Exception as e:
        print(f"Lỗi get_loto_stats_last_n_days (mới): {e}")
        return []

def get_prediction_consensus(last_row, db_name=DB_NAME):
    """
    (MỚI - SỬA LỖI GĐ 1) Lấy dự đoán từ "15 Cầu" (cache) và "Cầu Đã Lưu" (cache)
    để đếm vote THEO CẶP.
    """
    try:
        if not last_row or len(last_row) < 10:
            return []
            
        prediction_sources = {} 
        
        def get_pair_key(stl_list):
            if not stl_list or len(stl_list) != 2:
                return None
            sorted_pair = sorted(stl_list) 
            return f"{sorted_pair[0]}-{sorted_pair[1]}" 

        # (SỬA GĐ 1) Lấy từ 15 Cầu Cổ Điển + Cầu Đã Lưu (đã cache)
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
        
        if not managed_bridges:
            print("Cảnh báo Consensus: Không tìm thấy cầu nào trong CSDL.")
            return []
            
        for bridge in managed_bridges:
            try:
                # (SỬA GĐ 1) Đọc dự đoán N1 đã cache
                prediction_stl_str = bridge.get('next_prediction_stl')
                
                # Chỉ xử lý các cầu N1 (bỏ qua cầu chờ N2 hoặc lỗi)
                if not prediction_stl_str or \
                    'N2' in prediction_stl_str or \
                    'LỖI' in prediction_stl_str or \
                    ',' not in prediction_stl_str:
                    continue
                    
                stl = prediction_stl_str.split(',')
                pair_key = get_pair_key(stl)
                if not pair_key: continue
                    
                # Lấy tên (C1, C2... hoặc tên cầu V17)
                source_name = bridge["name"]
                
                # (SỬA LỖI GĐ 1) Sửa 'bridge_name' thành 'source_name'
                if source_name.startswith("Cầu "):
                     source_name = f"C{source_name.split(' ')[1]}"
                     
                if pair_key not in prediction_sources:
                    prediction_sources[pair_key] = []
                if source_name not in prediction_sources[pair_key]:
                    prediction_sources[pair_key].append(source_name)
            except Exception as e:
                print(f"Lỗi dự đoán Cầu (consensus cache) {bridge.get('name')}: {e}")
        
        # 3. Tổng hợp và Sắp xếp
        consensus_list = []
        for pair_key, sources in prediction_sources.items():
            count = len(sources)
            sources_str = ", ".join(sources)
            consensus_list.append((pair_key, count, sources_str))
            
        consensus_list.sort(key=lambda item: item[1], reverse=True)
        return consensus_list

    except Exception as e:
        print(f"Lỗi get_prediction_consensus (mới): {e}")
        return []

def get_high_win_rate_predictions(last_row, threshold=None, db_name=DB_NAME):
    """
    (CẬP NHẬT GĐ 8) Lấy dự đoán từ Cầu Đã Lưu CÓ TỶ LỆ CAO (dựa trên cache K2N).
    Đọc 'threshold' từ SETTINGS nếu không được cung cấp.
    """
    try:
        # (MỚI GĐ 8) Đọc từ SETTINGS
        if threshold is None:
            threshold = SETTINGS.HIGH_WIN_THRESHOLD
            
        if not last_row or len(last_row) < 10:
            return []
            
        high_win_bridges = []
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if not managed_bridges:
            return []
            
        for bridge in managed_bridges:
            try:
                # 1. Kiểm tra tỷ lệ (từ cache K2N)
                rate_str = str(bridge.get('win_rate_text', '0%')).replace('%', '')
                if not rate_str or rate_str == "N/A":
                    continue
                
                win_rate = float(rate_str)
                
                # 2. Nếu đạt ngưỡng
                if win_rate >= threshold:
                    # (SỬA GĐ 1) Lấy dự đoán từ cache
                    prediction_stl_str = bridge.get('next_prediction_stl')
                    
                    if not prediction_stl_str or \
                       'N2' in prediction_stl_str or \
                       'LỖI' in prediction_stl_str or \
                       ',' not in prediction_stl_str:
                        continue
                        
                    stl = prediction_stl_str.split(',')
                    
                    high_win_bridges.append({
                        'name': bridge['name'],
                        'stl': stl,
                        'rate': f"{win_rate:.2f}%"
                    })
            except Exception as e:
                print(f"Lỗi kiểm tra tỷ lệ cầu {bridge['name']}: {e}")
                
        return high_win_bridges
        
    except Exception as e:
        print(f"Lỗi get_high_win_rate_predictions: {e}")
        return []

def get_pending_k2n_bridges(last_row, prev_row, db_name=DB_NAME):
    """
    (MỚI) Lấy các cầu đã trượt N1 ở kỳ trước và đang chờ N2.
    - last_row: Hàng dữ liệu của kỳ quay MỚI NHẤT (để check hit).
    - prev_row: Hàng dữ liệu của kỳ TRƯỚC ĐÓ (để tạo dự đoán).
    Trả về: list[ {'name': str, 'stl': list[str]} ]
    """
    pending_bridges = []
    try:
        if not last_row or not prev_row:
            print("Cảnh báo K2N: Thiếu last_row hoặc prev_row.")
            return []
            
        # Loto trúng thưởng của kỳ mới nhất (để check)
        actualLotoSet = set(getAllLoto_V30(last_row))
        if not actualLotoSet:
             print("Cảnh báo K2N: Không có loto ở kỳ cuối.")
             return []
        
        # 1. Kiểm tra 15 Cầu Cổ Điển
        for i, bridge_func in enumerate(ALL_15_BRIDGE_FUNCTIONS_V5):
            try:
                # Dự đoán được tạo TỪ KỲ TRƯỚC ĐÓ
                stl = bridge_func(prev_row) 
                check_result = checkHitSet_V30_K2N(stl, actualLotoSet)
                
                # Nếu trượt N1
                if "❌" in check_result:
                    pending_bridges.append({
                        'name': f"Cầu {i+1}",
                        'stl': stl
                    })
            except Exception as e_inner:
                print(f"Lỗi K2N check (15 Cầu): {e_inner}")

        # 2. Kiểm tra Cầu Đã Lưu
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if managed_bridges:
            # (SỬA) Dùng hàm V17 mới
            # Vị trí TỪ KỲ TRƯỚC ĐÓ
            prev_positions = getAllPositions_V17_Shadow(prev_row)
            for bridge in managed_bridges:
                try:
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    a, b = prev_positions[idx1], prev_positions[idx2]
                    if a is None or b is None: continue
                    
                    stl = taoSTL_V30_Bong(a, b)
                    check_result = checkHitSet_V30_K2N(stl, actualLotoSet)
                    
                    if "❌" in check_result:
                        pending_bridges.append({
                            'name': bridge['name'],
                            'stl': stl
                        })
                except Exception as e_inner:
                    print(f"Lỗi K2N check (Cầu Đã Lưu): {e_inner}")
                    
        return pending_bridges

    except Exception as e:
        print(f"Lỗi get_pending_k2n_bridges: {e}")
        return []

# (MỚI) HÀM TÍNH ĐIỂM (Lấy từ analytics.py)
def _standardize_pair(stl_list):
    """Hàm nội bộ: Chuẩn hóa 1 cặp STL. Ví dụ ['30', '03'] -> '03-30'"""
    if not stl_list or len(stl_list) != 2:
        return None
    sorted_pair = sorted(stl_list) 
    return f"{sorted_pair[0]}-{sorted_pair[1]}" # Key: "03-30"

# (NÂNG CẤP GĐ 4) Cập nhật hàm chấm điểm (Quản lý Rủi ro)
def get_top_scored_pairs(stats, consensus, high_win, pending_k2n, gan_stats, top_memory_bridges, ai_predictions=None):
    """
    (NÂNG CẤP GĐ 4) Tính toán, chấm điểm và xếp hạng các cặp số.
    (NÂNG CẤP V6.2) Tích hợp AI làm nguồn chấm điểm.
    """
    try:
        # { '03-30': {'score': 0.0, 'reasons': [], 'is_gan': False, 'gan_days': 0} }
        scores = {}
        
        # (MỚI GĐ 8) Lấy ngưỡng từ SETTINGS
        HIGH_WIN_THRESHOLD = SETTINGS.HIGH_WIN_THRESHOLD
        K2N_RISK_START_THRESHOLD = SETTINGS.K2N_RISK_START_THRESHOLD
        K2N_RISK_PENALTY_PER_FRAME = SETTINGS.K2N_RISK_PENALTY_PER_FRAME
        
        # (MỚI V6.2) Tạo map tra cứu AI và Ngưỡng
        loto_prob_map = {}
        ai_prob_threshold = 50.0 # Ngưỡng AI (có thể đưa ra config.json sau)
        
        if ai_predictions:
            for pred in ai_predictions:
                loto_prob_map[pred['loto']] = pred['probability']
        
        # ... (Hàm phụ _parse_rate, _parse_streak) ...
        # ... (Nguồn 1: top_hot_lotos, Nguồn 2: gan_map) ...
        
        # --- 3. Chấm điểm từ 4 nguồn chính ---
        
        # (Nguồn 2: Consensus) ...
        # (Nguồn 3: Cầu Tỷ Lệ Cao) ...
        # (Nguồn 4: Cầu K2N Đang Chờ) ...
        # (Nguồn 5: Cầu Bạc Nhớ) ...
        
        # (Code chấm điểm cho 4 nguồn trên giữ nguyên)
        # ... (Dán code của 4 nguồn đó vào đây) ...

        # --- 4. Chấm điểm cộng (Loto Về Nhiều) và Gắn cờ (Lô Gan) ---
        
        # (MỚI V6.2) Tạo danh sách các cặp đã xử lý (để AI không lặp lại)
        processed_pairs = set(scores.keys())

        for pair_key in list(scores.keys()):
            loto1, loto2 = pair_key.split('-')
            
            # (Nguồn 1: Loto Về Nhiều) - (Giữ nguyên 1 điểm)
            if loto1 in top_hot_lotos or loto2 in top_hot_lotos:
                scores[pair_key]['score'] += 1.0
                scores[pair_key]['reasons'].append("Loto Hot")
                
            # (Nguồn 6: Gắn cờ Gan)
            gan_days_1 = gan_map.get(loto1, 0)
            gan_days_2 = gan_map.get(loto2, 0)
            max_gan = max(gan_days_1, gan_days_2)
            
            if max_gan > 0:
                scores[pair_key]['is_gan'] = True
                scores[pair_key]['gan_days'] = max_gan

            # (MỚI V6.2) Nguồn 7: Chấm điểm AI
            if loto_prob_map:
                prob_1 = loto_prob_map.get(loto1, 0.0)
                prob_2 = loto_prob_map.get(loto2, 0.0)
                max_prob = max(prob_1, prob_2)
                
                if max_prob >= ai_prob_threshold:
                    # Chấm điểm động cho AI: +1 điểm, cộng thêm 0.1 cho mỗi 1% trên ngưỡng
                    ai_score_bonus = 1.0 + ((max_prob - ai_prob_threshold) * 0.1)
                    scores[pair_key]['score'] += ai_score_bonus
                    scores[pair_key]['reasons'].append(f"AI > {max_prob:.1f}%")

        # (MỚI V6.2) Thêm các cặp SẠCH (Chỉ AI phát hiện)
        if loto_prob_map:
            for loto, prob in loto_prob_map.items():
                if prob >= ai_prob_threshold:
                    # Tạo các cặp cho loto này (ví dụ: loto '68')
                    # '00-68', '01-68', ..., '67-68', '68-69', ..., '68-99'
                    pairs_with_loto = [f"{str(i).zfill(2)}-{loto}" for i in range(int(loto))] + \
                                      [f"{loto}-{str(i).zfill(2)}" for i in range(int(loto), 100)]
                    
                    for pair_key in pairs_with_loto:
                        if pair_key not in processed_pairs: # Nếu là cặp mới mà V5 bỏ lỡ
                            if pair_key not in scores:
                                scores[pair_key] = {'score': 0.0, 'reasons': [], 'is_gan': False, 'gan_days': 0}
                            
                            # Chấm điểm động
                            ai_score_bonus = 1.0 + ((prob - ai_prob_threshold) * 0.1)
                            scores[pair_key]['score'] += ai_score_bonus
                            scores[pair_key]['reasons'].append(f"Chỉ AI > {prob:.1f}%")
                            
                            # Kiểm tra Gan cho cặp mới này
                            l1, l2 = pair_key.split('-')
                            gan_days_1 = gan_map.get(l1, 0)
                            gan_days_2 = gan_map.get(l2, 0)
                            max_gan = max(gan_days_1, gan_days_2)
                            if max_gan > 0:
                                scores[pair_key]['is_gan'] = True
                                scores[pair_key]['gan_days'] = max_gan

        # --- 5. Định dạng lại và Sắp xếp ---
        final_list = []
        for pair_key, data in scores.items():
            final_list.append({
                'pair': pair_key,
                'score': round(data['score'], 2),
                'reasons': ", ".join(data['reasons']),
                'is_gan': data['is_gan'],
                'gan_days': data['gan_days']
            })
            
        final_list.sort(key=lambda x: x['score'], reverse=True)
        
        return final_list

    except Exception as e:
        import traceback
        print(f"LỖI get_top_scored_pairs: {e}")
        print(traceback.format_exc())
        return []

# (MỚI) HÀM LÔ GAN (Lấy từ analytics.py)
def get_loto_gan_stats(all_data_ai, n_days=None):
    """
    (CẬP NHẬT GĐ 8) Tìm các loto (00-99) đã không xuất hiện trong n_days gần nhất.
    Đọc 'n_days' từ SETTINGS nếu không được cung cấp.
    """
    gan_stats = []
    try:
        # (MỚI GĐ 8) Đọc từ SETTINGS
        if n_days is None:
            n_days = SETTINGS.GAN_DAYS
            
        if not all_data_ai or len(all_data_ai) < n_days:
            print(f"Cảnh báo Lô Gan: Không đủ dữ liệu (cần {n_days} kỳ).")
            return []
            
        all_100_lotos = {str(i).zfill(2) for i in range(100)}
        
        recent_lotos = set()
        recent_rows = all_data_ai[-n_days:]
        for row in recent_rows:
            lotos_in_this_row = getAllLoto_V30(row)
            recent_lotos.update(lotos_in_this_row)
            
        gan_lotos = all_100_lotos - recent_lotos
        
        if not gan_lotos:
            return [] 

        full_history = all_data_ai[:] 
        full_history.reverse() 
        
        for loto in gan_lotos:
            days_gan = 0
            found = False
            for i, row in enumerate(full_history):
                if i < n_days: 
                    days_gan += 1
                    continue
                
                loto_set_this_day = set(getAllLoto_V30(row))
                if loto in loto_set_this_day:
                    found = True
                    break 
                else:
                    days_gan += 1 
            
            if found:
                gan_stats.append((loto, days_gan))
            else:
                gan_stats.append((loto, len(full_history)))

        gan_stats.sort(key=lambda x: x[1], reverse=True)
        return gan_stats

    except Exception as e:
        print(f"Lỗi get_loto_gan_stats: {e}")
        return []


# ===================================================================================
# (MỚI) HÀM BACKTEST CHO CẦU BẠC NHỚ (756 CẦU)
# ===================================================================================

# Import các hàm Bạc Nhớ từ file mới
try:
    from .bridges_memory import (
        get_27_loto_names,
        get_27_loto_positions,
        calculate_bridge_stl
    )
except ImportError:
    from bridges_memory import (
        get_27_loto_names,
        get_27_loto_positions,
        calculate_bridge_stl
    )

def BACKTEST_MEMORY_BRIDGES(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    """
    (MỚI) Chạy backtest cho 756 Cầu Bạc Nhớ (27x27 Cầu Tổng + 27x27 Cầu Hiệu).
    """
    print("Bắt đầu Backtest 756 Cầu Bạc Nhớ...")
    
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error

    loto_names = get_27_loto_names()
    num_positions = len(loto_names) # = 27
    
    algorithms = [] 
    headers = ["Kỳ (Cột A)"]
    
    for i in range(num_positions):
        for j in range(i, num_positions):
            name_sum = f"Tổng({loto_names[i]} + {loto_names[j]})"
            headers.append(name_sum)
            algorithms.append((i, j, 'sum', name_sum))
            
            name_diff = f"Hiệu(|{loto_names[i]} - {loto_names[j]}|)"
            headers.append(name_diff)
            algorithms.append((i, j, 'diff', name_diff))

    num_algorithms = len(algorithms) # = 756
    results = [headers]
    
    print(f"Đã tạo {num_algorithms} thuật toán Bạc Nhớ. Bắt đầu tiền xử lý...")

    processedData = []
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not prevRow or not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "" or len(actualRow) < 10 or not actualRow[9]:
            processedData.append({"soKy": actualRow[0] or k, "error": True})
            continue
        
        processedData.append({
          "soKy": actualRow[0] or k,
          "error": False,
          "prevLotos": get_27_loto_positions(prevRow),
          "actualLotoSet": set(getAllLoto_V30(actualRow))
        })
    
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
        finalRowK = f"Kỳ {int(last_data_row[0]) + 1}" if last_data_row[0].isdigit() else f"Kỳ {finalEndRow + 1}"
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


# (MỚI GĐ 2) HÀM DÒ CẦU BẠC NHỚ
def TIM_CAU_BAC_NHO_TOT_NHAT(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    """
    (MỚI GĐ 2) Dò 756 Cầu Bạc Nhớ và trả về kết quả (không lọc)
    để đưa vào hàm Tự động Dò Cầu.
    """
    print("... (Dò Cầu Tự Động) Bắt đầu Dò 756 Cầu Bạc Nhớ...")
    
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error

    loto_names = get_27_loto_names()
    num_positions = len(loto_names) # = 27
    
    algorithms = [] # (index1, index2, 'loại', 'tên')
    for i in range(num_positions):
        for j in range(i, num_positions):
            # TỔNG
            name_sum = f"Tổng({loto_names[i]} + {loto_names[j]})"
            algorithms.append((i, j, 'sum', name_sum))
            # HIỆU
            name_diff = f"Hiệu(|{loto_names[i]} - {loto_names[j]}|)"
            algorithms.append((i, j, 'diff', name_diff))

    num_algorithms = len(algorithms) # = 756
    
    processedData = []
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not prevRow or not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "" or len(actualRow) < 10 or not actualRow[9]:
            continue
        processedData.append({
            "prevLotos": get_27_loto_positions(prevRow),
            "actualLotoSet": set(getAllLoto_V30(actualRow))
        })
    
    totalTestDays = len(processedData)
    if totalTestDays == 0: 
        print("Lỗi TIM_CAU_BAC_NHO: Không có dữ liệu test")
        return [["LỖI:", "Không có dữ liệu hợp lệ để backtest."]]
        
    win_counts = [0] * num_algorithms

    for dayData in processedData:
        actualLotoSet = dayData["actualLotoSet"]
        prevLotos = dayData["prevLotos"]
        for j in range(num_algorithms):
            alg = algorithms[j]
            idx1, idx2, alg_type = alg[0], alg[1], alg[2]
            loto1, loto2 = prevLotos[idx1], prevLotos[idx2]
            pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
            if pred_stl[0] in actualLotoSet or pred_stl[1] in actualLotoSet:
                win_counts[j] += 1

    # Định dạng lại kết quả giống hệt TIM_CAU_TOT_NHAT_V16
    output = [["Hạng", "Tên Cầu", "Trúng/Tổng", "Tỷ lệ"]]
    results_list = []
    for j in range(num_algorithms):
        alg_name = algorithms[j][3]
        hits = win_counts[j]
        rate = (hits / totalTestDays) * 100 if totalTestDays > 0 else 0
        results_list.append({
            'name': alg_name,
            'hits': hits,
            'rate': rate,
            'hit_str': f"{hits}/{totalTestDays}",
            'rate_str': f"{rate:.2f}%"
        })
    
    results_list.sort(key=lambda x: x["hits"], reverse=True)
    
    for index, res in enumerate(results_list):
        output.append([
            index + 1,
            res["name"],
            res["hit_str"],
            res["rate_str"]
        ])
        
    print(f"... (Dò Cầu Tự Động) Hoàn tất Dò Cầu Bạc Nhớ ({len(output)-1} cầu).")
    return output


# ===================================================================================
# (MỚI) HÀM HỖ TRỢ BẢNG TỔNG HỢP (NÂNG CẤP BẠC NHỚ)
# ===================================================================================

def get_top_memory_bridge_predictions(all_data_ai, last_row, top_n=5):
    """
    (MỚI) Chạy backtest N1 756 cầu bạc nhớ NGẦM và trả về
    dự đoán của TOP N cầu tốt nhất.
    """
    print("... (BTH) Bắt đầu chạy backtest 756 cầu Bạc Nhớ ngầm...")
    
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(all_data_ai, 2, len(all_data_ai) + 1)
    if error: 
        print(f"Lỗi get_top_memory_bridge_predictions (validate): {error}")
        return []

    loto_names = get_27_loto_names()
    num_positions = len(loto_names) # = 27
    
    algorithms = [] # (index1, index2, 'loại')
    for i in range(num_positions):
        for j in range(i, num_positions):
            algorithms.append((i, j, 'sum'))
            algorithms.append((i, j, 'diff'))

    num_algorithms = len(algorithms) # = 756
    
    processedData = []
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not prevRow or not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "" or len(actualRow) < 10 or not actualRow[9]:
            continue
        processedData.append({
          "prevLotos": get_27_loto_positions(prevRow),
          "actualLotoSet": set(getAllLoto_V30(actualRow))
        })
    
    totalTestDays = len(processedData)
    if totalTestDays == 0: 
        print("Lỗi get_top_memory_bridge_predictions: Không có dữ liệu test")
        return []
        
    win_counts = [0] * num_algorithms

    for dayData in processedData:
        actualLotoSet = dayData["actualLotoSet"]
        prevLotos = dayData["prevLotos"]
        
        for j in range(num_algorithms):
            alg = algorithms[j]
            idx1, idx2, alg_type = alg[0], alg[1], alg[2]
            loto1, loto2 = prevLotos[idx1], prevLotos[idx2]
            pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
            
            if pred_stl[0] in actualLotoSet or pred_stl[1] in actualLotoSet:
                win_counts[j] += 1

    bridge_stats = [] # list of (rate, index)
    for j in range(num_algorithms):
        rate = (win_counts[j] / totalTestDays) * 100
        bridge_stats.append( (rate, j) )
        
    bridge_stats.sort(key=lambda x: x[0], reverse=True) 
    
    top_n_bridges = bridge_stats[:top_n]
    
    predictions_for_dashboard = []
    last_lotos = get_27_loto_positions(last_row)
    
    for rate, alg_index in top_n_bridges:
        alg = algorithms[alg_index]
        idx1, idx2, alg_type = alg[0], alg[1], alg[2]
        
        loto1, loto2 = last_lotos[idx1], last_lotos[idx2]
        pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
        
        if alg_type == 'sum':
            name = f"Tổng({loto_names[idx1]}+{loto_names[idx2]})"
        else:
            name = f"Hiệu(|{loto_names[idx1]}-{loto_names[idx2]}|)"
            
        predictions_for_dashboard.append({
            'name': name,
            'stl': pred_stl,
            'rate': f"{rate:.2f}%"
        })
        
    print(f"... (BTH) Backtest Bạc Nhớ hoàn tất. Trả về {len(predictions_for_dashboard)} dự đoán.")
    return predictions_for_dashboard

# ===================================================================================
# (MỚI GĐ 10) HÀM MÔ PHỎNG BẢNG TỔNG HỢP LỊCH SỬ
# ===================================================================================

def get_consensus_simulation(data_slice, last_row):
    """
    (MỚI GĐ 10) Bản sao của get_prediction_consensus
    Chạy N1 backtest trong bộ nhớ thay vì đọc cache CSDL.
    """
    prediction_sources = {} 
    
    def get_pair_key(stl_list):
        if not stl_list or len(stl_list) != 2: return None
        sorted_pair = sorted(stl_list) 
        return f"{sorted_pair[0]}-{sorted_pair[1]}" 

    # 1. Lấy từ 15 Cầu Cổ Điển
    for i, bridge_func in enumerate(ALL_15_BRIDGE_FUNCTIONS_V5):
        try:
            stl = bridge_func(last_row)
            pair_key = get_pair_key(stl)
            if not pair_key: continue
            source_name = f"C{i+1}"
            if pair_key not in prediction_sources:
                prediction_sources[pair_key] = []
            prediction_sources[pair_key].append(source_name)
        except Exception:
            pass # Bỏ qua lỗi trong mô phỏng

    # 2. Lấy từ Cầu Đã Lưu (chạy N1)
    bridges_to_test = get_all_managed_bridges(DB_NAME, only_enabled=True)
    if bridges_to_test:
        last_positions = getAllPositions_V17_Shadow(last_row)
        for bridge in bridges_to_test:
            try:
                idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                if idx1 == -1: continue # Bỏ qua cầu BN
                a, b = last_positions[idx1], last_positions[idx2]
                if a is None or b is None: continue
                
                stl = taoSTL_V30_Bong(a, b)
                pair_key = get_pair_key(stl)
                if not pair_key: continue
                    
                source_name = bridge["name"]
                if pair_key not in prediction_sources:
                    prediction_sources[pair_key] = []
                if source_name not in prediction_sources[pair_key]:
                    prediction_sources[pair_key].append(source_name)
            except Exception:
                pass # Bỏ qua
    
    consensus_list = []
    for pair_key, sources in prediction_sources.items():
        count = len(sources)
        sources_str = ", ".join(sources)
        consensus_list.append((pair_key, count, sources_str))
        
    consensus_list.sort(key=lambda item: item[1], reverse=True)
    return consensus_list

def get_high_win_simulation(data_slice, last_row, threshold):
    """
    (MỚI GĐ 10) Bản sao của get_high_win_rate_predictions
    Chạy K2N backtest trong bộ nhớ thay vì đọc cache CSDL.
    """
    high_win_bridges = []
    
    # 1. Chạy K2N Cache Mô phỏng
    cache_list, _ = _parse_k2n_results(
        BACKTEST_MANAGED_BRIDGES_K2N(data_slice, 2, len(data_slice) + 1, DB_NAME, history=False)
    )
    
    if not cache_list:
        return []
        
    # 2. Lọc kết quả
    for (win_rate_text, _, next_prediction_stl, _, bridge_name) in cache_list:
        try:
            win_rate = float(str(win_rate_text).replace('%', ''))
            
            if win_rate >= threshold:
                if not next_prediction_stl or \
                   'N2' in next_prediction_stl or \
                   'LỖI' in next_prediction_stl or \
                   ',' not in next_prediction_stl:
                    continue
                    
                stl = next_prediction_stl.split(',')
                high_win_bridges.append({
                    'name': bridge_name,
                    'stl': stl,
                    'rate': f"{win_rate:.2f}%"
                })
        except (ValueError, TypeError):
            continue
            
    return high_win_bridges

def get_historical_dashboard_data(all_data_ai, day_index, temp_settings):
    """
    (MỚI GĐ 10) Hàm "chủ" để mô phỏng Bảng Tổng Hợp tại một ngày trong quá khứ.
    """
    
    # 1. Cắt lát dữ liệu
    data_slice = all_data_ai[:day_index + 1]
    if len(data_slice) < 2:
        return None 
    
    last_row = data_slice[-1]
    
    # 2. Lấy các giá trị cài đặt tạm thời
    n_days_stats = int(temp_settings.get("STATS_DAYS", 7))
    n_days_gan = int(temp_settings.get("GAN_DAYS", 15))
    high_win_thresh = float(temp_settings.get("HIGH_WIN_THRESHOLD", 47.0))
    
    # 3. Chạy 7 hệ thống (phiên bản mô phỏng)
    
    # (1) Loto Hot
    stats_n_day = get_loto_stats_last_n_days(data_slice, n=n_days_stats)
    
    # (2) Cache K2N (để lấy pending)
    pending_k2n_data, _ = run_and_update_all_bridge_K2N_cache(
        all_data_ai=None, 
        data_slice=data_slice, 
        write_to_db=False # Quan trọng: Không ghi CSDL
    )
    
    # (3) Consensus (Vote)
    consensus = get_consensus_simulation(data_slice, last_row)
    
    # (4) Cầu Tỷ Lệ Cao
    high_win = get_high_win_simulation(data_slice, last_row, threshold=high_win_thresh)

    # (5) Cầu Bạc Nhớ
    top_memory_bridges = get_top_memory_bridge_predictions(data_slice, last_row, top_n=5)
    
    # (6) Lô Gan
    gan_stats = get_loto_gan_stats(data_slice, n_days=n_days_gan)
    
    # (7) Chấm điểm
    top_scores = get_top_scored_pairs(
        stats_n_day,
        consensus, 
        high_win, 
        pending_k2n_data, 
        gan_stats,
        top_memory_bridges 
    )
    
    return top_scores