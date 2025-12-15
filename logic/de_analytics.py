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

def normalize_value(v):
    """Normalize value to int 0..9 (extract last digit)"""
    try:
        s = str(v).strip()
        digits = ''.join(ch for ch in s if ch.isdigit())
        return int(digits[-1]) if digits else None
    except:
        return None

def compute_touch_metrics(touches, all_data, window_n=30, require_consecutive_end_n=None):
    """
    Compute comprehensive touch metrics for a touch combination.
    
    Args:
        touches: list/set of touch digits (0..9)
        all_data: full data rows (ordered oldest to newest)
        window_n: window size for analysis
        require_consecutive_end_n: minimum consecutive matches at end required for "chạm thông"
                                   (defaults to CHAM_THONG_MIN_CONSEC from settings, or 8)
    
    Returns:
        dict with keys:
            - total_count: number of rows in window where touch matched
            - max_consecutive: maximum consecutive matches
            - covers_last_n: True if touch appears in ALL last N rows
            - covers_last_n_at_end: True if final M rows ALL have matches (M >= require_consecutive_end_n)
            - consecutive_at_end: actual consecutive matches at end
            - rate_percent: (total_count / window_n) * 100
            - occur_kys: list of ky where matches occurred
            - window: actual window size used
    """
    # Get configuration for minimum consecutive at end
    if require_consecutive_end_n is None:
        try:
            from logic.constants import DEFAULT_SETTINGS
            require_consecutive_end_n = DEFAULT_SETTINGS.get('CHAM_THONG_MIN_CONSEC', 8)
        except:
            require_consecutive_end_n = 8
    
    if not all_data:
        return {
            'total_count': 0,
            'max_consecutive': 0,
            'covers_last_n': False,
            'covers_last_n_at_end': False,
            'consecutive_at_end': 0,
            'rate_percent': 0.0,
            'occur_kys': [],
            'window': 0
        }
    
    # Ensure touches is a set of ints
    touch_set = set(int(t) if isinstance(t, str) else t for t in touches)
    
    # Get last N rows
    last_rows = all_data[-window_n:] if len(all_data) >= window_n else all_data[:]
    actual_window = len(last_rows)
    
    # Compute metrics
    total_count = 0
    occur_kys = []
    max_consecutive = 0
    current_streak = 0
    
    for row in last_rows:
        de = local_get_gdb_last_2(row)
        if de and check_cham(de, touch_set):
            total_count += 1
            occur_kys.append(str(row[0]) if row else "?")
            current_streak += 1
            max_consecutive = max(max_consecutive, current_streak)
        else:
            current_streak = 0
    
    # consecutive_at_end is the streak at the very end of the window
    consecutive_at_end = current_streak
    
    # covers_last_n is True iff touch appears in EVERY row of the window
    covers_last_n = (total_count == actual_window) and (actual_window == window_n)
    
    # covers_last_n_at_end is True iff final M rows ALL have matches (M >= require_consecutive_end_n)
    covers_last_n_at_end = consecutive_at_end >= require_consecutive_end_n
    
    # Rate is independent of consecutive coverage
    rate_percent = round((total_count / actual_window) * 100, 1) if actual_window > 0 else 0.0
    
    return {
        'total_count': total_count,
        'max_consecutive': max_consecutive,
        'covers_last_n': covers_last_n,
        'covers_last_n_at_end': covers_last_n_at_end,
        'consecutive_at_end': consecutive_at_end,
        'rate_percent': rate_percent,
        'occur_kys': occur_kys,
        'window': actual_window
    }

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


def build_dan65_with_bo_priority(all_scores, freq_bo, gan_bo, vip_numbers=None, focus_numbers=None, top_sets_count=None, dan_size=None, min_per_top_set=None):
    """
    [V10.6] Build Dan 65 with VIP/FOCUS PRIORITY + SET PRIORITY
    
    Ensures VIP and focus numbers are ALWAYS included, then adds top-performing
    sets (bộ) representation, preventing exclusion of critical numbers.
    
    Args:
        all_scores: List of (number_str, score, info) tuples from calculate_number_scores
        freq_bo: Dict of set frequencies {bo_name: count}
        gan_bo: Dict of set gan days {bo_name: days}
        vip_numbers: List of VIP numbers (10 numbers) - FORCED inclusion
        focus_numbers: List of focus numbers (4 numbers) - FORCED inclusion
        top_sets_count: How many top sets to prioritize (None = use config, default 5)
        dan_size: Final Dan size (None = use config, default 65)
        min_per_top_set: Minimum numbers to include from each top set (None = use config, default 1)
    
    Returns:
        Tuple of (sorted_dan_list, inclusions_dict, excluded_high_scorers)
    """
    try:
        from logic.de_utils import BO_SO_DE
        from logic.constants import DEFAULT_SETTINGS
        
        # Use config values if not provided
        if top_sets_count is None:
            top_sets_count = DEFAULT_SETTINGS.get("DAN65_TOP_SETS_COUNT", 5)
        if dan_size is None:
            dan_size = DEFAULT_SETTINGS.get("DAN65_SIZE", 65)
        if min_per_top_set is None:
            min_per_top_set = DEFAULT_SETTINGS.get("DAN65_MIN_PER_TOP_SET", 1)
        
        excluded_threshold = DEFAULT_SETTINGS.get("DAN65_LOG_EXCLUDED_THRESHOLD", 30.0)
        
        # Normalize VIP/focus numbers
        vip_numbers = vip_numbers or []
        focus_numbers = focus_numbers or []
        
        # === PHASE 0: FORCE INCLUDE VIP AND FOCUS NUMBERS ===
        dan = set()
        vip_added = []
        focus_added = []
        
        print("\n" + "="*70)
        print("🎯 DAN 65 OPTIMIZATION LOG (V10.6)")
        print("="*70)
        
        if vip_numbers or focus_numbers:
            print(f"\n[PHASE 0] Force Include VIP/Focus Numbers:")
            
            # Add VIP numbers (10 numbers)
            for num in vip_numbers:
                if num not in dan:
                    dan.add(num)
                    vip_added.append(num)
            
            if vip_added:
                print(f"  ✅ VIP (10 numbers): {', '.join(vip_added)}")
            
            # Add Focus numbers (4 numbers)
            for num in focus_numbers:
                if num not in dan:
                    dan.add(num)
                    focus_added.append(num)
            
            if focus_added:
                print(f"  ✅ Focus (4 numbers): {', '.join(focus_added)}")
            
            print(f"  📊 Total forced: {len(vip_added) + len(focus_added)} numbers")
        
        # === PHASE 1: IDENTIFY TOP PERFORMING SETS ===
        set_scores = []
        KEP_SETS = ["00", "11", "22", "33", "44"]  # Duplicate sets
        
        for bo_name, nums in BO_SO_DE.items():
            freq = freq_bo.get(bo_name, 0)
            gan = gan_bo.get(bo_name, 0)
            
            # Enhanced scoring formula (matches V10.3 UI evaluation)
            base_score = freq * 1.5
            gan_penalty = gan * 0.3  # Reduced 40% from 0.5
            kep_bonus = 2.0 if bo_name in KEP_SETS else 0.0
            recent_bonus = 1.5 if gan < 7 else 0.0
            trending_bonus = 1.0 if freq >= 3 else 0.0
            
            total = base_score - gan_penalty + kep_bonus + recent_bonus + trending_bonus
            set_scores.append((bo_name, total, freq, gan))
        
        # Sort and get top N sets
        set_scores.sort(key=lambda x: x[1], reverse=True)
        top_sets = [item[0] for item in set_scores[:top_sets_count]]
        
        print(f"\n[PHASE 1] Top {top_sets_count} Sets Identified:")
        for i, (bo_name, score, freq, gan) in enumerate(set_scores[:top_sets_count], 1):
            kep_tag = " [KEP]" if bo_name in KEP_SETS else ""
            print(f"  {i}. Bộ {bo_name} (Score: {score:.1f}, Freq: {freq}, Gan: {gan}){kep_tag}")
        
        # === PHASE 2: FORCE INCLUDE NUMBERS FROM TOP SETS ===
        # (dan already initialized with VIP/focus numbers)
        included_from_top_sets = {}
        
        print(f"\n[PHASE 2] Add Numbers from Top Sets (after VIP/focus):")
        
        for bo_name in top_sets:
            bo_nums = BO_SO_DE.get(bo_name, [])
            
            # Get numbers from this set, sorted by their individual scores
            bo_candidates = [(num, score) for num, score, _ in all_scores if num in bo_nums]
            bo_candidates.sort(key=lambda x: x[1], reverse=True)
            
            # Force include at least min_per_top_set numbers
            added = 0
            added_nums = []
            for num, score in bo_candidates:
                if added >= min_per_top_set:
                    break
                dan.add(num)
                added_nums.append(num)
                added += 1
            
            included_from_top_sets[bo_name] = added
            if added > 0:
                print(f"  ✅ Bộ {bo_name}: Added {added} numbers ({', '.join(added_nums)})")
            else:
                print(f"  ⚠️ Bộ {bo_name}: No numbers available")
        
        # === PHASE 3: FILL REMAINING SLOTS WITH HIGHEST SCORES ===
        excluded_high_scorers = []
        
        for num, score, info in all_scores:
            if len(dan) >= dan_size:
                # Track high scorers that didn't make it
                if score >= excluded_threshold:
                    excluded_high_scorers.append((num, score, "Filled to capacity"))
            else:
                if num not in dan:
                    dan.add(num)
        
        # Log excluded high scorers
        if excluded_high_scorers:
            print(f"\n[PHASE 3] Excluded High Scorers (Score ≥ {excluded_threshold}):")
            for num, score, reason in excluded_high_scorers[:10]:  # Limit to top 10
                print(f"  ❌ {num} (Score: {score:.1f}) - {reason}")
            if len(excluded_high_scorers) > 10:
                print(f"  ... and {len(excluded_high_scorers) - 10} more")
        else:
            print(f"\n[PHASE 3] No high scorers excluded (all fit within Dan {dan_size})")
        
        # === SUMMARY ===
        total_from_top_sets = sum(included_from_top_sets.values())
        total_vip_focus = len(vip_added) + len(focus_added)
        total_from_others = len(dan) - total_from_top_sets - total_vip_focus
        kep_count = sum(1 for bo in top_sets if bo in KEP_SETS and included_from_top_sets.get(bo, 0) > 0)
        
        print(f"\n[SUMMARY] Dan {dan_size} Statistics:")
        print(f"  ✓ Total numbers: {len(dan)}")
        print(f"  ✓ VIP/Focus forced: {total_vip_focus} ({len(vip_added)} VIP + {len(focus_added)} focus)")
        print(f"  ✓ From top {top_sets_count} sets: {total_from_top_sets} ({total_from_top_sets/max(len(dan),1)*100:.1f}%)")
        print(f"  ✓ From other sources: {total_from_others} ({total_from_others/max(len(dan),1)*100:.1f}%)")
        print(f"  ✓ Duplicate sets represented: {kep_count}")
        print(f"  ✓ Total sets represented: {len(set(bo for bo in BO_SO_DE.keys() if any(n in dan for n in BO_SO_DE[bo])))}/15")
        print("="*70 + "\n")
        
        return sorted(dan), included_from_top_sets, excluded_high_scorers
        
    except Exception as e:
        print(f"[ERROR] build_dan65_with_bo_priority failed: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to simple top N selection
        return sorted([x[0] for x in all_scores[:dan_size]]), {}, []

    
def calculate_top_touch_combinations(all_data, num_touches=4, days=15, market_stats=None, filter_cham_thong_only=False):
    """
    Calculate top touch combinations with comprehensive metrics.
    Now returns covers_last_n, covers_last_n_at_end, total_count, max_consecutive, and rate_percent.
    
    Args:
        all_data: full data rows
        num_touches: number of touches in combination (default 4)
        days: deprecated, uses window_n from settings instead
        market_stats: optional market statistics
        filter_cham_thong_only: if True, only return combinations with covers_last_n_at_end=True
    """
    if not all_data: return []
    try:
        # Import window size and minimum consecutive from constants
        try:
            from logic.constants import DEFAULT_SETTINGS
            window_n = DEFAULT_SETTINGS.get('DE_WINDOW_KYS', 30)
            require_consecutive_end_n = DEFAULT_SETTINGS.get('CHAM_THONG_MIN_CONSEC', 8)
        except:
            window_n = 30
            require_consecutive_end_n = 8
        
        # Use window_n instead of days for consistent analysis
        recent = all_data[-window_n:]
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
            
            # Use new comprehensive metrics function with consecutive_end requirement
            metrics = compute_touch_metrics(t_list, all_data, window_n, require_consecutive_end_n)
            
            # Apply filter for "chạm thông" if requested
            if filter_cham_thong_only and not metrics.get('covers_last_n_at_end', False):
                continue
            
            # Filter based on rate or max_consecutive
            if metrics['rate_percent'] > 60 or metrics['max_consecutive'] >= 2:
                res.append({
                    'touches': t_list,
                    'total_count': metrics['total_count'],
                    'max_consecutive': metrics['max_consecutive'],
                    'covers_last_n': metrics['covers_last_n'],
                    'covers_last_n_at_end': metrics.get('covers_last_n_at_end', False),
                    'consecutive_at_end': metrics.get('consecutive_at_end', 0),
                    'rate_percent': metrics['rate_percent'],
                    'occur_kys': metrics['occur_kys'],
                    'window': metrics['window']
                })
                
        # Sort by consecutive_at_end first (prefer true "chạm thông"), then by total_count
        res.sort(key=lambda x: (x.get('covers_last_n_at_end', False), x.get('consecutive_at_end', 0), x['total_count'], x['rate_percent']), reverse=True)
        return res[:10] # Tăng giới hạn trả về từ 5 lên 10 để UI có đủ dữ liệu
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