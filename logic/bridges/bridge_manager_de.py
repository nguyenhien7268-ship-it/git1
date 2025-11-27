import os
import sys
import sqlite3
import re

# Import các tài nguyên chung
from logic.de_utils import get_touches_by_offset, generate_dan_de_from_touches, get_bo_name_by_pair, BO_SO_DE, get_gdb_last_2
try:
    from logic.config_manager import SETTINGS
    # Import DB_NAME và hàm upsert từ db_manager (Nơi định nghĩa chuẩn ManagedBridges)
    from logic.db_manager import DB_NAME, upsert_managed_bridge
    # Lấy thuật toán V17 từ thư viện cầu
    from logic.bridges.bridges_v16 import (
        getAllPositions_V17_Shadow,
        getPositionName_V17_Shadow,
        taoSTL_V30_Bong,
        get_index_from_name_V16,
    )
except ImportError as e:
    print(f"Lỗi Import trong bridge_manager_de: {e}")
    SETTINGS = None
    # Fallback path nếu import thất bại (Cần khớp với db_manager.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    DB_NAME = os.path.join(project_root, "data", "xo_so_prizes_all_logic.db")

# ===================================================================================
# HELPER FUNCTIONS (Dành riêng cho Đề)
# ===================================================================================
BONG_DUONG_MAP = {0: 5, 1: 6, 2: 7, 3: 8, 4: 9, 5: 0, 6: 1, 7: 2, 8: 3, 9: 4}

def get_4_touches(stl_pair):
    """Từ STL ['XY', 'YX'] suy ra 4 chạm (X, Y, Bóng X, Bóng Y)."""
    touches = set()
    for s in stl_pair:
        if s and s.isdigit():
            d1, d2 = int(s[0]), int(s[1])
            touches.update([d1, d2, BONG_DUONG_MAP.get(d1, d1), BONG_DUONG_MAP.get(d2, d2)])
    return touches

def check_hit_de_4_touches(stl_pair, gdb_str):
    """Kiểm tra xem GĐB có nằm trong 4 chạm của cầu không."""
    if not gdb_str or len(gdb_str) < 2: return False
    touches = get_4_touches(stl_pair)
    try:
        gdb_vals = {int(gdb_str[-2]), int(gdb_str[-1])}
        return not touches.isdisjoint(gdb_vals)
    except:
        return False

def _ensure_db_columns(cursor):
    """
    [SELF-HEALING] Kiểm tra và tự động thêm các cột thiếu trong DB.
    Sử dụng đúng tên bảng: ManagedBridges
    """
    try:
        # Lấy danh sách cột hiện tại
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [info[1] for info in cursor.fetchall()]

        # 1. Kiểm tra cột 'recent_win_count_10'
        if "recent_win_count_10" not in columns:
            print(">>> [DE MANAGER] Đang thêm cột 'recent_win_count_10' vào ManagedBridges...")
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN recent_win_count_10 INTEGER DEFAULT 0")
        
        # 2. Kiểm tra cột 'type' (QUAN TRỌNG)
        if "type" not in columns:
            print(">>> [DE MANAGER] Đang thêm cột 'type' vào ManagedBridges...")
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN type TEXT DEFAULT 'UNKNOWN'")
            
            # [DATA MIGRATION] Tự động cập nhật type cho dữ liệu cũ
            print(">>> [DE MANAGER] Đang phân loại lại cầu cũ (Data Migration)...")
            cursor.execute("UPDATE ManagedBridges SET type='DE_V17' WHERE name LIKE 'Đề %'")
            cursor.execute("UPDATE ManagedBridges SET type='CAU_BAC_NHO' WHERE name LIKE 'Tổng(%' OR name LIKE 'Hiệu(%'")
            cursor.execute("UPDATE ManagedBridges SET type='CAU_LO' WHERE type='UNKNOWN' AND name NOT LIKE 'Đề %'")
            
    except Exception as e:
        print(f"Lỗi Self-Healing DB: {e}")

# ===================================================================================
# LOGIC DÒ CẦU & QUẢN LÝ (CORE DE)
# ===================================================================================
def TIM_CAU_DE_TOT_NHAT(
    toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, db_name=DB_NAME
):
    """
    Dò tìm Cầu Đề V17 (4 Chạm) tốt nhất.
    """
    print(">>> [DE SYSTEM] Bắt đầu Dò Cầu Đề V17 (4 Chạm)...")
    allData = toan_bo_A_I
    if not allData or len(allData) < 10:
        return []
    
    positions_shadow = getAllPositions_V17_Shadow(allData[0])
    num_positions = len(positions_shadow)
    if num_positions == 0: return []
    
    algorithms = []
    for i in range(num_positions):
        for j in range(i, num_positions):
            algorithms.append((i, j))
    num_algorithms = len(algorithms)
    print(f">>> [DE SYSTEM] Đã tạo {num_algorithms} cặp vị trí. Đang xử lý dữ liệu...")
    
    # Pre-process Data
    start_idx = 2
    end_idx = len(allData) - 1
    cache_history = []
    for k in range(len(allData)):
        row = allData[k]
        gdb = str(row[2]) if len(row) > 2 else "00"
        if not gdb or gdb == 'nan': gdb = "00"
        cache_history.append({
            "positions": getAllPositions_V17_Shadow(row),
            "gdb": gdb.strip()
        })
        
    results = [["STT", "Cầu Đề (V17)", "Vị Trí", "Tỷ Lệ N1", "Tỷ Lệ K2N", "Chuỗi N1"]]
    bridges_to_add = []
    min_rate = 40.0
    try:
        if SETTINGS: min_rate = SETTINGS.AUTO_ADD_MIN_RATE - 10.0
    except: pass
    
    # Quét thuật toán
    for j in range(num_algorithms):
        idx1, idx2 = algorithms[j]
        wins_n1 = 0
        wins_k2n = 0
        current_streak = 0
        total_days = 0
        for k in range(start_idx, end_idx + 1):
            prev_data = cache_history[k-1]
            actual_data_k = cache_history[k]
            
            p1, p2 = prev_data["positions"][idx1], prev_data["positions"][idx2]
            if p1 is None or p2 is None:
                current_streak = 0; continue
                
            pred_stl = taoSTL_V30_Bong(p1, p2)
            is_win_n1 = check_hit_de_4_touches(pred_stl, actual_data_k["gdb"])
            
            is_win_n2 = False
            if not is_win_n1 and k + 1 < len(cache_history):
                actual_data_k1 = cache_history[k+1]
                is_win_n2 = check_hit_de_4_touches(pred_stl, actual_data_k1["gdb"])
            
            total_days += 1
            if is_win_n1:
                wins_n1 += 1; wins_k2n += 1; current_streak += 1
            else:
                current_streak = 0
                if is_win_n2: wins_k2n += 1
                
        if total_days > 10:
            rate_n1 = (wins_n1 / total_days) * 100
            rate_k2n = (wins_k2n / total_days) * 100
            if rate_k2n >= min_rate:
                pos1_name = getPositionName_V17_Shadow(idx1)
                pos2_name = getPositionName_V17_Shadow(idx2)
                bridge_name = f"Đề {pos1_name}+{pos2_name} (V17)"
                results.append([
                    len(results), bridge_name, f"{idx1}+{idx2}",
                    f"{rate_n1:.1f}%", f"{rate_k2n:.1f}%", str(current_streak)
                ])
                desc = f"Cầu Đề V17. N1: {rate_n1:.1f}%, K2N: {rate_k2n:.1f}%"
                bridges_to_add.append((bridge_name, desc, f"{rate_k2n:.1f}%", db_name, idx1, idx2))
    
    # Batch update DB
    count = 0
    if bridges_to_add:
        bridges_to_add.sort(key=lambda x: float(x[2].replace("%", "")), reverse=True)
        top_bridges = bridges_to_add[:50]
        print(f">>> [DE SYSTEM] Tìm thấy {len(bridges_to_add)} cầu. Đang lưu Top {len(top_bridges)}...")
        
        # 1. Lưu cầu (Insert/Update)
        for b in top_bridges:
            try:
                upsert_managed_bridge(b[0], b[1], b[2], b[3], b[4], b[5])
                count += 1
            except Exception as e:
                print(f"Lỗi lưu cầu đề {b[0]}: {e}")
        
        # 2. Cập nhật Type cho cầu vừa lưu
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            _ensure_db_columns(cursor) # Đảm bảo cột type tồn tại
            cursor.execute("UPDATE ManagedBridges SET type='DE_V17' WHERE name LIKE 'Đề %'")
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Lỗi cập nhật type: {e}")

    print(f">>> [DE SYSTEM] Hoàn tất. Đã lưu {count} cầu Đề.")
    return count

def find_and_auto_manage_bridges_de(all_data_ai, db_name=DB_NAME):
    try:
        if not all_data_ai: return "Lỗi: Không có dữ liệu."
        count = TIM_CAU_DE_TOT_NHAT(all_data_ai, 0, 0, db_name)
        return f"Đã cập nhật {count} cầu Đề (V17 4 Chạm)."
    except Exception as e:
        return f"Lỗi Dò Cầu Đề: {e}"

# ===================================================================================
# V78: DE BRIDGE MANAGER (Survival & Performance Profile)
# ===================================================================================

class DeBridgeManager:
    def __init__(self):
        self.max_health = 3
        self.lookback_window = 10

    def update_daily_stats(self, all_data_ai):
        if not all_data_ai or len(all_data_ai) < self.lookback_window + 2: return 0, []
        
        print(">>> [DE V78] Cập nhật Hồ Sơ Phong Độ...")
        last_row = all_data_ai[-1]; prev_row = all_data_ai[-2]
        gdb_today = get_gdb_last_2(last_row)
        pos_today = getAllPositions_V17_Shadow(last_row)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            # [FIX] Gọi hàm đảm bảo cấu trúc DB trước
            _ensure_db_columns(cursor)
            conn.commit()

            # [FIX] Sử dụng chính xác tên bảng ManagedBridges (CamelCase)
            cursor.execute("SELECT id, name, type, current_streak, recent_win_count_10 FROM ManagedBridges WHERE is_enabled=1 AND (type LIKE 'CAU_%' OR type LIKE 'DE_%' OR type LIKE '%BO%')")
            active_bridges = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Lỗi Đọc DB: {e}. Vui lòng chạy init_db_fix.py trước!")
            conn.close()
            return 0, []
        
        updated_count = 0
        active_list_ui = []
        data_window = all_data_ai[-(self.lookback_window + 2):-1] 
        
        for br_id, name, b_type, streak, hp_db in active_bridges:
            try:
                match = re.match(r"(.+)\+(.+) \((.+)\)", name)
                if not match: continue

                p1, p2, suffix = match.groups()
                idx1 = get_index_from_name_V16(p1.strip()); idx2 = get_index_from_name_V16(p2.strip())
                if idx1 is None or idx2 is None: continue
                
                # Check Win Hôm Nay
                pos_prev = getAllPositions_V17_Shadow(prev_row)
                dan_today = self._calculate_dan(int(pos_prev[idx1]), int(pos_prev[idx2]), suffix)
                is_win = (gdb_today in dan_today) if (gdb_today and dan_today) else False
                
                current_hp = hp_db if (hp_db is not None and 0 <= hp_db <= self.max_health) else self.max_health
                new_streak = streak + 1 if is_win else 0
                new_hp = self.max_health if is_win else current_hp - 1
                
                # Tính Win10
                wins_10 = 0
                for k in range(len(data_window) - 1):
                    row_k = data_window[k]; row_n = data_window[k+1]
                    g_next = get_gdb_last_2(row_n)
                    if not g_next: continue
                    p_k = getAllPositions_V17_Shadow(row_k)
                    d_k = self._calculate_dan(int(p_k[idx1]), int(p_k[idx2]), suffix)
                    if g_next in d_k: wins_10 += 1
                if is_win: wins_10 += 1
                wins_10 = min(wins_10, 10)

                is_enabled = 1 if new_hp > 0 else 0
                rank_score = (new_streak * 10) + (wins_10 * 5)
                
                pred_next = ""
                if is_enabled:
                    v1, v2 = int(pos_today[idx1]), int(pos_today[idx2])
                    pred_next = self._calculate_dan(v1, v2, suffix, return_string=True)
                
                desc = f"HP:{new_hp}/{self.max_health} | Form:{wins_10}/10"
                cursor.execute("UPDATE ManagedBridges SET current_streak=?, recent_win_count_10=?, is_enabled=?, next_prediction_stl=?, description=? WHERE id=?", 
                              (new_streak, wins_10, is_enabled, pred_next, desc, br_id))
                
                if is_enabled:
                    active_list_ui.append({"name": name, "type": b_type, "streak": new_streak, "wins_10": wins_10, "rank_score": rank_score, "predicted_value": pred_next, "hp": new_hp})
                    updated_count += 1
            except: continue
                
        conn.commit(); conn.close()
        return updated_count, sorted(active_list_ui, key=lambda x: x['rank_score'], reverse=True)

    def _calculate_dan(self, v1, v2, suffix, return_string=False):
        try:
            if "V17" in suffix or "4 Chạm" in suffix:
                stl = taoSTL_V30_Bong(v1, v2)
                touches = get_4_touches(stl)
                t_list = sorted(list(touches))
                return ",".join(map(str, t_list)) if return_string else generate_dan_de_from_touches(t_list)

            detected_bo = None; touches = set()
            if "Bộ" in suffix: detected_bo = get_bo_name_by_pair(v1, v2)
            elif "T" in suffix or "V" in suffix:
                k = int(suffix.split("+")[1]) if "+" in suffix else 0
                mode = "TONG" if "T" in suffix else "VITRI"
                base = (v1+v2)%10 if mode=="TONG" else v1
                touches = get_touches_by_offset(base, k, mode)
                t_set = set(touches)
                for bn, bnums in BO_SO_DE.items():
                    bd = set(int(x[0]) for x in bnums) | set(int(x[1]) for x in bnums)
                    if t_set == bd: detected_bo = bn; break
            
            if detected_bo:
                return f"Bộ {detected_bo}" if return_string else BO_SO_DE[detected_bo]
            else:
                t_list = sorted(list(touches))
                return ",".join(map(str, t_list)) if return_string else generate_dan_de_from_touches(t_list)
        except: return []

de_manager = DeBridgeManager()