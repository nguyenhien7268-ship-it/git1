# Tên file: logic/de_analytics.py
from collections import Counter
from itertools import combinations
try:
    from .de_utils import BO_SO_DE, get_gdb_last_2, check_cham, check_tong
except ImportError:
    from de_utils import BO_SO_DE, get_gdb_last_2, check_cham, check_tong

# --- GIỮ NGUYÊN LOGIC THỐNG KÊ CŨ (KHÔNG CẮT BỎ) ---
def analyze_market_trends(all_data_ai, n_days=30):
    if not all_data_ai:
        return {}, {}, {}, {}, {}, {}
        
    recent_data = all_data_ai[-n_days:] if len(all_data_ai) > n_days else all_data_ai
    
    freq_cham = Counter()
    freq_tong = Counter()
    freq_bo = Counter()
    
    # 1. TÍNH TẦN SUẤT
    for row in recent_data:
        de = get_gdb_last_2(row)
        if de:
            try:
                n1, n2 = int(de[0]), int(de[1])
                tong = (n1 + n2) % 10
                
                freq_cham[n1] += 1
                if n1 != n2: freq_cham[n2] += 1
                freq_tong[tong] += 1
                
                for bo_name, bo_list in BO_SO_DE.items():
                    if de in bo_list:
                        freq_bo[bo_name] += 1
                        break
            except ValueError:
                continue

    # 2. TÍNH GAN
    total_days = len(all_data_ai)
    gan_cham = {i: total_days for i in range(10)} 
    gan_tong = {i: total_days for i in range(10)}
    gan_bo = {bo: total_days for bo in BO_SO_DE.keys()}
    
    found_cham, found_tong, found_bo = set(), set(), set()
    
    reversed_data = list(reversed(all_data_ai))
    
    for day_idx, row in enumerate(reversed_data):
        if len(found_cham) == 10 and len(found_tong) == 10 and len(found_bo) == len(BO_SO_DE): 
            break 
        
        de = get_gdb_last_2(row)
        if de:
            try:
                n1, n2 = int(de[0]), int(de[1])
                tong = (n1 + n2) % 10
                
                if len(found_cham) < 10:
                    if n1 not in found_cham:
                        gan_cham[n1] = day_idx
                        found_cham.add(n1)
                    if n2 not in found_cham:
                        gan_cham[n2] = day_idx
                        found_cham.add(n2)
                
                if len(found_tong) < 10:
                    if tong not in found_tong:
                        gan_tong[tong] = day_idx
                        found_tong.add(tong)

                if len(found_bo) < len(BO_SO_DE):
                    for bo_name, bo_list in BO_SO_DE.items():
                        if de in bo_list and bo_name not in found_bo:
                            gan_bo[bo_name] = day_idx
                            found_bo.add(bo_name)
                            break
            except ValueError:
                continue
                
    return {
        "freq_cham": dict(freq_cham),
        "freq_tong": dict(freq_tong),
        "freq_bo": dict(freq_bo),
        "gan_cham": gan_cham,
        "gan_tong": gan_tong,
        "gan_bo": gan_bo
    }

# --- CÁC HÀM PHÂN TÍCH V77 (NÂNG CẤP) ---

def get_de_consensus(bridges):
    """Tổng hợp Vote từ cầu (Consensus)"""
    vote_cham = Counter()
    
    for bridge in bridges:
        b_type = str(bridge.get('type', '')).upper()
        val = str(bridge.get('predicted_value', ''))
        weight = bridge.get('streak', 1)
        
        # Nếu là cầu bộ -> Vote cho các số trong bộ
        if 'BO' in b_type and val in BO_SO_DE:
             for n in BO_SO_DE[val]:
                 # Tách số đề n thành 2 chạm
                 c1, c2 = int(n[0]), int(n[1])
                 vote_cham[c1] += weight
                 vote_cham[c2] += weight
        else:
            # Nếu là cầu chạm/tổng -> Parse list
            parts = [v.strip() for v in val.split(',') if v.strip().isdigit()]
            for p in parts:
                vote_cham[int(p)] += weight
                
    return {"consensus_cham": vote_cham.most_common()}

def calculate_number_scores(bridges):
    """
    Chấm điểm 00-99 (V77 Ultimate).
    Ưu tiên Cầu Bộ: Điểm x 2.
    """
    scores = {f"{i:02d}": 0 for i in range(100)}
    for bridge in bridges:
        b_type = str(bridge.get('type', '')).upper()
        val = str(bridge.get('predicted_value', ''))
        streak = bridge.get('streak', 1)
        
        if not val: continue
        
        # LOGIC MỚI: Ưu tiên bộ
        if 'BO' in b_type:
            if val in BO_SO_DE:
                for s in BO_SO_DE[val]: 
                    scores[s] += streak * 2.0 # Bộ được nhân đôi điểm
        else:
            # Cầu chạm/tổng thường
            parts = []
            if ',' in val:
                parts = [int(v) for v in val.split(',') if v.strip().isdigit()]
            elif val.isdigit():
                parts = [int(val)]
                
            if not parts: continue

            if 'CHAM' in b_type or 'VITRI' in b_type:
                for s in scores:
                    if check_cham(s, parts): scores[s] += streak
            elif 'TONG' in b_type:
                for s in scores:
                    if check_tong(s, parts): scores[s] += streak
                
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def get_top_strongest_sets(bridges):
    """
    Tìm ra các Bộ Số có cầu chạy mạnh nhất (V77).
    Chỉ tính cầu loại 'BO' hoặc cầu trùng khớp bộ.
    """
    if not bridges:
        return []
    
    set_scores = {bo: 0 for bo in BO_SO_DE.keys()}
    
    for bridge in bridges:
        try:
            b_type = str(bridge.get('type', '')).upper()
            val = str(bridge.get('predicted_value', ''))
            streak = bridge.get('streak', 1)
            
            # Đảm bảo streak là số hợp lệ
            if not isinstance(streak, (int, float)):
                try:
                    streak = float(streak) if streak else 1
                except (ValueError, TypeError):
                    streak = 1
            
            # Chỉ cộng điểm nếu loại cầu được xác định là BO
            if 'BO' in b_type and val in set_scores:
                set_scores[val] += streak
        except Exception:
            # Bỏ qua lỗi và tiếp tục với cầu tiếp theo
            continue
            
    # Lọc bộ có điểm > 0 và sort giảm dần
    sorted_sets = sorted(set_scores.items(), key=lambda x: x[1], reverse=True)
    result = [x[0] for x in sorted_sets if x[1] > 0]
    
    # Đảm bảo luôn trả về ít nhất một kết quả nếu có cầu hoạt động
    if not result and bridges:
        # Fallback: Trả về top 3 bộ có điểm cao nhất (kể cả điểm 0)
        sorted_all = sorted(set_scores.items(), key=lambda x: x[1], reverse=True)
        result = [x[0] for x in sorted_all[:3]]
    
    return result

# --- PHÂN TÍCH TỔ HỢP 4 CHẠM (COMBINATORIAL TOUCH ANALYSIS) ---

def calculate_top_touch_combinations(all_data, num_touches=4, days=10):
    """
    Tính toán Max Streak và Win Rate cho TẤT CẢ các tổ hợp 4 chạm khả thi (210 tổ hợp).
    
    Args:
        all_data: Toàn bộ dữ liệu A:I
        num_touches: Số lượng chạm trong mỗi tổ hợp (mặc định: 4)
        days: Số ngày dữ liệu gần nhất để phân tích (mặc định: 10)
    
    Returns:
        list: Danh sách các tổ hợp đã được xếp hạng, mỗi phần tử là dict:
            {
                'touches': [0, 1, 2, 3],  # Danh sách 4 chạm
                'streak': 5,               # Max Streak (chuỗi thắng liên tiếp dài nhất)
                'rate_hits': 8,            # Số lần thắng
                'rate_total': 10,          # Tổng số kỳ
                'rate_percent': 80.0       # Tỉ lệ thắng (%)
            }
    """
    if not all_data or len(all_data) < 2:
        return []
    
    # Lấy dữ liệu gần nhất (days ngày)
    recent_data = all_data[-days:] if len(all_data) > days else all_data
    
    # Tạo tất cả các tổ hợp 4 chạm từ 0-9 (C(10,4) = 210)
    all_touches = list(range(10))  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    touch_combinations = list(combinations(all_touches, num_touches))
    
    results = []
    
    # Duyệt qua từng tổ hợp 4 chạm
    for touch_combo in touch_combinations:
        touch_list = sorted(list(touch_combo))  # Chuyển tuple thành list đã sắp xếp
        
        # Backtest trên dữ liệu gần nhất
        wins = []  # Danh sách kết quả: True (thắng) hoặc False (thua)
        current_streak = 0
        max_streak = 0
        
        # Duyệt qua từng ngày trong recent_data
        for i in range(len(recent_data)):
            row = recent_data[i]
            de = get_gdb_last_2(row)
            
            if de:
                # Kiểm tra xem số đề có dính chạm không
                is_win = check_cham(de, touch_list)
                wins.append(is_win)
                
                # Cập nhật streak
                if is_win:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
            else:
                # Nếu không có dữ liệu đề, coi như thua
                wins.append(False)
                current_streak = 0
        
        # Tính toán thống kê
        rate_hits = sum(wins)  # Số lần thắng
        rate_total = len(wins)  # Tổng số kỳ
        rate_percent = (rate_hits / rate_total * 100) if rate_total > 0 else 0.0
        
        # Lưu kết quả
        results.append({
            'touches': touch_list,
            'streak': max_streak,
            'rate_hits': rate_hits,
            'rate_total': rate_total,
            'rate_percent': rate_percent
        })
    
    # Sắp xếp kết quả:
    # 1. Ưu tiên theo Max Streak (giảm dần)
    # 2. Nếu Streak bằng nhau, ưu tiên theo Win Rate (giảm dần)
    results.sort(key=lambda x: (x['streak'], x['rate_percent']), reverse=True)
    
    return results