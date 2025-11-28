# Tên file: git1/logic/bridges/bridge_manager_core.py
#
# (PHIÊN BẢN V7.9.10 - KHÔI PHỤC FULL LOGIC CŨ + TÍCH HỢP PHASE C + FIX DB)
#

import os
import sqlite3
import sys
from dataclasses import dataclass
from typing import List, Optional

# =========================================================================
# PATH FIX: Tự động thêm thư mục gốc (git1 - Sao chép/) vào sys.path
# =========================================================================
try:
    # Lấy đường dẫn thư mục hiện tại (logic/bridges)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Đi lên 2 cấp để lấy thư mục gốc (git1 - Sao chép/)
    project_root = os.path.dirname(os.path.dirname(current_dir))

    # Thêm thư mục gốc vào sys.path NẾU nó chưa có
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"[PATH FIX] Đã thêm {project_root} vào sys.path")
    else:
        print(f"[PATH FIX] {project_root} đã có trong sys.path")
except Exception as e_path:
    print(f"[PATH FIX] LỖI: Không thể thêm đường dẫn gốc: {e_path}")

# =========================================================================
# IMPORT SETTINGS & DB
# =========================================================================
try:
    # Dùng import tuyệt đối (từ gốc logic)
    from logic.config_manager import SETTINGS
    print("[IMPORT V4] Đã import thành công: SETTINGS")
except ImportError as e:
    print(f"[IMPORT V4] LỖI IMPORT SETTINGS: {e}")
    # Fallback an toàn
    SETTINGS = type("obj", (object,), {"AUTO_ADD_MIN_RATE": 50.0, "AUTO_PRUNE_MIN_RATE": 40.0})

# Import DB functions (CRUD và Management)
try:
    from logic.data_repository import get_all_managed_bridges
    from logic.db_manager import DB_NAME, update_managed_bridge, upsert_managed_bridge
    print("[IMPORT V4] Đã import thành công: data_repository, db_manager")
except ImportError as e:
    print(f"[IMPORT V4] LỖI IMPORT DB/REPO: {e}")
    DB_NAME = "data/xo_so_prizes_all_logic.db"
    def upsert_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def update_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def get_all_managed_bridges(*args, **kwargs): return []

# =========================================================================
# IMPORT HÀM CẦU (ĐẦY ĐỦ CHO CẢ LOGIC CŨ VÀ MỚI)
# =========================================================================
try:
    # 1. Import Classic Utils & 15 Hàm Cầu Cố Định (CHO PHASE C - MỚI)
    from logic.bridges.bridges_classic import (
        checkHitSet_V30_K2N, 
        getAllLoto_V30,
        # 15 Cầu Lô Cố Định
        getCau1_STL_P5_V30_V5, getCau2_VT1_V30_V5, getCau3_VT2_V30_V5,
        getCau4_VT3_V30_V5, getCau5_TDB1_V30_V5, getCau6_VT5_V30_V5,
        getCau7_Moi1_V30_V5, getCau8_Moi2_V30_V5, getCau9_Moi3_V30_V5,
        getCau10_Moi4_V30_V5, getCau11_Moi5_V30_V5, getCau12_Moi6_V30_V5,
        getCau13_G7_3_P8_V30_V5, getCau14_G1_P2_V30_V5, getCau15_DE_P7_V30_V5
    )
    
    # 2. Import Memory & V16 (CHO LOGIC CŨ - KHÔI PHỤC)
    from logic.bridges.bridges_memory import (
        calculate_bridge_stl,
        get_27_loto_names,
        get_27_loto_positions,
    )
    from logic.bridges.bridges_v16 import (
        getAllPositions_V17_Shadow,
        getPositionName_V17_Shadow,
        taoSTL_V30_Bong,
    )

    print("[IMPORT V4] Đã import thành công: Full Bridge Functions (Classic, V16, Memory)")
except ImportError as e:
    print(f"[IMPORT V4] LỖI IMPORT HÀM CẦU: {e}")
    # Định nghĩa hàm giả lập để tránh crash nếu thiếu file
    def getAllPositions_V17_Shadow(r): return []
    def getPositionName_V17_Shadow(i): return "Lỗi"
    def taoSTL_V30_Bong(a, b): return ["00", "00"]
    def calculate_bridge_stl(l1, l2, t): return ["00", "00"]
    def get_27_loto_names(): return []
    def get_27_loto_positions(r): return []
    def checkHitSet_V30_K2N(p, loto_set): return "Lỗi"
    def getAllLoto_V30(r): return []


# =========================================================================
# [PHASE C] BẢNG ÁNH XẠ 15 CẦU LÔ CỐ ĐỊNH (MAPPING TABLE) - MỚI
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
# 0. ĐỊNH NGHĨA DATA STRUCTURES (KHÔI PHỤC)
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
# 0. HELPER: SELF-HEALING DB (MỚI - TỰ VÁ LỖI THIẾU CỘT)
# ===================================================================================
def _ensure_core_db_columns(cursor):
    """Đảm bảo bảng ManagedBridges có đủ cột cần thiết cho Cầu Lô."""
    try:
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [info[1] for info in cursor.fetchall()]
        
        # Thêm cột type nếu thiếu
        if "type" not in columns:
            print(">>> [LO MANAGER] Tự động thêm cột 'type' vào DB...")
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN type TEXT DEFAULT 'UNKNOWN'")
            
        # Thêm các cột khác để đồng bộ
        if "recent_win_count_10" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN recent_win_count_10 INTEGER DEFAULT 0")
        if "next_prediction_stl" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN next_prediction_stl TEXT DEFAULT ''")
            
    except Exception as e:
        print(f"Lỗi Self-Healing DB (Core): {e}")

# ===================================================================================
# I. HÀM DÒ CẦU V17 SHADOW (KHÔI PHỤC NGUYÊN BẢN)
# ===================================================================================
def TIM_CAU_TOT_NHAT_V16(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME
):
    """
    (V7.0) Hàm dò cầu V17 (Shadow)
    """
    print("Bắt đầu Dò Cầu Tốt Nhất V17 (Shadow)...")

    allData, finalEndRow, startCheckRow, offset = (
        toan_bo_A_I,
        ky_ket_thuc_kiem_tra,
        ky_bat_dau_kiem_tra + 1,
        ky_bat_dau_kiem_tra,
    )

    headers = ["STT", "Cầu (V17 Shadow)", "Vị Trí", "Tỷ Lệ %", "Chuỗi"]
    results = [headers]

    try:
        positions_shadow = getAllPositions_V17_Shadow(allData[0])
        num_positions_shadow = len(positions_shadow)
    except:
        return [["LỖI:", "Không thể lấy Vị Trí V17 Shadow."]]

    if num_positions_shadow == 0:
        return [["LỖI:", "Không thể lấy Vị Trí V17 Shadow."]]

    algorithms = []
    for i in range(num_positions_shadow):
        for j in range(i, num_positions_shadow):
            algorithms.append((i, j))

    num_algorithms = len(algorithms)
    print(f"Đã tạo {num_algorithms} thuật toán V17. Bắt đầu tiền xử lý {len(allData)} hàng...")

    processedData = []
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        prevRow, actualRow = allData[prevRow_idx], allData[actualRow_idx]
        if (
            not prevRow
            or not actualRow
            or len(actualRow) < 10
        ):
            continue

        processedData.append(
            {
                "prevPositions": getAllPositions_V17_Shadow(prevRow),
                "actualLotoSet": set(getAllLoto_V30(actualRow)),
            }
        )

    print("Tiền xử lý hoàn tất. Bắt đầu dò cầu...")

    totalTestDays = len(processedData)
    if totalTestDays == 0:
        return [["LỖI:", "Không có dữ liệu hợp lệ để backtest."]]

    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE
    bridges_to_add = []

    for j in range(num_algorithms):
        alg = algorithms[j]
        idx1, idx2 = alg[0], alg[1]
        win_count, current_streak, max_streak = 0, 0, 0

        for dayData in processedData:
            prevPositions = dayData["prevPositions"]
            actualLotoSet = dayData["actualLotoSet"]
            a, b = prevPositions[idx1], prevPositions[idx2]
            if a is None or b is None:
                current_streak = 0
                continue

            pred_stl = taoSTL_V30_Bong(a, b)
            check_result = checkHitSet_V30_K2N(pred_stl, actualLotoSet)

            if "✅" in check_result:
                win_count += 1
                current_streak += 1
            else:
                current_streak = 0
            max_streak = max(max_streak, current_streak)

        if totalTestDays > 0:
            rate = (win_count / totalTestDays) * 100
            if rate >= AUTO_ADD_MIN_RATE:
                pos1_name = getPositionName_V17_Shadow(idx1)
                pos2_name = getPositionName_V17_Shadow(idx2)
                bridge_name = f"{pos1_name}+{pos2_name}"
                rate_str = f"{rate:.2f}%"

                results.append(
                    [
                        len(results),
                        bridge_name,
                        f"{pos1_name} + {pos2_name}",
                        rate_str,
                        f"{current_streak} (Max {max_streak})",
                    ]
                )
                bridges_to_add.append(
                    (bridge_name, bridge_name, rate_str, db_name, idx1, idx2)
                )

    if bridges_to_add:
        print(f"Dò cầu V17: Tự động thêm/cập nhật {len(bridges_to_add)} cầu...")
        try:
            # Dùng list comprehension để batch update
            [
                upsert_managed_bridge(n, d, r, db, i1, i2)
                for n, d, r, db, i1, i2 in bridges_to_add
            ]
        except Exception as e_db:
            print(f"Lỗi khi batch update cầu V17: {e_db}")

    print("Hoàn tất Dò Cầu Tốt Nhất V17.")
    return results


# ===================================================================================
# II. HÀM DÒ CẦU BẠC NHỚ (KHÔI PHỤC NGUYÊN BẢN)
# ===================================================================================
def TIM_CAU_BAC_NHO_TOT_NHAT(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME
):
    """
    (V7.0) Hàm dò cầu Bạc Nhớ
    """
    print("Bắt đầu Dò Cầu Bạc Nhớ Tốt Nhất (756 cầu)...")

    allData, finalEndRow, startCheckRow, offset = (
        toan_bo_A_I,
        ky_ket_thuc_kiem_tra,
        ky_bat_dau_kiem_tra + 1,
        ky_bat_dau_kiem_tra,
    )

    loto_names = get_27_loto_names()
    num_positions = len(loto_names)

    algorithms = []
    headers = ["STT", "Cầu (Bạc Nhớ)", "Vị Trí", "Tỷ Lệ %", "Chuỗi"]

    for i in range(num_positions):
        for j in range(i, num_positions):
            name_sum = f"Tổng({loto_names[i]} + {loto_names[j]})"
            algorithms.append((i, j, "sum", name_sum))
            name_diff = f"Hiệu(|{loto_names[i]} - {loto_names[j]}|)"
            algorithms.append((i, j, "diff", name_diff))

    num_algorithms = len(algorithms)
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
            or len(actualRow) < 10
        ):
            continue

        processedData.append(
            {
                "prevLotos": get_27_loto_positions(prevRow),
                "actualLotoSet": set(getAllLoto_V30(actualRow)),
            }
        )

    print("Tiền xử lý hoàn tất. Bắt đầu dò cầu...")

    totalTestDays = len(processedData)
    if totalTestDays == 0:
        return [["LỖI:", "Không có dữ liệu hợp lệ để backtest."]]

    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE
    bridges_to_add = []

    for j in range(num_algorithms):
        alg = algorithms[j]
        idx1, idx2, alg_type, alg_name = alg[0], alg[1], alg[2], alg[3]
        win_count, current_streak, max_streak = 0, 0, 0

        for dayData in processedData:
            prevLotos = dayData["prevLotos"]
            actualLotoSet = dayData["actualLotoSet"]
            loto1, loto2 = prevLotos[idx1], prevLotos[idx2]
            pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
            check_result = checkHitSet_V30_K2N(pred_stl, actualLotoSet)

            if "✅" in check_result:
                win_count += 1
                current_streak += 1
            else:
                current_streak = 0
            max_streak = max(max_streak, current_streak)

        if totalTestDays > 0:
            rate = (win_count / totalTestDays) * 100
            if rate >= AUTO_ADD_MIN_RATE:
                rate_str = f"{rate:.2f}%"
                results.append(
                    [
                        len(results),
                        alg_name,
                        f"{loto_names[idx1]} + {loto_names[idx2]}",
                        rate_str,
                        f"{current_streak} (Max {max_streak})",
                    ]
                )
                # Bạc nhớ (V17) có pos1_idx = -1
                bridges_to_add.append((alg_name, alg_name, rate_str, db_name, -1, -1))

    if bridges_to_add:
        print(f"Dò cầu Bạc Nhớ: Tự động thêm/cập nhật {len(bridges_to_add)} cầu...")
        try:
            [
                upsert_managed_bridge(n, d, r, db, i1, i2)
                for n, d, r, db, i1, i2 in bridges_to_add
            ]
        except Exception as e_db:
            print(f"Lỗi khi batch update cầu Bạc Nhớ: {e_db}")

    print("Hoàn tất Dò Cầu Bạc Nhớ.")
    return results

# ===================================================================================
# III. [MỚI] HÀM QUẢN LÝ 15 CẦU LÔ CỐ ĐỊNH (PHASE C) - ĐÃ FIX
# ===================================================================================
def _update_fixed_lo_bridges(all_data_ai, db_name):
    """
    (V2.1) Tính toán hiệu quả của 15 Cầu Lô Cố Định và lưu vào DB với ID chuẩn.
    Hàm này chạy song song với các logic cũ.
    """
    print(">>> [LO MANAGER] Đang cập nhật 15 Cầu Lô Cố Định (Phase C)...")
    if not all_data_ai or len(all_data_ai) < 10: return 0
    
    # Cấu hình check: 10 kỳ gần nhất
    check_days = 10 
    # Lấy buffer dữ liệu đủ để check
    scan_data = all_data_ai[- (check_days + 5):]
    
    updated_count = 0
    
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
        
        # Lưu vào DB với ID CHUẨN (LO_STL_FIXED_XX)
        try:
            # FIX: Sử dụng tham số vị trí thay vì từ khóa
            upsert_managed_bridge(
                bridge_id,          # name
                full_desc,          # description
                f"{win_rate:.0f}%", # win_rate_text
                db_name,            # db_name
                -1,                 # pos1_idx
                -1                  # pos2_idx
            )
            
            # Update chi tiết Type & Enabled
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            
            # [SELF-HEALING] Gọi hàm vá lỗi DB trước khi update
            _ensure_core_db_columns(cursor)
            
            is_enabled = 1 if win_rate >= 40 else 0
            
            cursor.execute("""
                UPDATE ManagedBridges 
                SET type='CAU_LO_FIXED', current_streak=?, next_prediction_stl=?, is_enabled=?
                WHERE name=?
            """, (current_streak, pred_val, is_enabled, bridge_id))
            conn.commit()
            conn.close()
            updated_count += 1
        except Exception as e:
            print(f"Lỗi update Fixed Bridge {bridge_id}: {e}")
            
    return updated_count

# ===================================================================================
# IV. HÀM QUẢN LÝ CHUNG (WRAPPER & PRUNE) - ĐÃ CẬP NHẬT
# ===================================================================================

def find_and_auto_manage_bridges(all_data_ai, db_name=DB_NAME):
    """
    (V7.9.10) Wrapper Tổng Hợp:
    1. Chạy dò cầu V17 Shadow (Logic Cũ - KHÔI PHỤC).
    2. Chạy dò cầu Bạc Nhớ (Logic Cũ - KHÔI PHỤC).
    3. Chạy cập nhật 15 Cầu Lô Cố Định (Logic Mới - Phase C).
    """
    try:
        if not all_data_ai: return "Lỗi: Không có dữ liệu A:I để dò cầu."
        
        msg = []
        
        # 1. Logic Cũ (V17 Shadow)
        print("... [Auto] Bắt đầu dò V17 Shadow (Classic) ...")
        ky_bat_dau = 2
        ky_ket_thuc = len(all_data_ai) + 1
        res_v17 = TIM_CAU_TOT_NHAT_V16(all_data_ai, ky_bat_dau, ky_ket_thuc, db_name)
        c_v17 = len(res_v17) - 1 if res_v17 else 0
        msg.append(f"V17 Shadow: {c_v17} cầu")
        
        # 2. Logic Cũ (Bạc Nhớ)
        print("... [Auto] Bắt đầu dò Bạc Nhớ (Classic) ...")
        res_bn = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, ky_bat_dau, ky_ket_thuc, db_name)
        c_bn = len(res_bn) - 1 if res_bn else 0
        msg.append(f"Bạc Nhớ: {c_bn} cầu")
        
        # 3. Logic Mới (Fixed Classic - Phase C)
        print("... [Auto] Cập nhật 15 Cầu Cố Định (New) ...")
        count_fix = _update_fixed_lo_bridges(all_data_ai, db_name)
        msg.append(f"Fixed Classic: {count_fix} cầu")
        
        return " | ".join(msg)
        
    except Exception as e:
        return f"Lỗi nghiêm trọng trong find_and_auto_manage_bridges: {e}"

def prune_bad_bridges(all_data_ai, db_name=DB_NAME):
    """(V7.0) Tự động TẮT các cầu yếu - Khôi phục nguyên bản"""
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
                # [PHASE 4 - PINNING] Bỏ qua cầu đã ghim
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
    """(V7.7) Tự động BẬT/TẮT cầu - Khôi phục nguyên bản"""
    try:
        AUTO_PRUNE_MIN_RATE = SETTINGS.AUTO_PRUNE_MIN_RATE
    except: AUTO_PRUNE_MIN_RATE = 40.0

    en, dis = 0, 0
    skipped_pinned = 0
    try:
        bridges = get_all_managed_bridges(db_name, only_enabled=False)
        for b in bridges:
            try:
                # [PHASE 4 - PINNING] Bỏ qua cầu đã ghim
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
    """(V7.0) Khởi tạo DB Bạc Nhớ - Khôi phục nguyên bản"""
    print("Bắt đầu nạp 756 cầu Bạc Nhớ vào database...")
    bridges_to_add = []
    total_bridges = 0
    
    for i in range(27):
        for j in range(i, 27):
            bridges_to_add.append((f"Tổng({i:02d}+{j:02d})", "Tổng", "N/A", db_name, -1, -1))
            total_bridges += 1
            bridges_to_add.append((f"Hiệu({i:02d}-{j:02d})", "Hiệu", "N/A", db_name, -1, -1))
            total_bridges += 1
            
    added_count, skipped_count = 0, 0
    for idx, (bridge_name, description, win_rate, db, pos1, pos2) in enumerate(bridges_to_add):
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM ManagedBridges WHERE name = ?", (bridge_name,))
            if cursor.fetchone():
                skipped_count += 1
            else:
                is_en = 1 if enable_all else 0
                cursor.execute(
                    "INSERT INTO ManagedBridges (name, description, win_rate_text, pos1_idx, pos2_idx, is_enabled) VALUES (?, ?, ?, ?, ?, ?)",
                    (bridge_name, description, win_rate, pos1, pos2, is_en)
                )
                conn.commit()
                added_count += 1
            conn.close()
            
            if progress_callback and (idx+1)%50==0:
                progress_callback(idx+1, total_bridges, f"Đã xử lý {idx+1}...")
        except: skipped_count += 1

    return True, f"Đã nạp {added_count} cầu Bạc Nhớ mới. Bỏ qua {skipped_count}.", added_count, skipped_count