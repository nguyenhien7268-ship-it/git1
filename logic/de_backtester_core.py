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
    Chạy backtest lịch sử (Phiên bản Fix Sync Dashboard & Pending State).
    Ưu tiên cấu hình Index từ DB để đồng bộ kết quả với Bảng Cầu Động.
    """
    try:
        # 1. Validation Input
        if not bridge_config:
            return [{'date': 'LỖI', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Config None'}]
        if not all_data or len(all_data) < 2:
            return [{'date': 'LỖI', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Data < 2'}]
        
        # 2. Xác định phạm vi Backtest
        total_len = len(all_data)
        if total_len >= days + 1:
            start_index = total_len - days
            actual_days = days
        else:
            start_index = 1
            actual_days = total_len - 1
        
        end_index = total_len - 1
        results = []
        
        # 3. Parse Config & Biến cờ
        bridge_name = bridge_config.get("name", "")
        bridge_type = bridge_config.get("type", "UNKNOWN")
        
        is_scanner = bridge_config.get("is_scanner_result", False)
        def_string = bridge_config.get("def_string", bridge_name)
        
        pos1_name = bridge_config.get("pos1_name")
        pos2_name = bridge_config.get("pos2_name")
        k_offset = bridge_config.get("k_offset", 0)
        
        # [FIX] Extract k_offset from bridge name if not provided in config
        # This handles bridges loaded from DB that don't have k_offset field
        if k_offset == 0 and "_K" in bridge_name:
            try:
                parts = bridge_name.split("_K")
                if len(parts) > 1:
                    k_str = parts[-1]
                    # Handle cases like "K4" or just "4"
                    if k_str.isdigit():
                        k_offset = int(k_str)
            except:
                pass  # Keep default k_offset = 0
        
        # 4. Mapping Vị Trí (Index) - Logic Đồng Bộ Dashboard
        # Khởi tạo Backtester helper chỉ để dùng các hàm tiện ích nếu cần
        backtester = DeBacktesterCore(all_data)
        idx1, idx2 = None, None
        use_v16 = False
        
        if not is_scanner:
            # Ưu tiên lấy Index từ DB (Chính xác tuyệt đối)
            pos1_idx = bridge_config.get("pos1_idx")
            pos2_idx = bridge_config.get("pos2_idx")
            
            if pos1_idx is not None:
                idx1 = int(pos1_idx)
                if pos2_idx is not None: idx2 = int(pos2_idx)
                # Nếu có index hợp lệ -> Dùng logic V16
                if idx1 >= 0: use_v16 = True
            else:
                # Fallback: Parse từ tên nếu mất index
                if hasattr(backtester, 'v16_map') and backtester.v16_map:
                    # Helper xử lý tên cầu (Inline)
                    def _fix_name_fmt(n):
                        if not n: return n
                        import re
                        if '[' in n and ']' in n: return n
                        m = re.match(r'^G(\d+)\.(\d+)(\d)$', n) # Fix dạng G1.01
                        if m: return f"G{m.group(1)}[{m.group(3)}]"
                        m = re.match(r'^G(\d+)\.(\d+)$', n) # Fix dạng G1.0
                        if m: return f"G{m.group(1)}[{m.group(2)}]"
                        return n

                    if pos1_name: idx1 = backtester.v16_map.get(_fix_name_fmt(pos1_name))
                    if pos2_name: idx2 = backtester.v16_map.get(_fix_name_fmt(pos2_name))
                    
                    if idx1 is not None: use_v16 = True
                
                # Fallback cuối cùng: Map Compact (Cũ)
                if idx1 is None and pos1_name: idx1 = backtester._get_col_idx(pos1_name)
                if idx2 is None and pos2_name: idx2 = backtester._get_col_idx(pos2_name)

            if idx1 is None and not is_scanner:
                return [{'date': 'LỖI', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': f'FAIL: Mất vị trí 1 ({pos1_name})'}]

        # 5. VÒNG LẶP BACKTEST CHÍNH
        for i in range(start_index, min(start_index + actual_days + 1, total_len)):
            try:
                row_today = all_data[i]
                row_prev = all_data[i - 1]
                
                date_str = str(row_today[0]) if row_today[0] else f"Ngày {i}"
                
                # [QUAN TRỌNG] Kiểm tra xem ngày này đã có kết quả chưa
                # Nếu chưa có kết quả (None, null, empty), đánh dấu là PENDING
                gdb_today = get_gdb_last_2(row_today)
                is_pending_day = False
                
                # Logic xác định ngày chờ: GĐB rỗng hoặc các ký tự placeholder
                if gdb_today is None or str(gdb_today).strip() in ["", "..", "??", "None"]:
                    is_pending_day = True
                    gdb_today = "??"

                # --- LẤY SỐ TẠI VỊ TRÍ (HỢP NHẤT LOGIC) ---
                n1, n2 = 0, 0
                has_n2 = True 
                
                if is_scanner:
                    # Logic cho cầu Scanner (GDB.0-G1.0)
                    # Hàm _parse_scanner_def_and_get_values cần tồn tại trong file (hoặc import)
                    # Nếu trong file gốc chưa có, bạn cần đảm bảo hàm này có sẵn bên dưới
                    try:
                        val1, val2 = _parse_scanner_def_and_get_values(def_string, row_prev)
                        if val1 is None: continue 
                        n1 = val1
                        n2 = val2 if val2 is not None else 0
                        has_n2 = (val2 is not None)
                    except: continue
                else:
                    # Logic V16 (Đồng bộ với Dashboard)
                    has_n2 = (idx2 is not None)
                    
                    # Kiểm tra và dùng logic V16 Shadow nếu khả dụng
                    if use_v16 and getAllPositions_V17_Shadow:
                        pos_vals = getAllPositions_V17_Shadow(row_prev)
                        
                        # Safety check bounds
                        if idx1 >= len(pos_vals) or pos_vals[idx1] is None: 
                            continue # Skip bad data
                        n1 = int(pos_vals[idx1])
                        
                        if has_n2:
                            if idx2 >= len(pos_vals) or pos_vals[idx2] is None: 
                                continue # Skip bad data
                            n2 = int(pos_vals[idx2])
                    else:
                        # Fallback logic cũ (Compact)
                        v1 = backtester._clean_num(row_prev[idx1])
                        if not v1: continue
                        n1 = int(v1[-1])
                        if has_n2:
                            v2 = backtester._clean_num(row_prev[idx2])
                            if not v2: continue
                            n2 = int(v2[-1])

                # --- TÍNH TOÁN DỰ ĐOÁN ---
                is_win = False
                pred_str = ""
                
                # Logic: Bộ -> Động -> Tổng -> Classic
                if bridge_type == "DE_SET" or "DE_SET_" in bridge_name or (is_scanner and "Bộ" in bridge_name):
                    if has_n2:
                        pair_val = f"{n1}{n2}"
                        set_name = get_set_name_of_number(pair_val)
                        if set_name and set_name in BO_SO_DE:
                            dan_so = BO_SO_DE[set_name]
                            if is_pending_day:
                                is_win = False # Pending coi như chưa thắng (để xử lý hiển thị sau)
                            else:
                                is_win = gdb_today in dan_so
                            pred_str = f"Bộ {set_name}"
                        else:
                            is_win = False
                            pred_str = f"Bộ ?? ({pair_val})"
                    else:
                        pred_str = "Lỗi: Cầu Bộ thiếu Vị trí 2"
                
                elif bridge_type == "DE_DYNAMIC_K" or "DE_DYN_" in bridge_name or is_scanner:
                    base_sum = (n1 + n2) % 10 if has_n2 else n1
                    touches = get_touches_by_offset(base_sum, k_offset, logic_type="TONG")
                    dan_de = generate_dan_de_from_touches(touches)
                    
                    if is_pending_day:
                        is_win = False
                    else:
                        is_win = gdb_today in dan_de
                        
                    pred_str = f"Chạm {','.join(map(str, touches))}"
                
                elif bridge_type == "DE_POS_SUM" or "DE_POS_" in bridge_name:
                    base_sum = (n1 + n2) % 10 if has_n2 else n1
                    if is_pending_day:
                        is_win = False
                    else:
                        is_win = check_cham(gdb_today, [base_sum])
                    pred_str = f"Chạm {base_sum}"
                
                else: # CLASSIC
                    base_sum = (n1 + n2) % 10 if has_n2 else n1
                    t1, t2 = base_sum, (base_sum + 5) % 10
                    if is_pending_day:
                        is_win = False
                    else:
                        is_win = check_cham(gdb_today, [t1, t2])
                    pred_str = f"Chạm {t1},{t2}"

                # --- TẠO KẾT QUẢ ---
                if is_pending_day:
                    status_text = "Chờ"
                    # [MẸO UI] Có thể set is_win=True tạm thời để UI không tô đỏ nếu cần, 
                    # nhưng để False và check status="Chờ" là chuẩn nhất.
                    # Ở đây ta giữ is_win=False nhưng status rõ ràng.
                else:
                    status_text = "Ăn" if is_win else "Gãy"
                
                results.append({
                    'date': date_str,
                    'pred': pred_str,
                    'result': gdb_today,
                    'is_win': is_win,
                    'status': status_text
                })

            except Exception as e:
                results.append({'date': date_str, 'pred': 'ERR', 'result': 'N/A', 'is_win': False, 'status': f'ERR: {str(e)[:10]}'})
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

# ==============================================================================
# [BỔ SUNG] CÁC HÀM HELPER ĐỂ GIẢI MÃ CẦU SCANNER (SMART V2)
# ==============================================================================

def _parse_scanner_def_and_get_values(def_str, row_data):
    """
    Giải mã chuỗi định nghĩa cầu (VD: 'GDB.0-G1.0') và lấy giá trị từ dòng dữ liệu.
    """
    try:
        parts = def_str.split('-')
        if len(parts) != 2: return None, None
        
        v1 = _get_single_pos_value(parts[0], row_data)
        v2 = _get_single_pos_value(parts[1], row_data)
        
        return v1, v2
    except:
        return None, None

def _get_single_pos_value(pos_code, row_data):
    """
    Lấy giá trị số tại 1 vị trí. (Phiên bản V3 - Hỗ trợ Bóng Dương)
    Hỗ trợ: GDB.0, G1.1, Bong(G1.1)
    """
    try:
        # [NEW] XỬ LÝ BÓNG DƯƠNG (Bong(...) hoặc B(...))
        if "ong(" in pos_code or pos_code.startswith("B("):
            # Tách lấy nội dung bên trong dấu ngoặc
            # VD: Bong(G1.1) -> inner = G1.1
            start = pos_code.find("(") + 1
            end = pos_code.find(")")
            if start > 0 and end > start:
                inner_code = pos_code[start:end]
                # Đệ quy: Lấy giá trị của cái bên trong
                val = _get_single_pos_value(inner_code, row_data)
                if val is not None:
                    # Tính bóng: (val + 5) % 10
                    return (val + 5) % 10
                return None

        # --- LOGIC CŨ (LẤY GIÁ TRỊ GỐC) ---
        code_parts = pos_code.split('.')
        prize_name = code_parts[0]
        
        col_idx = -1
        if prize_name in ["GĐB", "GDB"]: col_idx = 2
        elif prize_name == "G1": col_idx = 3
        elif prize_name == "G2": col_idx = 4
        elif prize_name == "G3": col_idx = 5
        elif prize_name == "G4": col_idx = 6
        elif prize_name == "G5": col_idx = 7
        elif prize_name == "G6": col_idx = 8
        elif prize_name == "G7": col_idx = 9
        
        if col_idx < 0 or col_idx >= len(row_data): return None

        raw_val = row_data[col_idx]
        val_str = str(raw_val)

        sub_idx = 0
        char_idx = 0
        if len(code_parts) == 2: 
            char_idx = int(code_parts[1])
        elif len(code_parts) == 3:
            sub_idx = int(code_parts[1])
            char_idx = int(code_parts[2])

        if "-" in val_str or ";" in val_str:
            sep = "-" if "-" in val_str else ";"
            sub_nums = val_str.split(sep)
            if sub_idx < len(sub_nums):
                target = sub_nums[sub_idx]
                if char_idx < len(target): return int(target[char_idx])
        else:
            if isinstance(raw_val, list) and sub_idx < len(raw_val):
                s = str(raw_val[sub_idx])
                if char_idx < len(s): return int(s[char_idx])
            
            if char_idx < len(val_str):
                return int(val_str[char_idx])

        return None
    except:
        return None

def _expand_bo_so(root_pair_str):
    """Sinh dàn 8 số của Bộ đề"""
    try:
        a, b = int(root_pair_str[0]), int(root_pair_str[1])
        a_b, b_b = (a + 5) % 10, (b + 5) % 10
        pairs = {f"{a}{b}", f"{b}{a}", f"{a}{b_b}", f"{b_b}{a}", 
                 f"{a_b}{b}", f"{b}{a_b}", f"{a_b}{b_b}", f"{b_b}{a_b}"}
        return list(pairs)
    except:
        return []    