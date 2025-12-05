# Tên file: code6/logic/de_analytics.py
# (PHIÊN BẢN V3.9.7 - ROBUST SCORING: LUÔN CÓ ĐIỂM SỐ)

from collections import Counter
from itertools import combinations
from typing import List, Tuple, Optional, Dict, Any
import re

# --- CẤU HÌNH ---
BO_SO_DICT = {
    "00": [0, 55, 5, 50], "11": [11, 66, 16, 61], "22": [22, 77, 27, 72],
    "33": [33, 88, 38, 83], "44": [44, 99, 49, 94], 
    "01": [1, 10, 6, 60, 51, 15, 56, 65], "02": [2, 20, 7, 70, 52, 25, 57, 75],
    "03": [3, 30, 8, 80, 53, 35, 58, 85], "04": [4, 40, 9, 90, 54, 45, 59, 95],
    "12": [12, 21, 17, 71, 26, 62, 67, 76], "13": [13, 31, 18, 81, 36, 63, 68, 86],
    "14": [14, 41, 19, 91, 46, 64, 69, 96],
    "23": [23, 32, 28, 82, 37, 73, 78, 87], "24": [24, 42, 29, 92, 47, 74, 79, 97],
    "34": [34, 43, 39, 93, 48, 84, 89, 98]
}

SCORE_CONFIG = {
    "bo_uu_tien_1": 50, "bo_uu_tien_2": 40, "cham_ti_le": 20, "cham_thong": 15,
    'DE_KILLER_MULTIPLIER': 3.0, 'DE_SET_MULTIPLIER': 2.0, 'DE_NORMAL_MULTIPLIER': 1.0,
    'DE_MARKET_CHAM_BONUS': 2.0, 'DE_MARKET_BO_BONUS': 1.0
}
SCORING_WEIGHTS = SCORE_CONFIG

# --- HELPER ---
def local_get_gdb_last_2(row):
    """Lấy 2 số cuối an toàn tuyệt đối"""
    try:
        val = None
        if isinstance(row, (list, tuple)):
            if len(row) > 2: val = row[2]
            elif len(row) > 0: val = row[-1]
        elif hasattr(row, 'get'): 
            val = row.get('Giai_Dac_Biet') or row.get('De')
        
        if val is not None:
            s = str(val).strip()
            digits = "".join(filter(str.isdigit, s))
            if len(digits) >= 2: return digits[-2:]
            elif len(digits) == 1: return digits.zfill(2)
    except: pass
    return None

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

def calculate_number_scores(bridges, market_stats=None):
    """
    Tính điểm số học:
    Điểm = 10 (Sàn) + (Tần suất * 0.5) + Điểm Cầu - Phạt Gan
    """
    # 1. Khởi tạo điểm sàn 10.0 cho tất cả 100 số (Không bao giờ Empty)
    scores = {f"{i:02d}": 10.0 for i in range(100)}
    
    try:
        freq_cham = market_stats.get('freq_cham', {}) if market_stats else {}
        gan_cham = market_stats.get('gan_cham', {}) if market_stats else {}
        
        # 2. CỘNG ĐIỂM THỐNG KÊ (BASE SCORE)
        for s in scores:
            try:
                n1, n2 = int(s[0]), int(s[1])
                # Tần suất càng cao điểm càng cao
                f_score = (freq_cham.get(n1, 0) + freq_cham.get(n2, 0)) * 0.5
                scores[s] += f_score
                
                # Trừ điểm nếu Gan quá cao (>20 ngày)
                g_max = max(gan_cham.get(n1, 0), gan_cham.get(n2, 0))
                if g_max > 20: scores[s] -= (g_max - 20) * 0.2
            except: pass

        # 3. CỘNG ĐIỂM CẦU (BRIDGE BONUS)
        if bridges:
            for bridge in bridges:
                try:
                    val = str(bridge.get('predicted_value', ''))
                    w = float(bridge.get('streak', 1))
                    b_type = str(bridge.get('type', '')).upper()
                    
                    if 'KILLER' in b_type:
                        if 'CHAM' in val:
                            d = int(val.split()[-1])
                            for s in scores: 
                                if check_cham(s, [d]): scores[s] -= (w * 3.0)
                    else:
                        if not val: continue
                        # Cộng điểm Bộ
                        if 'BO' in b_type or 'SET' in b_type:
                            bk = None
                            s_val = "".join(filter(str.isdigit, val))
                            if s_val.zfill(2) in BO_SO_DICT: bk = s_val.zfill(2)
                            if bk:
                                for s in BO_SO_DICT[bk]: scores[s] += (w * 2.0)
                        # Cộng điểm thường
                        else:
                            parts = []
                            if ',' in val: parts = [int(v) for v in val.split(',') if v.strip().isdigit()]
                            elif val.isdigit(): parts = [int(val)]
                            if parts:
                                for s in scores:
                                    if check_cham(s, parts): scores[s] += w
                except: continue # Skip bad bridge
    except Exception as e:
        print(f"Scoring Error: {e}")
        # Nếu lỗi logic lớn, vẫn trả về scores mặc định (đã khởi tạo)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def calculate_top_touch_combinations(all_data, num_touches=4, days=15, market_stats=None):
    """Tính 4 chạm thông (Duyệt nhanh)"""
    if not all_data: return []
    try:
        recent = all_data[-days:]
        res = []
        
        # Lấy Top Chạm Tần Suất để ghép (Tối ưu tốc độ)
        freq = Counter()
        for row in recent:
            de = local_get_gdb_last_2(row)
            if de: freq[int(de[0])] += 1; freq[int(de[1])] += 1
        
        top_digits = [k for k,v in freq.most_common(8)] # Lấy 8 số hay về nhất để tổ hợp
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
            # Chỉ lấy combo có tỷ lệ > 60% hoặc đang thông > 2 ngày
            if rate > 60 or max_s >= 2:
                res.append({'touches': t_list, 'streak': max_s, 'rate_percent': rate})
                
        res.sort(key=lambda x: (x['streak'], x['rate_percent']), reverse=True)
        return res[:5]
    except: return []

# =============================================================================
# MATRIX V3.9 (GIỮ NGUYÊN)
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
    if df is None or df.empty: return [], [], []
    try:
        # Trend
        de_vals = []
        for x in df.tail(15)['De']:
            s = str(x)
            d = "".join(filter(str.isdigit, s))
            if d: de_vals.append(int(d))
        c = Counter([x%10 for x in de_vals])
        ct = [k for k,v in c.most_common(4)]
    except: ct = [0,1,2,3]
    
    try:
        # Cầu
        last_str = str(df.iloc[-1]['De'])
        d = "".join(filter(str.isdigit, last_str))
        last = int(d) if d else 0
        t = (last//10 + last%10)%10
        ctl = list(set([t, (t+5)%10, (t+1)%10, (t-1)%10]))
    except: ctl = [4,5,6,7]
    
    try:
        # Bộ
        bo = ["12", "01"] if last%2==0 else ["23", "03"]
    except: bo = ["00"]
    
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
        for s in BO_SO_DICT.get(b, []):
            bang_diem[s] += pts; ghi_chu[s].append(f"Bộ {b}")
            
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

get_gdb_last_2 = local_get_gdb_last_2