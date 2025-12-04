# Tên file: code6/logic/bridges/bridge_manager_core.py
# (PHIÊN BẢN V8.6 - FIX TRIỆT ĐỂ LỖI N/A CHO CẢ CẦU MỚI VÀ CŨ)

import os
import sqlite3
import sys
import re
from dataclasses import dataclass
from typing import List, Optional, Dict

# =========================================================================
# PATH FIX
# =========================================================================
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception: pass

# =========================================================================
# IMPORTS
# =========================================================================
try:
    from logic.config_manager import SETTINGS
except ImportError:
    SETTINGS = type("obj", (object,), {"AUTO_ADD_MIN_RATE": 50.0, "AUTO_PRUNE_MIN_RATE": 40.0})

try:
    # Import hàm lấy danh sách cầu để bảo toàn dữ liệu cũ
    from logic.data_repository import get_all_managed_bridges
    from logic.db_manager import DB_NAME, update_managed_bridge, upsert_managed_bridge
except ImportError:
    DB_NAME = "data/xo_so_prizes_all_logic.db"
    def upsert_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def update_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def get_all_managed_bridges(*args, **kwargs): return []

try:
    from logic.bridges.bridges_classic import (
        checkHitSet_V30_K2N, getAllLoto_V30,
        getCau1_STL_P5_V30_V5, getCau2_VT1_V30_V5, getCau3_VT2_V30_V5,
        getCau4_VT3_V30_V5, getCau5_TDB1_V30_V5, getCau6_VT5_V30_V5,
        getCau7_Moi1_V30_V5, getCau8_Moi2_V30_V5, getCau9_Moi3_V30_V5,
        getCau10_Moi4_V30_V5, getCau11_Moi5_V30_V5, getCau12_Moi6_V30_V5,
        getCau13_G7_3_P8_V30_V5, getCau14_G1_P2_V30_V5, getCau15_DE_P7_V30_V5
    )
    from logic.bridges.bridges_memory import (
        calculate_bridge_stl, get_27_loto_names, get_27_loto_positions,
    )
    from logic.bridges.bridges_v16 import (
        getAllPositions_V17_Shadow, getPositionName_V17_Shadow, taoSTL_V30_Bong,
    )
except ImportError:
    pass

# =========================================================================
# MAPPING CẦU CỐ ĐỊNH
# =========================================================================
LO_BRIDGE_MAP = {
    "LO_STL_FIXED_01": {"func": getCau1_STL_P5_V30_V5, "desc": "Cầu Lô 01 (GĐB+5)"},
    "LO_STL_FIXED_02": {"func": getCau2_VT1_V30_V5,    "desc": "Cầu Lô 02 (G6.2+G7.3)"},
    "LO_STL_FIXED_03": {"func": getCau3_VT2_V30_V5,    "desc": "Cầu Lô 03 (Đuôi GĐB+G1)"},
    "LO_STL_FIXED_04": {"func": getCau4_VT3_V30_V5,    "desc": "Cầu Lô 04 (GĐB Sát Đuôi)"},
    "LO_STL_FIXED_05": {"func": getCau5_TDB1_V30_V5,   "desc": "Cầu Lô 05 (Đầu G7.0+Đuôi G7.3)"},
    "LO_STL_FIXED_06": {"func": getCau6_VT5_V30_V5,    "desc": "Cầu Lô 06 (G7.1+G7.2)"},
    "LO_STL_FIXED_07": {"func": getCau7_Moi1_V30_V5,   "desc": "Cầu Lô 07 (G5.0+G7.0)"},
    "LO_STL_FIXED_08": {"func": getCau8_Moi2_V30_V5,   "desc": "Cầu Lô 08 (G3.0+G4.0)"},
    "LO_STL_FIXED_09": {"func": getCau9_Moi3_V30_V5,   "desc": "Cầu Lô 09 (Đầu GĐB+Đầu G1)"},
    "LO_STL_FIXED_10": {"func": getCau10_Moi4_V30_V5,  "desc": "Cầu Lô 10 (G2.1+G3.2)"},
    "LO_STL_FIXED_11": {"func": getCau11_Moi5_V30_V5,  "desc": "Cầu Lô 11 (GĐB+G3.1)"},
    "LO_STL_FIXED_12": {"func": getCau12_Moi6_V30_V5,  "desc": "Cầu Lô 12 (Đuôi GĐB+G3.2)"},
    "LO_STL_FIXED_13": {"func": getCau13_G7_3_P8_V30_V5, "desc": "Cầu Lô 13 (G7.3+8)"},
    "LO_STL_FIXED_14": {"func": getCau14_G1_P2_V30_V5,   "desc": "Cầu Lô 14 (G1+2)"},
    "LO_STL_FIXED_15": {"func": getCau15_DE_P7_V30_V5,   "desc": "Cầu Lô 15 (GĐB+7)"},
}

def _sanitize_name_v2(name):
    return name.replace("[", "_").replace("]", "").replace("(", "_").replace(")", "").replace(".", "_").replace("+", "_").replace(" ", "")

def _ensure_core_db_columns(cursor):
    try:
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [info[1] for info in cursor.fetchall()]
        if "type" not in columns: cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN type TEXT DEFAULT 'UNKNOWN'")
        # Ensure search columns exist (failsafe)
        if "search_rate_text" not in columns: cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN search_rate_text TEXT DEFAULT ''")
    except: pass

def _get_existing_bridges_map(db_name) -> Dict:
    """Helper: Lấy toàn bộ cầu hiện có để tra cứu K1N cũ."""
    try:
        bridges = get_all_managed_bridges(db_name)
        # Map: { "LO_POS_...": "55%" } (Giá trị là win_rate_text hiện tại)
        return {b['name']: b.get('win_rate_text', 'N/A') for b in bridges}
    except Exception:
        return {}

# ===================================================================================
# I. HÀM DÒ CẦU V17 SHADOW (MODIFIED: PRESERVE K1N + AUTO HEAL N/A)
# ===================================================================================
def TIM_CAU_TOT_NHAT_V16(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    print("Bắt đầu Dò Cầu Lô Vị Trí (V17 Shadow) - Logic Bảo Toàn K1N...")
    allData, finalEndRow, startCheckRow, offset = toan_bo_A_I, ky_ket_thuc_kiem_tra, ky_bat_dau_kiem_tra + 1, ky_bat_dau_kiem_tra
    headers = ["STT", "Cầu (V17)", "Vị Trí", "Tỷ Lệ K2N (Scan)", "Chuỗi"]
    results = [headers]

    # [BƯỚC 1] Lấy danh sách cầu hiện tại để bảo vệ K1N
    existing_bridges_map = _get_existing_bridges_map(db_name)

    try:
        positions_shadow = getAllPositions_V17_Shadow(allData[0])
        num_positions_shadow = len(positions_shadow)
    except: return [["LỖI:", "Không thể lấy Vị Trí V17 Shadow."]]
    
    if num_positions_shadow == 0: return [["LỖI:", "Không thể lấy Vị Trí V17 Shadow."]]

    algorithms = []
    for i in range(num_positions_shadow):
        for j in range(i, num_positions_shadow):
            algorithms.append((i, j))

    processedData = []
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        processedData.append({
            "prevPositions": getAllPositions_V17_Shadow(allData[prevRow_idx]),
            "actualLotoSet": set(getAllLoto_V30(allData[actualRow_idx])),
        })

    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE
    bridges_to_add = []

    for idx1, idx2 in algorithms:
        win_count, current_streak, max_streak = 0, 0, 0
        for dayData in processedData:
            a, b = dayData["prevPositions"][idx1], dayData["prevPositions"][idx2]
            if a is None or b is None:
                current_streak = 0
                continue
            
            # ĐÂY LÀ LOGIC K2N
            if "✅" in checkHitSet_V30_K2N(taoSTL_V30_Bong(a, b), dayData["actualLotoSet"]):
                win_count += 1; current_streak += 1
            else: current_streak = 0
            max_streak = max(max_streak, current_streak)

        totalTestDays = len(processedData)
        if totalTestDays > 0:
            scan_rate = (win_count / totalTestDays) * 100
            if scan_rate >= AUTO_ADD_MIN_RATE:
                pos1_name = getPositionName_V17_Shadow(idx1)
                pos2_name = getPositionName_V17_Shadow(idx2)
                
                safe_p1 = _sanitize_name_v2(pos1_name)
                safe_p2 = _sanitize_name_v2(pos2_name)
                std_id = f"LO_POS_{safe_p1}_{safe_p2}"
                display_desc = f"Vị trí: {pos1_name} + {pos2_name}"
                scan_rate_str = f"{scan_rate:.2f}%"

                results.append([len(results), std_id, f"{pos1_name}+{pos2_name}", scan_rate_str, f"{current_streak}"])
                
                # [FIX V8.6] Logic K1N thông minh (Auto Heal)
                # Nếu cầu đã có và K1N hợp lệ -> Giữ nguyên
                # Nếu cầu MỚI hoặc cầu CŨ đang bị N/A -> Lấy luôn Scan Rate làm K1N (để không bị trống)
                preserved_k1n = scan_rate_str 
                
                if std_id in existing_bridges_map:
                    old_k1n = existing_bridges_map[std_id]
                    if old_k1n and old_k1n != 'N/A' and old_k1n != '':
                         preserved_k1n = old_k1n

                bridge_data_dict = {
                    "pos1_idx": idx1, "pos2_idx": idx2,
                    "search_rate_text": scan_rate_str,  # <-- CẬP NHẬT K2N VÀO ĐÂY
                    "search_period": totalTestDays,
                    "is_enabled": 1,
                    "type": "LO_POS"
                }
                
                # Tham số thứ 3 (win_rate) truyền preserved_k1n để bảo toàn hoặc tự vá lỗi
                bridges_to_add.append((std_id, display_desc, preserved_k1n, db_name, idx1, idx2, bridge_data_dict))

    if bridges_to_add:
        print(f"Dò cầu V17: Đang lưu {len(bridges_to_add)} cầu (Cập nhật Scan Rate)...")
        try:
            [upsert_managed_bridge(n, d, r, db, i1, i2, data_dict) for n, d, r, db, i1, i2, data_dict in bridges_to_add]
            # Bulk Update Type
            conn = sqlite3.connect(db_name)
            conn.execute("UPDATE ManagedBridges SET type='LO_POS' WHERE name LIKE 'LO_POS_%'")
            conn.commit(); conn.close()
        except Exception as e: print(f"Lỗi lưu cầu V17: {e}")

    return results

# ===================================================================================
# II. HÀM DÒ CẦU BẠC NHỚ (MODIFIED: PRESERVE K1N + AUTO HEAL N/A)
# ===================================================================================
def TIM_CAU_BAC_NHO_TOT_NHAT(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    print("Bắt đầu Dò Cầu Bạc Nhớ - Logic Bảo Toàn K1N...")
    allData, finalEndRow, startCheckRow, offset = toan_bo_A_I, ky_ket_thuc_kiem_tra, ky_bat_dau_kiem_tra + 1, ky_bat_dau_kiem_tra
    loto_names = get_27_loto_names()
    processedData = []
    
    # [BƯỚC 1] Lấy danh sách cầu hiện tại
    existing_bridges_map = _get_existing_bridges_map(db_name)

    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        processedData.append({
            "prevLotos": get_27_loto_positions(allData[prevRow_idx]),
            "actualLotoSet": set(getAllLoto_V30(allData[actualRow_idx])),
        })

    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE
    bridges_to_add = []
    results = [["STT", "Cầu (Bạc Nhớ)", "Vị Trí", "Tỷ Lệ K2N", "Chuỗi"]]

    algorithms = []
    for i in range(len(loto_names)):
        for j in range(i, len(loto_names)):
            std_sum = f"LO_MEM_SUM_{loto_names[i]}_{loto_names[j]}"
            desc_sum = f"Bạc Nhớ: Tổng({loto_names[i]} + {loto_names[j]})"
            algorithms.append((i, j, "sum", std_sum, desc_sum))
            
            std_diff = f"LO_MEM_DIFF_{loto_names[i]}_{loto_names[j]}"
            desc_diff = f"Bạc Nhớ: Hiệu(|{loto_names[i]} - {loto_names[j]}|)"
            algorithms.append((i, j, "diff", std_diff, desc_diff))

    for idx1, idx2, alg_type, std_id, desc in algorithms:
        win_count, current_streak, max_streak = 0, 0, 0
        for dayData in processedData:
            loto1, loto2 = dayData["prevLotos"][idx1], dayData["prevLotos"][idx2]
            if "✅" in checkHitSet_V30_K2N(calculate_bridge_stl(loto1, loto2, alg_type), dayData["actualLotoSet"]):
                win_count += 1; current_streak += 1
            else: current_streak = 0
            max_streak = max(max_streak, current_streak)

        totalTestDays = len(processedData)
        if totalTestDays > 0:
            scan_rate = (win_count / totalTestDays) * 100
            if scan_rate >= AUTO_ADD_MIN_RATE:
                scan_rate_str = f"{scan_rate:.2f}%"
                results.append([len(results), std_id, desc, scan_rate_str, f"{current_streak}"])
                
                # [FIX V8.6] Logic K1N thông minh (Auto Heal)
                preserved_k1n = scan_rate_str 
                
                if std_id in existing_bridges_map:
                    old_k1n = existing_bridges_map[std_id]
                    if old_k1n and old_k1n != 'N/A' and old_k1n != '':
                        preserved_k1n = old_k1n

                bridge_data = {
                    "pos1_idx": -1, "pos2_idx": -1,
                    "search_rate_text": scan_rate_str, # Cập nhật K2N
                    "search_period": totalTestDays,
                    "is_enabled": 1,
                    "type": "LO_MEM"
                }
                # Truyền preserved_k1n vào win_rate argument
                bridges_to_add.append((std_id, desc, preserved_k1n, db_name, -1, -1, bridge_data))

    if bridges_to_add:
        print(f"Dò Bạc Nhớ: Đang lưu {len(bridges_to_add)} cầu chuẩn (Cập nhật Scan Rate)...")
        try:
            [upsert_managed_bridge(n, d, r, db, i1, i2, data_dict) for n, d, r, db, i1, i2, data_dict in bridges_to_add]
            conn = sqlite3.connect(db_name)
            conn.execute("UPDATE ManagedBridges SET type='LO_MEM' WHERE name LIKE 'LO_MEM_%'")
            conn.commit(); conn.close()
        except Exception as e: print(f"Lỗi lưu Bạc Nhớ: {e}")

    return results

# ===================================================================================
# III. HÀM QUẢN LÝ 15 CẦU LÔ CỐ ĐỊNH (UPDATE K1N - CHÍNH CHỦ)
# ===================================================================================
def _update_fixed_lo_bridges(all_data_ai, db_name):
    """
    (V2.2 FIXED) Tính toán hiệu quả 15 Cầu Lô Cố Định -> Cập nhật cả K1N và K2N
    """
    print(">>> [LO MANAGER] Đang cập nhật 15 Cầu Lô Cố Định (Phase C - Fix N/A)...")
    if not all_data_ai or len(all_data_ai) < 10: return 0
    
    # Cấu hình check: 10 kỳ gần nhất
    check_days = 10 
    # Lấy buffer dữ liệu đủ để check
    scan_data = all_data_ai[- (check_days + 5):]
    
    updated_count = 0
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    _ensure_core_db_columns(cursor)
    
    for bridge_id, info in LO_BRIDGE_MAP.items():
        func = info["func"]
        desc = info["desc"]
        
        wins = 0
        current_streak = 0
        
        # Backtest nhanh
        for i in range(len(scan_data) - 1 - check_days, len(scan_data) - 1):
            if i < 0: continue
            row_prev = scan_data[i]
            row_next = scan_data[i+1]
            
            try:
                stl = func(row_prev) # Dự đoán
                lotos_next = set(getAllLoto_V30(row_next)) # Kết quả
                
                # Check K1N (Đánh giá theo ngày)
                if "✅" in checkHitSet_V30_K2N(stl, lotos_next):
                    wins += 1
                    current_streak += 1
                else:
                    current_streak = 0
            except: pass
            
        # Dự đoán tương lai
        last_row = all_data_ai[-1]
        try:
            next_stl = func(last_row)
            pred_val = f"{next_stl[0]},{next_stl[1]}"
        except: 
            pred_val = "Error"
            
        win_rate = (wins / check_days) * 100
        full_desc = f"{desc}. Phong độ {wins}/{check_days}."
        
        # [FIX QUAN TRỌNG] Dùng chung giá trị cho cả Search Rate và Win Rate để hết N/A
        rate_str = f"{win_rate:.0f}%"
        
        try:
            # Upsert
            cursor.execute("SELECT count(*) FROM ManagedBridges WHERE name=?", (bridge_id,))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                # Nếu mới thêm: Ghi cả win_rate_text và search_rate_text
                cursor.execute("""
                    INSERT INTO ManagedBridges (name, description, win_rate_text, search_rate_text, current_streak, next_prediction_stl, is_enabled, type, db_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (bridge_id, full_desc, rate_str, rate_str, current_streak, pred_val, 1 if win_rate>=40 else 0, 'LO_STL_FIXED', db_name))
            else:
                # Nếu đã có: Cập nhật đè cả win_rate_text để đảm bảo không bị N/A
                cursor.execute("""
                    UPDATE ManagedBridges 
                    SET description=?, win_rate_text=?, search_rate_text=?, current_streak=?, next_prediction_stl=?, is_enabled=?, type='LO_STL_FIXED'
                    WHERE name=?
                """, (full_desc, rate_str, rate_str, current_streak, pred_val, 1 if win_rate>=40 else 0, bridge_id))
            updated_count += 1
        except Exception as e: 
            print(f"Lỗi update Fixed Bridge {bridge_id}: {e}")
            
    conn.commit(); conn.close()
    return updated_count

# ===================================================================================
# IV. WRAPPER CHUNG
# ===================================================================================
def find_and_auto_manage_bridges(all_data_ai, db_name=DB_NAME):
    try:
        if not all_data_ai: return "Lỗi: Không có dữ liệu."
        msg = []
        
        # 1. Dò tìm cầu K2N -> Update vào Search Rate (Giữ K1N)
        print("... [Auto] Dò V17 Shadow (K2N Scan) ...")
        res_v17 = TIM_CAU_TOT_NHAT_V16(all_data_ai, 2, len(all_data_ai)+1, db_name)
        msg.append(f"V17 (Scan): {len(res_v17)-1 if res_v17 else 0} cầu")
        
        # 2. Dò tìm Bạc nhớ K2N -> Update vào Search Rate (Giữ K1N)
        print("... [Auto] Dò Bạc Nhớ (K2N Scan) ...")
        res_bn = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, 2, len(all_data_ai)+1, db_name)
        msg.append(f"Bạc Nhớ (Scan): {len(res_bn)-1 if res_bn else 0} cầu")
        
        # 3. Cập nhật cầu Fixed K1N -> Update vào Win Rate (Đúng chuẩn)
        print("... [Auto] Cập nhật Fixed (K1N Real) ...")
        c_fix = _update_fixed_lo_bridges(all_data_ai, db_name)
        msg.append(f"Fixed (K1N): {c_fix} cầu")
        
        return " | ".join(msg)
    except Exception as e: return f"Lỗi: {e}"

# ... (Các hàm prune/init giữ nguyên như cũ) ...
def prune_bad_bridges(all_data_ai, db_name=DB_NAME):
    try:
        AUTO_PRUNE_MIN_RATE = SETTINGS.AUTO_PRUNE_MIN_RATE
    except: AUTO_PRUNE_MIN_RATE = 40.0

    disabled_count = 0
    skipped_pinned = 0
    try:
        bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if not bridges: return "Không có cầu để lọc."
        
        for b in bridges:
            try:
                # 1. Bỏ qua cầu ghim
                is_pinned = b.get("is_pinned", 0)
                if is_pinned:
                    skipped_pinned += 1
                    continue
                
                # 2. Lấy các tỷ lệ
                # K2N (Search Rate) - Ưu tiên số 1 để đánh giá tiềm năng hiện tại
                k2n_str = str(b.get("search_rate_text", "0")).replace("%", "")
                try: k2n_val = float(k2n_str)
                except: k2n_val = 0.0
                
                # K1N (Win Rate) - Ưu tiên số 2 (Thành tích thực tế)
                k1n_str = str(b.get("win_rate_text", "0")).replace("%", "")
                try: k1n_val = float(k1n_str)
                except: k1n_val = 0.0

                # 3. Logic Quyết Định: CHỈ TẮT KHI CẢ HAI ĐỀU TỆ
                # Nếu K2N tốt (>= 40%) -> GIỮ (Tiềm năng)
                # Nếu K1N tốt (>= 40%) -> GIỮ (Đang ăn thực tế)
                # Chỉ tắt khi: K2N < 40% VÀ K1N < 40%
                
                # Trường hợp đặc biệt: Cầu mới tinh (K2N=0, K1N=N/A hoặc 0)
                # Để tránh tắt nhầm cầu chưa kịp chạy, ta có thể kiểm tra thêm:
                # Nếu K2N == 0.0 và K1N == 0.0 -> Có thể là cầu chưa có dữ liệu -> BỎ QUA (Không tắt)
                # Hoặc nếu muốn nghiêm ngặt: Tắt luôn. 
                # Đề xuất: Nếu cả 2 đều bằng 0, coi như chưa có dữ liệu, không tắt.
                
                should_disable = False
                
                if k2n_val > 0 or k1n_val > 0:
                    # Có ít nhất 1 dữ liệu để đánh giá
                    # Nếu cả hai đều dưới ngưỡng -> Tắt
                    # (Lưu ý: Nếu k2n=0 nhưng k1n=100 -> Giữ. Nếu k2n=30, k1n=0 -> Tắt)
                    
                    # Logic: Giữ lại nếu có BẤT KỲ chỉ số nào đạt chuẩn
                    is_k2n_ok = (k2n_val >= AUTO_PRUNE_MIN_RATE)
                    is_k1n_ok = (k1n_val >= AUTO_PRUNE_MIN_RATE)
                    
                    if not is_k2n_ok and not is_k1n_ok:
                        should_disable = True
                else:
                    # Cả 2 đều = 0 (Cầu mới hoặc lỗi data)
                    # Tùy chọn: Không làm gì để an toàn
                    should_disable = False

                if should_disable:
                    update_managed_bridge(b["id"], b["description"], 0, db_name)
                    disabled_count += 1
                    
            except Exception as e_inner:
                print(f"Lỗi check cầu {b.get('name')}: {e_inner}")
                pass
                
    except Exception as e: return f"Lỗi lọc cầu: {e}"

    msg = f"Lọc cầu hoàn tất. Đã TẮT {disabled_count} cầu yếu (Cả K1N & K2N < {AUTO_PRUNE_MIN_RATE}%)."
    if skipped_pinned > 0:
        msg += f" Bỏ qua {skipped_pinned} cầu đã ghim."
    return msg

def auto_manage_bridges(all_data_ai, db_name=DB_NAME):
    return prune_bad_bridges(all_data_ai, db_name) # Redirect to prune for simplicity

def init_all_756_memory_bridges_to_db(db_name=DB_NAME, progress_callback=None, enable_all=False):
    print("Khởi tạo Bạc Nhớ chuẩn V2.1...")
    loto_names = get_27_loto_names()
    added = 0
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    _ensure_core_db_columns(cursor)
    
    for i in range(len(loto_names)):
        for j in range(i, len(loto_names)):
            sid = f"LO_MEM_SUM_{loto_names[i]}_{loto_names[j]}"
            sdesc = f"Bạc Nhớ: Tổng({loto_names[i]} + {loto_names[j]})"
            cursor.execute("INSERT OR IGNORE INTO ManagedBridges (name, description, type, is_enabled) VALUES (?, ?, 'LO_MEM', ?)", (sid, sdesc, 1 if enable_all else 0))
            if cursor.rowcount > 0: added += 1
            
            did = f"LO_MEM_DIFF_{loto_names[i]}_{loto_names[j]}"
            ddesc = f"Bạc Nhớ: Hiệu(|{loto_names[i]} - {loto_names[j]}|)"
            cursor.execute("INSERT OR IGNORE INTO ManagedBridges (name, description, type, is_enabled) VALUES (?, ?, 'LO_MEM', ?)", (did, ddesc, 1 if enable_all else 0))
            if cursor.rowcount > 0: added += 1
            
    conn.commit(); conn.close()
    return True, f"Thêm {added} cầu Bạc Nhớ chuẩn.", added, 0