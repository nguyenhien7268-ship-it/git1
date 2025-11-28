# Tên file: logic/bridges/bridge_manager_de.py
# (PHIÊN BẢN V7.9.8 - FIX CRITICAL: THÊM CỘT 'next_prediction_stl' VÀO DB)

import os
import sys
import sqlite3
import re

# Import các tài nguyên chung
from logic.de_utils import get_touches_by_offset, generate_dan_de_from_touches, get_bo_name_by_pair, BO_SO_DE, get_gdb_last_2
try:
    from logic.config_manager import SETTINGS
    # Import DB_NAME và hàm upsert từ db_manager
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
    # Fallback path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    DB_NAME = os.path.join(project_root, "data", "xo_so_prizes_all_logic.db")

# ===================================================================================
# HELPER FUNCTIONS
# ===================================================================================
def _ensure_db_columns(cursor):
    """
    [SELF-HEALING] Kiểm tra và tự động thêm các cột thiếu trong DB.
    """
    try:
        cursor.execute("PRAGMA table_info(ManagedBridges)")
        columns = [info[1] for info in cursor.fetchall()]

        # 1. Cột đếm số lần thắng trong 10 kỳ gần nhất
        if "recent_win_count_10" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN recent_win_count_10 INTEGER DEFAULT 0")
        
        # 2. Cột phân loại cầu
        if "type" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN type TEXT DEFAULT 'UNKNOWN'")
            
        # 3. [CRITICAL FIX] Cột lưu dự đoán ngày tiếp theo
        if "next_prediction_stl" not in columns:
            cursor.execute("ALTER TABLE ManagedBridges ADD COLUMN next_prediction_stl TEXT DEFAULT ''")
            
    except Exception as e:
        print(f"Lỗi Self-Healing DB: {e}")

# ===================================================================================
# V2.5: DE BRIDGE MANAGER (Fix Missing Column)
# ===================================================================================

class DeBridgeManager:
    """
    Trình quản lý Cầu Đề (V2.5 - Fix Missing Column)
    """
    def __init__(self):
        self.max_health = 3
        self.lookback_window = 10

    def update_daily_stats(self, all_data_ai):
        if not all_data_ai or len(all_data_ai) < self.lookback_window + 2: return 0, []
        
        print(">>> [DE MANAGER V2.5] Cập nhật Hồ Sơ Phong Độ (Fix Missing Column)...")
        last_row = all_data_ai[-1]; prev_row = all_data_ai[-2]
        gdb_today = get_gdb_last_2(last_row)
        pos_today = getAllPositions_V17_Shadow(last_row)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            _ensure_db_columns(cursor) # Đảm bảo cột next_prediction_stl tồn tại
            conn.commit()
            # Lấy danh sách cầu đang bật
            cursor.execute("SELECT id, name, type, current_streak, recent_win_count_10, description FROM ManagedBridges WHERE is_enabled=1 AND (type LIKE 'DE_%' OR type LIKE 'CAU_DE%')")
            active_bridges = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Lỗi Đọc DB: {e}. Vui lòng chạy init_db_fix.py trước!")
            conn.close()
            return 0, []
        
        updated_count = 0
        active_list_ui = []
        data_window = all_data_ai[-(self.lookback_window + 2):-1] 
        
        for br_id, name, b_type, streak, hp_db, desc in active_bridges:
            try:
                # ==============================================================
                # PARSER V2.1: Phân tích ID Cầu
                # ==============================================================
                parsed_info = self._parse_bridge_id_v2(name, b_type)
                if not parsed_info:
                    parsed_info = self._parse_bridge_id_legacy(name)
                
                if not parsed_info: continue 

                idx1, idx2, k_offset, mode = parsed_info
                # ==============================================================

                # 1. Tính kết quả (Streak)
                pos_prev = getAllPositions_V17_Shadow(prev_row)
                dan_today = self._calculate_dan_logic(pos_prev, idx1, idx2, k_offset, mode, return_string=False)
                
                is_win = (gdb_today in dan_today) if (gdb_today and dan_today) else False
                
                current_hp = hp_db if (hp_db is not None and 0 <= hp_db <= self.max_health) else self.max_health
                new_streak = streak + 1 if is_win else 0
                new_hp = self.max_health if is_win else current_hp - 1
                
                # 2. Backtest 10 kỳ
                wins_10 = 0
                for k in range(len(data_window) - 1):
                    row_k = data_window[k]; row_n = data_window[k+1]
                    g_next = get_gdb_last_2(row_n)
                    if not g_next: continue
                    p_k = getAllPositions_V17_Shadow(row_k)
                    d_k = self._calculate_dan_logic(p_k, idx1, idx2, k_offset, mode, return_string=False)
                    if g_next in d_k: wins_10 += 1
                if is_win: wins_10 += 1
                wins_10 = min(wins_10, 10)

                # 3. Sinh tồn & Xếp hạng
                is_enabled = 1 if new_hp > 0 else 0
                rank_score = (new_streak * 10) + (wins_10 * 5)
                
                # 4. Dự đoán ngày mai (HIỂN THỊ TINH GỌN - CHỈ SỐ)
                pred_display = ""
                if is_enabled:
                    # Gọi hàm tính toán với display_mode=True để lấy chuỗi số gọn
                    pred_display = self._calculate_dan_logic(pos_today, idx1, idx2, k_offset, mode, return_string=True, display_mode=True)
                
                # 5. Cập nhật DB
                new_desc = desc.split(".")[0] if desc and "." in desc else (desc or name)
                new_desc += f". HP:{new_hp}/{self.max_health} | Win10:{wins_10}"
                
                cursor.execute("UPDATE ManagedBridges SET current_streak=?, recent_win_count_10=?, is_enabled=?, next_prediction_stl=?, description=? WHERE id=?", 
                              (new_streak, wins_10, is_enabled, pred_display, new_desc, br_id))
                
                if is_enabled:
                    # [SHOTGUN FIX] Thêm nhiều Key để đảm bảo UI nhận được dữ liệu
                    active_list_ui.append({
                        "name": name, 
                        "type": b_type, 
                        "streak": new_streak, 
                        "recent_win_count_10": wins_10, # Key chuẩn DB
                        "wins_10": wins_10,             # Key backup
                        "rank_score": rank_score, 
                        "predicted_value": pred_display, # Key 1
                        "next_prediction_stl": pred_display, # Key 2
                        "prediction": pred_display,      # Key 3
                        "hp": new_hp, 
                        "description": new_desc
                    })
                    updated_count += 1
            except Exception as e: 
                print(f"Lỗi xử lý cầu {name}: {e}") # Bật log để debug nếu cần
                continue
                
        conn.commit(); conn.close()
        return updated_count, sorted(active_list_ui, key=lambda x: x['rank_score'], reverse=True)

    def _parse_bridge_id_v2(self, name, b_type):
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
                    idx1 = self._map_std_name_to_index(p1_str) 
                    idx2 = self._map_std_name_to_index(p2_str)
                    return idx1, idx2, int(k_str), "DYNAMIC"

            elif "DE_POS" in name or b_type == "DE_POS_SUM":
                match = re.search(r"DE_POS_(.+)_([^_]+)", name)
                if match:
                    p1_str, p2_str = match.groups()
                    idx1 = self._map_safe_name_to_index(p1_str)
                    idx2 = self._map_safe_name_to_index(p2_str)
                    return idx1, idx2, 0, "POS_SUM"
                    
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
        match = re.match(r"(G\d+\.?\d*|GDB)(\d+)", safe_name)
        if match:
            g_name, g_idx = match.groups()
            reconstructed = f"{g_name}[{g_idx}]"
            return get_index_from_name_V16(reconstructed)
        return None

    def _calculate_dan_logic(self, positions, idx1, idx2, k_offset, mode, return_string=False, display_mode=False):
        """
        Tính dàn đề.
        Args:
            display_mode: Nếu True, trả về string "2, 7" (Clean).
        """
        try:
            if idx1 is None or idx2 is None: return [] if not return_string else ""
            
            v1 = int(positions[idx1])
            v2 = int(positions[idx2])

            base_sum = 0
            if mode == "DYNAMIC":
                base_sum = (v1 + v2) % 10
            elif mode == "POS_SUM" or mode == "LEGACY_V17":
                base_sum = (v1 + v2) % 10
            
            # Tính các chạm (Touch)
            touches = []
            if mode == "DYNAMIC":
                 touches = get_touches_by_offset(base_sum, k_offset) 
            else:
                 # POS_SUM: Tổng và Bóng
                 touches = [base_sum, (base_sum+5)%10]
            
            # Xử lý hiển thị TINH GỌN (Bỏ chữ 'Chạm', chỉ lấy số)
            if display_mode:
                # Trả về string dạng "2, 7"
                t_str = ", ".join(map(str, sorted(list(set(touches)))))
                return t_str
            
            # Sinh dàn số đầy đủ
            final_dan = generate_dan_de_from_touches(touches)
            return ",".join(final_dan) if return_string else final_dan

        except: return [] if not return_string else ""

de_manager = DeBridgeManager()

def find_and_auto_manage_bridges_de(all_data_ai, db_name=DB_NAME):
    from logic.bridges.de_bridge_scanner import run_de_scanner
    count, _ = run_de_scanner(all_data_ai)
    return f"Đã cập nhật {count} cầu Đề (V2.1 Standard)."