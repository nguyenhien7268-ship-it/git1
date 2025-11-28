# Tên file: git1/logic/de_backtester_core.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.de_utils import (
    get_gdb_last_2, 
    get_touches_by_offset, 
    generate_dan_de_from_touches,
    check_cham
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
        # Xử lý tên như "G2.1" -> "G2"
        clean = name.split('.')[0].split('_')[0]
        return self.col_map.get(clean)

    def _clean_num(self, val):
        return ''.join(filter(str.isdigit, str(val)))


def _restore_brackets_format(pos_name):
    """
    Chuyển đổi tên vị trí từ format đã xóa ngoặc về format có ngoặc.
    Ví dụ: G14 -> G1[4], G3.43 -> G3.4[3], GDB4 -> GDB[4]
    
    Logic: getPositionName_V17_Shadow trả về format có ngoặc (VD: G1[4]),
    nhưng de_bridge_scanner.py xóa ngoặc thành G14. Hàm này khôi phục lại.
    
    Args:
        pos_name: Tên vị trí đã xóa ngoặc (VD: G14, G3.43, GDB4)
    
    Returns:
        Tên vị trí có ngoặc (VD: G1[4], G3.4[3], GDB[4])
    """
    if not pos_name:
        return pos_name
    
    import re
    # Nếu đã có ngoặc, trả về nguyên
    if '[' in pos_name and ']' in pos_name:
        return pos_name
    
    # Pattern 1: GDB(số) - VD: GDB4 -> GDB[4]
    match_gdb = re.match(r'^GDB(\d)$', pos_name)
    if match_gdb:
        return f"GDB[{match_gdb.group(1)}]"
    
    # Pattern 2: G(số).(số)(số) - VD: G3.43 -> G3.4[3]
    # Lưu ý: Số cuối cùng là index trong ngoặc
    match_dot = re.match(r'^G(\d+)\.(\d+)(\d)$', pos_name)
    if match_dot:
        return f"G{match_dot.group(1)}.{match_dot.group(2)}[{match_dot.group(3)}]"
    
    # Pattern 3: G(số)(số) - VD: G14 -> G1[4]
    # Lưu ý: Số cuối cùng là index trong ngoặc, số trước đó là tên giải
    match_simple = re.match(r'^G(\d+)(\d)$', pos_name)
    if match_simple:
        # Tách số cuối làm index, phần còn lại làm tên giải
        digits = match_simple.group(1)
        index = match_simple.group(2)
        return f"G{digits}[{index}]"
    
    # Nếu không match, trả về nguyên (có thể là format khác hoặc đã đúng)
    return pos_name


def run_de_bridge_historical_test(bridge_config, all_data, days=30):
    """
    Chạy backtest lịch sử chi tiết cho một cầu Đề cụ thể.
    
    Args:
        bridge_config: Dict chứa cấu hình cầu (từ DB)
        all_data: Toàn bộ dữ liệu A:I
        days: Số ngày cần backtest (mặc định 30)
    
    Returns:
        list: List các dict với format:
            [{'date': '...', 'pred': '...', 'result': '...', 'is_win': True/False, 'status': 'Ăn/Gãy'}]
    """
    # Bao bọc toàn bộ logic trong try-except
    try:
        # Error handling: Kiểm tra input
        if not bridge_config:
            return [{'date': 'LỖI CẤU HÌNH DB', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Config is None'}]
        
        if not all_data or len(all_data) < 2:
            return [{'date': 'LỖI DỮ LIỆU', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Không đủ dữ liệu lịch sử'}]
        
        # Logic: Để backtest days ngày, ta cần days+1 hàng dữ liệu
        # - Dữ liệu dùng để dự đoán: all_data[i-1] (ngày trước)
        # - Ngày dự đoán cho: all_data[i] (ngày hiện tại)
        # - Vòng lặp chạy từ start_index đến len(all_data) - 1
        
        if len(all_data) < 2:
            return [{'date': 'LỖI DỮ LIỆU', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Dữ liệu quá ngắn'}]
        
        # Tính start_index: Bắt đầu từ ngày nào để có đủ days kết quả
        # Nếu có đủ dữ liệu: start_index = len(all_data) - days
        # Nếu không đủ: start_index = 1 (bắt đầu từ ngày thứ 2)
        if len(all_data) >= days + 1:
            start_index = len(all_data) - days
            actual_days = days
        else:
            start_index = 1
            actual_days = len(all_data) - 1  # Số ngày có thể backtest
        
        # Đảm bảo start_index >= 1 (cần ít nhất 1 ngày trước để tính toán)
        if start_index < 1:
            start_index = 1
            actual_days = min(len(all_data) - 1, days)
        
        results = []
        bridge_name = bridge_config.get("name", "")
        bridge_type = bridge_config.get("type", "")
        
        # Validation: Kiểm tra các trường cần thiết
        if not bridge_name:
            return [{'date': 'LỖI CẤU HÌNH DB', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Bridge name is missing'}]
        
        if not bridge_type:
            bridge_type = "UNKNOWN"  # Fallback nếu không có type
        
        # Parse bridge config
        pos1_name = bridge_config.get("pos1_name")
        pos2_name = bridge_config.get("pos2_name")
        k_offset = bridge_config.get("k_offset", 0)
        
        # Nếu không có pos1_name/pos2_name, thử parse từ tên cầu
        if not pos1_name or not pos2_name:
            # Parse từ tên cầu (VD: DE_DYN_GDB_G1_K2 hoặc DE_POS_G2.1_G3.2)
            if bridge_type == "DE_DYNAMIC_K" or "DE_DYN_" in bridge_name:
                # Format: DE_DYN_{name1}_{name2}_K{k}
                parts = bridge_name.split("_")
                if len(parts) >= 4:
                    pos1_name = parts[2]  # GDB
                    pos2_name = parts[3]  # G1
                    # Tìm phần K (có thể là parts[4] hoặc parts[5] nếu có thêm phần)
                    for p in parts[4:]:
                        if p.startswith("K"):
                            try:
                                k_offset = int(p[1:])
                                break
                            except:
                                pass
            elif bridge_type == "DE_POS_SUM" or "DE_POS_" in bridge_name:
                # Format: DE_POS_{pos1}_{pos2}
                # Lưu ý: pos1 và pos2 có thể chứa dấu chấm (VD: G2.1)
                parts = bridge_name.split("_")
                if len(parts) >= 4:
                    pos1_name = parts[2]  # G2.1 (giữ nguyên dấu chấm)
                    pos2_name = parts[3]  # G3.2 (giữ nguyên dấu chấm)
        
        # Tạo DeBacktesterCore instance (dùng all_data để có đủ dữ liệu)
        backtester = DeBacktesterCore(all_data)
        
        # Xử lý mapping vị trí
        idx1, idx2 = None, None
        use_v16 = False
        
        # Ưu tiên: Nếu có pos1_idx và pos2_idx trong config (từ DB), dùng trực tiếp
        pos1_idx_from_db = bridge_config.get("pos1_idx")
        pos2_idx_from_db = bridge_config.get("pos2_idx")
        
        if pos1_idx_from_db is not None:
            # Kiểm tra cấu hình hợp lệ: pos1_idx phải là số và trong phạm vi hợp lệ
            try:
                pos1_idx_from_db = int(pos1_idx_from_db)
                if pos1_idx_from_db < 0 or pos1_idx_from_db >= 214:  # V17 Shadow có 214 vị trí (0-213)
                    error_msg = f"FAIL: pos1_idx không hợp lệ: {pos1_idx_from_db} (phải trong khoảng 0-213)"
                    return [{'date': 'LỖI CẤU HÌNH', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': error_msg}]
            except (ValueError, TypeError):
                error_msg = f"FAIL: pos1_idx không phải là số hợp lệ: {pos1_idx_from_db}"
                return [{'date': 'LỖI CẤU HÌNH', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': error_msg}]
            
            # Có pos1_idx từ DB (DE_POS bridge hoặc cầu đã lưu)
            idx1 = pos1_idx_from_db
            if pos2_idx_from_db is not None:
                try:
                    pos2_idx_from_db = int(pos2_idx_from_db)
                    if pos2_idx_from_db < 0 or pos2_idx_from_db >= 214:
                        error_msg = f"FAIL: pos2_idx không hợp lệ: {pos2_idx_from_db} (phải trong khoảng 0-213)"
                        return [{'date': 'LỖI CẤU HÌNH', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': error_msg}]
                    idx2 = pos2_idx_from_db
                except (ValueError, TypeError):
                    error_msg = f"FAIL: pos2_idx không phải là số hợp lệ: {pos2_idx_from_db}"
                    return [{'date': 'LỖI CẤU HÌNH', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': error_msg}]
            else:
                idx2 = None  # Cầu đơn vị trí
            
            # Kiểm tra xem có phải V16 position không (idx >= 0 và < 150)
            if idx1 >= 0 and (idx2 is None or idx2 >= 0):
                use_v16 = True
        else:
            # Không có pos_idx, parse từ tên hoặc pos_name
            # Ưu tiên tìm trong Map V16 nếu là Cầu Bệt
            if hasattr(backtester, 'v16_map') and backtester.v16_map:
                # Convert tên vị trí từ format đã xóa ngoặc (G14) về format có ngoặc (G1[4])
                # để tìm trong v16_map
                pos1_name_with_brackets = _restore_brackets_format(pos1_name)
                idx1 = backtester.v16_map.get(pos1_name_with_brackets)
                
                if pos2_name:
                    pos2_name_with_brackets = _restore_brackets_format(pos2_name)
                    idx2 = backtester.v16_map.get(pos2_name_with_brackets)
                    if idx1 is not None and idx2 is not None:
                        use_v16 = True
                else:
                    if idx1 is not None:
                        use_v16 = True
            
            # Nếu không tìm thấy trong V16, quay về Map đơn giản
            if idx1 is None:
                idx1 = backtester._get_col_idx(pos1_name)
            if idx2 is None and pos2_name:
                idx2 = backtester._get_col_idx(pos2_name)
        
        if idx1 is None:
            error_msg = f"FAIL: Không tìm thấy vị trí pos1 (name: {pos1_name}, idx: {pos1_idx_from_db})"
            return [{'date': 'LỖI CẤU HÌNH DB', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': error_msg}]
        
        # Kiểm tra idx2: Nếu có pos2_idx_from_db từ DB thì OK (có thể None cho cầu đơn)
        # Nếu không có pos2_idx_from_db, kiểm tra xem có cần pos2_name không
        if idx2 is None and pos2_idx_from_db is None:
            # Không có pos2_idx từ DB, kiểm tra xem có cần pos2_name không
            if pos2_name:
                # Cần pos2 nhưng không tìm thấy idx
                error_msg = f"FAIL: Không tìm thấy vị trí pos2 (name: {pos2_name}, idx: {pos2_idx_from_db})"
                return [{'date': 'LỖI CẤU HÌNH DB', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': error_msg}]
        
        # Validation: Kiểm tra type hợp lệ
        if bridge_type not in ["DE_DYNAMIC_K", "DE_POS_SUM", "DE_POS", "CLASSIC", "UNKNOWN"]:
            if not ("DE_DYN_" in bridge_name or "DE_POS_" in bridge_name):
                error_msg = f"FAIL: Bridge type không hợp lệ: {bridge_type}"
                return [{'date': 'LỖI CẤU HÌNH DB', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': error_msg}]
        
        # Vòng lặp backtest: Chạy từ start_index đến len(all_data) - 1
        # Logic: 
        # - Dữ liệu dùng để dự đoán: row_prev = all_data[i-1] (ngày trước)
        # - Ngày dự đoán cho: row_today = all_data[i] (kết quả ngày hiện tại)
        # - Vòng lặp chạy chính xác actual_days lần
        end_index = len(all_data) - 1  # Tránh ngày cuối cùng (ngày mà ta dùng để dự đoán cho ngày T+1)
        
        for i in range(start_index, min(start_index + actual_days, end_index + 1)):
            try:
                # Kiểm tra index hợp lệ trước khi truy cập
                if i >= len(all_data) or i - 1 < 0:
                    continue
                
                row_today = all_data[i]  # Ngày dự đoán cho
                row_prev = all_data[i - 1]  # Dữ liệu dùng để dự đoán
                
                # Kiểm tra row có đủ phần tử không
                if not row_today or len(row_today) < 2:
                    continue
                if not row_prev or len(row_prev) < 2:
                    continue
                
                # Lấy ngày/kỳ (ưu tiên cột đầu tiên, nếu không có thì dùng index)
                try:
                    date_str = str(row_today[0]) if row_today[0] else f"Ngày {i}"
                except (IndexError, TypeError):
                    date_str = f"Ngày {i}"
                
                # Lấy GĐB thực tế
                gdb_today = get_gdb_last_2(row_today)
                if not gdb_today:
                    continue
                
                # Bước 1: Lấy số từ vị trí
                n1, n2 = 0, 0
                has_n2 = (idx2 is not None)
                
                # Bước 1: Lấy số từ vị trí (với error handling đầy đủ)
                if use_v16 and getAllPositions_V17_Shadow:
                    try:
                        pos_vals = getAllPositions_V17_Shadow(row_prev)
                        # Kiểm tra index hợp lệ trước khi truy cập
                        if idx1 >= len(pos_vals) or pos_vals[idx1] is None:
                            raise ValueError(f"Vị trí idx1={idx1} không hợp lệ hoặc rỗng")
                        n1 = int(pos_vals[idx1])
                        if has_n2:
                            if idx2 >= len(pos_vals) or pos_vals[idx2] is None:
                                raise ValueError(f"Vị trí idx2={idx2} không hợp lệ hoặc rỗng")
                            n2 = int(pos_vals[idx2])
                    except (IndexError, ValueError, TypeError) as e:
                        # Nếu lỗi khi lấy vị trí, bỏ qua ngày này
                        raise ValueError(f"Lỗi lấy vị trí: {e}")
                else:
                    # Kiểm tra index hợp lệ trước khi truy cập
                    if idx1 >= len(row_prev):
                        raise IndexError(f"idx1={idx1} vượt quá độ dài row_prev={len(row_prev)}")
                    v1_str = backtester._clean_num(row_prev[idx1])
                    if not v1_str:
                        raise ValueError(f"Không thể lấy số từ vị trí idx1={idx1}")
                    n1 = int(v1_str[-1])
                    
                    if has_n2:
                        if idx2 >= len(row_prev):
                            raise IndexError(f"idx2={idx2} vượt quá độ dài row_prev={len(row_prev)}")
                        v2_str = backtester._clean_num(row_prev[idx2])
                        if not v2_str:
                            raise ValueError(f"Không thể lấy số từ vị trí idx2={idx2}")
                        n2 = int(v2_str[-1])
                
                # Bước 2: Tính toán base
                if has_n2:
                    base_sum = (n1 + n2) % 10
                    desc_base = f"({n1}+{n2})"
                else:
                    base_sum = n1
                    desc_base = f"({n1})"
                
                # Bước 3: Tính toán dự đoán và kiểm tra
                is_win = False
                pred_str = ""
                
                if bridge_type == "DE_DYNAMIC_K" or "DE_DYN_" in bridge_name:
                    # DYNAMIC: Dùng get_touches_by_offset
                    touches = get_touches_by_offset(base_sum, k_offset, logic_type="TONG")
                    dan_de = generate_dan_de_from_touches(touches)
                    is_win = gdb_today in dan_de
                    pred_str = f"Chạm {','.join(map(str, touches))}"
                elif bridge_type == "DE_POS_SUM" or "DE_POS_" in bridge_name:
                    # POS_SUM: Chạm đơn giản
                    pred_val = base_sum
                    is_win = check_cham(gdb_today, [pred_val])
                    pred_str = f"Chạm {pred_val}"
                else:
                    # CLASSIC: Chạm (Gốc + Bóng)
                    t1 = base_sum
                    t2 = (base_sum + 5) % 10
                    is_win = check_cham(gdb_today, [t1, t2])
                    pred_str = f"Chạm {t1},{t2}"
                
                status = "Ăn" if is_win else "Gãy"
                
                results.append({
                    'date': date_str,
                    'pred': pred_str,
                    'result': gdb_today,
                    'is_win': is_win,
                    'status': status
                })
                
            except (IndexError, ValueError, TypeError, AttributeError) as e:
                # Bắt các lỗi logic/index (tuple index out of range, etc.)
                try:
                    error_date = f"Kỳ {row_today[0]}" if row_today and len(row_today) > 0 and row_today[0] else f"Ngày {i}"
                except:
                    error_date = f"Ngày {i}"
                error_msg = str(e)[:50] if e else "Unknown error"
                results.append({
                    'date': error_date,
                    'pred': 'LỖI',
                    'result': 'N/A',
                    'is_win': False,
                    'status': f'FAIL: {error_msg}'
                })
                continue
            except Exception as e:
                # Bắt các lỗi khác
                try:
                    error_date = f"Kỳ {row_today[0]}" if row_today and len(row_today) > 0 and row_today[0] else f"Ngày {i}"
                except:
                    error_date = f"Ngày {i}"
                error_msg = str(e)[:50] if e else "Unknown error"
                results.append({
                    'date': error_date,
                    'pred': 'LỖI',
                    'result': 'N/A',
                    'is_win': False,
                    'status': f'FAIL: {error_msg}'
                })
                continue
        
        # Nếu không có kết quả nào (tất cả đều lỗi), trả về thông báo lỗi
        if not results:
            return [{'date': 'LỖI TÍNH TOÁN', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': 'FAIL: Không thể tính toán backtest cho cầu này'}]
        
        return results
    
    except Exception as e:
        # Ghi log lỗi và trả về thông báo lỗi rõ ràng
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] run_de_bridge_historical_test failed: {e}")
        print(error_trace)
        
        error_msg = f"FAIL: {str(e)[:100]}"  # Giới hạn độ dài thông báo
        return [{'date': 'LỖI CẤU HÌNH DB', 'pred': 'N/A', 'result': 'N/A', 'is_win': False, 'status': error_msg}]


def calculate_de_bridge_max_lose_history(bridge_config, all_data):
    """
    Tính toán chuỗi Gãy Lâu Nhất (Max Lose Streak) của cầu Đề trong toàn bộ lịch sử.
    
    Args:
        bridge_config: Dict chứa cấu hình cầu (từ DB)
        all_data: Toàn bộ dữ liệu A:I
    
    Returns:
        int: Số ngày gãy liên tiếp lâu nhất (Max Lose Streak), hoặc -1 nếu lỗi
    """
    if not bridge_config or not all_data or len(all_data) < 2:
        return -1
    
    try:
        # Sử dụng hàm backtest đã có để tính toán
        # Chạy backtest trên toàn bộ lịch sử (không giới hạn days)
        results = run_de_bridge_historical_test(bridge_config, all_data, days=len(all_data))
        
        if not results or len(results) == 0:
            return -1
        
        # Tính toán Max Lose Streak từ kết quả backtest
        max_lose_streak = 0
        current_lose_streak = 0
        
        for result in results:
            is_win = result.get('is_win', False)
            if not is_win:
                # Gãy: Tăng chuỗi gãy hiện tại
                current_lose_streak += 1
                max_lose_streak = max(max_lose_streak, current_lose_streak)
            else:
                # Ăn: Reset chuỗi gãy
                current_lose_streak = 0
        
        return max_lose_streak
    
    except Exception as e:
        print(f"[ERROR] calculate_de_bridge_max_lose_history failed: {e}")
        import traceback
        traceback.print_exc()
        return -1