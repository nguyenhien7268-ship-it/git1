# Tên file: logic/de_analytics.py
from collections import Counter
from itertools import combinations
import re

try:
    from .de_utils import BO_SO_DE, get_gdb_last_2, check_cham, check_tong
except ImportError:
    from de_utils import BO_SO_DE, get_gdb_last_2, check_cham, check_tong

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

# --- CÁC HÀM PHÂN TÍCH V77 (ĐÃ FIX KEY MISMATCH THEO LOG DEBUG) ---

def _normalize_bo_key(val):
    """
    Helper: Chuẩn hóa giá trị cầu về đúng key trong BO_SO_DE.
    Dựa trên log: Key thực tế là "00", "01", "12" (không có chữ Bo).
    """
    if val is None: 
        print(f"[DEBUG _normalize_bo_key] Input is None")
        return None
    val_str = str(val).strip()
    
    # 1. Kiểm tra trực tiếp (VD: "01" khớp "01")
    if val_str in BO_SO_DE:
        return val_str
        
    # 2. Xử lý làm sạch: Bỏ chữ "Bo", "Bộ", khoảng trắng... -> Lấy số
    # VD: "Bo 01" -> "01", "Bộ 12" -> "12"
    digits_only = "".join(filter(str.isdigit, val_str))
    
    if digits_only:
        # Pad về 2 chữ số (VD: "1" -> "01", "0" -> "00")
        padded_val = digits_only.zfill(2)
        
        # Kiểm tra lại với key chuẩn (VD: "01")
        if padded_val in BO_SO_DE:
            return padded_val
            
        # Fallback: Kiểm tra lại với prefix "Bo " (đề phòng dữ liệu hỗn hợp)
        prefix_val = f"Bo {padded_val}"
        if prefix_val in BO_SO_DE:
            return prefix_val
    
    # ⚡ DEBUG: Log khi normalize thất bại (chỉ log lần đầu để tránh spam)
    if not hasattr(_normalize_bo_key, '_logged_failures'):
        _normalize_bo_key._logged_failures = set()
    failure_key = f"{val_str}_{digits_only}"
    if failure_key not in _normalize_bo_key._logged_failures and len(_normalize_bo_key._logged_failures) < 5:
        print(f"[DEBUG _normalize_bo_key] Failed to normalize: '{val}' (str: '{val_str}', digits: '{digits_only}')")
        print(f"[DEBUG _normalize_bo_key] Available BO_SO_DE keys: {list(BO_SO_DE.keys())[:10]}...")
        _normalize_bo_key._logged_failures.add(failure_key)
    return None

def get_de_consensus(bridges):
    """Tổng hợp Vote từ cầu (Consensus)"""
    vote_cham = Counter()
    
    for bridge in bridges:
        b_type = str(bridge.get('type', '')).upper()
        val = str(bridge.get('predicted_value', ''))
        weight = bridge.get('streak', 1)
        
        # FIX: Chuẩn hóa key bộ
        bo_key = _normalize_bo_key(val)
        
        # Nếu là cầu bộ -> Vote cho các số trong bộ
        if 'BO' in b_type and bo_key:
             for n in BO_SO_DE[bo_key]:
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
        
        if 'BO' in b_type:
            # FIX: Chuẩn hóa key bộ
            bo_key = _normalize_bo_key(val)
            if bo_key:
                for s in BO_SO_DE[bo_key]: 
                    scores[s] += streak * 2.0 
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

def get_top_strongest_sets(bridges, market_stats=None, last_row=None):
    """
    Tìm ra các Bộ Số có cầu chạy mạnh nhất (V77).
    Logic mới: Ưu tiên ghép cầu vị trí (2 vị trí) thành bộ số.
    Các cầu trùng (cùng dự đoán 1 bộ) có tỉ lệ cao và đang thông sẽ được ưu tiên.
    
    Args:
        bridges: Danh sách các cầu (bridges) để tính điểm
        market_stats: Dict chứa thống kê thị trường với keys:
            - freq_bo: Dict {bo_name: frequency} - Tần suất về của bộ số
            - gan_bo: Dict {bo_name: gan_days} - Số ngày gan của bộ số
        last_row: Dòng dữ liệu cuối cùng để lấy giá trị vị trí (optional)
    
    Returns:
        List[str]: Top 3 bộ số đẹp nhất (đã kết hợp điểm từ bridges + tần suất + gan)
    """
    # ⚡ DEBUG LOGGING: Kiểm tra BO_SO_DE và input
    print(f"[DEBUG ANALYTICS] BO_SO_DE size: {len(BO_SO_DE)}")
    print(f"[DEBUG ANALYTICS] Input bridges count: {len(bridges) if bridges else 0}")
    
    # ⚡ DEBUG: Thống kê các loại bridge
    if bridges:
        type_counter = {}
        for bridge in bridges:
            b_type = str(bridge.get('type', 'UNKNOWN')).upper()
            type_counter[b_type] = type_counter.get(b_type, 0) + 1
        print(f"[DEBUG ANALYTICS] Bridge types distribution: {type_counter}")
        
        # In mẫu một vài bridge để xem cấu trúc
        print(f"[DEBUG ANALYTICS] Sample bridges (first 3):")
        for i, bridge in enumerate(bridges[:3]):
            print(f"  Bridge {i}: type={bridge.get('type')}, predicted_value={bridge.get('predicted_value')}, name={bridge.get('name')}")
    
    # ⚡ FIX: Kiểm tra BO_SO_DE có rỗng không
    if not BO_SO_DE or len(BO_SO_DE) == 0:
        print("[ERROR ANALYTICS] BO_SO_DE is EMPTY! Returning default sets.")
        # Trả về danh sách bộ mặc định để tránh crash
        default_sets = ["00", "01", "12"] if "00" in BO_SO_DE else list(BO_SO_DE.keys())[:3] if BO_SO_DE else []
        return default_sets
    
    if not bridges:
        print("[DEBUG ANALYTICS] No bridges provided, returning empty list.")
        return []
    
    set_scores = {bo: 0 for bo in BO_SO_DE.keys()}
    
    # ⚡ LOGIC MỚI: GHÉP CẦU VỊ TRÍ THÀNH BỘ SỐ (Ưu tiên cao nhất)
    # Tìm các cầu vị trí và ghép chúng thành bộ số
    position_bridges = []
    for bridge in bridges:
        b_type = str(bridge.get('type', '')).upper()
        # Tìm cầu vị trí (DE_POS_SUM hoặc có pos1_idx, pos2_idx)
        if 'DE_POS' in b_type or ('POS' in b_type and bridge.get('pos1_idx') is not None and bridge.get('pos2_idx') is not None):
            position_bridges.append(bridge)
    
    if position_bridges and last_row:
        try:
            from logic.de_utils import get_bo_name_by_pair
            from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow
            
            # Lấy giá trị tại các vị trí từ last_row
            last_positions = getAllPositions_V17_Shadow(last_row)
            
            # Tạo dict để đếm số cầu trùng (consensus) cho mỗi bộ số
            bo_consensus = {}  # {bo_name: [list of bridges]}
            
            for bridge in position_bridges:
                try:
                    idx1 = bridge.get('pos1_idx')
                    idx2 = bridge.get('pos2_idx')
                    
                    # Bỏ qua nếu không có vị trí hợp lệ
                    if idx1 is None or idx2 is None or idx1 < 0 or idx2 < 0:
                        continue
                    if idx1 >= len(last_positions) or idx2 >= len(last_positions):
                        continue
                    
                    val1 = last_positions[idx1]
                    val2 = last_positions[idx2]
                    
                    if val1 is None or val2 is None:
                        continue
                    
                    # Lấy chữ số cuối của mỗi vị trí
                    try:
                        d1 = int(str(val1)[-1])
                        d2 = int(str(val2)[-1])
                    except (ValueError, TypeError):
                        continue
                    
                    # Ghép 2 vị trí thành cặp số và tìm bộ tương ứng
                    bo_name = get_bo_name_by_pair(d1, d2)
                    if bo_name and bo_name in set_scores:
                        if bo_name not in bo_consensus:
                            bo_consensus[bo_name] = []
                        bo_consensus[bo_name].append(bridge)
                except Exception:
                    continue  # Bỏ qua cầu lỗi
                        
            # Tính điểm cho các bộ số được ghép từ cầu vị trí
            # Ưu tiên: Cầu trùng (consensus) + Tỉ lệ cao + Đang thông
            for bo_name, bridge_list in bo_consensus.items():
                consensus_count = len(bridge_list)
                
                # Tính điểm base từ consensus (nhiều cầu trùng = điểm cao)
                base_score = consensus_count * 3.0  # Mỗi cầu trùng = +3 điểm
                
                # Tính điểm bổ sung từ tỉ lệ và streak của các cầu
                total_win_rate = 0.0
                total_streak = 0.0
                for bridge in bridge_list:
                    win_rate = bridge.get('win_rate', 0)
                    streak = bridge.get('streak', 1)
                    if not isinstance(streak, (int, float)):
                        try: streak = float(streak) if streak else 1
                        except: streak = 1
                    
                    total_win_rate += win_rate
                    total_streak += streak
                
                avg_win_rate = total_win_rate / consensus_count if consensus_count > 0 else 0
                avg_streak = total_streak / consensus_count if consensus_count > 0 else 0
                
                # Điểm bổ sung: Tỉ lệ cao và đang thông
                bonus_score = (avg_win_rate / 100.0 * 2.0) + (avg_streak * 1.5)
                
                # Tổng điểm cho bộ số này
                final_score = base_score + bonus_score
                set_scores[bo_name] += final_score
                
                print(f"[DEBUG ANALYTICS] Bộ {bo_name}: +{final_score:.1f} (consensus={consensus_count}, win_rate={avg_win_rate:.1f}%, streak={avg_streak:.1f})")
                
        except ImportError as e:
            print(f"[WARNING ANALYTICS] Cannot import required modules for position bridge scoring: {e}")
        except Exception as e:
            print(f"[WARNING ANALYTICS] Error processing position bridges: {e}")
    
    # ⚡ DEBUG: Đếm số bridge loại BO
    bo_bridge_count = 0
    bo_bridge_details = []
    
    # ⚡ FIX: Nếu không có bridge BO, tính điểm từ các bridge khác (chuyển chạm -> bộ)
    has_bo_bridges = False
    
    for bridge in bridges:
        try:
            b_type = str(bridge.get('type', '')).upper()
            val = str(bridge.get('predicted_value', ''))
            streak = bridge.get('streak', 1)
            
            if not isinstance(streak, (int, float)):
                try: streak = float(streak) if streak else 1
                except: streak = 1
            
            # ⚡ DEBUG: Kiểm tra bridge loại BO
            if 'BO' in b_type:
                has_bo_bridges = True
                bo_bridge_count += 1
                bo_key = _normalize_bo_key(val)
                if bo_key:
                    old_score = set_scores[bo_key]
                    set_scores[bo_key] += streak
                    bo_bridge_details.append({
                        'name': bridge.get('name', 'Unknown'),
                        'type': b_type,
                        'val': val,
                        'bo_key': bo_key,
                        'streak': streak,
                        'score_before': old_score,
                        'score_after': set_scores[bo_key]
                    })
                else:
                    bo_bridge_details.append({
                        'name': bridge.get('name', 'Unknown'),
                        'type': b_type,
                        'val': val,
                        'bo_key': None,
                        'error': 'normalize_failed'
                    })
        except Exception as e:
            print(f"[DEBUG ANALYTICS] Exception processing bridge {bridge.get('name', 'Unknown')}: {e}")
            continue
    
    # ⚡ FIX: Nếu không có bridge BO, tính điểm từ các bridge khác (chạm -> bộ)
    if not has_bo_bridges:
        print("[DEBUG ANALYTICS] No BO bridges found. Calculating scores from other bridges (cham -> bo)...")
        try:
            from logic.de_utils import get_bo_name_by_pair
            
            for bridge in bridges:
                try:
                    b_type = str(bridge.get('type', '')).upper()
                    val = str(bridge.get('predicted_value', ''))
                    streak = bridge.get('streak', 1)
                    
                    if not isinstance(streak, (int, float)):
                        try: streak = float(streak) if streak else 1
                        except: streak = 1
                    
                    if not val: continue
                    
                    # Parse predicted_value (có thể là chạm: "2,3,7,8" hoặc số đơn: "9")
                    parts = []
                    if ',' in val:
                        parts = [int(v.strip()) for v in val.split(',') if v.strip().isdigit()]
                    elif val.isdigit():
                        parts = [int(val)]
                    
                    if not parts: continue
                    
                    # Từ các chạm, tạo các cặp số và tìm bộ tương ứng
                    # Logic: Mỗi chạm có thể tạo số gốc và bóng dương
                    # Từ các số đó, tạo cặp và tìm bộ tương ứng
                    bo_sets_found = set()
                    
                    # Tạo danh sách số từ chạm (kể cả bóng)
                    all_digits = set()
                    for cham in parts:
                        all_digits.add(cham)
                        all_digits.add((cham + 5) % 10)  # Bóng dương
                    
                    # Tạo tất cả các cặp số từ danh sách digits
                    digits_list = sorted(list(all_digits))
                    for i in range(len(digits_list)):
                        for j in range(i, len(digits_list)):
                            d1, d2 = digits_list[i], digits_list[j]
                            # Tìm bộ từ cặp số (01 và 10 đều thuộc cùng một bộ)
                            bo_name = get_bo_name_by_pair(d1, d2)
                            if bo_name and bo_name in set_scores:
                                bo_sets_found.add(bo_name)
                    
                    # Cộng điểm cho tất cả các bộ tìm được (mỗi bộ chỉ cộng 1 lần)
                    for bo_name in bo_sets_found:
                        set_scores[bo_name] += streak
                        
                except Exception as e:
                    print(f"[DEBUG ANALYTICS] Exception processing non-BO bridge {bridge.get('name', 'Unknown')}: {e}")
                    continue
                    
        except ImportError:
            print("[ERROR ANALYTICS] Cannot import get_bo_name_by_pair. Skipping non-BO bridge scoring.")
    
    # ⚡ DEBUG: In thống kê
    print(f"[DEBUG ANALYTICS] BO bridges found: {bo_bridge_count}")
    if bo_bridge_details:
        print(f"[DEBUG ANALYTICS] BO bridge details (first 5):")
        for detail in bo_bridge_details[:5]:
            print(f"  - {detail}")
    else:
        print("[DEBUG ANALYTICS] No BO bridges found or all failed to normalize!")
    
    # ⚡ KẾT HỢP VỚI THỐNG KÊ THỊ TRƯỜNG (Tần suất + Gan)
    if market_stats:
        freq_bo = market_stats.get('freq_bo', {})
        gan_bo = market_stats.get('gan_bo', {})
        
        print(f"[DEBUG ANALYTICS] Kết hợp thống kê thị trường: freq_bo={len(freq_bo)}, gan_bo={len(gan_bo)}")
        
        # Tính điểm bổ sung từ tần suất và gan
        # ⚡ FIX: Giảm trọng số và normalize để tránh ưu tiên quá nhiều bộ kép
        for bo_name in set_scores.keys():
            # Điểm từ tần suất: Bộ về nhiều = điểm cao
            freq_score = freq_bo.get(bo_name, 0)
            
            # ⚡ NORMALIZE: Bộ kép (4 số) vs Bộ thường (8 số)
            # Bộ kép có ít số hơn nên tần suất tự nhiên cao hơn
            # Normalize bằng cách chia cho số lượng số trong bộ
            num_numbers_in_bo = len(BO_SO_DE.get(bo_name, []))
            normalized_freq = freq_score / max(num_numbers_in_bo, 1)  # Tránh chia 0
            
            # Điểm từ gan: Bộ gan ít (sắp về) = điểm cao (nghịch đảo)
            gan_days = gan_bo.get(bo_name, 999)
            gan_score = max(0, 10 - min(gan_days, 10))  # Gan <= 10 ngày = điểm cao
            
            # ⚡ GIẢM TRỌNG SỐ: Từ (freq x2, gan x1) xuống (freq x0.5, gan x0.5)
            # Để điểm từ bridges vẫn là yếu tố chính
            bonus_score = (normalized_freq * 0.5) + (gan_score * 0.5)
            
            # ⚡ GIỚI HẠN ĐIỂM BONUS: Tối đa 5 điểm để không làm lệch quá nhiều
            bonus_score = min(bonus_score, 5.0)
            
            set_scores[bo_name] += bonus_score
            
            if bonus_score > 0:
                print(f"[DEBUG ANALYTICS] Bộ {bo_name}: +{bonus_score:.2f} (freq={freq_score}->{normalized_freq:.2f}, gan={gan_days}, num_in_bo={num_numbers_in_bo})")
    else:
        print("[DEBUG ANALYTICS] Không có thống kê thị trường, chỉ tính điểm từ bridges.")
    
    # ⚡ DEBUG: In top 5 set_scores để xem điểm
    top_5_scores = sorted(set_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"[DEBUG ANALYTICS] Top 5 set scores (after market stats): {top_5_scores}")
            
    all_sets_sorted = sorted(set_scores.items(), key=lambda x: x[1], reverse=True)
    active_sets = [x[0] for x in all_sets_sorted if x[1] > 0]
    
    print(f"[DEBUG ANALYTICS] Active sets (score > 0): {len(active_sets)}")
    print(f"[DEBUG ANALYTICS] Top 3 active sets: {active_sets[:3]}")
    
    if active_sets:
        result = active_sets[:3]
        print(f"[DEBUG ANALYTICS] Returning top 3 active sets: {result}")
        return result
    elif bridges:
        result = [x[0] for x in all_sets_sorted[:3]]
        print(f"[DEBUG ANALYTICS] No active sets, returning top 3 overall: {result}")
        return result
    else:
        print("[DEBUG ANALYTICS] No bridges, returning empty list.")
        return []

# --- PHÂN TÍCH TỔ HỢP 4 CHẠM (KẾT HỢP THỐNG KÊ) ---
def calculate_top_touch_combinations(all_data, num_touches=4, days=10, market_stats=None):
    """
    Tính toán Max Streak và Win Rate cho TẤT CẢ các tổ hợp 4 chạm khả thi.
    Kết hợp với thống kê tần suất/gan chạm để tăng độ chính xác.
    
    Args:
        all_data: Dữ liệu lịch sử
        num_touches: Số chạm trong tổ hợp (mặc định 4)
        days: Số ngày gần nhất để phân tích (mặc định 10)
        market_stats: Dict chứa thống kê thị trường với keys:
            - freq_cham: Dict {cham: frequency} - Tần suất về của chạm
            - gan_cham: Dict {cham: gan_days} - Số ngày gan của chạm
    
    Returns:
        List[dict]: Danh sách tổ hợp chạm với điểm đã kết hợp thống kê
    """
    if not all_data or len(all_data) < 2: return []
    recent_data = all_data[-days:] if len(all_data) > days else all_data
    all_touches = list(range(10)) 
    touch_combinations = list(combinations(all_touches, num_touches))
    results = []
    
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
        
        # ⚡ KẾT HỢP THỐNG KÊ THỊ TRƯỜNG: Tính điểm bổ sung từ tần suất/gan chạm
        market_bonus_score = 0.0
        if market_stats:
            freq_cham = market_stats.get('freq_cham', {})
            gan_cham = market_stats.get('gan_cham', {})
            
            # Tính điểm từ tần suất: Chạm về nhiều = điểm cao
            total_freq = sum(freq_cham.get(cham, 0) for cham in touch_list)
            # Tính điểm từ gan: Chạm gan ít (sắp về) = điểm cao
            total_gan_days = sum(gan_cham.get(cham, 999) for cham in touch_list)
            avg_gan = total_gan_days / len(touch_list) if touch_list else 999
            gan_bonus = max(0, 10 - min(avg_gan, 10))  # Gan <= 10 ngày = điểm cao
            
            # Cộng điểm bổ sung (trọng số: tần suất x1.5, gan x1)
            market_bonus_score = (total_freq * 1.5) + (gan_bonus * 1.0)
        
        # Thêm điểm thống kê vào streak để ưu tiên tổ hợp có thống kê tốt
        adjusted_streak = max_streak + (market_bonus_score / 10.0)  # Chia 10 để không làm lệch quá nhiều
        
        results.append({
            'touches': touch_list, 
            'streak': max_streak,  # Giữ nguyên streak gốc
            'adjusted_streak': adjusted_streak,  # Streak đã điều chỉnh với thống kê
            'rate_hits': rate_hits, 
            'rate_total': rate_total, 
            'rate_percent': rate_percent,
            'market_bonus': market_bonus_score  # Điểm bổ sung từ thống kê
        })
    
    # Sắp xếp theo adjusted_streak (đã kết hợp thống kê) và rate_percent
    results.sort(key=lambda x: (x['adjusted_streak'], x['rate_percent']), reverse=True)
    return results