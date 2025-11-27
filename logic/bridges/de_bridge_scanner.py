# Tên file: logic/bridges/de_bridge_scanner.py
import sqlite3
from logic.db_manager import DB_NAME
from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, getPositionName_V17_Shadow
from logic.de_utils import (
    get_gdb_last_2, check_cham, check_tong, 
    get_touches_by_offset, generate_dan_de_from_touches
)

class DeBridgeScanner:
    def __init__(self):
        # [CẤU HÌNH] Điều kiện lọc cầu
        self.min_streak = 3        # Cầu phải ăn thông ít nhất 3 kỳ
        self.scan_depth = 30       # Quét trong 30 kỳ gần nhất
        self.history_check_len = 10 # Kiểm tra phong độ trong 10 kỳ gần đây
        self.min_wins_required = 4  # Cần thắng ít nhất 4/10 kỳ (40%)

    def scan_all(self, all_data_ai):
        if not all_data_ai or len(all_data_ai) < self.scan_depth:
            print(f">>> [DEBUG] Dữ liệu quá ngắn: {len(all_data_ai) if all_data_ai else 0} dòng.")
            return 0, []

        last_row = all_data_ai[-1]
        num_cols = len(last_row)
        print(f">>> [DE SCANNER] Bắt đầu chế độ 'Dynamic Offset' (V77 Ultimate) trên {num_cols} cột...")
        
        found_bridges = []

        # 1. QUÉT BIẾN THIÊN ĐỘNG (Dynamic Offset - 10 Biến thể K)
        # Đây là logic mới thay thế cho logic vét cạn đầu đuôi cũ
        bridges_dynamic = self._scan_dynamic_offset(all_data_ai)
        found_bridges.extend(bridges_dynamic)

        # 2. Quét thuật toán cổ điển (Backup - Giữ nguyên logic cũ)
        bridges_classic = self._scan_algorithm_sum(all_data_ai, "DE_CHAM", check_cham, "Cầu Bệt")
        found_bridges.extend(bridges_classic)
        
        # Sắp xếp theo chuỗi ăn thông giảm dần
        found_bridges.sort(key=lambda x: x['streak'], reverse=True)
        
        print(f">>> [DE SCANNER] Tổng tìm thấy: {len(found_bridges)} cầu (Đã lọc Best K).")
        
        self._save_to_db(found_bridges)
        return len(found_bridges), found_bridges

    def _scan_dynamic_offset(self, all_data_ai):
        results = []
        scan_data = all_data_ai[-self.scan_depth:]
        last_row = all_data_ai[-1]
        max_idx = len(last_row)
        
        # Tạo danh sách cặp vị trí (Quét toàn bộ các cặp có thể)
        pairs_to_scan = []
        for i in range(2, max_idx):
            for j in range(i + 1, max_idx):
                name_i = self._get_col_name(i, max_idx)
                name_j = self._get_col_name(j, max_idx)
                pairs_to_scan.append((i, j, name_i, name_j))

        # Duyệt qua từng cặp vị trí
        for idx1, idx2, name1, name2 in pairs_to_scan:
            best_k_variant = None
            best_k_wins = -1

            # Vòng lặp K từ 0 đến 9 (ĐÚNG KẾ HOẠCH)
            # Thử mọi biến thể cộng thêm từ 0 đến 9
            for k in range(10):
                wins_in_window = []
                
                # Backtest kiểm tra hiệu quả
                for day in range(len(scan_data) - 1, len(scan_data) - 1 - self.history_check_len, -1):
                    if day < 1: break
                    row_today = scan_data[day]
                    gdb_today = get_gdb_last_2(row_today)
                    if not gdb_today: continue

                    row_prev = scan_data[day-1]
                    try:
                        # Lấy số tại vị trí (dùng số cuối cùng của giải làm đại diện)
                        v1_str = self._clean_num(row_prev[idx1])
                        v2_str = self._clean_num(row_prev[idx2])
                        if not v1_str or not v2_str: continue
                        
                        num1 = int(v1_str[-1])
                        num2 = int(v2_str[-1])
                        base_sum = (num1 + num2) % 10
                        
                        # Tính 4 chạm theo công thức K (đã có trong de_utils)
                        touches = get_touches_by_offset(base_sum, k)
                        dan_test = generate_dan_de_from_touches(touches)
                        
                        wins_in_window.append(1 if gdb_today in dan_test else 0)
                    except: continue

                total_wins = sum(wins_in_window)
                
                # Tìm K tốt nhất cho cặp này (Best K)
                if total_wins > best_k_wins:
                    best_k_wins = total_wins
                    if total_wins >= self.min_wins_required:
                        # Dự đoán tương lai để lưu
                        try:
                            v1_last = self._clean_num(last_row[idx1])
                            v2_last = self._clean_num(last_row[idx2])
                            if v1_last and v2_last:
                                n1 = int(v1_last[-1])
                                n2 = int(v2_last[-1])
                                base_last = (n1 + n2) % 10
                                
                                final_touches = get_touches_by_offset(base_last, k)
                                final_dan = generate_dan_de_from_touches(final_touches)
                                
                                best_k_variant = {
                                    "name": f"{name1}+{name2} (T+{k})", # Tên đúng chuẩn T+K
                                    "type": "DE_DYNAMIC_K",
                                    "streak": total_wins,
                                    "predicted_value": ",".join(map(str, final_touches)),
                                    "full_dan": ",".join(final_dan),
                                    "win_rate": (total_wins/len(wins_in_window))*100 if wins_in_window else 0
                                }
                        except: pass

            # Chỉ lưu biến thể tốt nhất của cặp này vào kết quả
            if best_k_variant:
                results.append(best_k_variant)
                
        return results

    def _get_col_name(self, idx, total_cols):
        # Data compact 10 cột
        if total_cols <= 11:
            mapping = {2: "GĐB", 3: "G1", 4: "G2", 5: "G3", 6: "G4", 7: "G5", 8: "G6", 9: "G7"}
            return mapping.get(idx, f"Cột_{idx}")
        # Data full 27 cột
        else:
            if idx == 2: return "GĐB"
            if idx == 3: return "G1"
            if 4 <= idx <= 5: return f"G2.{idx-3}"
            if 6 <= idx <= 11: return f"G3.{idx-5}"
            if 12 <= idx <= 15: return f"G4.{idx-11}"
            if 16 <= idx <= 21: return f"G5.{idx-15}"
            if 22 <= idx <= 24: return f"G6.{idx-21}"
            if 25 <= idx <= 28: return f"G7.{idx-24}"
            return f"Pos_{idx}"

    def _clean_num(self, val):
        return ''.join(filter(str.isdigit, str(val)))

    def _scan_algorithm_sum(self, all_data_ai, cau_type, check_func, name_prefix):
        # [Giữ nguyên logic cũ]
        found_bridges = []
        try:
            sample_pos = getAllPositions_V17_Shadow(all_data_ai[-1])
            limit_pos = min(len(sample_pos), 50) 
            scan_data = all_data_ai[-self.scan_depth:]
            
            for i in range(limit_pos):
                for j in range(i, limit_pos):
                    current_streak = 0
                    for k in range(len(scan_data) - 1, 0, -1):
                        row_today = scan_data[k]
                        gdb_today = get_gdb_last_2(row_today)
                        row_prev = scan_data[k-1]
                        pos_prev = getAllPositions_V17_Shadow(row_prev)
                        
                        if not gdb_today or pos_prev[i] is None or pos_prev[j] is None: break
                        try:
                            pred_val = (int(pos_prev[i]) + int(pos_prev[j])) % 10
                            if check_func(gdb_today, [pred_val]): current_streak += 1
                            else: break
                        except: break
                    
                    if current_streak >= self.min_streak:
                        pos1_name = getPositionName_V17_Shadow(i)
                        pos2_name = getPositionName_V17_Shadow(j)
                        try:
                            next_val = (int(getAllPositions_V17_Shadow(all_data_ai[-1])[i]) + int(getAllPositions_V17_Shadow(all_data_ai[-1])[j])) % 10
                            found_bridges.append({
                                "name": f"{name_prefix} {pos1_name}+{pos2_name}",
                                "type": cau_type,
                                "streak": current_streak,
                                "predicted_value": str(next_val),
                                "full_dan": "",
                                "win_rate": 100.0
                            })
                        except: pass
        except Exception as e:
            print(f">>> [DEBUG] Lỗi quét cầu cổ điển: {e}")
            
        return sorted(found_bridges, key=lambda x: x['streak'], reverse=True)[:20]

    def _save_to_db(self, bridges):
        if not bridges: return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Xóa sạch cầu cũ để cập nhật danh sách mới
            cursor.execute("DELETE FROM ManagedBridges WHERE type IN ('DE_DYNAMIC_K', 'DE_SMART_FORM', 'DE_CHAM')")
            
            # Lưu Top 30 cầu tốt nhất
            for b in bridges[:30]: 
                desc = b.get('full_dan', '')
                if desc:
                    desc = f"Phong độ {b['streak']}/10. Dàn: {desc}"
                else:
                    desc = f"Thông {b['streak']} kỳ."
                
                cursor.execute("""
                    INSERT INTO ManagedBridges 
                    (name, type, description, win_rate_text, current_streak, next_prediction_stl, is_enabled) 
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (b['name'], b['type'], desc, f"{b['win_rate']:.0f}%", b['streak'], b['predicted_value']))
            
            conn.commit()
            print(f">>> [DB] Đã lưu thành công {len(bridges[:30])} cầu vào bảng ManagedBridges.")
            conn.close()
        except Exception as e:
            print(f"Lỗi lưu DB: {e}")

def run_de_scanner(data):
    return DeBridgeScanner().scan_all(data)