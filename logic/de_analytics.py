# Tên file: logic/de_analytics.py
# (PHIÊN BẢN V3.8.2 - FIXED IMPORT & FULL SCORING LOGIC)

from collections import Counter
from itertools import combinations
from typing import List, Tuple, Optional, Dict, Any
import re

# Import Utils
try:
    from .de_utils import BO_SO_DE, get_gdb_last_2, check_cham, check_tong, get_set_name_of_number
except ImportError:
    from de_utils import BO_SO_DE, get_gdb_last_2, check_cham, check_tong, get_set_name_of_number

# [NEW] Import SCORING_WEIGHTS từ constants
try:
    from logic.constants import SCORING_WEIGHTS
except ImportError:
    # Fallback nếu không tìm thấy constants
    SCORING_WEIGHTS = {
        'DE_KILLER_MULTIPLIER': 3.0,
        'DE_SET_MULTIPLIER': 2.0,
        'DE_NORMAL_MULTIPLIER': 1.0,
        'DE_MARKET_CHAM_BONUS': 2.0,
        'DE_MARKET_BO_BONUS': 1.0
    }

# --- CẤU HÌNH MA TRẬN GIAO THOA (NEW) ---
BO_SO_DICT = {
    "00": [0, 55, 5, 50], "11": [11, 66, 16, 61], "22": [22, 77, 27, 72],
    "33": [33, 88, 38, 83], "44": [44, 99, 49, 94], "01": [1, 10, 6, 60, 51, 15, 56, 65],
    "02": [2, 20, 7, 70, 52, 25, 57, 75], "03": [3, 30, 8, 80, 53, 35, 58, 85],
    "04": [4, 40, 9, 90, 54, 45, 59, 95], "12": [12, 21, 17, 71, 26, 62, 67, 76],
    "13": [13, 31, 18, 81, 36, 63, 68, 86], "14": [14, 41, 19, 91, 46, 64, 69, 96],
    "23": [23, 32, 28, 82, 37, 73, 78, 87], "24": [24, 42, 29, 92, 47, 74, 79, 97],
    "34": [34, 43, 39, 93, 48, 84, 89, 98],
}
SCORE_CONFIG = {"bo_uu_tien_1": 50, "bo_uu_tien_2": 40, "cham_ti_le": 20, "cham_thong": 15}

# --- GIỮ NGUYÊN LOGIC THỐNG KÊ CŨ ---
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

# --- CÁC HÀM HỖ TRỢ ---

def _normalize_bo_key(val):
    """
    Helper: Chuẩn hóa giá trị cầu về đúng key trong BO_SO_DE.
    """
    if val is None: return None
    val_str = str(val).strip()
    
    # 1. Kiểm tra trực tiếp
    if val_str in BO_SO_DE: return val_str
        
    # 2. Xử lý làm sạch
    digits_only = "".join(filter(str.isdigit, val_str))
    
    if digits_only:
        padded_val = digits_only.zfill(2)
        if padded_val in BO_SO_DE: return padded_val
        prefix_val = f"Bo {padded_val}"
        if prefix_val in BO_SO_DE: return prefix_val
    
    return None

def get_de_consensus(bridges):
    """Tổng hợp Vote từ cầu (Consensus)"""
    vote_cham = Counter()
    
    for bridge in bridges:
        b_type = str(bridge.get('type', '')).upper()
        val = str(bridge.get('predicted_value', ''))
        weight = bridge.get('streak', 1)
        
        bo_key = _normalize_bo_key(val)
        
        if ('BO' in b_type or 'SET' in b_type) and bo_key:
             for n in BO_SO_DE[bo_key]:
                 c1, c2 = int(n[0]), int(n[1])
                 vote_cham[c1] += weight
                 vote_cham[c2] += weight
        else:
            parts = [v.strip() for v in val.split(',') if v.strip().isdigit()]
            for p in parts:
                vote_cham[int(p)] += weight
                
    return {"consensus_cham": vote_cham.most_common()}

# --- CORE SCORING ENGINE (V3.8.2 FIXED) ---

def calculate_number_scores(bridges, market_stats=None):
    """
    V3.8 ULTIMATE SCORING ENGINE:
    Tính điểm số học dựa trên công thức:
    Final Score = (Attack Score) - (Defense Penalty) + (Market Bonus)
    (Fixed: Nhận diện đúng cầu DE_SET và import SCORING_WEIGHTS)
    """
    # Khởi tạo bảng điểm 00-99
    scores = {f"{i:02d}": 0.0 for i in range(100)}
    
    # Chuẩn bị dữ liệu thống kê bonus
    freq_cham = market_stats.get('freq_cham', {}) if market_stats else {}
    freq_bo = market_stats.get('freq_bo', {}) if market_stats else {}
    max_freq_cham = max(freq_cham.values()) if freq_cham else 1
    
    # 1. DUYỆT CẦU (BRIDGES) - TẤN CÔNG & PHÒNG THỦ
    for bridge in bridges:
        b_type = str(bridge.get('type', '')).upper()
        val = str(bridge.get('predicted_value', ''))
        
        try:
            streak = float(bridge.get('streak', 1))
        except (ValueError, TypeError):
            streak = 1.0
            
        weight = streak 
        
        # --- LOGIC PHÒNG THỦ (CẦU LOẠI - KILLER) ---
        if 'KILLER' in b_type or 'LOAI' in b_type:
            penalty = weight * SCORING_WEIGHTS['DE_KILLER_MULTIPLIER']
            
            if 'CHAM' in val or 'CHẠM' in val:
                try:
                    digit_char = val.split(" ")[-1]
                    if digit_char.isdigit():
                        digit = int(digit_char)
                        for s in scores:
                            if check_cham(s, [digit]):
                                scores[s] -= penalty
                except Exception: pass
                
            elif 'TONG' in val or 'TỔNG' in val:
                try:
                    t_char = val.split(" ")[-1]
                    if t_char.isdigit():
                        t = int(t_char)
                        for s in scores:
                            if check_tong(s, [t]):
                                scores[s] -= penalty
                except Exception: pass
            
            elif 'BO' in val or 'BỘ' in val:
                 bo_key = _normalize_bo_key(val)
                 if bo_key and bo_key in BO_SO_DE:
                     for s in BO_SO_DE[bo_key]:
                         scores[s] -= penalty

        # --- LOGIC TẤN CÔNG (CẦU CHỐT - POSITIVE) ---
        else:
            if not val: continue
            
            # [FIXED] Ưu tiên 1: Cầu Bộ (Set) - Kiểm tra cả 'BO' và 'SET'
            if 'BO' in b_type or 'SET' in b_type:
                bo_key = _normalize_bo_key(val)
                if bo_key and bo_key in BO_SO_DE:
                    for s in BO_SO_DE[bo_key]:
                        scores[s] += (weight * SCORING_WEIGHTS['DE_SET_MULTIPLIER'])
            
            # Ưu tiên 2: Các loại cầu khác
            else:
                parts = []
                if ',' in val:
                    parts = [int(v) for v in val.split(',') if v.strip().isdigit()]
                elif val.strip().isdigit():
                    parts = [int(val.strip())]
                
                if not parts: continue

                if 'TONG' in b_type or 'TỔNG' in b_type:
                    for s in scores:
                        if check_tong(s, parts): 
                            scores[s] += (weight * SCORING_WEIGHTS['DE_NORMAL_MULTIPLIER'])
                
                else: # Mặc định là Chạm
                    for s in scores:
                        if check_cham(s, parts): 
                            scores[s] += (weight * SCORING_WEIGHTS['DE_NORMAL_MULTIPLIER'])

    # 2. CỘNG ĐIỂM THỊ TRƯỜNG (MARKET BONUS)
    if market_stats:
        for s in scores:
            n1, n2 = int(s[0]), int(s[1])
            f1 = freq_cham.get(n1, 0)
            f2 = freq_cham.get(n2, 0)
            avg_freq = (f1 + f2) / 2
            stats_bonus = (avg_freq / max_freq_cham) * SCORING_WEIGHTS['DE_MARKET_CHAM_BONUS'] if max_freq_cham > 0 else 0
            
            my_set = get_set_name_of_number(s)
            if my_set in freq_bo:
                stats_bonus += SCORING_WEIGHTS['DE_MARKET_BO_BONUS']
            
            scores[s] += stats_bonus

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def get_top_strongest_sets(bridges, market_stats=None, last_row=None):
    """
    Tìm ra các Bộ Số có cầu chạy mạnh nhất (V77 logic preserved).
    """
    if not BO_SO_DE or len(BO_SO_DE) == 0:
        default_sets = ["00", "01", "12"] if "00" in BO_SO_DE else list(BO_SO_DE.keys())[:3] if BO_SO_DE else []
        return default_sets
    
    if not bridges: return []
    
    set_scores = {bo: 0 for bo in BO_SO_DE.keys()}
    
    # 1. GHÉP CẦU VỊ TRÍ
    position_bridges = []
    for bridge in bridges:
        b_type = str(bridge.get('type', '')).upper()
        if 'DE_POS' in b_type or ('POS' in b_type and bridge.get('pos1_idx') is not None and bridge.get('pos2_idx') is not None):
            position_bridges.append(bridge)
    
    if position_bridges and last_row:
        try:
            from logic.de_utils import get_bo_name_by_pair
            from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow
            last_positions = getAllPositions_V17_Shadow(last_row)
            bo_consensus = {}
            
            for bridge in position_bridges:
                try:
                    idx1 = bridge.get('pos1_idx')
                    idx2 = bridge.get('pos2_idx')
                    if idx1 is None or idx2 is None or idx1 >= len(last_positions) or idx2 >= len(last_positions): continue
                    
                    val1 = last_positions[idx1]
                    val2 = last_positions[idx2]
                    if val1 is None or val2 is None: continue
                    
                    d1 = int(str(val1)[-1])
                    d2 = int(str(val2)[-1])
                    
                    bo_name = get_bo_name_by_pair(d1, d2)
                    if bo_name and bo_name in set_scores:
                        if bo_name not in bo_consensus: bo_consensus[bo_name] = []
                        bo_consensus[bo_name].append(bridge)
                except Exception: continue
                        
            for bo_name, bridge_list in bo_consensus.items():
                consensus_count = len(bridge_list)
                base_score = consensus_count * 3.0
                total_win_rate = sum([b.get('win_rate', 0) for b in bridge_list])
                total_streak = sum([float(b.get('streak', 1)) for b in bridge_list])
                
                avg_win_rate = total_win_rate / consensus_count if consensus_count > 0 else 0
                avg_streak = total_streak / consensus_count if consensus_count > 0 else 0
                bonus_score = (avg_win_rate / 100.0 * 2.0) + (avg_streak * 1.5)
                set_scores[bo_name] += (base_score + bonus_score)
                
        except Exception: pass
    
    # 2. CẦU BỘ TRỰC TIẾP
    has_bo_bridges = False
    for bridge in bridges:
        try:
            b_type = str(bridge.get('type', '')).upper()
            val = str(bridge.get('predicted_value', ''))
            streak = float(bridge.get('streak', 1))
            
            if 'BO' in b_type or 'SET' in b_type:
                has_bo_bridges = True
                bo_key = _normalize_bo_key(val)
                if bo_key: set_scores[bo_key] += streak
        except Exception: continue
    
    # 3. FALLBACK: TÍNH TỪ CẦU CHẠM
    if not has_bo_bridges:
        try:
            from logic.de_utils import get_bo_name_by_pair
            for bridge in bridges:
                b_type = str(bridge.get('type', '')).upper()
                val = str(bridge.get('predicted_value', ''))
                streak = float(bridge.get('streak', 1))
                
                if 'CHAM' in str(val) or ',' in str(val) or str(val).isdigit():
                    parts = []
                    if ',' in val: parts = [int(v.strip()) for v in val.split(',') if v.strip().isdigit()]
                    elif val.isdigit(): parts = [int(val)]
                    elif 'CHAM' in val: 
                        try: parts = [int(val.split(' ')[1])]
                        except: pass
                    
                    if not parts: continue
                    
                    # Tạo bộ từ các chạm (Giả định ghép với bóng)
                    bo_sets_found = set()
                    all_digits = set()
                    for cham in parts:
                        all_digits.add(cham)
                        all_digits.add((cham + 5) % 10)
                    
                    digits_list = sorted(list(all_digits))
                    for i in range(len(digits_list)):
                        for j in range(i, len(digits_list)):
                            d1, d2 = digits_list[i], digits_list[j]
                            bo_name = get_bo_name_by_pair(d1, d2)
                            if bo_name: bo_sets_found.add(bo_name)
                    
                    for bo_name in bo_sets_found:
                        if bo_name in set_scores: set_scores[bo_name] += streak
        except: pass
    
    # 4. KẾT HỢP THỊ TRƯỜNG
    if market_stats:
        freq_bo = market_stats.get('freq_bo', {})
        gan_bo = market_stats.get('gan_bo', {})
        for bo_name in set_scores.keys():
            freq_score = freq_bo.get(bo_name, 0)
            num_numbers_in_bo = len(BO_SO_DE.get(bo_name, []))
            normalized_freq = freq_score / max(num_numbers_in_bo, 1)
            gan_days = gan_bo.get(bo_name, 999)
            gan_score = max(0, 10 - min(gan_days, 10))
            bonus_score = (normalized_freq * 0.5) + (gan_score * 0.5)
            set_scores[bo_name] += min(bonus_score, 5.0)

    all_sets_sorted = sorted(set_scores.items(), key=lambda x: x[1], reverse=True)
    return [x[0] for x in all_sets_sorted[:3]]

def calculate_top_touch_combinations(all_data, num_touches=4, days=10, market_stats=None):
    """Tính toán tổ hợp 4 chạm."""
    if not all_data or len(all_data) < 2: return []
    recent_data = all_data[-days:] if len(all_data) > days else all_data
    all_touches = list(range(10)) 
    touch_combinations = list(combinations(all_touches, num_touches))
    results = []
    
    freq_cham = market_stats.get('freq_cham', {}) if market_stats else {}
    gan_cham = market_stats.get('gan_cham', {}) if market_stats else {}

    for touch_combo in touch_combinations:
        touch_list = sorted(list(touch_combo))
        wins = []
        current_streak = 0
        max_streak = 0
        
        for i in range(len(recent_data)):
            row = recent_data[i]
            de = get_gdb_last_2(row)
            if de:
                is_win = check_cham(de, touch_list)
                wins.append(is_win)
                if is_win:
                    current_streak += 1; max_streak = max(max_streak, current_streak)
                else: current_streak = 0
            else:
                wins.append(False); current_streak = 0
        
        rate_hits = sum(wins); rate_total = len(wins)
        rate_percent = (rate_hits / rate_total * 100) if rate_total > 0 else 0.0
        
        # Market bonus
        total_freq = sum(freq_cham.get(cham, 0) for cham in touch_list)
        total_gan_days = sum(gan_cham.get(cham, 999) for cham in touch_list)
        avg_gan = total_gan_days / len(touch_list) if touch_list else 999
        gan_bonus = max(0, 10 - min(avg_gan, 10))
        market_bonus_score = (total_freq * 1.5) + (gan_bonus * 1.0)
        
        adjusted_streak = max_streak + (market_bonus_score / 10.0)
        
        results.append({
            'touches': touch_list, 
            'streak': max_streak,
            'adjusted_streak': adjusted_streak,
            'rate_percent': rate_percent,
            'market_bonus': market_bonus_score
        })
    
    results.sort(key=lambda x: (x['adjusted_streak'], x['rate_percent']), reverse=True)
    return results


# ======================================================================
# MA TRẬN GIAO THOA: Chạm Thông + Chạm Tỉ Lệ + Bộ Số
# ======================================================================

def _normalize_special_value(val: Any) -> Optional[int]:
    """Chuyển kết quả giải đặc biệt về int, bỏ ký tự không phải số."""
    if val is None:
        return None
    s = str(val)
    digits = "".join(ch for ch in s if ch.isdigit())
    if digits == "":
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _ai_rows_to_dataframe(all_data_ai) -> Tuple[Optional["pd.DataFrame"], str]:
    """
    Chuyển dữ liệu A:I (list/tuple) thành DataFrame với cột Ngay & Giai_Dac_Biet.
    """
    try:
        import pandas as pd  # Lazy import để tránh làm nặng startup UI
    except ImportError:
        return None, "Thiếu pandas, không thể tạo DataFrame."

    if not all_data_ai:
        return None, "Dữ liệu trống."

    columns = [
        "Ky", "Ngay", "Giai_Dac_Biet",
        "Giai_1", "Giai_2", "Giai_3", "Giai_4", "Giai_5", "Giai_6", "Giai_7",
    ]
    try:
        df = pd.DataFrame(all_data_ai, columns=columns[: len(all_data_ai[0])])
    except Exception:
        return None, "Không thể chuyển dữ liệu thành DataFrame."

    if "Ngay" in df.columns:
        df["Ngay"] = pd.to_datetime(df["Ngay"], errors="coerce")

    return df, "OK"


def analyze_independent_factors(df) -> Tuple[List[int], List[int], List[str]]:
    """
    Tính các yếu tố độc lập: Chạm Thông, Chạm Tỉ Lệ, Bộ Số.
    """
    special_col = None
    for candidate in ["De", "Giai_Dac_Biet"]:
        if candidate in df.columns:
            special_col = candidate
            break
    if not special_col:
        raise ValueError("Không tìm thấy cột 'De' hoặc 'Giai_Dac_Biet' trong dữ liệu.")

    work_df = df.copy()
    work_df[special_col] = work_df[special_col].apply(_normalize_special_value)
    work_df = work_df.dropna(subset=[special_col])

    if work_df.empty:
        raise ValueError("Dữ liệu giải đặc biệt trống sau khi chuẩn hóa.")

    if "Ngay" in work_df.columns:
        work_df = work_df.sort_values(by="Ngay")

    # 1. Chạm Thông: top 4 đuôi trong 15 kỳ gần nhất
    tail_df = work_df.tail(15)
    cham_thong_counts = tail_df[special_col].astype(int).apply(lambda x: x % 10).value_counts()
    cham_thong = list(cham_thong_counts.sort_values(ascending=False).index[:4])

    # 2. Chạm Tỉ Lệ: dựa vào tổng 2 số cuối kỳ gần nhất
    last_value = int(work_df.iloc[-1][special_col])
    total_last_two = (last_value % 10) + ((last_value // 10) % 10)
    total_last_two %= 10
    cham_ti_le = [
        total_last_two % 10,
        (total_last_two + 1) % 10,
        (total_last_two + 5) % 10,
        (10 - total_last_two) % 10,
    ]

    # 3. Bộ Số: placeholder logic (chẵn/lẻ kỳ gần nhất)
    bo_so_chon = ["12", "01"] if last_value % 2 == 0 else ["23", "03"]

    return cham_thong, cham_ti_le, bo_so_chon


def process_intersection_matrix(cham_thong, cham_ti_le, bo_so_chon):
    bang_diem = {i: 0 for i in range(100)}
    ghi_chu = {i: [] for i in range(100)}

    if len(bo_so_chon) > 0:
        for so in BO_SO_DICT.get(bo_so_chon[0], []):
            bang_diem[so] += SCORE_CONFIG["bo_uu_tien_1"]
            ghi_chu[so].append(f"Bộ {bo_so_chon[0]}")
    if len(bo_so_chon) > 1:
        for so in BO_SO_DICT.get(bo_so_chon[1], []):
            bang_diem[so] += SCORE_CONFIG["bo_uu_tien_2"]
            ghi_chu[so].append(f"Bộ {bo_so_chon[1]}")

    for so in range(100):
        d, u = so // 10, so % 10
        if (d in cham_ti_le) or (u in cham_ti_le):
            bang_diem[so] += SCORE_CONFIG["cham_ti_le"]
            if bang_diem[so]:
                ghi_chu[so].append("Chạm Tỉ Lệ")
        if (d in cham_thong) or (u in cham_thong):
            bang_diem[so] += SCORE_CONFIG["cham_thong"]
            if bang_diem[so]:
                ghi_chu[so].append("Chạm Thông")

    final = [
        {
            "so": f"{so:02d}",
            "diem": v,
            "rank": "S" if v >= 60 else "A" if v >= 40 else "B",
            "note": "+".join(ghi_chu[so]),
        }
        for so, v in bang_diem.items()
        if v > 0
    ]
    return sorted(final, key=lambda x: x["diem"], reverse=True)


def run_intersection_matrix_analysis(all_data_ai_or_df):
    """
    Wrapper: nhận DataFrame hoặc all_data_ai (list), trả về dict kết quả ma trận giao thoa.
    """
    df = None
    message = ""

    try:
        import pandas as pd  # noqa: F401
    except ImportError:
        return {"ranked": [], "message": "Thiếu pandas, bỏ qua giao thoa."}

    if all_data_ai_or_df is None:
        return {"ranked": [], "message": "Dữ liệu trống."}

    if hasattr(all_data_ai_or_df, "columns"):
        df = all_data_ai_or_df
        message = "OK"
    else:
        df, message = _ai_rows_to_dataframe(all_data_ai_or_df)

    if df is None:
        return {"ranked": [], "message": message}

    try:
        cham_thong, cham_ti_le, bo_so_chon = analyze_independent_factors(df)
        ranked = process_intersection_matrix(cham_thong, cham_ti_le, bo_so_chon)
        return {
            "cham_thong": cham_thong,
            "cham_ti_le": cham_ti_le,
            "bo_so_chon": bo_so_chon,
            "ranked": ranked,
            "message": "OK",
        }
    except Exception as e:
        return {"ranked": [], "message": str(e)}