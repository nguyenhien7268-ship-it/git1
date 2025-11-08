import sqlite3

# Import các hàm DB
try:
    from .db_manager import DB_NAME, get_all_managed_bridges, update_bridge_win_rate_batch
except ImportError:
    try:
        from db_manager import DB_NAME, get_all_managed_bridges, update_bridge_win_rate_batch
    except ImportError:
        print("Lỗi: Không thể import db_manager trong backtester.py")
        DB_NAME = 'xo_so_prizes_all_logic.db'
        def get_all_managed_bridges(d, o): return []
        def update_bridge_win_rate_batch(r, d): return False, "Lỗi Import"

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

# Import các hàm cầu V16
try:
    from .bridges_v16 import (
        getAllPositions_V16, 
        getPositionName_V16, 
        get_index_from_name_V16,
        taoSTL_V30_Bong
    )
except ImportError:
    try:
        from bridges_v16 import (
            getAllPositions_V16, 
            getPositionName_V16, 
            get_index_from_name_V16,
            taoSTL_V30_Bong
        )
    except ImportError:
        print("Lỗi: Không thể import bridges_v16 trong backtester.py")
        def getAllPositions_V16(r): return []
        def getPositionName_V16(i): return "Lỗi"
        def get_index_from_name_V16(n): return None
        def taoSTL_V30_Bong(a, b): return ['00', '00']


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

def BACKTEST_15_CAU_K2N_V30_AI_V8(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    """ (CẬP NHẬT) Sắp xếp giảm dần + Dự đoán ở trên + Thêm đếm Chuỗi (Streak) """
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error
    headers = ["Kỳ (Cột A)", "Cầu 1 (Đề+5)", "Cầu 2 (G6+G7)", "Cầu 3 (GĐB+G1)", 
               "Cầu 4 (GĐB+G1)", "Cầu 5 (G7+G7)", "Cầu 6 (G7+G7)", 
               "Cầu 7 (G5+G7)", "Cầu 8 (G3+G4)", "Cầu 9 (GĐB+G1)",
               "Cầu 10 (G2+G3)", "Cầu 11 (GĐB+G3)", "Cầu 12 (GĐB+G3)",
               "Cầu 13 (G7.3+8)", "Cầu 14 (G1+2)", "Cầu 15 (Đề+7)", "Tổng Trúng"]
    results = [headers]
    
    # (MỚI) Biến theo dõi K2N
    in_frame = [False] * 15
    prediction_in_frame = [None] * 15
    current_streak_k2n = [0] * 15 # (MỚI) Đếm chuỗi K2N
    
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
                if in_frame[j]:
                    # --- Đang ở Ngày 2 (N2) ---
                    pred = prediction_in_frame[j]
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        cell_output, totalHits = f"{','.join(pred)} ✅ (Ăn N2)", totalHits + 1
                        current_streak_k2n[j] += 1 # (MỚI) Thắng -> Tăng chuỗi
                    else:
                        cell_output = f"{','.join(pred)} ❌ (Trượt K2N)"
                        current_streak_k2n[j] = 0 # (MỚI) Gãy -> Reset chuỗi
                    in_frame[j], prediction_in_frame[j] = False, None
                else:
                    # --- Đang ở Ngày 1 (N1) ---
                    pred = cau_functions[j](prevRow)
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        cell_output, totalHits = f"{','.join(pred)} ✅ (Ăn N1)", totalHits + 1
                        current_streak_k2n[j] += 1 # (MỚI) Thắng -> Tăng chuỗi
                    else:
                        cell_output = f"{','.join(pred)} (Trượt N1...)"
                        # (MỚI) Chuỗi chưa bị reset, chờ N2
                        in_frame[j], prediction_in_frame[j] = True, pred
                daily_results_row.append(cell_output)
            daily_results_row.append(totalHits)
            data_rows.append(daily_results_row)
        except Exception as e:
            data_rows.append([actualSoKy, f"Lỗi: {e}"] + [""] * 15)
    
    # (CẬP NHẬT) Sắp xếp giảm dần
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
        results.insert(1, rate_row) # Chèn Tỷ Lệ vào dưới Header
        
        # (MỚI) Thêm hàng chuỗi K2N
        streak_row = ["Chuỗi K2N (khung)"]
        streak_row.extend([f"{s} khung" for s in current_streak_k2n])
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
    
    results.insert(3, finalRow) # (MỚI) Chèn hàng dự đoán ở vị trí 3
    results.extend(data_rows) # Thêm dữ liệu đã đảo ngược
    
    return results

def BACKTEST_15_CAU_N1_V31_AI_V8(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    """ (CẬP NHẬT) Backtest 15 Cầu Lô N1 (Sắp xếp giảm dần) """
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error
    headers = ["Kỳ (Cột A)", "Cầu 1 (Đề+5)", "Cầu 2 (G6+G7)", "Cầu 3 (GĐB+G1)", 
               "Cầu 4 (GĐB+G1)", "Cầu 5 (G7+G7)", "Cầu 6 (G7+G7)", 
               "Cầu 7 (G5+G7)", "Cầu 8 (G3+G4)", "Cầu 9 (GĐB+G1)",
               "Cầu 10 (G2+G3)", "Cầu 11 (GĐB+G3)", "Cầu 12 (GĐB+G3)",
               "Cầu 13 (G7.3+8)", "Cầu 14 (G1+2)", "Cầu 15 (Đề+7)", "Tổng Trúng"]
    results = [headers]
    cau_functions = ALL_15_BRIDGE_FUNCTIONS_V5
    
    data_rows = [] # (MỚI)
    
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
            
    data_rows.reverse() # Sắp xếp giảm dần
    
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
    
    results.insert(2, finalRow) # Chèn hàng dự đoán
    results.extend(data_rows) # Thêm dữ liệu
    
    return results

def TIM_CAU_TOT_NHAT_V16(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """(CẬP NHẬT) Lọc ra các cầu đã lưu."""
    print("Bắt đầu Dò Cầu Tốt Nhất V16...")
    
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
          "prevPositions": getAllPositions_V16(prevRow),
          "actualLotoSet": set(getAllLoto_V30(actualRow))
        })
    
    totalTestDays = len(processedData)
    if totalTestDays == 0: 
        return [["LỖI:", "Không có dữ liệu hợp lệ để backtest."]]

    print(f"Tiền xử lý hoàn tất. {totalTestDays} ngày test. Bắt đầu dò 5778 cầu...")
    allPositions = getAllPositions_V16(allData[0])
    numPositions = len(allPositions)
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
            pos1_name, pos2_name = getPositionName_V16(pos1_idx), getPositionName_V16(pos2_idx)
            results.append({"name": f"{pos1_name} + {pos2_name}", "hits": hits})
            combinationCount += 1
            if combinationCount % 500 == 0:
                print(f"Đã dò {combinationCount} / 5778 cầu...")
    
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
    output.append([f"HOÀN THÀNH: Đã chạy tất cả {combinationCount} cầu.", "", "", ""])
    print("Hoàn thành Dò Cầu V16.")
    return output

def BACKTEST_CUSTOM_CAU_V16(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, custom_bridge_name, mode):
    """ (CẬP NHẬT) Sắp xếp giảm dần """
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
        
        data_rows = [] # (MỚI)

        for k in range(startCheckRow, finalEndRow + 1):
            prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
            if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
            prevRow_data, actualRow = allData[prevRow_idx], allData[actualRow_idx]
            if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "": break
            if not prevRow_data or len(actualRow) < 10 or not actualRow[2] or not actualRow[9]:
                data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"])
                continue
            
            actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
            prevPositions = getAllPositions_V16(prevRow_data)
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
        
        data_rows.reverse() # Sắp xếp giảm dần
        results.extend(data_rows) # Thêm dữ liệu

        if totalTestDays > 0:
            rate = (win_count / totalTestDays) * 100
            results.insert(1, ["Tỷ Lệ %", f"{rate:.2f}% ({win_count}/{totalTestDays})"])
        
        if mode == 'K2N':
            finalRowK = f"Kỳ {int(allData[finalEndRow - offset][0]) + 1}" if allData[finalEndRow - offset][0].isdigit() else f"Kỳ {finalEndRow + 1}"
            final_cell = "---"
            if in_frame: final_cell = f"{','.join(prediction_in_frame)} (Đang chờ N2)"
            results.insert(2, [finalRowK, final_cell]) # Chèn hàng dự đoán
        
        return results
    except Exception as e:
        print(f"Lỗi BACKTEST_CUSTOM_CAU_V16: {e}")
        return [["LỖI:", str(e)]]

# (MỚI) HÀM BACKTEST CHO CÁC CẦU ĐÃ LƯU
def BACKTEST_MANAGED_BRIDGES_N1(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """(CẬP NHẬT) Chạy backtest N1 cho Cầu Đã Lưu (Sắp xếp giảm dần)"""
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
    
    data_rows = [] # (MỚI)
    
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "": break
        if not prevRow or len(actualRow) < 10 or not actualRow[2] or not actualRow[9]:
            data_rows.append([actualRow[0] or k, "Lỗi dữ liệu hàng"])
            continue
        
        actualSoKy, actualLotoSet = actualRow[0] or k, set(getAllLoto_V30(actualRow))
        prevPositions = getAllPositions_V16(prevRow)
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
            
    data_rows.reverse() # Sắp xếp giảm dần
    
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
        last_positions = getAllPositions_V16(last_data_row)
        
        for bridge in bridges_to_test:
            idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
            a, b = last_positions[idx1], last_positions[idx2]
            if a is None or b is None:
                finalRow.append("Lỗi Vị Trí")
                continue
            pred = taoSTL_V30_Bong(a, b)
            finalRow.append(f"{','.join(pred)} (Dự đoán N1)")
        
        results.insert(2, finalRow) # Chèn hàng dự đoán
        results.extend(data_rows) # Thêm dữ liệu
        
    except Exception as e:
        print(f"Lỗi dự đoán Cầu Đã Lưu: {e}")
        results.append(["LỖI DỰ ĐOÁN"])

    return results

# (MỚI) HÀM K2N CHO CẦU ĐÃ LƯU (VỚI STREAK)
def BACKTEST_MANAGED_BRIDGES_K2N(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """(MỚI) Chạy backtest K2N cho Cầu Đã Lưu + đếm chuỗi (streak)."""
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
        
    results = [headers] # (SỬA LỖI) KHỞI TẠO BIẾN RESULTS NGAY ĐÂY
    
    # (MỚI) Biến theo dõi K2N
    in_frame = [False] * num_bridges
    prediction_in_frame = [None] * num_bridges
    current_streak_k2n = [0] * num_bridges # Đếm chuỗi K2N
    
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
        prevPositions = getAllPositions_V16(prevRow)
        daily_results_row = [actualSoKy]
        
        for j, bridge in enumerate(bridges_to_test):
            try:
                if in_frame[j]:
                    # --- Đang ở Ngày 2 (N2) ---
                    pred = prediction_in_frame[j]
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    if "✅" in check_result:
                        cell_output = f"{','.join(pred)} ✅ (Ăn N2)"
                        current_streak_k2n[j] += 1
                    else:
                        cell_output = f"{','.join(pred)} ❌ (Trượt K2N)"
                        current_streak_k2n[j] = 0
                    in_frame[j], prediction_in_frame[j] = False, None
                else:
                    # --- Đang ở Ngày 1 (N1) ---
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    a, b = prevPositions[idx1], prevPositions[idx2]
                    if a is None or b is None:
                        daily_results_row.append("Lỗi Vị Trí")
                        continue
                    
                    pred = taoSTL_V30_Bong(a, b)
                    check_result = checkHitSet_V30_K2N(pred, actualLotoSet)
                    
                    if "✅" in check_result:
                        cell_output = f"{','.join(pred)} ✅ (Ăn N1)"
                        current_streak_k2n[j] += 1
                    else:
                        cell_output = f"{','.join(pred)} (Trượt N1...)"
                        in_frame[j], prediction_in_frame[j] = True, pred
                
                daily_results_row.append(cell_output)
            except Exception as e:
                daily_results_row.append(f"Lỗi: {e}")
        data_rows.append(daily_results_row)
            
    data_rows.reverse() # Sắp xếp giảm dần
    
    totalTestDays = len(data_rows)
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
        
        # (MỚI) Thêm hàng chuỗi K2N
        streak_row = ["Chuỗi K2N (khung)"]
        streak_row.extend([f"{s} khung" for s in current_streak_k2n])
        results.insert(2, streak_row) # Chèn Chuỗi
            
    try:
        last_data_row = allData[finalEndRow - offset]
        finalRowK = f"Kỳ {int(last_data_row[0]) + 1}" if last_data_row[0].isdigit() else f"Kỳ {finalEndRow + 1}"
        finalRow = [finalRowK]
        last_positions = getAllPositions_V16(last_data_row)
        
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
        
        results.insert(3, finalRow) # (MỚI) Chèn hàng dự đoán ở vị trí 3
        results.extend(data_rows) # Thêm dữ liệu
        
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
        
        # 1. Chạy backtest N1
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
# (MỚI) CÁC HÀM CHO BẢNG TỔNG HỢP QUYẾT ĐỊNH
# ===================================================================================

def get_loto_stats_last_n_days(all_data_ai, n=7):
    """
    (MỚI) Lấy thống kê tần suất loto trong N ngày gần nhất.
    Trả về: list[('loto', count_nhay, count_ky)], 
             ví dụ: [('33', 4, 3), ('01', 3, 3)]
             (Loto 33 về 4 nháy, xuất hiện trong 3/7 kỳ)
    """
    try:
        if not all_data_ai or len(all_data_ai) == 0:
            return []
            
        if len(all_data_ai) < n:
            n = len(all_data_ai)
        
        last_n_rows = all_data_ai[-n:]
        
        all_lotos_hits = [] # Để đếm tổng số nháy
        day_appearance_counter = Counter() # Để đếm tổng số kỳ (ngày)
        
        for row in last_n_rows:
            lotos_in_this_row = getAllLoto_V30(row)
            
            # 1. Đếm tổng số nháy (giống như cũ)
            all_lotos_hits.extend(lotos_in_this_row)
            
            # 2. Đếm số kỳ xuất hiện (mới)
            unique_lotos_in_this_row = set(lotos_in_this_row)
            day_appearance_counter.update(unique_lotos_in_this_row) # update 1 lần cho mỗi loto/kỳ
        
        # Đếm tổng số nháy
        loto_hit_counts = Counter(all_lotos_hits)
        
        # Sắp xếp theo tổng số nháy (ưu tiên)
        sorted_lotos_by_hits = sorted(loto_hit_counts.items(), key=lambda item: item[1], reverse=True)
        
        # Kết hợp dữ liệu
        final_stats = []
        for loto, hit_count in sorted_lotos_by_hits:
            day_count = day_appearance_counter.get(loto, 0) # Lấy số kỳ đã xuất hiện
            final_stats.append((loto, hit_count, day_count)) # (loto, tổng_nháy, tổng_kỳ)
            
        return final_stats
        
    except Exception as e:
        print(f"Lỗi get_loto_stats_last_n_days (mới): {e}")
        return []

def get_prediction_consensus(last_row, db_name=DB_NAME):
    """
    (MỚI) Lấy dự đoán từ "15 Cầu" và "Cầu Đã Lưu" để đếm vote THEO CẶP.
    Trả về: list[('cap_so', count, 'sources')]
    ví dụ: [('03-30', 2, 'C1, G5.6[3]')]
    """
    try:
        if not last_row or len(last_row) < 10:
            return []
            
        prediction_sources = {} # { 'pair_key': ['C1', 'GDB[0]...'] }
        
        def get_pair_key(stl_list):
            """Chuẩn hóa 1 cặp STL. Ví dụ ['30', '03'] -> '03-30'"""
            if not stl_list or len(stl_list) != 2:
                return None
            # Sắp xếp để chuẩn hóa, ví dụ ['30', '03'] -> ['03', '30']
            sorted_pair = sorted(stl_list) 
            return f"{sorted_pair[0]}-{sorted_pair[1]}" # Key: "03-30"

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
            except Exception as e:
                print(f"Lỗi dự đoán 15 Cầu (consensus): {e}")

        # 2. Lấy từ Cầu Đã Lưu
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if managed_bridges:
            last_positions = getAllPositions_V16(last_row)
            for bridge in managed_bridges:
                try:
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    a, b = last_positions[idx1], last_positions[idx2]
                    if a is None or b is None: continue
                    
                    stl = taoSTL_V30_Bong(a, b)
                    pair_key = get_pair_key(stl)
                    if not pair_key: continue
                        
                    source_name = bridge["name"]
                    if pair_key not in prediction_sources:
                        prediction_sources[pair_key] = []
                    # Chỉ thêm 1 lần cho 1 cầu (tránh trùng lặp)
                    if source_name not in prediction_sources[pair_key]:
                        prediction_sources[pair_key].append(source_name)
                except Exception as e:
                    print(f"Lỗi dự đoán Cầu Đã Lưu (consensus): {e}")
        
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

def get_high_win_rate_predictions(last_row, threshold=80.0, db_name=DB_NAME):
    """
    (MỚI) Lấy dự đoán từ các cầu CÓ TỶ LỆ CAO (dựa trên Cầu Đã Lưu).
    Trả về: list[ {'name': str, 'stl': list, 'rate': str} ]
    """
    try:
        if not last_row or len(last_row) < 10:
            return []
            
        high_win_bridges = []
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if not managed_bridges:
            return []
            
        last_positions = getAllPositions_V16(last_row)
        
        for bridge in managed_bridges:
            try:
                # 1. Kiểm tra tỷ lệ
                rate_str = str(bridge.get('win_rate_text', '0%')).replace('%', '')
                if not rate_str or rate_str == "N/A":
                    continue
                
                win_rate = float(rate_str)
                
                # 2. Nếu đạt ngưỡng
                if win_rate >= threshold:
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    a, b = last_positions[idx1], last_positions[idx2]
                    if a is None or b is None: continue
                    
                    stl = taoSTL_V30_Bong(a, b)
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
            # Vị trí TỪ KỲ TRƯỚC ĐÓ
            prev_positions = getAllPositions_V16(prev_row)
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