# Tên file: logic/bridges/lo_bridge_scanner.py
# (PHIÊN BẢN V1.0 - TÁCH LOGIC SCANNING TỪ BRIDGE_MANAGER_CORE)
#
# Mục đích: Tách riêng logic Dò tìm (Scanning/Discovery) cầu Lô
#           khỏi logic Quản lý (Management) để tuân thủ SRP.

import os
import sqlite3
import sys
from typing import Dict

# =========================================================================
# PATH FIX
# =========================================================================
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    pass

# =========================================================================
# IMPORTS
# =========================================================================
try:
    from logic.config_manager import SETTINGS
except ImportError:
    SETTINGS = type("obj", (object,), {"AUTO_ADD_MIN_RATE": 50.0, "AUTO_PRUNE_MIN_RATE": 40.0})

try:
    from logic.data_repository import get_all_managed_bridges
    from logic.db_manager import (
        DB_NAME, upsert_managed_bridge,
        update_bridge_k2n_cache_batch
    )
except ImportError:
    DB_NAME = "data/xo_so_prizes_all_logic.db"
    def upsert_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def update_bridge_k2n_cache_batch(*args, **kwargs): return False, "Lỗi Import"
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

# =========================================================================
# HELPER FUNCTIONS
# =========================================================================
def _sanitize_name_v2(name):
    """Sanitize bridge name for safe database storage."""
    return name.replace("[", "_").replace("]", "").replace("(", "_").replace(")", "").replace(".", "_").replace("+", "_").replace(" ", "")


def _ensure_core_db_columns(cursor):
    """Ensure required database columns exist."""
    try:
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [info[1] for info in cursor.fetchall()]
        if "type" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN type TEXT DEFAULT 'UNKNOWN'")
        if "search_rate_text" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN search_rate_text TEXT DEFAULT ''")
    except:
        pass


def _get_existing_bridges_map(db_name) -> Dict:
    """Helper: Lấy toàn bộ cầu hiện có để tra cứu K1N cũ."""
    try:
        bridges = get_all_managed_bridges(db_name)
        # Trả về Set các tên cầu để check nhanh
        return {b['name']: b.get('win_rate_text', 'N/A') for b in bridges}
    except Exception:
        return {}


# ===================================================================================
# I. HÀM DÒ CẦU V17 SHADOW (FIXED: FORCE UPDATE OLD BRIDGES)
# ===================================================================================
def TIM_CAU_TOT_NHAT_V16(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """
    Dò tìm các cầu Lô Vị Trí (V17 Shadow) tốt nhất.
    
    Args:
        toan_bo_A_I: Dữ liệu toàn bộ kỳ quay
        ky_bat_dau_kiem_tra: Kỳ bắt đầu kiểm tra
        ky_ket_thuc_kiem_tra: Kỳ kết thúc kiểm tra
        db_name: Đường dẫn database
        
    Returns:
        List of results with bridge information
    """
    print("Bắt đầu Dò Cầu Lô Vị Trí (V17 Shadow) - Chế độ Force Update...")
    allData, finalEndRow, startCheckRow, offset = toan_bo_A_I, ky_ket_thuc_kiem_tra, ky_bat_dau_kiem_tra + 1, ky_bat_dau_kiem_tra
    headers = ["STT", "Cầu (V17)", "Vị Trí", "Tỷ Lệ K2N (Scan)", "Chuỗi"]
    results = [headers]

    last_row_real = allData[-1]
    try:
        last_positions = getAllPositions_V17_Shadow(last_row_real)
    except:
        return results

    # Danh sách cầu đang có trong DB (để ép cập nhật)
    existing_bridges_map = _get_existing_bridges_map(db_name)

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

    processedData = []
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        processedData.append({
            "prevPositions": getAllPositions_V17_Shadow(allData[prevRow_idx]),
            "actualLotoSet": set(getAllLoto_V30(allData[actualRow_idx])),
        })

    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE
    bridges_to_upsert = []
    bridges_to_cache = []

    for idx1, idx2 in algorithms:
        # 1. Tạo tên cầu trước để check tồn tại
        pos1_name = getPositionName_V17_Shadow(idx1)
        pos2_name = getPositionName_V17_Shadow(idx2)
        safe_p1 = _sanitize_name_v2(pos1_name)
        safe_p2 = _sanitize_name_v2(pos2_name)
        std_id = f"LO_POS_{safe_p1}_{safe_p2}"

        # 2. Tính toán hiệu suất quá khứ
        win_count, current_streak, max_streak = 0, 0, 0
        for dayData in processedData:
            a, b = dayData["prevPositions"][idx1], dayData["prevPositions"][idx2]
            if a is None or b is None:
                current_streak = 0
                continue
            
            if "✅" in checkHitSet_V30_K2N(taoSTL_V30_Bong(a, b), dayData["actualLotoSet"]):
                win_count += 1
                current_streak += 1
            else:
                current_streak = 0
            max_streak = max(max_streak, current_streak)

        totalTestDays = len(processedData)
        if totalTestDays > 0:
            scan_rate = (win_count / totalTestDays) * 100
            scan_rate_str = f"{scan_rate:.2f}%"

            # 3. QUYẾT ĐỊNH CÓ LƯU KHÔNG?
            # Lưu nếu: (Tỷ lệ cao) HOẶC (Cầu đã có trong DB cần update số liệu mới)
            is_good_bridge = (scan_rate >= AUTO_ADD_MIN_RATE)
            is_existing_bridge = (std_id in existing_bridges_map)

            if is_good_bridge or is_existing_bridge:
                
                # Tính dự đoán (Fix N/A do số 0)
                try:
                    p1_val = last_positions[idx1]
                    p2_val = last_positions[idx2]
                    
                    if p1_val is not None and p2_val is not None and str(p1_val) != "" and str(p2_val) != "":
                        next_stl = taoSTL_V30_Bong(p1_val, p2_val)
                        next_pred_str = ",".join(next_stl)
                    else:
                        next_pred_str = "N/A"
                except:
                    next_pred_str = "Error"

                # Logic K1N
                preserved_k1n = scan_rate_str
                if is_existing_bridge:
                    old_k1n = existing_bridges_map[std_id]
                    if old_k1n and old_k1n not in ['N/A', '', None]:
                         preserved_k1n = old_k1n

                # Chỉ thêm vào results hiển thị nếu là cầu tốt (để log đỡ rác)
                if is_good_bridge:
                    results.append([len(results), std_id, f"{pos1_name}+{pos2_name}", scan_rate_str, f"{current_streak}"])

                # NHƯNG luôn đẩy vào queue cập nhật DB
                bridge_data_dict = {
                    "pos1_idx": idx1, "pos2_idx": idx2,
                    "search_rate_text": scan_rate_str,
                    "search_period": totalTestDays,
                    "is_enabled": 1,
                    "type": "LO_POS"
                }
                bridges_to_upsert.append((std_id, f"Vị trí: {pos1_name} + {pos2_name}", preserved_k1n, db_name, idx1, idx2, bridge_data_dict))
                bridges_to_cache.append((scan_rate_str, current_streak, next_pred_str, max_streak, std_id))

    if bridges_to_upsert:
        print(f"Dò cầu V17: Đang cập nhật {len(bridges_to_upsert)} cầu (bao gồm cầu cũ)...")
        try:
            [upsert_managed_bridge(n, d, r, db, i1, i2, data_dict) for n, d, r, db, i1, i2, data_dict in bridges_to_upsert]
            update_bridge_k2n_cache_batch(bridges_to_cache, db_name)
            conn = sqlite3.connect(db_name)
            conn.execute("UPDATE ManagedBridges SET type='LO_POS' WHERE name LIKE 'LO_POS_%'")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Lỗi lưu cầu V17: {e}")

    return results


# ===================================================================================
# II. HÀM DÒ CẦU BẠC NHỚ (FIXED: FORCE UPDATE OLD BRIDGES)
# ===================================================================================
def TIM_CAU_BAC_NHO_TOT_NHAT(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME):
    """
    Dò tìm các cầu Bạc Nhớ tốt nhất.
    
    Args:
        toan_bo_A_I: Dữ liệu toàn bộ kỳ quay
        ky_bat_dau_kiem_tra: Kỳ bắt đầu kiểm tra
        ky_ket_thuc_kiem_tra: Kỳ kết thúc kiểm tra
        db_name: Đường dẫn database
        
    Returns:
        List of results with bridge information
    """
    print("Bắt đầu Dò Cầu Bạc Nhớ - Chế độ Force Update...")
    allData, finalEndRow, startCheckRow, offset = toan_bo_A_I, ky_ket_thuc_kiem_tra, ky_bat_dau_kiem_tra + 1, ky_bat_dau_kiem_tra
    loto_names = get_27_loto_names()
    processedData = []
    
    last_row_real = allData[-1]
    try:
        last_lotos = get_27_loto_positions(last_row_real)
    except:
        return []

    existing_bridges_map = _get_existing_bridges_map(db_name)

    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(allData) or prevRow_idx < 0:
            continue
        processedData.append({
            "prevLotos": get_27_loto_positions(allData[prevRow_idx]),
            "actualLotoSet": set(getAllLoto_V30(allData[actualRow_idx])),
        })

    AUTO_ADD_MIN_RATE = SETTINGS.AUTO_ADD_MIN_RATE
    bridges_to_upsert = []
    bridges_to_cache = []
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
                win_count += 1
                current_streak += 1
            else:
                current_streak = 0
            max_streak = max(max_streak, current_streak)

        totalTestDays = len(processedData)
        if totalTestDays > 0:
            scan_rate = (win_count / totalTestDays) * 100
            scan_rate_str = f"{scan_rate:.2f}%"
            
            is_good = (scan_rate >= AUTO_ADD_MIN_RATE)
            is_exist = (std_id in existing_bridges_map)

            if is_good or is_exist:
                try:
                    val1 = last_lotos[idx1]
                    val2 = last_lotos[idx2]
                    if val1 is not None and val2 is not None:
                        next_stl = calculate_bridge_stl(val1, val2, alg_type)
                        next_pred_str = ",".join(next_stl)
                    else:
                        next_pred_str = "N/A"
                except:
                    next_pred_str = "Error"

                preserved_k1n = scan_rate_str 
                if is_exist:
                    old_k1n = existing_bridges_map[std_id]
                    if old_k1n and old_k1n not in ['N/A', '', None]:
                        preserved_k1n = old_k1n

                if is_good:
                    results.append([len(results), std_id, desc, scan_rate_str, f"{current_streak}"])

                bridge_data = {
                    "pos1_idx": -1, "pos2_idx": -1,
                    "search_rate_text": scan_rate_str,
                    "search_period": totalTestDays,
                    "is_enabled": 1,
                    "type": "LO_MEM"
                }
                
                bridges_to_upsert.append((std_id, desc, preserved_k1n, db_name, -1, -1, bridge_data))
                bridges_to_cache.append((scan_rate_str, current_streak, next_pred_str, max_streak, std_id))

    if bridges_to_upsert:
        print(f"Dò Bạc Nhớ: Đang cập nhật {len(bridges_to_upsert)} cầu (bao gồm cầu cũ)...")
        try:
            [upsert_managed_bridge(n, d, r, db, i1, i2, data_dict) for n, d, r, db, i1, i2, data_dict in bridges_to_upsert]
            update_bridge_k2n_cache_batch(bridges_to_cache, db_name)
            conn = sqlite3.connect(db_name)
            conn.execute("UPDATE ManagedBridges SET type='LO_MEM' WHERE name LIKE 'LO_MEM_%'")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Lỗi lưu Bạc Nhớ: {e}")

    return results


# ===================================================================================
# III. HÀM CẬP NHẬT CẦU CỐ ĐỊNH
# ===================================================================================
def update_fixed_lo_bridges(all_data_ai, db_name):
    """
    Cập nhật 15 cầu Lô Cố Định (Fixed Bridges).
    
    Args:
        all_data_ai: Dữ liệu toàn bộ kỳ quay
        db_name: Đường dẫn database
        
    Returns:
        Number of bridges updated
    """
    print(">>> [LO MANAGER] Đang cập nhật 15 Cầu Lô Cố Định (Phase C - Fix N/A)...")
    if not all_data_ai or len(all_data_ai) < 10:
        return 0
    
    check_days = 10 
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
        
        for i in range(len(scan_data) - 1 - check_days, len(scan_data) - 1):
            if i < 0:
                continue
            row_prev = scan_data[i]
            row_next = scan_data[i+1]
            try:
                stl = func(row_prev)
                lotos_next = set(getAllLoto_V30(row_next))
                if "✅" in checkHitSet_V30_K2N(stl, lotos_next):
                    wins += 1
                    current_streak += 1
                else:
                    current_streak = 0
            except:
                pass
            
        last_row = all_data_ai[-1]
        try:
            next_stl = func(last_row)
            pred_val = f"{next_stl[0]},{next_stl[1]}"
        except: 
            pred_val = "Error"
            
        win_rate = (wins / check_days) * 100
        full_desc = f"{desc}. Phong độ {wins}/{check_days}."
        rate_str = f"{win_rate:.0f}%"
        
        try:
            cursor.execute("SELECT count(*) FROM ManagedBridges WHERE name=?", (bridge_id,))
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                cursor.execute("""
                    INSERT INTO ManagedBridges (name, description, win_rate_text, search_rate_text, current_streak, next_prediction_stl, is_enabled, type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (bridge_id, full_desc, rate_str, rate_str, current_streak, pred_val, 1 if win_rate>=40 else 0, 'LO_STL_FIXED'))
            else:
                cursor.execute("""
                    UPDATE ManagedBridges 
                    SET description=?, win_rate_text=?, search_rate_text=?, current_streak=?, next_prediction_stl=?, is_enabled=?, type='LO_STL_FIXED'
                    WHERE name=?
                """, (full_desc, rate_str, rate_str, current_streak, pred_val, 1 if win_rate>=40 else 0, bridge_id))
            updated_count += 1
        except Exception as e: 
            print(f"Lỗi update Fixed Bridge {bridge_id}: {e}")
            
    conn.commit()
    conn.close()
    return updated_count
