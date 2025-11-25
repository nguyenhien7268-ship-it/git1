# Tên file: logic/bridges/de_bridge_scanner.py
import sqlite3
from logic.db_manager import DB_NAME
from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, getPositionName_V17_Shadow
from logic.de_utils import get_gdb_last_2, check_cham, check_tong, BO_SO_DE

class DeBridgeScanner:
    def __init__(self):
        self.min_streak = 3  # Chỉ lấy cầu ăn thông > 3 ngày
        self.scan_depth = 20 # Quét 20 kỳ gần nhất

    def scan_all(self, all_data_ai):
        if not all_data_ai or len(all_data_ai) < self.scan_depth:
            return 0, []

        print(">>> [DE SCANNER] Bắt đầu quét cầu Đề (Chạm, Tổng, Bộ)...")
        
        # 1. Quét Cầu Chạm (Cộng 2 vị trí % 10)
        bridges_cham = self._scan_algorithm_sum(all_data_ai, "DE_CHAM", check_cham, "Cầu Chạm")
        
        # 2. Quét Cầu Tổng (Cộng 2 vị trí % 10)
        bridges_tong = self._scan_algorithm_sum(all_data_ai, "DE_TONG", check_tong, "Cầu Tổng")
        
        # 3. Quét Cầu Bộ (Ghép 2 vị trí -> Số -> Bộ)
        bridges_bo = self._scan_algorithm_bo(all_data_ai)
        
        print(f">>> [DE SCANNER] Kết quả: {len(bridges_cham)} Chạm, {len(bridges_tong)} Tổng, {len(bridges_bo)} Bộ.")

        # 4. Lưu và Trả về
        all_bridges = bridges_cham + bridges_tong + bridges_bo
        self._save_to_db(all_bridges)
        
        return len(all_bridges), all_bridges

    def _scan_algorithm_sum(self, all_data_ai, cau_type, check_func, name_prefix):
        """Quét cầu dạng cộng: (Pos1 + Pos2) % 10"""
        found_bridges = []
        sample_pos = getAllPositions_V17_Shadow(all_data_ai[-1])
        limit_pos = min(len(sample_pos), 60) 
        scan_data = all_data_ai[-self.scan_depth:]
        
        for i in range(limit_pos):
            for j in range(i, limit_pos):
                current_streak = 0
                for k in range(len(scan_data) - 1, 0, -1):
                    row_today = scan_data[k]
                    gdb_today = get_gdb_last_2(row_today)
                    row_prev = scan_data[k-1]
                    pos_prev = getAllPositions_V17_Shadow(row_prev)
                    
                    if not gdb_today or pos_prev[i] is None or pos_prev[j] is None:
                        break
                    try:
                        pred_val = (int(pos_prev[i]) + int(pos_prev[j])) % 10
                        if check_func(gdb_today, [pred_val]):
                            current_streak += 1
                        else:
                            break
                    except:
                        break
                
                if current_streak >= self.min_streak:
                    pos1_name = getPositionName_V17_Shadow(i)
                    pos2_name = getPositionName_V17_Shadow(j)
                    last_pos = getAllPositions_V17_Shadow(all_data_ai[-1])
                    if last_pos[i] and last_pos[j]:
                        next_val = (int(last_pos[i]) + int(last_pos[j])) % 10
                        found_bridges.append({
                            "name": f"{name_prefix} {pos1_name}+{pos2_name}",
                            "type": cau_type,
                            "streak": current_streak,
                            "predicted_value": next_val,
                            "win_rate": 100.0
                        })
        return sorted(found_bridges, key=lambda x: x['streak'], reverse=True)

    def _scan_algorithm_bo(self, all_data_ai):
        """Quét cầu Bộ: Ghép Pos1 và Pos2 thành số XY -> Suy ra Bộ của XY"""
        found_bridges = []
        sample_pos = getAllPositions_V17_Shadow(all_data_ai[-1])
        limit_pos = min(len(sample_pos), 50)
        scan_data = all_data_ai[-self.scan_depth:]
        
        def find_bo_name(num_str):
            for bo_name, bo_list in BO_SO_DE.items():
                if num_str in bo_list: return bo_name
            return None

        for i in range(limit_pos):
            for j in range(limit_pos):
                if i == j: continue
                current_streak = 0
                for k in range(len(scan_data) - 1, 0, -1):
                    row_today = scan_data[k]
                    gdb_today = get_gdb_last_2(row_today)
                    row_prev = scan_data[k-1]
                    pos_prev = getAllPositions_V17_Shadow(row_prev)
                    
                    if not gdb_today or pos_prev[i] is None or pos_prev[j] is None: break
                    try:
                        num_formed = f"{pos_prev[i]}{pos_prev[j]}"
                        bo_name = find_bo_name(num_formed)
                        if not bo_name: break
                        
                        if gdb_today in BO_SO_DE[bo_name]:
                            current_streak += 1
                        else:
                            break
                    except: break
                
                if current_streak >= self.min_streak:
                    p1 = getPositionName_V17_Shadow(i)
                    p2 = getPositionName_V17_Shadow(j)
                    l_pos = getAllPositions_V17_Shadow(all_data_ai[-1])
                    if l_pos[i] and l_pos[j]:
                        next_num = f"{l_pos[i]}{l_pos[j]}"
                        next_bo = find_bo_name(next_num)
                        if next_bo:
                            found_bridges.append({
                                "name": f"Cầu Bộ {p1}&{p2}",
                                "type": "DE_BO",
                                "streak": current_streak,
                                "predicted_value": next_bo,
                                "win_rate": 100.0
                            })
        return sorted(found_bridges, key=lambda x: x['streak'], reverse=True)

    def _save_to_db(self, bridges):
        if not bridges: return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS managed_bridges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT, type TEXT, description TEXT, win_rate_text TEXT, 
                    current_streak INTEGER, next_prediction_stl TEXT, 
                    pos1_idx INTEGER DEFAULT -1, pos2_idx INTEGER DEFAULT -1, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_favorite INTEGER DEFAULT 0
                )
            """)
            cursor.execute("DELETE FROM managed_bridges WHERE type IN ('DE_CHAM', 'DE_TONG', 'DE_BO')")
            
            for b in bridges:
                desc = f"Thông {b['streak']} kỳ."
                prefix = "BO" if b['type'] == "DE_BO" else ("CHAM" if "CHAM" in b['type'] else "TONG")
                pred_str = f"{prefix}:{b['predicted_value']}"
                
                cursor.execute("""
                    INSERT INTO managed_bridges 
                    (name, type, description, win_rate_text, current_streak, next_prediction_stl, is_favorite) 
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (b['name'], b['type'], desc, "100%", b['streak'], pred_str))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Lỗi lưu DB: {e}")

def run_de_scanner(data):
    return DeBridgeScanner().scan_all(data)