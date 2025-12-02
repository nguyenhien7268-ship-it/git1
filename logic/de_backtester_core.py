# Tên file: logic/de_backtester_core.py
# (PHIÊN BẢN V8.3 - FULL RESTORE & FIX DE_SET)

import sys
import os
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.de_utils import (
    get_gdb_last_2, 
    get_touches_by_offset, 
    generate_dan_de_from_touches,
    check_cham,
    # [NEW] Import logic bộ
    get_set_name_of_number,
    BO_SO_DE
)

# Import Logic V16 cho Cầu Bệt
try:
    from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, getPositionName_V17_Shadow
except ImportError:
    getAllPositions_V17_Shadow = None
    getPositionName_V17_Shadow = None

class DeBacktesterCore:
    def __init__(self, all_data):
        self.data = all_data
        # Map cột đơn giản (Dữ liệu Compact)
        self.col_map = {"GĐB": 2, "GDB": 2, "G1": 3, "G2": 4, "G3": 5, "G4": 6, "G5": 7, "G6": 8, "G7": 9}
        
        # Xây dựng Map V16 (Vị trí chi tiết cho Cầu Bệt)
        self.v16_map = {}
        if getPositionName_V17_Shadow:
            try:
                # Quét 150 vị trí đầu tiên
                for i in range(150):
                    name = getPositionName_V17_Shadow(i)
                    if name:
                        self.v16_map[name] = i
            except: pass

    # [RESTORED] Method này đã được khôi phục nguyên trạng để đảm bảo không lỗi các module khác
    def run_backtest(self, config, days_to_test=365):
        """
        Chạy backtest cho một cấu hình cầu cụ thể.
        Hỗ trợ: Dynamic (2 pos), Classic Sum (2 pos), Classic Single (1 pos).
        """
        if not self.data or len(self.data) < days_to_test:
            return {"error": "Không đủ dữ liệu."}

        test_data = self.data[-days_to_test:]
        
        stats = {
            "total_days": 0, "wins": 0, "loss": 0,
            "current_streak": 0, "max_win_streak": 0, "max_loss_streak": 0,
            "win_rate": 0.0, 
            "history_log": [] # Trả về log chi tiết
        }

        # Đọc cấu hình cầu
        pos1_name = config.get('pos1_name')
        pos2_name = config.get('pos2_name')
        k = config.get('k_offset', 0)
        mode = config.get('type', 'DYNAMIC')

        # XỬ LÝ CHỈ SỐ (MAPPING)
        idx1, idx2 = None, None
        use_v16 = False

        # Ưu tiên tìm trong Map V16 nếu là Cầu Bệt (CLASSIC)
        if mode == 'CLASSIC' and hasattr(self, 'v16_map') and self.v16_map:
            idx1 = self.v16_map.get(pos1_name)
            if pos2_name: # Chỉ tìm idx2 nếu tên pos2 tồn tại
                idx2 = self.v16_map.get(pos2_name)
                if idx1 is not None and idx2 is not None: use_v16 = True
            else:
                # Nếu chỉ có pos1 và tìm thấy trong v16 map -> Dùng V16
                if idx1 is not None: use_v16 = True 
        
        # Nếu không tìm thấy trong V16, quay về Map đơn giản (Compact)
        if idx1 is None: idx1 = self._get_col_idx(pos1_name)
        if idx2 is None and pos2_name: idx2 = self._get_col_idx(pos2_name)

        # Kiểm tra lỗi: Pos1 bắt buộc phải có, Pos2 có thể None (nếu cầu đơn)
        if idx1 is None:
            return {"error": f"Không tìm thấy vị trí: {pos1_name}"}
        if pos2_name and idx2 is None:
            return {"error": f"Không tìm thấy vị trí: {pos2_name}"}

        current_streak = 0
        
        # VÒNG LẶP BACKTEST
        for i in range(1, len(test_data)):
            row_today = test_data[i]
            row_prev = test_data[i-1]
            
            gdb_today = get_gdb_last_2(row_today)
            if not gdb_today: continue

            try:
                n1, n2 = 0, 0
                has_n2 = (idx2 is not None)
                
                # --- [BƯỚC 1: LẤY SỐ] ---
                if use_v16 and getAllPositions_V17_Shadow:
                    # Logic V16: Lấy chính xác chữ số tại vị trí (VD: số thứ 2 của G1)
                    pos_vals = getAllPositions_V17_Shadow(row_prev)
                    if pos_vals[idx1] is None: continue
                    n1 = int(pos_vals[idx1])
                    if has_n2:
                        if pos_vals[idx2] is None: continue
                        n2 = int(pos_vals[idx2])
                else:
                    # Logic Thường: Lấy số cuối cùng của giải
                    v1_str = self._clean_num(row_prev[idx1])
                    if not v1_str: continue
                    n1 = int(v1_str[-1])
                    
                    if has_n2:
                        v2_str = self._clean_num(row_prev[idx2])
                        if v2_str: n2 = int(v2_str[-1])
                        else: continue # Nếu cần n2 mà không lấy được thì bỏ qua

                # --- [BƯỚC 2: TÍNH TOÁN BASE] ---
                if has_n2:
                    base_sum = (n1 + n2) % 10
                    desc_base = f"({n1}+{n2})"
                else:
                    # Nếu chỉ có 1 vị trí (Bệt), lấy chính nó
                    base_sum = n1 
                    desc_base = f"({n1})"

                # --- [BƯỚC 3: SINH DÀN & KIỂM TRA] ---
                is_win = False
                desc = ""

                if mode == 'DYNAMIC':
                    touches = get_touches_by_offset(base_sum, k, logic_type="TONG")
                    dan_de = generate_dan_de_from_touches(touches)
                    is_win = gdb_today in dan_de
                    desc = f"{desc_base}%{k} -> Chạm {touches}"
                else:
                    # CLASSIC: Chạm (Gốc + Bóng)
                    t1 = base_sum
                    t2 = (base_sum + 5) % 10
                    is_win = check_cham(gdb_today, [t1, t2])
                    desc = f"{desc_base} -> Chạm {t1}, {t2}"

                # --- [BƯỚC 4: THỐNG KÊ] ---
                stats["total_days"] += 1
                if is_win:
                    stats["wins"] += 1
                    if current_streak >= 0:
                        current_streak += 1
                    else:
                        current_streak = 1
                else:
                    stats["loss"] += 1
                    if current_streak <= 0:
                        current_streak -= 1
                    else:
                        current_streak = -1
                
                # Cập nhật Max Records
                if current_streak > stats["max_win_streak"]: 
                    stats["max_win_streak"] = current_streak
                if current_streak < 0 and abs(current_streak) > stats["max_loss_streak"]:
                    stats["max_loss_streak"] = abs(current_streak)

                # Lưu log (Chỉ lưu 60 ngày cuối để tối ưu hiệu năng hiển thị)
                if i >= len(test_data) - 60:
                    stats["history_log"].append({
                        "date": row_today[0],
                        "gdb": gdb_today,
                        "desc": desc,
                        "result": "✅ ĂN" if is_win else "❌ XỊT",
                        "is_win": is_win
                    })

            except Exception: continue

        # Tổng kết cuối cùng
        stats["current_streak"] = current_streak
        stats["win_rate"] = (stats["wins"] / stats["total_days"] * 100) if stats["total_days"] > 0 else 0
        
        return stats

    def _get_col_idx(self, name):
        if not name: return None
        clean = name.split('.')[0].split('_')[0]
        return self.col_map.get(clean)

    def _clean_num(self, val):
        return ''.join(filter(str.isdigit, str(val)))

def _restore_brackets_format(pos_name):
    """Khôi phục format G14 -> G1[4] để mapping V16 hiểu."""
    if not pos_name: return pos_name
    import re
    if '[' in pos_name and ']' in pos_name: return pos_name
    
    match_gdb = re.match(r'^GDB(\d)$', pos_name)
    if match_gdb: return f"GDB[{match_gdb.group(1)}]"
    
    match_dot = re.match(r'^G(\d+)\.(\d+)(\d)$', pos_name)
    if match_dot: return f"G{match_dot.group(1)}.{match_dot.group(2)}[{match_dot.group(3)}]"
    
    match_simple = re.match(r'^G(\d+)(\d)$', pos_name)
    if match_simple: return f"G{match_simple.group(1)}[{match_simple.group(2)}]"
    
    return pos_name

def run_de_bridge_historical_test(bridge_config, all_data, days=30):
    """
    Chạy backtest lịch sử chi tiết cho một cầu Đề cụ thể.
    Hỗ trợ: DE_DYNAMIC_K, DE_POS, DE_SET (Mới).
    """
    try:
        # 1. Validation Input
        if not bridge_config:
            return [{'date': 'LỖI', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Config None'}]
        if not all_data or len(all_data) < 2:
            return [{'date': 'LỖI', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Data < 2'}]
        
        # 2. Xác định phạm vi Backtest
        if len(all_data) >= days + 1:
            start_index = len(all_data) - days
            actual_days = days
        else:
            start_index = 1
            actual_days = len(all_data) - 1
        
        end_index = len(all_data) - 1
        results = []
        
        # 3. Parse Config
        bridge_name = bridge_config.get("name", "")
        bridge_type = bridge_config.get("type", "UNKNOWN")
        pos1_name = bridge_config.get("pos1_name")
        pos2_name = bridge_config.get("pos2_name")
        k_offset = bridge_config.get("k_offset", 0)
        
        # Parse tên cầu nếu thiếu thông tin
        if not pos1_name or not pos2_name:
            parts = bridge_name.split("_")
            if (bridge_type == "DE_DYNAMIC_K" or "DE_DYN_" in bridge_name) and len(parts) >= 4:
                pos1_name, pos2_name = parts[2], parts[3]
                for p in parts[4:]:
                    if p.startswith("K"): k_offset = int(p[1:])
            elif (bridge_type == "DE_POS_SUM" or "DE_POS_" in bridge_name or bridge_type == "DE_SET" or "DE_SET_" in bridge_name) and len(parts) >= 4:
                pos1_name, pos2_name = parts[2], parts[3]

        # 4. Mapping Vị Trí (Index)
        backtester = DeBacktesterCore(all_data)
        idx1, idx2 = None, None
        use_v16 = False
        
        # 4a. Dùng Index từ DB (Nếu có)
        pos1_idx = bridge_config.get("pos1_idx")
        pos2_idx = bridge_config.get("pos2_idx")
        
        if pos1_idx is not None:
            idx1 = int(pos1_idx)
            if pos2_idx is not None: idx2 = int(pos2_idx)
            if idx1 >= 0: use_v16 = True
        else:
            # 4b. Parse từ tên (V16 Map)
            if hasattr(backtester, 'v16_map') and backtester.v16_map:
                p1_fmt = _restore_brackets_format(pos1_name)
                idx1 = backtester.v16_map.get(p1_fmt)
                if pos2_name:
                    p2_fmt = _restore_brackets_format(pos2_name)
                    idx2 = backtester.v16_map.get(p2_fmt)
                    if idx1 is not None and idx2 is not None: use_v16 = True
                elif idx1 is not None: use_v16 = True
            
            # 4c. Fallback Compact Map
            if idx1 is None: idx1 = backtester._get_col_idx(pos1_name)
            if idx2 is None and pos2_name: idx2 = backtester._get_col_idx(pos2_name)

        if idx1 is None:
            return [{'date': 'LỖI', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': f'FAIL: Mất vị trí 1 ({pos1_name})'}]

        # 5. [FIX] Thêm DE_SET vào danh sách hợp lệ
        valid_types = ["DE_DYNAMIC_K", "DE_POS_SUM", "DE_POS", "CLASSIC", "UNKNOWN", "DE_SET"]
        if bridge_type not in valid_types:
            if not any(x in bridge_name for x in ["DE_DYN_", "DE_POS_", "DE_SET_"]):
                return [{'date': 'LỖI', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': f'FAIL: Type {bridge_type} không hỗ trợ'}]

        # 6. VÒNG LẶP BACKTEST CHÍNH
        for i in range(start_index, min(start_index + actual_days, end_index + 1)):
            try:
                row_today = all_data[i]
                row_prev = all_data[i - 1]
                
                date_str = str(row_today[0]) if row_today[0] else f"Ngày {i}"
                gdb_today = get_gdb_last_2(row_today)
                if not gdb_today: continue
                
                # --- LẤY SỐ TẠI VỊ TRÍ ---
                n1, n2 = 0, 0
                has_n2 = (idx2 is not None)
                
                if use_v16 and getAllPositions_V17_Shadow:
                    pos_vals = getAllPositions_V17_Shadow(row_prev)
                    if idx1 >= len(pos_vals) or pos_vals[idx1] is None: continue
                    n1 = int(pos_vals[idx1])
                    if has_n2:
                        if idx2 >= len(pos_vals) or pos_vals[idx2] is None: continue
                        n2 = int(pos_vals[idx2])
                else:
                    v1 = backtester._clean_num(row_prev[idx1])
                    if not v1: continue
                    n1 = int(v1[-1])
                    if has_n2:
                        v2 = backtester._clean_num(row_prev[idx2])
                        if not v2: continue
                        n2 = int(v2[-1])

                # --- TÍNH TOÁN DỰ ĐOÁN (THEO TYPE) ---
                is_win = False
                pred_str = ""
                
                # [FIX] LOGIC CẦU BỘ (DE_SET)
                if bridge_type == "DE_SET" or "DE_SET_" in bridge_name:
                    if has_n2:
                        pair_val = f"{n1}{n2}"
                        set_name = get_set_name_of_number(pair_val)
                        if set_name and set_name in BO_SO_DE:
                            dan_so = BO_SO_DE[set_name]
                            is_win = gdb_today in dan_so
                            pred_str = f"Bộ {set_name}"
                        else:
                            is_win = False
                            pred_str = f"Bộ ?? ({pair_val})"
                    else:
                        pred_str = "Lỗi: Cầu Bộ thiếu Vị trí 2"
                
                # LOGIC CẦU ĐỘNG
                elif bridge_type == "DE_DYNAMIC_K" or "DE_DYN_" in bridge_name:
                    base_sum = (n1 + n2) % 10 if has_n2 else n1
                    touches = get_touches_by_offset(base_sum, k_offset, logic_type="TONG")
                    dan_de = generate_dan_de_from_touches(touches)
                    is_win = gdb_today in dan_de
                    pred_str = f"Chạm {','.join(map(str, touches))}"
                
                # LOGIC CẦU TỔNG
                elif bridge_type == "DE_POS_SUM" or "DE_POS_" in bridge_name:
                    base_sum = (n1 + n2) % 10 if has_n2 else n1
                    is_win = check_cham(gdb_today, [base_sum])
                    pred_str = f"Chạm {base_sum}"
                
                # CLASSIC
                else:
                    base_sum = (n1 + n2) % 10 if has_n2 else n1
                    t1, t2 = base_sum, (base_sum + 5) % 10
                    is_win = check_cham(gdb_today, [t1, t2])
                    pred_str = f"Chạm {t1},{t2}"

                results.append({
                    'date': date_str,
                    'pred': pred_str,
                    'result': gdb_today,
                    'is_win': is_win,
                    'status': "Ăn" if is_win else "Gãy"
                })

            except Exception as e:
                results.append({'date': date_str, 'pred': 'ERR', 'result': 'N/A', 'is_win': False, 'status': f'ERR: {str(e)[:20]}'})
                continue

        if not results:
            return [{'date': 'LỖI', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Không có kết quả nào'}]
            
        return results

    except Exception as e:
        return [{'date': 'LỖI', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': f'CRASH: {str(e)}'}]

def calculate_de_bridge_max_lose_history(bridge_config, all_data):
    """Wrapper cho tính max lose (Giữ nguyên)"""
    if not bridge_config or not all_data: return -1
    try:
        results = run_de_bridge_historical_test(bridge_config, all_data, days=len(all_data))
        if not results or "FAIL" in str(results[0].get('status', '')): return -1
        
        max_lose = 0
        curr_lose = 0
        for r in results:
            if not r['is_win']:
                curr_lose += 1
                max_lose = max(max_lose, curr_lose)
            else:
                curr_lose = 0
        return max_lose
    except: return -1