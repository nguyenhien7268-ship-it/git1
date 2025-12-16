# Tên file: logic/bridges/bridge_manager_de.py
# (PHIÊN BẢN V8.0 - RESTORED & FIXED INDENTATION)

import os
import sys
import sqlite3
import re

# Import các tài nguyên chung
from logic.de_utils import get_touches_by_offset, generate_dan_de_from_touches, get_bo_name_by_pair, BO_SO_DE, get_gdb_last_2, get_set_name_of_number
try:
    from logic.config_manager import SETTINGS
    from logic.db_manager import DB_NAME, upsert_managed_bridge
    from logic.bridges.bridges_v16 import (
        getAllPositions_V17_Shadow,
        getPositionName_V17_Shadow,
        taoSTL_V30_Bong,
        get_index_from_name_V16,
    )
except ImportError as e:
    print(f"Lỗi Import trong bridge_manager_de: {e}")
    SETTINGS = None
    # Fallback path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    DB_NAME = os.path.join(project_root, "data", "xo_so_prizes_all_logic.db")

# ===================================================================================
# HELPER FUNCTIONS
# ===================================================================================
def _ensure_db_columns(cursor):
    """[SELF-HEALING] Kiểm tra và tự động thêm các cột thiếu trong DB."""
    try:
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [info[1] for info in cursor.fetchall()]

        if "recent_win_count_10" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN recent_win_count_10 INTEGER DEFAULT 0")
        
        if "type" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN type TEXT DEFAULT 'UNKNOWN'")
            
        if "next_prediction_stl" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN next_prediction_stl TEXT DEFAULT ''")
            
    except Exception as e:
        print(f"Lỗi Self-Healing DB: {e}")

# ===================================================================================
# V2.5: DE BRIDGE MANAGER
# ===================================================================================

class DeBridgeManager:
    """
    Trình quản lý Cầu Đề (V2.5)
    """
    def __init__(self):
        self.max_health = 3
        self.lookback_window = 10

    def update_daily_stats(self, all_data_ai):
        if not all_data_ai or len(all_data_ai) < self.lookback_window + 2: return 0, []
        
        print(">>> [DE MANAGER] Cập nhật Hồ Sơ Phong Độ...")
        last_row = all_data_ai[-1]; prev_row = all_data_ai[-2]
        gdb_today = get_gdb_last_2(last_row)
        pos_today = getAllPositions_V17_Shadow(last_row)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            _ensure_db_columns(cursor)
            conn.commit()
            cursor.execute("SELECT id, name, type, current_streak, recent_win_count_10, description FROM ManagedBridges WHERE is_enabled=1 AND (type LIKE 'DE_%' OR type LIKE 'CAU_DE%')")
            active_bridges = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Lỗi Đọc DB: {e}")
            conn.close()
            return 0, []
        
        updated_count = 0
        active_list_ui = []
        
        for br_id, name, b_type, streak, hp_db, desc in active_bridges:
            try:
                # PARSER V2.1: Phân tích ID Cầu
                parsed_info = self._parse_bridge_id_v2(name, b_type)
                if not parsed_info:
                    parsed_info = self._parse_bridge_id_legacy(name)
                
                if not parsed_info: continue 

                idx1, idx2, k_offset, mode = parsed_info

                # 1. Tính kết quả (Streak)
                pos_prev = getAllPositions_V17_Shadow(prev_row)
                dan_today = self._calculate_dan_logic(pos_prev, idx1, idx2, k_offset, mode, return_string=False)
                
                is_win = (gdb_today in dan_today) if (gdb_today and dan_today) else False
                
                current_hp = hp_db if (hp_db is not None and 0 <= hp_db <= self.max_health) else self.max_health
                new_streak = streak + 1 if is_win else 0
                new_hp = self.max_health if is_win else current_hp - 1
                
                # 2. Backtest 10 kỳ
                wins_10 = 0
                recent_data = all_data_ai[-11:] if len(all_data_ai) >= 11 else all_data_ai
                
                for i in range(min(10, len(recent_data) - 1)):
                    idx_today = len(recent_data) - 1 - i
                    idx_prev = idx_today - 1
                    if idx_prev < 0: break
                    
                    row_today_k = recent_data[idx_today]
                    row_prev_k = recent_data[idx_prev]
                    g_today = get_gdb_last_2(row_today_k)
                    if not g_today: continue
                    p_prev = getAllPositions_V17_Shadow(row_prev_k)
                    d_prev = self._calculate_dan_logic(p_prev, idx1, idx2, k_offset, mode, return_string=False)
                    if g_today in d_prev:
                        wins_10 += 1

                # Tính Search Rate
                search_rate_val = (wins_10 / 10.0) * 100
                new_search_rate = f"{search_rate_val:.0f}%"

                # 3. Sinh tồn & Xếp hạng
                is_enabled = 1 if new_hp > 0 else 0
                rank_score = (new_streak * 10) + (wins_10 * 5)
                
                # 4. Dự đoán ngày mai
                pred_display = ""
                if is_enabled:
                    pred_display = self._calculate_dan_logic(pos_today, idx1, idx2, k_offset, mode, return_string=True, display_mode=True)
                
                # 5. Cập nhật DB
                new_desc = desc.split(".")[0] if desc and "." in desc else (desc or name)
                new_desc += f". HP:{new_hp}/{self.max_health} | Win10:{wins_10}"
                
                cursor.execute("""
                    UPDATE ManagedBridges 
                    SET current_streak=?, recent_win_count_10=?, is_enabled=?, next_prediction_stl=?, description=?, search_rate_text=? 
                    WHERE id=?""", 
                    (new_streak, wins_10, is_enabled, pred_display, new_desc, new_search_rate, br_id))
                
                if is_enabled:
                    active_list_ui.append({
                        "name": name, 
                        "type": b_type, 
                        "streak": new_streak, 
                        "recent_win_count_10": wins_10,
                        "wins_10": wins_10,
                        "rank_score": rank_score, 
                        "predicted_value": pred_display,
                        "next_prediction_stl": pred_display,
                        "prediction": pred_display,
                        "hp": new_hp, 
                        "description": new_desc
                    })
                    updated_count += 1
            except Exception as e: 
                # print(f"Lỗi xử lý cầu {name}: {e}")
                continue
                
        conn.commit(); conn.close()
        return updated_count, sorted(active_list_ui, key=lambda x: x['rank_score'], reverse=True)

    def _parse_bridge_id_v2(self, name, b_type):
        """
        [FIXED] Parser hỗ trợ cả tên cũ và tên mới (dấu chấm/ngoặc).
        Sử dụng _map_safe_name_to_index để đảm bảo đọc được mọi định dạng.
        """
        try:
            if "DE_DYN" in name or b_type == "DE_DYNAMIC_K":
                parts = name.split("_")
                k_str = "0"
                for p in parts:
                    if p.startswith("K") and p[1:].isdigit():
                        k_str = p[1:]
                        break
                
                match = re.search(r"DE_DYN_(.+)_([^_]+)_K(\d+)", name)
                if match:
                    p1_str, p2_str, _ = match.groups()
                    idx1 = self._map_safe_name_to_index(p1_str) 
                    idx2 = self._map_safe_name_to_index(p2_str)
                    if idx1 is not None and idx2 is not None:
                        return idx1, idx2, int(k_str), "DYNAMIC"

            elif "DE_POS" in name or b_type == "DE_POS_SUM":
                match = re.search(r"DE_POS_(.+)_([^_]+)", name)
                if match:
                    p1_str, p2_str = match.groups()
                    idx1 = self._map_safe_name_to_index(p1_str)
                    idx2 = self._map_safe_name_to_index(p2_str)
                    if idx1 is not None and idx2 is not None:
                        return idx1, idx2, 0, "POS_SUM"
            
            elif "DE_SET" in name or b_type == "DE_SET":
                match = re.search(r"DE_SET_(.+)_([^_]+)", name)
                if match:
                    p1_str, p2_str = match.groups()
                    idx1 = self._map_safe_name_to_index(p1_str)
                    idx2 = self._map_safe_name_to_index(p2_str)
                    
                    if idx1 is None: idx1 = self._map_std_name_to_index(p1_str)
                    if idx2 is None: idx2 = self._map_std_name_to_index(p2_str)
                    
                    if idx1 is not None and idx2 is not None:
                        return idx1, idx2, 0, "SET"
                    
        except: return None
        return None

    def _parse_bridge_id_legacy(self, name):
        try:
            match = re.match(r"(.+)\+(.+) \((.+)\)", name)
            if match:
                p1, p2, suffix = match.groups()
                idx1 = get_index_from_name_V16(p1.strip())
                idx2 = get_index_from_name_V16(p2.strip())
                return idx1, idx2, 0, "LEGACY_V17"
        except: pass
        return None

    def _map_std_name_to_index(self, std_name):
        mapping = {
            "GDB": 4, "G1": 9, "G2": 19, "G3": 49, 
            "G4": 65, "G5": 89, "G6": 98, "G7": 106
        }
        return mapping.get(std_name, None)

    def _map_safe_name_to_index(self, safe_name):
        """
        [FIXED] Phân tích tên vị trí linh hoạt.
        Hỗ trợ: G2.1[0], G2.1.0, G2.1[0
        """
        try:
            # Regex mới chấp nhận dấu . và [
            match = re.match(r"(G\d+\.?\d*|GDB)[\[\.]?(\d+)", safe_name)
            
            if match:
                g_name, g_idx = match.groups()
                # Tái tạo về format chuẩn mà thư viện V16 hiểu
                reconstructed = f"{g_name}[{g_idx}]"
                return get_index_from_name_V16(reconstructed)
            return None
        except: return None

    def _calculate_dan_logic(self, positions, idx1, idx2, k_offset, mode, return_string=False, display_mode=False):
        try:
            if idx1 is None or idx2 is None: return [] if not return_string else ""
            
            # Kiểm tra bounds
            if idx1 >= len(positions) or idx2 >= len(positions):
                 return [] if not return_string else ""

            v1_raw = positions[idx1]
            v2_raw = positions[idx2]
            
            if v1_raw is None or v2_raw is None:
                return [] if not return_string else ""

            v1 = int(v1_raw)
            v2 = int(v2_raw)

            base_sum = 0
            if mode == "DYNAMIC":
                base_sum = (v1 + v2) % 10
            elif mode == "POS_SUM" or mode == "LEGACY_V17":
                base_sum = (v1 + v2) % 10
            elif mode == "SET":
                combined_number = f"{v1}{v2}"
                set_name = get_set_name_of_number(combined_number)
                if set_name:
                    set_numbers = BO_SO_DE.get(set_name, [])
                    if display_mode:
                        return f"Bộ {set_name}"
                    if return_string:
                        return ",".join(set_numbers)
                    else:
                        return set_numbers
                else:
                    return [] if not return_string else ""
            
            # Tính các chạm
            touches = []
            if mode == "DYNAMIC":
                 touches = get_touches_by_offset(base_sum, k_offset) 
            else:
                 touches = [base_sum, (base_sum+5)%10]
            
            if display_mode:
                t_str = ", ".join(map(str, sorted(list(set(touches)))))
                return t_str
            
            final_dan = generate_dan_de_from_touches(touches)
            return ",".join(final_dan) if return_string else final_dan

        except: return [] if not return_string else ""

de_manager = DeBridgeManager()

def find_and_auto_manage_bridges_de(all_data_ai, db_name=DB_NAME):
    from logic.bridges.de_bridge_scanner import run_de_scanner
    count, _ = run_de_scanner(all_data_ai)
    return f"Đã cập nhật {count} cầu Đề."
