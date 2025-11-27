# Tên file: logic/de_analytics.py
from collections import Counter
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
    set_scores = {bo: 0 for bo in BO_SO_DE.keys()}
    
    for bridge in bridges:
        b_type = str(bridge.get('type', '')).upper()
        val = str(bridge.get('predicted_value', ''))
        streak = bridge.get('streak', 1)
        
        # Chỉ cộng điểm nếu loại cầu được xác định là BO
        if 'BO' in b_type and val in set_scores:
            set_scores[val] += streak
            
    # Lọc bộ có điểm > 0 và sort giảm dần
    sorted_sets = sorted(set_scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in sorted_sets if x[1] > 0]