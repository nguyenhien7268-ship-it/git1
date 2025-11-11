import sqlite3
# Import SETTINGS
try:
    from ..config_manager import SETTINGS # ĐÃ SỬA (Lên 1 cấp)
except ImportError:
    from config_manager import SETTINGS
    # Fallback definition cho SETTINGS
    SETTINGS = type('obj', (object,), {
        'AUTO_ADD_MIN_RATE': 50.0, 
        'AUTO_PRUNE_MIN_RATE': 40.0
    })

# Import DB functions (CRUD và Management)
try:
    from ..db_manager import ( # ĐÃ SỬA (Lên 1 cấp)
        DB_NAME, 
        upsert_managed_bridge, 
        update_managed_bridge
    )
    # Import từ Repository
    from ..data_repository import get_all_managed_bridges # ĐÃ SỬA (Lên 1 cấp)
except ImportError:
    # Fallback cho DB/Repo
    print("Lỗi: Không thể import db_manager/data_repository trong bridge_manager_core.py")
    DB_NAME = 'data/xo_so_prizes_all_logic.db' # <--- ĐÃ SỬA
    def upsert_managed_bridge(n, d, r, db): return False, "Lỗi Import"
    def update_managed_bridge(id, d, e, db): return False, "Lỗi Import"
    def get_all_managed_bridges(d, o): return []

# Import Bridge Logic và Helpers (Các import này là TƯƠNG ĐỐI VỊ TRÍ, nên giữ nguyên)
try:
    from .bridges_v16 import ( # GIỮ NGUYÊN
        taoSTL_V30_Bong,
        getAllPositions_V17_Shadow,
        getPositionName_V17_Shadow
    )
    from .bridges_classic import getAllLoto_V30 # GIỮ NGUYÊN
    from .bridges_memory import ( # GIỮ NGUYÊN
        get_27_loto_names,
        get_27_loto_positions,
        calculate_bridge_stl
    )
    # Import validation helper từ backtester.py
    from ..backtester import _validate_backtest_params # ĐÃ SỬA (Lên 1 cấp)
except ImportError:
    print("Lỗi: Không thể import bridge/backtester helpers trong bridge_manager_core.py")
    def taoSTL_V30_Bong(a, b): return ['00', '00']
    def getAllPositions_V17_Shadow(r): return []
    def getPositionName_V17_Shadow(i): return "Lỗi V17"
    def getAllLoto_V30(r): return []
    def get_27_loto_names(): return []
    def get_27_loto_positions(r): return []
    def calculate_bridge_stl(l1, l2, type): return ['00', '00']
    def _validate_backtest_params(a, b, c): return None, None, None, None, [["LỖI:", "Lỗi Import."]]


# ===================================================================================
# I. HÀM TÌM CẦU TỐT NHẤT (CHUYỂN TỪ backtester.py)
# ===================================================================================

def TIM_CAU_TOT_NHAT_V16(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """ Dò Cầu Tốt Nhất V17 (Shadow) và trả về TOP 20 cầu CHƯA lưu. """
    print("Bắt đầu Dò Cầu Tốt Nhất V17 (Shadow)...") 
    
    saved_bridge_names = {b['name'] for b in get_all_managed_bridges(db_name)}
    print(f"Đã tìm thấy {len(saved_bridge_names)} cầu đã lưu để lọc.")
    
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
    
    numPositions = len(getAllPositions_V17_Shadow(allData[0])) 
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

def TIM_CAU_BAC_NHO_TOT_NHAT(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra):
    """ Dò 756 Cầu Bạc Nhớ và trả về kết quả (để đưa vào hàm Tự động Dò Cầu). """
    print("... (Dò Cầu Tự Động) Bắt đầu Dò 756 Cầu Bạc Nhớ...")
    
    allData, finalEndRow, startCheckRow, offset, error = _validate_backtest_params(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
    if error: return error

    loto_names = get_27_loto_names()
    num_positions = len(loto_names) 
    
    algorithms = []
    for i in range(num_positions):
        for j in range(i, num_positions):
            name_sum = f"Tổng({loto_names[i]} + {loto_names[j]})"
            algorithms.append((i, j, 'sum', name_sum))
            name_diff = f"Hiệu(|{loto_names[i]} - {loto_names[j]}|)"
            algorithms.append((i, j, 'diff', name_diff))

    num_algorithms = len(algorithms) 
    
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
# II. HÀM QUẢN LÝ CẦU TỰ ĐỘNG (CHUYỂN TỪ backtester.py)
# ===================================================================================

def find_and_auto_manage_bridges(all_data_ai, db_name=DB_NAME):
    """
    Chạy dò cầu V17 + Bạc Nhớ và tự động Thêm/Cập nhật CSDL.
    """
    # FIX: Sửa truy cập SETTINGS
    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE

    added_count = 0
    updated_count = 0
    
    try:
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(all_data_ai) + (ky_bat_dau_kiem_tra - 1)
        
        # --- Bước 1: Chạy cả hai hệ thống dò cầu ---
        results_v17 = TIM_CAU_TOT_NHAT_V16(all_data_ai, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name)
        results_memory = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)

        # Gộp kết quả
        combined_results_data = []
        if results_v17 and len(results_v17) > 1:
            combined_results_data.extend([row for row in results_v17[1:] if "---" not in str(row[0])])
            
        if results_memory and len(results_memory) > 1:
            combined_results_data.extend([row for row in results_memory[1:] if "---" not in str(row[0])])

        if not combined_results_data:
            return "Lỗi: Cả hai hệ thống dò cầu (V17 & Bạc Nhớ) đều không trả về dữ liệu."
            
        existing_bridges = {b['name'] for b in get_all_managed_bridges(db_name)}
        
        # --- Bước 2: Duyệt kết quả TỔNG HỢP và "Upsert" ---
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
                    
                    desc_prefix = "Tự động (V17)"
                    if "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
                        desc_prefix = "Tự động (BN)"
                        
                    desc = f"{desc_prefix} (Tỷ lệ: {win_rate_str}%)"
                    
                    # Gọi hàm Upsert
                    success, msg = upsert_managed_bridge(bridge_name, desc, f"{win_rate_str}%", db_name)
                    
                    if success:
                        if bridge_name in existing_bridges:
                            updated_count += 1
                        else:
                            added_count += 1
                            
            except Exception as e_row:
                print(f"Lỗi xử lý hàng: {row}, Lỗi: {e_row}")
                
        return f"Hoàn tất Dò Cầu Tổng Hợp: Thêm {added_count} cầu mới và cập nhật {updated_count} cầu (V17 + BN)."

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return f"LỖI find_and_auto_manage_bridges: {e}"

def prune_bad_bridges(all_data_ai, db_name=DB_NAME):
    """
    Chạy backtest Cầu Đã Lưu và tự động TẮT các cầu kém hiệu quả (dựa trên cache K2N).
    """
    # FIX: Sửa truy cập SETTINGS
    AUTO_PRUNE_MIN_RATE = SETTINGS.AUTO_PRUNE_MIN_RATE
        
    disabled_count = 0
    try:
        # Lấy danh sách cầu đã lưu (bao gồm cả ID và mô tả)
        managed_bridges_map = {b['name']: b for b in get_all_managed_bridges(db_name, only_enabled=True)}

        if not managed_bridges_map:
             return "Lỗi: Không có cầu nào được Bật để lọc."

        print(f"... (Lọc Cầu Yếu) Đang kiểm tra {len(managed_bridges_map)} cầu đã bật...")
        
        # Bước 2: Duyệt các cầu đã cache và lọc
        for bridge_name, bridge_data in managed_bridges_map.items():
            try:
                # Đọc tỷ lệ từ cache K2N
                win_rate_str = str(bridge_data.get('win_rate_text', '0%')).replace('%', '')
                
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