# Tên file: logic/bridges/de_bridge_scanner.py
import sqlite3
from logic.db_manager import DB_NAME
from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, getPositionName_V17_Shadow
from logic.de_utils import (
    get_gdb_last_2, check_cham, check_tong, 
    get_touches_by_offset, generate_dan_de_from_touches
)

class DeBridgeScanner:
    """
    Bộ quét cầu Đề tự động (Automated DE Bridge Scanner)
    Phiên bản: V2.1 (Standardized Naming)
    """
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
        print(f">>> [DE SCANNER] Bắt đầu quét (V2.1 Standardized) trên {num_cols} cột...")
        
        found_bridges = []

        # 1. QUÉT BIẾN THIÊN ĐỘNG (Dynamic Offset - 10 Biến thể K)
        # Logic: Lấy số cuối của các giải (Prizes) + K biến thiên
        bridges_dynamic = self._scan_dynamic_offset(all_data_ai)
        found_bridges.extend(bridges_dynamic)

        # 2. QUÉT VỊ TRÍ SỐ HỌC (Arithmetic Positions)
        # Logic: Cộng giá trị của 2 vị trí số cụ thể (Digits) (V17 Shadow supported)
        bridges_classic = self._scan_algorithm_sum(all_data_ai)
        found_bridges.extend(bridges_classic)
        
        # Sắp xếp theo chuỗi ăn thông giảm dần
        found_bridges.sort(key=lambda x: x['streak'], reverse=True)
        
        print(f">>> [DE SCANNER] Tổng tìm thấy: {len(found_bridges)} cầu (Đã lọc Best K).")
        
        self._save_to_db(found_bridges)
        return len(found_bridges), found_bridges

    def _scan_dynamic_offset(self, all_data_ai):
        """
        Quét cầu dựa trên biến thiên K của đuôi các giải.
        Naming Standard: DE_DYN_{Pos1}_{Pos2}_K{k}
        """
        results = []
        scan_data = all_data_ai[-self.scan_depth:]
        last_row = all_data_ai[-1]
        max_idx = len(last_row)
        
        # Tạo danh sách cặp vị trí (Quét toàn bộ các cặp có thể dựa trên cột dữ liệu)
        pairs_to_scan = []
        for i in range(2, max_idx):
            for j in range(i + 1, max_idx):
                name_i = self._get_standard_prize_name(i, max_idx)
                name_j = self._get_standard_prize_name(j, max_idx)
                pairs_to_scan.append((i, j, name_i, name_j))

        # Duyệt qua từng cặp vị trí
        for idx1, idx2, name1, name2 in pairs_to_scan:
            best_k_variant = None
            best_k_wins = -1

            # Vòng lặp K từ 0 đến 9
            for k in range(10):
                wins_in_window = []
                
                # Backtest
                for day in range(len(scan_data) - 1, len(scan_data) - 1 - self.history_check_len, -1):
                    if day < 1: break
                    row_today = scan_data[day]
                    gdb_today = get_gdb_last_2(row_today)
                    if not gdb_today: continue

                    row_prev = scan_data[day-1]
                    try:
                        v1_str = self._clean_num(row_prev[idx1])
                        v2_str = self._clean_num(row_prev[idx2])
                        if not v1_str or not v2_str: continue
                        
                        num1 = int(v1_str[-1])
                        num2 = int(v2_str[-1])
                        base_sum = (num1 + num2) % 10
                        
                        touches = get_touches_by_offset(base_sum, k)
                        dan_test = generate_dan_de_from_touches(touches)
                        
                        wins_in_window.append(1 if gdb_today in dan_test else 0)
                    except: continue

                total_wins = sum(wins_in_window)
                
                if total_wins > best_k_wins:
                    best_k_wins = total_wins
                    if total_wins >= self.min_wins_required:
                        # Dự đoán tương lai
                        try:
                            v1_last = self._clean_num(last_row[idx1])
                            v2_last = self._clean_num(last_row[idx2])
                            if v1_last and v2_last:
                                n1 = int(v1_last[-1])
                                n2 = int(v2_last[-1])
                                base_last = (n1 + n2) % 10
                                
                                final_touches = get_touches_by_offset(base_last, k)
                                final_dan = generate_dan_de_from_touches(final_touches)
                                
                                # CHUẨN HÓA TÊN V2.1
                                std_name = f"DE_DYN_{name1}_{name2}_K{k}"
                                display_desc = f"Đuôi {name1} + Đuôi {name2} (K={k})"

                                best_k_variant = {
                                    "name": std_name,
                                    "type": "DE_DYNAMIC_K",
                                    "streak": total_wins,
                                    "predicted_value": ",".join(map(str, final_touches)),
                                    "full_dan": ",".join(final_dan),
                                    "win_rate": (total_wins/len(wins_in_window))*100 if wins_in_window else 0,
                                    "display_desc": display_desc
                                }
                        except: pass

            if best_k_variant:
                results.append(best_k_variant)
                
        return results

    def _get_standard_prize_name(self, idx, total_cols):
        """
        Trả về tên giải chuẩn (dùng cho tên cầu).
        Ví dụ: GDB, G1, G2.1
        """
        # Logic mapping cho Data compact 10 cột
        if total_cols <= 11:
            mapping = {
                2: "GDB", 3: "G1", 4: "G2", 5: "G3", 
                6: "G4", 7: "G5", 8: "G6", 9: "G7"
            }
            return mapping.get(idx, f"C{idx}")
        
        # Logic mapping cho Data full 27 cột
        else:
            if idx == 2: return "GDB"
            if idx == 3: return "G1"
            if 4 <= idx <= 5: return f"G2.{idx-3}"
            if 6 <= idx <= 11: return f"G3.{idx-5}"
            if 12 <= idx <= 15: return f"G4.{idx-11}"
            if 16 <= idx <= 21: return f"G5.{idx-15}"
            if 22 <= idx <= 24: return f"G6.{idx-21}"
            if 25 <= idx <= 28: return f"G7.{idx-24}"
            return f"Pos{idx}"

    def _clean_num(self, val):
        return ''.join(filter(str.isdigit, str(val)))

    def _scan_algorithm_sum(self, all_data_ai):
        """
        Quét cầu cộng vị trí số (Digits).
        Naming Standard: DE_POS_{PosName1}_{PosName2}
        """
        found_bridges = []
        try:
            # Dùng V17 Shadow để lấy toàn bộ 214 vị trí (Gốc + Bóng)
            sample_pos = getAllPositions_V17_Shadow(all_data_ai[-1])
            # Giới hạn quét để tối ưu hiệu năng (50 vị trí đầu quan trọng nhất)
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
                            # Logic: Tổng 2 vị trí % 10 -> Ra Chạm
                            pred_val = (int(pos_prev[i]) + int(pos_prev[j])) % 10
                            if check_cham(gdb_today, [pred_val]): 
                                current_streak += 1
                            else: 
                                break
                        except: break
                    
                    if current_streak >= self.min_streak:
                        # Lấy tên vị trí chuẩn từ V16/V17
                        pos1_name = getPositionName_V17_Shadow(i)
                        pos2_name = getPositionName_V17_Shadow(j)
                        
                        try:
                            val_i = int(getAllPositions_V17_Shadow(all_data_ai[-1])[i])
                            val_j = int(getAllPositions_V17_Shadow(all_data_ai[-1])[j])
                            next_val = (val_i + val_j) % 10
                            
                            # CHUẨN HÓA TÊN V2.1
                            # Lưu ý: Chỉ xóa ngoặc [], giữ lại dấu chấm . nếu có (VD: G2.1)
                            safe_p1 = pos1_name.replace("[", "").replace("]", "")
                            safe_p2 = pos2_name.replace("[", "").replace("]", "")
                            
                            std_name = f"DE_POS_{safe_p1}_{safe_p2}"
                            display_desc = f"Tổng vị trí: {pos1_name} + {pos2_name}"

                            found_bridges.append({
                                "name": std_name,
                                "type": "DE_POS_SUM", # Loại cầu mới rõ ràng hơn
                                "streak": current_streak,
                                "predicted_value": str(next_val),
                                "full_dan": "",
                                "win_rate": 100.0,
                                "display_desc": display_desc
                            })
                        except: pass
        except Exception as e:
            print(f">>> [DEBUG] Lỗi quét cầu số học: {e}")
            
        return sorted(found_bridges, key=lambda x: x['streak'], reverse=True)[:20]

    def _save_to_db(self, bridges):
        if not bridges: return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Xóa các loại cầu cũ (bao gồm cả loại cũ và mới để tránh duplicate)
            cursor.execute("DELETE FROM ManagedBridges WHERE type IN ('DE_DYNAMIC_K', 'DE_POS_SUM', 'DE_CHAM')")
            
            count = 0
            for b in bridges[:30]: 
                # Ưu tiên lấy display_desc nếu có, không thì fallback
                desc = b.get('display_desc', '')
                full_dan_info = b.get('full_dan', '')
                
                final_desc = desc
                if full_dan_info:
                    final_desc += f". Dàn: {full_dan_info}"
                final_desc += f". Thông {b['streak']} kỳ."

                cursor.execute("""
                    INSERT INTO ManagedBridges 
                    (name, type, description, win_rate_text, current_streak, next_prediction_stl, is_enabled) 
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (b['name'], b['type'], final_desc, f"{b['win_rate']:.0f}%", b['streak'], b['predicted_value']))
                count += 1
            
            conn.commit()
            print(f">>> [DB] Đã lưu thành công {count} cầu vào bảng ManagedBridges.")
            conn.close()
        except Exception as e:
            print(f"Lỗi lưu DB: {e}")

def run_de_scanner(data):
    return DeBridgeScanner().scan_all(data)