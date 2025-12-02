# Tên file: logic/bridges/bridge_manager_core.py
#
# (PHIÊN BẢN V8.1 - SAFE MODE - NAMING V2.1 STANDARD)
# Chỉ sửa logic đặt tên, giữ nguyên cấu trúc class và import cũ.

import os
import sqlite3
import sys
import re
from dataclasses import dataclass
from typing import List, Optional

# =========================================================================
# PATH FIX: Giữ nguyên logic cũ để đảm bảo không lỗi import
# =========================================================================
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"[PATH FIX] Đã thêm {project_root} vào sys.path")
except Exception as e_path:
    print(f"[PATH FIX] LỖI: {e_path}")

# =========================================================================
# IMPORT SETTINGS & DB
# =========================================================================
try:
    from logic.config_manager import SETTINGS
    print("[IMPORT] Đã import thành công: SETTINGS")
except ImportError:
    SETTINGS = type("obj", (object,), {"AUTO_ADD_MIN_RATE": 50.0, "AUTO_PRUNE_MIN_RATE": 40.0})

try:
    from logic.data_repository import get_all_managed_bridges
    from logic.db_manager import DB_NAME, update_managed_bridge, upsert_managed_bridge
except ImportError:
    DB_NAME = "data/xo_so_prizes_all_logic.db"
    def upsert_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def update_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def get_all_managed_bridges(*args, **kwargs): return []

# =========================================================================
# IMPORT HÀM CẦU
# =========================================================================
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
except ImportError as e:
    print(f"[IMPORT] Lỗi import hàm cầu: {e}")
    # Dummy funcs
    def getAllPositions_V17_Shadow(r): return []
    def getPositionName_V17_Shadow(i): return "Lỗi"
    def taoSTL_V30_Bong(a, b): return ["00", "00"]
    def calculate_bridge_stl(l1, l2, t): return ["00", "00"]
    def get_27_loto_names(): return []
    def get_27_loto_positions(r): return []
    def checkHitSet_V30_K2N(p, loto_set): return "Lỗi"
    def getAllLoto_V30(r): return []

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

# ===================================================================================
# 0. ĐỊNH NGHĨA DATA STRUCTURES (KHÔI PHỤC ĐỂ TRÁNH LỖI DEPENDENCY)
# ===================================================================================
@dataclass
class BridgeLocation:
    index: int
    type_id: int = 0  # 0: Normal, 1: Shadow, etc.

@dataclass
class Bridge:
    locations: List[BridgeLocation]
    value: int
    predicted_value: int
    score: float
    bridge_type: str = "UNKNOWN"
    
    def __str__(self):
        return f"Bridge(Type={self.bridge_type}, Score={self.score}, Pred={self.predicted_value})"

# ===================================================================================
# HELPER: NAMING CONVENTION V2.1
# ===================================================================================
def _sanitize_name_v2(name):
    """Làm sạch tên để tạo ID chuẩn (GDB[0] -> GDB_0)."""
    return name.replace("[", "_").replace("]", "").replace("(", "_").replace(")", "").replace(".", "_").replace("+", "_").replace(" ", "")

def _ensure_core_db_columns(cursor):
    """Self-healing DB columns."""
    try:
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [info[1] for info in cursor.fetchall()]
        if "type" not in columns: cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN type TEXT DEFAULT 'UNKNOWN'")
        if "recent_win_count_10" not in columns: cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN recent_win_count_10 INTEGER DEFAULT 0")
        if "next_prediction_stl" not in columns: cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN next_prediction_stl TEXT DEFAULT ''")
    except: pass

# ===================================================================================
# I. HÀM DÒ CẦU V17 SHADOW (STANDARD V2.1)
# ===================================================================================
def TIM_CAU_TOT_NHAT_V16(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """
    (V8.1) Hàm dò cầu V17 - Chuẩn hóa tên 'LO_POS_...'
    """
    print("Bắt đầu Dò Cầu Lô Vị Trí (V17 Shadow) - Chuẩn V2.1...")
    allData, finalEndRow, startCheckRow, offset = toan_bo_A_I, ky_ket_thuc_kiem_tra, ky_bat_dau_kiem_tra + 1, ky_bat_dau_kiem_tra
    headers = ["STT", "Cầu (V17)", "Vị Trí", "Tỷ Lệ %", "Chuỗi"]
    results = [headers]

    try:
        positions_shadow = getAllPositions_V17_Shadow(allData[0])
        num_positions_shadow = len(positions_shadow)
    except: return [["LỖI:", "Không thể lấy Vị Trí V17 Shadow."]]
    
    if num_positions_shadow == 0: return [["LỖI:", "Không thể lấy Vị Trí V17 Shadow."]]

    algorithms = []
    for i in range(num_positions_shadow):
        for j in range(i, num_positions_shadow):
            algorithms.append((i, j))

    print(f"Đã tạo {len(algorithms)} thuật toán. Đang xử lý...")

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
            
            if "✅" in checkHitSet_V30_K2N(taoSTL_V30_Bong(a, b), dayData["actualLotoSet"]):
                win_count += 1; current_streak += 1
            else: current_streak = 0
            max_streak = max(max_streak, current_streak)

        totalTestDays = len(processedData)
        if totalTestDays > 0:
            rate = (win_count / totalTestDays) * 100
            if rate >= AUTO_ADD_MIN_RATE:
                pos1_name = getPositionName_V17_Shadow(idx1)
                pos2_name = getPositionName_V17_Shadow(idx2)
                
                # [NAMING V2.1 CHANGE] 
                # Cũ: bridge_name = f"{pos1_name}+{pos2_name}"
                # Mới: LO_POS_...
                safe_p1 = _sanitize_name_v2(pos1_name)
                safe_p2 = _sanitize_name_v2(pos2_name)
                std_id = f"LO_POS_{safe_p1}_{safe_p2}"
                display_desc = f"Vị trí: {pos1_name} + {pos2_name}"
                rate_str = f"{rate:.2f}%"

                results.append([len(results), std_id, f"{pos1_name}+{pos2_name}", rate_str, f"{current_streak}"])
                
                bridge_data_dict = {
                    "pos1_idx": idx1, "pos2_idx": idx2,
                    "search_rate_text": rate_str, "search_period": totalTestDays,
                    "is_enabled": 1,
                    "type": "LO_POS" # Cập nhật type chuẩn
                }
                # Sử dụng ID chuẩn (std_id) thay vì tên cũ
                bridges_to_add.append((std_id, display_desc, rate_str, db_name, idx1, idx2, bridge_data_dict))

    if bridges_to_add:
        print(f"Dò cầu V17: Đang lưu {len(bridges_to_add)} cầu chuẩn LO_POS...")
        try:
            [upsert_managed_bridge(n, d, r, db, i1, i2, data_dict) for n, d, r, db, i1, i2, data_dict in bridges_to_add]
            # Bulk Update Type
            conn = sqlite3.connect(db_name)
            conn.execute("UPDATE ManagedBridges SET type='LO_POS' WHERE name LIKE 'LO_POS_%'")
            conn.commit(); conn.close()
        except Exception as e: print(f"Lỗi lưu cầu V17: {e}")

    return results

# ===================================================================================
# II. HÀM DÒ CẦU BẠC NHỚ (STANDARD V2.1)
# ===================================================================================
def TIM_CAU_BAC_NHO_TOT_NHAT(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """
    (V8.1) Hàm dò cầu Bạc Nhớ - Chuẩn hóa tên 'LO_MEM_...'
    """
    print("Bắt đầu Dò Cầu Bạc Nhớ - Chuẩn V2.1...")
    allData, finalEndRow, startCheckRow, offset = toan_bo_A_I, ky_ket_thuc_kiem_tra, ky_bat_dau_kiem_tra + 1, ky_bat_dau_kiem_tra
    loto_names = get_27_loto_names()
    processedData = []
    
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0: continue
        processedData.append({
            "prevLotos": get_27_loto_positions(allData[prevRow_idx]),
            "actualLotoSet": set(getAllLoto_V30(allData[actualRow_idx])),
        })

    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE
    bridges_to_add = []
    results = [["STT", "Cầu (Bạc Nhớ)", "Vị Trí", "Tỷ Lệ %", "Chuỗi"]]

    algorithms = []
    for i in range(len(loto_names)):
        for j in range(i, len(loto_names)):
            # [NAMING V2.1 CHANGE] 
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
            rate = (win_count / totalTestDays) * 100
            if rate >= AUTO_ADD_MIN_RATE:
                rate_str = f"{rate:.2f}%"
                results.append([len(results), std_id, desc, rate_str, f"{current_streak}"])
                bridge_data = {
                    "pos1_idx": -1, "pos2_idx": -1,
                    "search_rate_text": rate_str, "search_period": totalTestDays,
                    "is_enabled": 1,
                    "type": "LO_MEM" # Type chuẩn
                }
                bridges_to_add.append((std_id, desc, rate_str, db_name, -1, -1, bridge_data))

    if bridges_to_add:
        print(f"Dò Bạc Nhớ: Đang lưu {len(bridges_to_add)} cầu chuẩn LO_MEM...")
        try:
            [upsert_managed_bridge(n, d, r, db, i1, i2, data_dict) for n, d, r, db, i1, i2, data_dict in bridges_to_add]
            conn = sqlite3.connect(db_name)
            conn.execute("UPDATE ManagedBridges SET type='LO_MEM' WHERE name LIKE 'LO_MEM_%'")
            conn.commit(); conn.close()
        except Exception as e: print(f"Lỗi lưu Bạc Nhớ: {e}")

    return results

# ===================================================================================
# III. HÀM QUẢN LÝ 15 CẦU LÔ CỐ ĐỊNH (PHASE C)
# ===================================================================================
def _update_fixed_lo_bridges(all_data_ai, db_name):
    """
    (V8.1) Cập nhật 15 Cầu Lô - Chuẩn hóa Type = LO_STL_FIXED
    """
    print(">>> [LO MANAGER] Cập nhật 15 Cầu Lô Cố Định...")
    if not all_data_ai or len(all_data_ai) < 10: return 0
    scan_data = all_data_ai[-15:]
    updated_count = 0
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    _ensure_core_db_columns(cursor)
    
    for bridge_id, info in LO_BRIDGE_MAP.items():
        func, desc = info["func"], info["desc"]
        wins, current_streak = 0, 0
        
        for i in range(len(scan_data) - 1 - 10, len(scan_data) - 1):
            if i < 0: continue
            try:
                if "✅" in checkHitSet_V30_K2N(func(scan_data[i]), set(getAllLoto_V30(scan_data[i+1]))):
                    wins += 1; current_streak += 1
                else: current_streak = 0
            except: pass
            
        try: next_stl = func(all_data_ai[-1]); pred_val = f"{next_stl[0]},{next_stl[1]}"
        except: pred_val = ""
            
        win_rate = (wins / 10) * 100
        full_desc = f"{desc}. Phong độ {wins}/10."
        
        try:
            # Upsert
            cursor.execute("SELECT count(*) FROM ManagedBridges WHERE name=?", (bridge_id,))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                cursor.execute("""
                    INSERT INTO ManagedBridges (name, description, win_rate_text, current_streak, next_prediction_stl, is_enabled, type, db_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (bridge_id, full_desc, f"{win_rate:.0f}%", current_streak, pred_val, 1 if win_rate>=40 else 0, 'LO_STL_FIXED', db_name))
            else:
                cursor.execute("""
                    UPDATE ManagedBridges 
                    SET description=?, win_rate_text=?, current_streak=?, next_prediction_stl=?, is_enabled=?, type='LO_STL_FIXED'
                    WHERE name=?
                """, (full_desc, f"{win_rate:.0f}%", current_streak, pred_val, 1 if win_rate>=40 else 0, bridge_id))
            updated_count += 1
        except Exception as e: print(f"Lỗi fixed bridge: {e}")
            
    conn.commit(); conn.close()
    return updated_count

# ===================================================================================
# IV. WRAPPER CHUNG & CÁC HÀM CŨ (GIỮ NGUYÊN)
# ===================================================================================
def find_and_auto_manage_bridges(all_data_ai, db_name=DB_NAME):
    try:
        if not all_data_ai: return "Lỗi: Không có dữ liệu."
        msg = []
        
        print("... [Auto] Dò V17 Shadow ...")
        res_v17 = TIM_CAU_TOT_NHAT_V16(all_data_ai, 2, len(all_data_ai)+1, db_name)
        msg.append(f"V17: {len(res_v17)-1 if res_v17 else 0} cầu")
        
        print("... [Auto] Dò Bạc Nhớ ...")
        res_bn = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, 2, len(all_data_ai)+1, db_name)
        msg.append(f"Bạc Nhớ: {len(res_bn)-1 if res_bn else 0} cầu")
        
        print("... [Auto] Cập nhật Fixed ...")
        c_fix = _update_fixed_lo_bridges(all_data_ai, db_name)
        msg.append(f"Fixed: {c_fix} cầu")
        
        return " | ".join(msg)
    except Exception as e: return f"Lỗi: {e}"

def prune_bad_bridges(all_data_ai, db_name=DB_NAME):
    # (KHÔI PHỤC NGUYÊN BẢN CŨ)
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
                is_pinned = b.get("is_pinned", 0)
                if is_pinned:
                    skipped_pinned += 1
                    continue
                
                wr_str = str(b.get("win_rate_text", "0")).replace("%", "")
                if float(wr_str) < AUTO_PRUNE_MIN_RATE:
                    update_managed_bridge(b["id"], b["description"], 0, db_name)
                    disabled_count += 1
            except: pass
    except Exception as e: return f"Lỗi lọc cầu: {e}"

    msg = f"Lọc cầu hoàn tất. Đã TẮT {disabled_count} cầu yếu (Tỷ lệ < {AUTO_PRUNE_MIN_RATE}%)."
    if skipped_pinned > 0:
        msg += f" Bỏ qua {skipped_pinned} cầu đã ghim."
    return msg

def auto_manage_bridges(all_data_ai, db_name=DB_NAME):
    # (KHÔI PHỤC NGUYÊN BẢN CŨ)
    try:
        AUTO_PRUNE_MIN_RATE = SETTINGS.AUTO_PRUNE_MIN_RATE
    except: AUTO_PRUNE_MIN_RATE = 40.0

    en, dis = 0, 0
    skipped_pinned = 0
    try:
        bridges = get_all_managed_bridges(db_name, only_enabled=False)
        for b in bridges:
            try:
                is_pinned = b.get("is_pinned", 0)
                if is_pinned:
                    skipped_pinned += 1
                    continue
                
                wr = float(str(b.get("win_rate_text", "0")).replace("%", "") if b.get("win_rate_text") else "0")
                is_on = b["is_enabled"]
                old_desc = b["description"]
                
                if wr >= AUTO_PRUNE_MIN_RATE and not is_on:
                    update_managed_bridge(b["id"], old_desc, 1, db_name)
                    en += 1
                elif wr < AUTO_PRUNE_MIN_RATE and is_on:
                    update_managed_bridge(b["id"], old_desc, 0, db_name)
                    dis += 1
            except: pass
    except Exception as e: return f"Lỗi auto manage: {e}"
    
    msg = f"Quản lý tự động: BẬT {en}, TẮT {dis} (Ngưỡng {AUTO_PRUNE_MIN_RATE}%)."
    if skipped_pinned > 0:
        msg += f" Bỏ qua {skipped_pinned} cầu đã ghim."
    return msg

def init_all_756_memory_bridges_to_db(db_name=DB_NAME, progress_callback=None, enable_all=False):
    """(V8.1) Khởi tạo Bạc Nhớ ID Chuẩn V2.1"""
    print("Khởi tạo Bạc Nhớ chuẩn V2.1...")
    loto_names = get_27_loto_names()
    added = 0
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    _ensure_core_db_columns(cursor)
    
    for i in range(len(loto_names)):
        for j in range(i, len(loto_names)):
            # [NAMING V2.1]
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