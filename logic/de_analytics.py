# Tên file: code6/logic/de_analytics.py
# (PHIÊN BẢN V3.9.19 - FIX: LINK TO DE_UTILS SOURCE OF TRUTH)

from collections import Counter
from itertools import combinations
from typing import List, Tuple, Optional, Dict, Any
import re

# --- IMPORT NGUỒN CHUẨN (SOURCE OF TRUTH) ---
try:
    from logic.de_utils import BO_SO_DE, get_gdb_last_2 as utils_get_gdb
except ImportError:
    # Fallback chỉ dùng khi chạy độc lập test (không khuyến khích)
    BO_SO_DE = {}
    def utils_get_gdb(r): return "00"

# --- CHUYỂN ĐỔI DỮ LIỆU ---
# Analytics cần tính toán số học (int), trong khi de_utils lưu string.
# Ta tự động convert từ BO_SO_DE chuẩn sang dạng int.
BO_SO_DICT = {}
if BO_SO_DE:
    for k, v_list in BO_SO_DE.items():
        # Chuyển ["01", "10"] -> [1, 10]
        BO_SO_DICT[k] = [int(x) for x in v_list if str(x).isdigit()]
else:
    # Fallback an toàn (tránh crash nếu import lỗi)
    BO_SO_DICT = {
        "00": [0, 55, 5, 50], "11": [11, 66, 16, 61], 
        # ... (Các bộ khác sẽ tự động có nếu import thành công)
    }

SCORE_CONFIG = {
    "bo_uu_tien_1": 50, "bo_uu_tien_2": 40, "cham_ti_le": 20, "cham_thong": 15,
    'DE_KILLER_MULTIPLIER': 3.0, 'DE_SET_MULTIPLIER': 2.0, 'DE_NORMAL_MULTIPLIER': 1.0,
    'DE_MARKET_CHAM_BONUS': 2.0, 'DE_MARKET_BO_BONUS': 1.0
}
SCORING_WEIGHTS = SCORE_CONFIG

# --- HELPER ---
# Sử dụng hàm từ utils để đồng bộ logic lấy số
def local_get_gdb_last_2(row):
    return utils_get_gdb(row)

def check_cham(val_str, cham_list):
    try:
        if not val_str: return False
        n1, n2 = int(val_str[0]), int(val_str[1])
        return (n1 in cham_list) or (n2 in cham_list)
    except: return False

# =============================================================================
# LOGIC THỐNG KÊ & TÍNH ĐIỂM (UPDATED)
# =============================================================================

def analyze_market_trends(all_data_ai, n_days=30):
    if not all_data_ai: return {}, {}, {}, {}, {}, {}
    recent_data = all_data_ai[-n_days:] if len(all_data_ai) > n_days else all_data_ai
    
    freq_cham, freq_tong, freq_bo = Counter(), Counter(), Counter()
    
    # Tần suất (Short-term)
    for row in recent_data:
        de = local_get_gdb_last_2(row)
        if de:
            try:
                n_val = int(de)
                n1, n2 = int(de[0]), int(de[1])
                tong = (n1 + n2) % 10
                freq_cham[n1] += 1
                if n1 != n2: freq_cham[n2] += 1
                freq_tong[tong] += 1
                for bo_name, bo_list in BO_SO_DICT.items():
                    if n_val in bo_list: freq_bo[bo_name] += 1; break
            except: continue

    # Gan (Long-term)
    total_len = len(all_data_ai)
    gan_cham = {i: total_len for i in range(10)}
    gan_bo = {bo: total_len for bo in BO_SO_DICT.keys()}
    found_cham, found_bo = set(), set()
    
    for i, row in enumerate(reversed(all_data_ai)):
        de = local_get_gdb_last_2(row)
        if de:
            try:
                n_val = int(de)
                n1, n2 = int(de[0]), int(de[1])
                if n1 not in found_cham: gan_cham[n1] = i; found_cham.add(n1)
                if n2 not in found_cham: gan_cham[n2] = i; found_cham.add(n2)
                for bo_name, bo_list in BO_SO_DICT.items():
                    if bo_name not in found_bo and n_val in bo_list:
                        gan_bo[bo_name] = i; found_bo.add(bo_name); break
            except: pass
        if len(found_cham) == 10 and len(found_bo) == len(BO_SO_DICT): break

    return {
        "freq_cham": dict(freq_cham), "freq_tong": dict(freq_tong), "freq_bo": dict(freq_bo),
        "gan_cham": gan_cham, "gan_tong": {}, "gan_bo": gan_bo
    }

# Tên file: code6/logic/de_analytics.py
# (PHIÊN BẢN V4.0 - ANTI-INFLATION: PHÂN TẦNG ĐIỂM SỐ)

def calculate_number_scores(bridges, market_stats=None):
    """
    Tính điểm số học [OPTIMIZED V4 - ANTI-INFLATION]:
    Ngăn chặn việc spam cầu rác (nhiều số) lấn át cầu chất lượng (ít số).
    
    Cơ chế Phân Tầng:
    - Tier 1 (<= 12 số): Hệ số chuẩn 40.0 (Ưu tiên cực cao cho Bộ/Kép).
    - Tier 2 (> 12 số):  Hệ số chuẩn 5.0 (Dìm điểm cực mạnh cho Chạm/Tổng).
    => Tỷ lệ chênh lệch: 1 Cầu Bộ = 20 Cầu Chạm (thay vì 2.5 như trước).
    """
    scores = {f"{i:02d}": 10.0 for i in range(100)}
    bridge_count_per_num = Counter() 
    
    try:
        # --- 1. CỘNG ĐIỂM THỐNG KÊ (Giữ nguyên) ---
        freq_cham = market_stats.get('freq_cham', {}) if market_stats else {}
        gan_cham = market_stats.get('gan_cham', {}) if market_stats else {}
        
        for s in scores:
            try:
                n1, n2 = int(s[0]), int(s[1])
                f_score = (freq_cham.get(n1, 0) + freq_cham.get(n2, 0)) * 0.5
                scores[s] += f_score
                g_max = max(gan_cham.get(n1, 0), gan_cham.get(n2, 0))
                if g_max > 20: scores[s] -= (g_max - 20) * 0.2
            except: pass

        # --- 2. TÍNH ĐIỂM CẦU (LOGIC PHÂN TẦNG V4) ---
        if bridges:
            for bridge in bridges:
                try:
                    streak = float(bridge.get('streak', 0))
                    val = str(bridge.get('predicted_value', ''))
                    b_type = str(bridge.get('type', '')).upper()
                    
                    # A. XÁC ĐỊNH SỐ LƯỢNG SỐ (Target Numbers)
                    target_numbers = set()
                    
                    # Ưu tiên lấy list số trực tiếp từ Scanner
                    if 'numbers' in bridge and isinstance(bridge['numbers'], list):
                        target_numbers.update(bridge['numbers'])
                    else:
                        # Fallback parsing (cho các cầu cũ chưa update scanner)
                        if 'BO' in b_type or 'SET' in b_type or 'Bộ' in val:
                            for bo_key, bo_nums in BO_SO_DICT.items():
                                if bo_key in val or f"Bộ {bo_key}" in val:
                                    target_numbers.update([f"{n:02d}" for n in bo_nums])
                        elif 'CHAM' in val or 'Chạm' in val or ',' in val:
                            parts = [int(v) for v in val.replace("Chạm","").replace("Loại","").split(',') if v.strip().isdigit()]
                            if parts:
                                if 'CHAM' in val or 'Chạm' in val or 'DYNAMIC' in b_type or 'KILLER' in b_type:
                                    for p in parts:
                                        for i in range(10):
                                            target_numbers.add(f"{p}{i}"); target_numbers.add(f"{i}{p}")
                                else:
                                    target_numbers.update([f"{p:02d}" for p in parts])

                    # B. TÍNH ĐIỂM PHÂN TẦNG (TIERED SCORING - V4)
                    count = len(target_numbers)
                    if count > 0:
                        # --- [V4 CHANGE START] ---
                        # Phân loại giai cấp cầu
                        if count <= 12: 
                            # Giai cấp Thượng Lưu (Bộ, Kép, Dàn ít số)
                            # Thưởng rất lớn để bứt phá
                            BASE_CONSTANT = 40.0 
                        else:
                            # Giai cấp Bình Dân (Chạm, Tổng, Dàn nhiều số)
                            # Phạt nặng để giảm nhiễu (Noise Reduction)
                            BASE_CONSTANT = 3.0
                            
                        density_weight = BASE_CONSTANT / float(count)
                        # --- [V4 CHANGE END] ---
                        
                        # Hệ số Phong độ (Streak Bonus)
                        # Tăng nhẹ bonus streak để ưu tiên cầu bền bỉ
                        streak_bonus = 1.0 + (streak * 0.15) 
                        
                        abs_score = density_weight * streak_bonus
                        
                        # C. ÁP DỤNG (THƯỞNG HOẶC PHẠT)
                        is_killer = 'KILLER' in b_type or 'LOẠI' in val.upper()
                        
                        for num_str in target_numbers:
                            if num_str in scores:
                                if is_killer:
                                    # Cầu Killer loại ít số (tự tin cao) sẽ trừ điểm cực nặng
                                    scores[num_str] -= abs_score
                                else:
                                    scores[num_str] += abs_score
                                    bridge_count_per_num[num_str] += 1

                except Exception: continue

    except Exception as e:
        print(f"Scoring Error: {e}")

    # Trả về list tuple đã sort: [('88', 15.5, '3 cầu'), ('89', 14.2, '2 cầu')...]
    return sorted([(k, v, f"{bridge_count_per_num[k]} cầu") for k, v in scores.items()], key=lambda x: x[1], reverse=True)
    
def calculate_top_touch_combinations(all_data, num_touches=4, days=15, market_stats=None):
    if not all_data: return []
    try:
        recent = all_data[-days:]
        res = []
        freq = Counter()
        for row in recent:
            de = local_get_gdb_last_2(row)
            if de: freq[int(de[0])] += 1; freq[int(de[1])] += 1
        
        top_digits = [k for k,v in freq.most_common(8)] 
        if len(top_digits) < num_touches: top_digits = list(range(10))

        seen_combos = set()
        for i in combinations(top_digits, num_touches):
            combo = tuple(sorted(list(i)))
            if combo in seen_combos: continue
            seen_combos.add(combo)
            
            t_list = list(combo)
            wins = 0; streak = 0; max_s = 0
            for row in recent:
                de = local_get_gdb_last_2(row)
                if de and check_cham(de, t_list):
                    wins +=1; streak +=1; max_s = max(max_s, streak)
                else: streak = 0
                
            rate = (wins/len(recent))*100 if len(recent)>0 else 0
            if rate > 60 or max_s >= 2:
                res.append({'touches': t_list, 'streak': max_s, 'rate_percent': rate})
                
        res.sort(key=lambda x: (x['streak'], x['rate_percent']), reverse=True)
        return res[:5]
    except: return []

# =============================================================================
# MATRIX V3.9.19 (SMART SET SELECTION - CONSISTENT DATA)
# =============================================================================
def _ai_rows_to_dataframe(all_data_ai):
    try:
        import pandas as pd
        cols = ["Ky", "Ngay", "Giai_Dac_Biet", "Giai_1", "Giai_2", "Giai_3", "Giai_4", "Giai_5", "Giai_6", "Giai_7"]
        df = pd.DataFrame(all_data_ai, columns=cols[:len(all_data_ai[0])] if all_data_ai else None)
        if "Giai_Dac_Biet" in df.columns: df["De"] = df["Giai_Dac_Biet"]
        return df, "OK"
    except Exception as e: return None, str(e)

def analyze_independent_factors(df):
    """
    Phân tích các yếu tố độc lập.
    [V3.9.19] Sử dụng BO_SO_DICT chuẩn từ de_utils.
    """
    if df is None or df.empty: return [], [], []
    
    # 1. Trend Chạm
    try:
        de_vals = []
        for x in df.tail(15)['De']:
            s = str(x)
            d = "".join(filter(str.isdigit, s))
            if d: de_vals.append(int(d))
        c = Counter([x%10 for x in de_vals])
        ct = [k for k,v in c.most_common(4)]
    except: ct = [0,1,2,3]
    
    # 2. Cầu Vị Trí
    try:
        last_str = str(df.iloc[-1]['De'])
        d = "".join(filter(str.isdigit, last_str))
        last = int(d) if d else 0
        t = (last//10 + last%10)%10
        ctl = list(set([t, (t+5)%10, (t+1)%10, (t-1)%10]))
    except: ctl = [4,5,6,7]
    
    # 3. [SMART LOGIC] CHỌN BỘ - Dùng BO_SO_DICT chuẩn
    try:
        recent_de = []
        for x in df.tail(30)['De']:
            s = str(x).strip()
            digits = "".join(filter(str.isdigit, s))
            if len(digits) >= 2: recent_de.append(digits[-2:])
            elif len(digits) == 1: recent_de.append(digits.zfill(2))
        
        bo_stats = {b: {'f': 0, 'last_idx': -1} for b in BO_SO_DICT.keys()}
        
        for idx, val_str in enumerate(recent_de):
            try:
                val = int(val_str)
                for b_name, b_list in BO_SO_DICT.items():
                    if val in b_list:
                        bo_stats[b_name]['f'] += 1
                        bo_stats[b_name]['last_idx'] = idx
                        break
            except: continue
            
        scored_bo = []
        total_len = len(recent_de)
        
        for b_name, stats in bo_stats.items():
            freq = stats['f']
            gan = (total_len - 1 - stats['last_idx']) if stats['last_idx'] != -1 else 30
            
            # Hệ số Tần suất = 1.5
            score = (freq * 1.5) - (gan * 0.5)
            scored_bo.append((b_name, score))
            
        scored_bo.sort(key=lambda x: x[1], reverse=True)
        top_bo = [item[0] for item in scored_bo[:2]]
        
        if not top_bo:
             top_bo = ["12", "01"] # Fallback
             
        bo = top_bo

    except Exception as e:
        print(f"[SmartMatrix] Error: {e}")
        bo = ["00"]
    
    return ct, ctl, bo

def run_intersection_matrix_analysis(all_data_ai_or_df):
    df = None
    if hasattr(all_data_ai_or_df, "columns"): df = all_data_ai_or_df
    else: df, _ = _ai_rows_to_dataframe(all_data_ai_or_df)
    
    cham_thong, cham_ti_le, bo_chon = analyze_independent_factors(df)
    
    bang_diem = {i: 0 for i in range(100)}
    ghi_chu = {i: [] for i in range(100)}
    
    for i, b in enumerate(bo_chon):
        pts = SCORE_CONFIG["bo_uu_tien_1"] if i==0 else SCORE_CONFIG["bo_uu_tien_2"]
        # Lấy số từ BO_SO_DICT chuẩn (dạng int)
        for s_int in BO_SO_DICT.get(b, []):
            bang_diem[s_int] += pts; ghi_chu[s_int].append(f"Bộ {b} (Hot)")
            
    for s in range(100):
        d, u = s//10, s%10
        if d in cham_ti_le or u in cham_ti_le:
            bang_diem[s] += 20; ghi_chu[s].append("Cầu")
        if d in cham_thong or u in cham_thong:
            bang_diem[s] += 15; ghi_chu[s].append("Trend")
            
    final = []
    for s, p in bang_diem.items():
        if p > 0:
            rank = "S" if p>=70 else ("A" if p>=50 else "B")
            final.append({"so": f"{s:02d}", "diem": p, "rank": rank, "note": "+".join(ghi_chu[s])})
            
    return {"ranked": sorted(final, key=lambda x:x["diem"], reverse=True), 
            "cham_thong": cham_thong, "cham_ti_le": cham_ti_le, "bo_so_chon": bo_chon}

# Ánh xạ hàm để tương thích ngược
get_gdb_last_2 = local_get_gdb_last_2