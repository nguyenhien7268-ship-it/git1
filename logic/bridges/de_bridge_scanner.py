# Tên file: logic/bridges/de_bridge_scanner.py
# (PHIÊN BẢN V11.2 - K1N-PRIMARY REFACTOR: READ-ONLY SCANNER)
# Returns Candidate objects instead of writing to DB directly.

import sqlite3
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple, Set

# Fallback imports
try:
    from logic.db_manager import DB_NAME, get_all_managed_bridge_names, load_rates_cache
    from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, getPositionName_V17_Shadow
    from logic.de_utils import (
        get_gdb_last_2, check_cham, get_touches_by_offset, 
        generate_dan_de_from_touches, get_set_name_of_number, BO_SO_DE
    )
    from logic.models import Candidate
    from logic.common_utils import normalize_bridge_name
except ImportError:
    DB_NAME = "lottery.db"
    pass 

class DeBridgeScanner:
    """
    Bộ quét cầu Đề tự động (Automated DE Bridge Scanner)
    Phiên bản: V10.1 (Speed Optimized)
    Chiến thuật: Sử dụng Ma trận số nguyên (Integer Matrix) để loại bỏ chi phí xử lý chuỗi.
    """

    def __init__(self):
        # [CONFIGURATION]
        self.min_streak = 3        # Cầu Lô/Vị trí
        self.min_streak_bo = 1     # Cầu Bộ
        self.scan_depth = 30       # Số kỳ quét (Short-term)
        self.memory_depth = 90     # Số kỳ quét Bạc Nhớ (Long-term)
        
        self.history_check_len = 10 
        self.min_wins_required = 4  
        self.validation_len = 15   
        self.min_val_wins = 2      
        
        # Cấu hình Killer & Memory
        self.min_killer_streak = 12 
        self.min_memory_confidence = 60.0 

        # Cứu Cầu
        self.rescue_wins_10 = 7    
        self.min_wins_bo_10 = 2    

    def _preprocess_data(self, all_data_ai: List[List[str]]) -> List[List[Optional[int]]]:
        """
        [OPTIMIZATION CORE] Chuyển đổi dữ liệu thô sang ma trận số nguyên 1 lần duy nhất.
        Trả về: List các hàng, mỗi hàng là list 214 số nguyên (vị trí V17).
        """
        matrix = []
        for row in all_data_ai:
            try:
                # Dùng hàm V17 để lấy 214 vị trí (bao gồm bóng)
                # Hàm này trả về list các số nguyên hoặc None
                positions = getAllPositions_V17_Shadow(row)
                matrix.append(positions)
            except:
                matrix.append([None] * 214) # Fallback nếu lỗi
        return matrix

    def scan_all(
        self, 
        all_data_ai: List[List[str]], 
        db_name: str = DB_NAME
    ) -> Tuple[List[Candidate], Dict[str, Any]]:
        """
        Scan for DE bridges and return Candidate objects (READ-ONLY, no DB writes).
        
        V11.2 K1N-Primary Refactor:
        - Returns Candidate objects instead of writing to DB
        - Attaches K1N/K2N rates from cache
        - Excludes existing bridges before returning
        - Returns metadata about scan results
        
        Args:
            all_data_ai: Historical lottery data
            db_name: Database path for reading existing bridges
            
        Returns:
            Tuple of (candidates: List[Candidate], meta: Dict):
                - candidates: List of bridge candidates with rates attached
                - meta: Dict with 'found_total', 'excluded_existing', 'returned_count'
        """
        if not self._validate_input_data(all_data_ai):
            return [], {'found_total': 0, 'excluded_existing': 0, 'returned_count': 0}

        print(f">>> [DE SCANNER V11.2] Bắt đầu quét (K1N-Primary Read-Only)...")
        
        # 1. [OPTIMIZATION] Tiền xử lý dữ liệu sang dạng số
        data_matrix = self._preprocess_data(all_data_ai)
        
        found_bridges: List[Dict[str, Any]] = []

        # 2. CHIẾN THUẬT TOÁN HỌC (Sử dụng data_matrix)
        found_bridges.extend(self._scan_dynamic_offset(all_data_ai, data_matrix))
        found_bridges.extend(self._scan_algorithm_sum(all_data_ai, data_matrix))
        found_bridges.extend(self._scan_set_bridges(all_data_ai, data_matrix))
        found_bridges.extend(self._scan_pascal_topology(all_data_ai))

        # 3. CHIẾN THUẬT KHAI PHÁ DỮ LIỆU (DATA MINING)
        bridges_memory = self._scan_memory_pattern(all_data_ai)
        print(f">>> [DE SCANNER] Bạc Nhớ tìm thấy: {len(bridges_memory)}")
        found_bridges.extend(bridges_memory)

        # 4. CHIẾN THUẬT LOẠI TRỪ (KILLER) (Sử dụng data_matrix)
        bridges_killer = self._scan_killer_bridges(all_data_ai, data_matrix)
        print(f">>> [DE SCANNER] Cầu Loại tìm thấy: {len(bridges_killer)}")
        found_bridges.extend(bridges_killer)

        # 5. RANK AND CONVERT TO CANDIDATES (NO DB WRITE)
        self._rank_bridges(found_bridges)
        found_total = len(found_bridges)
        
        # 6. LOAD EXISTING NAMES AND RATES CACHE (SINGLE DB CALL EACH)
        print(f">>> [DE SCANNER] Loading existing bridges and rates cache...")
        existing_names = get_all_managed_bridge_names(db_name)
        rates_cache = load_rates_cache(db_name)
        
        # 7. CONVERT TO CANDIDATES WITH RATES AND EXCLUDE EXISTING
        candidates = self._convert_to_candidates(found_bridges, existing_names, rates_cache)
        excluded_count = found_total - len(candidates)
        
        meta = {
            'found_total': found_total,
            'excluded_existing': excluded_count,
            'returned_count': len(candidates)
        }
        
        print(f">>> [DE SCANNER] Kết quả: {found_total} tìm thấy, {excluded_count} đã tồn tại, {len(candidates)} trả về.")
        return candidates, meta

    # --- CORE HELPERS ---

    def _validate_input_data(self, data: List[List[str]]) -> bool:
        required_len = self.scan_depth + self.validation_len
        if not data or len(data) < required_len:
            if data and len(data) >= self.scan_depth:
                self.validation_len = 0 
                return True
            return False
        return True

    def _clean_str(self, raw_val) -> str:
        if not raw_val: return ""
        return ''.join(filter(str.isdigit, str(raw_val)))

    def _calculate_ranking_score(self, streak: int, wins_10: int, bridge_type: str) -> float:
        type_bonus = 0.0
        if bridge_type == 'DE_SET': type_bonus = 2.0
        elif bridge_type == 'DE_PASCAL': type_bonus = 1.0
        elif bridge_type == 'DE_MEMORY': return 15.0 + (wins_10 / 2)
        elif bridge_type == 'DE_KILLER': return streak * 2.0

        stability_bonus = 1.5 if wins_10 >= 8 else 0.0
        return (streak * 1.5) + (wins_10 * 1.0) + type_bonus + stability_bonus

    def _rank_bridges(self, bridges: List[Dict[str, Any]]) -> None:
        for b in bridges:
            streak = b.get('streak', 0)
            try:
                wr = float(b.get('win_rate', 0))
                wins_10 = int((wr / 100.0) * 10)
            except (ValueError, TypeError):
                wins_10 = 0
            b['ranking_score'] = self._calculate_ranking_score(streak, wins_10, b.get('type', ''))
        bridges.sort(key=lambda x: x['ranking_score'], reverse=True)
    
    def _convert_to_candidates(
        self, 
        bridges: List[Dict[str, Any]], 
        existing_names: Set[str],
        rates_cache: Dict[str, Dict[str, float]]
    ) -> List[Candidate]:
        """
        Convert bridge dicts to Candidate objects with K1N/K2N rates attached.
        
        Excludes bridges whose normalized names already exist in DB.
        Attaches rates from cache, sets rate_missing flag if not found.
        
        Args:
            bridges: List of bridge dictionaries from scan
            existing_names: Set of normalized existing bridge names
            rates_cache: Dict mapping normalized names to rates
            
        Returns:
            List of Candidate objects (excluding existing bridges)
        """
        candidates = []
        
        for b in bridges:
            name = b.get('name', '')
            if not name:
                continue
            
            # Normalize name for duplicate checking
            norm_name = normalize_bridge_name(name)
            
            # Skip if already exists
            if norm_name in existing_names:
                continue
            
            # Get rates from cache
            rates = rates_cache.get(norm_name, {})
            k1n_lo = rates.get('k1n_rate_lo', 0.0)
            k1n_de = rates.get('k1n_rate_de', 0.0)
            k2n_lo = rates.get('k2n_rate_lo', 0.0)
            k2n_de = rates.get('k2n_rate_de', 0.0)
            
            # Set rate_missing flag if no rates found
            rate_missing = (k1n_de == 0.0 and k2n_de == 0.0)
            
            # Build description
            desc = b.get('display_desc', '')
            full_dan = b.get('full_dan', '')
            final_desc = f"{desc}. Dàn: {full_dan}" if full_dan else desc
            streak = b.get('streak', 0)
            final_desc += f". Thông {streak} kỳ."
            
            # Determine kind (single vs set)
            bridge_type = b.get('type', '')
            kind = 'set' if bridge_type == 'DE_SET' else 'single'
            
            # Calculate win_count_10 from win_rate
            try:
                wr = float(b.get('win_rate', 0))
                win_count_10 = int((wr / 100.0) * 10)
            except (ValueError, TypeError):
                win_count_10 = 0
            
            # Create Candidate object
            candidate = Candidate(
                name=name,
                normalized_name=norm_name,
                type='de',
                kind=kind,
                k1n_lo=k1n_lo,
                k1n_de=k1n_de,
                k2n_lo=k2n_lo,
                k2n_de=k2n_de,
                stl=b.get('predicted_value', 'N/A'),
                reason=bridge_type,
                pos1_idx=b.get('pos1_idx'),
                pos2_idx=b.get('pos2_idx'),
                description=final_desc,
                streak=streak,
                win_count_10=win_count_10,
                rate_missing=rate_missing,
                metadata={
                    'win_rate': b.get('win_rate', 0.0),
                    'full_dan': full_dan,
                    'ranking_score': b.get('ranking_score', 0.0)
                }
            )
            
            candidates.append(candidate)
        
        return candidates

    def _validate_bridge(self, all_data_ai, data_matrix, idx1, idx2, k_param, mode) -> bool:
        """
        Hàm validate sử dụng data_matrix để tăng tốc.
        """
        if self.validation_len <= 0: return True
        start_idx = len(all_data_ai) - self.scan_depth - self.validation_len
        end_idx = len(all_data_ai) - self.scan_depth
        if start_idx < 1: return True

        val_wins = 0
        # data_matrix index tương ứng với all_data_ai index
        scan_slice_indices = range(start_idx, end_idx)
        
        for real_idx in scan_slice_indices:
            row_curr = all_data_ai[real_idx] # Vẫn cần row gốc để lấy GĐB
            # row_prev lấy từ matrix để nhanh hơn
            row_prev_vals = data_matrix[real_idx - 1] 
            
            gdb = get_gdb_last_2(row_curr)
            if not gdb: continue
            
            try:
                is_win = False
                # Lấy giá trị trực tiếp từ matrix, không cần parse
                v1 = row_prev_vals[idx1]
                v2 = row_prev_vals[idx2] if idx2 is not None else None
                
                if v1 is None or (idx2 is not None and v2 is None): continue
                
                if mode == "DYNAMIC":
                    # Dynamic offset logic
                    touches = get_touches_by_offset((v1 + v2) % 10, k_param)
                    is_win = check_cham(gdb, touches)
                elif mode == "DE_POS_SUM":
                    pred = (v1 + v2) % 10
                    is_win = check_cham(gdb, [pred])
                elif mode == "SET":
                    s_name = get_set_name_of_number(f"{v1}{v2}")
                    if s_name:
                        is_win = gdb in BO_SO_DE.get(s_name, [])
                if is_win: val_wins += 1
            except Exception: continue
            
        return val_wins >= self.min_val_wins

    # =========================================================================
    # MODULE 1: BẠC NHỚ (Giữ nguyên vì logic khác biệt)
    # =========================================================================
    
    def _scan_memory_pattern(self, all_data_ai: List[List[str]]) -> List[Dict[str, Any]]:
        results = []
        mining_depth = min(len(all_data_ai) - 1, self.memory_depth)
        mining_data = all_data_ai[-mining_depth:]
        
        triggers = [
            (2, "GDB_Tail", "Đuôi ĐB"), 
            (2, "GDB_Head", "Đầu ĐB"),
            (3, "G1_Tail", "Đuôi G1"),
        ]

        last_row = all_data_ai[-1]

        for col_idx, trigger_code, trigger_name in triggers:
            current_signal = self._get_signal_value(last_row, col_idx, trigger_code)
            if current_signal is None: continue

            matching_next_days_gdb = []
            
            for k in range(len(mining_data) - 2):
                row_k = mining_data[k]
                hist_signal = self._get_signal_value(row_k, col_idx, trigger_code)
                
                if hist_signal == current_signal:
                    row_next = mining_data[k+1]
                    gdb_next = get_gdb_last_2(row_next)
                    if gdb_next:
                        matching_next_days_gdb.append(gdb_next)

            if len(matching_next_days_gdb) < 5: continue

            touch_counts = Counter()
            for gdb in matching_next_days_gdb:
                if len(gdb) == 2:
                    touch_counts[int(gdb[0])] += 1
                    touch_counts[int(gdb[1])] += 1
            
            total_matches = len(matching_next_days_gdb)
            if total_matches == 0: continue
            
            best_touch, count = touch_counts.most_common(1)[0]
            confidence = (count / total_matches) * 100

            if confidence >= self.min_memory_confidence:
                touches = [best_touch]
                final_dan = generate_dan_de_from_touches(touches)
                
                results.append({
                    "name": f"DE_MEM_{trigger_code}_{current_signal}",
                    "type": "DE_MEMORY",
                    "streak": int(confidence),
                    "predicted_value": f"CHẠM {best_touch}",
                    "full_dan": ",".join(final_dan),
                    "win_rate": confidence,
                    "display_desc": f"Bạc nhớ: Khi {trigger_name} về {current_signal} -> Hay về Chạm {best_touch} ({count}/{total_matches} lần)"
                })
        return results

    def _get_signal_value(self, row: List[str], col_idx: int, code: str) -> Optional[int]:
        try:
            val_str = self._clean_str(row[col_idx])
            if not val_str: return None
            
            if "Tail" in code:
                return int(val_str[-1])
            elif "Head" in code:
                if len(val_str) >= 2:
                    return int(val_str[0])
            return None
        except:
            return None

    # =========================================================================
    # MODULE 2: CẦU LOẠI (KILLER) - OPTIMIZED SCAN
    # =========================================================================

    def _scan_killer_bridges(self, all_data_ai: List[List[str]], data_matrix: List[List[Optional[int]]]) -> List[Dict[str, Any]]:
        results = []
        try:
            # 117 Vị trí (107 gốc + 10 bóng)
            limit_pos = 117
            
            # Chỉ số bắt đầu quét
            scan_end_idx = len(all_data_ai)
            scan_start_idx = max(1, scan_end_idx - self.scan_depth)
            
            for i in range(limit_pos):
                for j in range(i, limit_pos):
                    killer_streak = 0
                    # Quét ngược từ gần nhất về quá khứ
                    for k in range(scan_end_idx - 1, 0, -1):
                        # Dừng nếu vượt quá độ sâu quét
                        if scan_end_idx - k > self.scan_depth: break
                        
                        gdb = get_gdb_last_2(all_data_ai[k])
                        # Lấy giá trị trực tiếp từ matrix [k-1] (ngày trước đó)
                        row_prev_vals = data_matrix[k-1]
                        
                        v1 = row_prev_vals[i]
                        v2 = row_prev_vals[j]
                        
                        if not gdb or v1 is None or v2 is None: break
                        
                        pred_touch = (v1 + v2) % 10
                        has_touch = check_cham(gdb, [pred_touch])
                        
                        if not has_touch: killer_streak += 1
                        else: break

                    if killer_streak >= self.min_killer_streak:
                        # Dự đoán cho ngày mai
                        curr_vals = data_matrix[-1]
                        v1, v2 = curr_vals[i], curr_vals[j]
                        
                        if v1 is not None and v2 is not None:
                            next_killer_touch = (v1 + v2) % 10
                            p1_n = getPositionName_V17_Shadow(i).replace('[', '.').replace(']', '')
                            p2_n = getPositionName_V17_Shadow(j).replace('[', '.').replace(']', '')
                            
                            results.append({
                                "name": f"DE_KILLER_{p1_n}_{p2_n}",
                                "type": "DE_KILLER",
                                "streak": killer_streak,
                                "predicted_value": f"LOẠI CHẠM {next_killer_touch}",
                                "full_dan": "",
                                "win_rate": 0,
                                "display_desc": f"LOẠI Chạm {next_killer_touch} (Thông {killer_streak} kỳ). Từ: {p1_n}+{p2_n}",
                                "pos1_idx": i,
                                "pos2_idx": j
                            })
        except Exception as e:
            print(f">>> [ERROR] Lỗi quét Cầu Loại: {e}")
        
        results.sort(key=lambda x: x['streak'], reverse=True)
        return results[:15]

    # =========================================================================
    # MODULE 3: CẦU PASCAL
    # =========================================================================

    def _scan_pascal_topology(self, all_data_ai: List[List[str]]) -> List[Dict[str, Any]]:
        results = []
        scan_data = all_data_ai[-self.scan_depth:]
        sources = [
            {"name": "GDB", "cols": [2]},
            {"name": "G1", "cols": [3]},
            {"name": "GDB_G1", "cols": [2, 3]}
        ]

        for src in sources:
            consecutive_streak = 0
            wins_10 = 0
            for k in range(len(scan_data) - 1, 0, -1):
                row_curr = scan_data[k]
                row_prev = scan_data[k-1]
                gdb = get_gdb_last_2(row_curr)
                if not gdb: break
                
                # Pascal vẫn cần xử lý chuỗi vì cấu trúc đặc thù, nhưng số lượng ít nên không sao
                input_digits = []
                valid_input = True
                for col_idx in src["cols"]:
                    val_str = self._clean_str(row_prev[col_idx])
                    if not val_str: valid_input = False; break
                    input_digits.extend([int(d) for d in val_str])
                
                if not valid_input or len(input_digits) < 2: continue
                
                final_pair = self._compute_pascal_reduction(input_digits)
                if final_pair is None: continue
                
                pred_val = f"{final_pair[0]}{final_pair[1]}"
                rev_val = f"{final_pair[1]}{final_pair[0]}"
                is_win = (gdb == pred_val or gdb == rev_val)
                days_ago = len(scan_data) - 1 - k
                if is_win:
                    if consecutive_streak == days_ago: consecutive_streak += 1
                    if days_ago < self.history_check_len: wins_10 += 1
                else:
                    if consecutive_streak > 0: break 
            
            if consecutive_streak >= self.min_streak or wins_10 >= self.rescue_wins_10:
                # [FIX] Tính tổng số kỳ thắng trên 30 ngày để khớp với Popup
                total_wins_30 = 0
                total_days_30 = 0
                for k in range(len(scan_data) - 1, 0, -1):
                    row_curr = scan_data[k]
                    row_prev = scan_data[k-1]
                    gdb = get_gdb_last_2(row_curr)
                    if not gdb: continue
                    
                    input_digits = []
                    valid_input = True
                    for col_idx in src["cols"]:
                        val_str = self._clean_str(row_prev[col_idx])
                        if not val_str: valid_input = False; break
                        input_digits.extend([int(d) for d in val_str])
                    
                    if not valid_input or len(input_digits) < 2: continue
                    
                    final_pair = self._compute_pascal_reduction(input_digits)
                    if final_pair is None: continue
                    
                    # Only count this day if we have valid data
                    total_days_30 += 1
                    
                    pred_val = f"{final_pair[0]}{final_pair[1]}"
                    rev_val = f"{final_pair[1]}{final_pair[0]}"
                    if gdb == pred_val or gdb == rev_val: total_wins_30 += 1
                
                last_row = all_data_ai[-1]
                next_input = []
                for col_idx in src["cols"]:
                    v = self._clean_str(last_row[col_idx])
                    if v: next_input.extend([int(d) for d in v])
                next_pair = self._compute_pascal_reduction(next_input)
                if next_pair:
                    val_str = f"{next_pair[0]}{next_pair[1]}"
                    rev_str = f"{next_pair[1]}{next_pair[0]}"
                    display_val = f"{val_str},{rev_str}" if val_str != rev_str else val_str
                    results.append({
                        "name": f"DE_PASCAL_{src['name']}",
                        "type": "DE_PASCAL",
                        "streak": total_wins_30,
                        "predicted_value": display_val,
                        "full_dan": display_val,
                        "win_rate": (total_wins_30 / total_days_30 * 100) if total_days_30 > 0 else 0,
                        "display_desc": f"Cầu Pascal ({src['name']}) - STL: {display_val}"
                    })
        return results

    def _compute_pascal_reduction(self, digits: List[int]) -> Optional[Tuple[int, int]]:
        current_layer = digits
        while len(current_layer) > 2:
            next_layer = []
            for i in range(len(current_layer) - 1):
                sum_val = (current_layer[i] + current_layer[i+1]) % 10
                next_layer.append(sum_val)
            current_layer = next_layer
        if len(current_layer) == 2:
            return (current_layer[0], current_layer[1])
        return None

    # =========================================================================
    # MODULE 4: DYNAMIC & SUM (CLASSIC) - OPTIMIZED SCAN
    # =========================================================================

    def _scan_dynamic_offset(self, all_data_ai: List[List[str]], data_matrix: List[List[Optional[int]]]) -> List[Dict[str, Any]]:
        results = []
        scan_len = len(all_data_ai)
        scan_start_idx = max(1, scan_len - self.scan_depth)
        
        last_row_vals = data_matrix[-1]
        
        # Chỉ quét các vị trí GĐB (0-4), G1 (5-9), G7 (99-106) để tối ưu hơn nữa nếu cần
        # Nhưng với Matrix, ta có thể quét full 117 vị trí nhanh chóng.
        # Lưu ý: data_matrix chứa 214 vị trí (bao gồm bóng).
        # Ta quét 117 vị trí đầu (gốc + bóng vip)
        num_cols = 117
        
        pairs = []
        # Tối ưu cặp quét: 
        # Chỉ quét i, j trong khoảng 0-117.
        for i in range(num_cols):
            for j in range(i + 1, num_cols):
                pairs.append((i, j))
        
        for idx1, idx2 in pairs:
            # Lấy giá trị kỳ cuối để dự đoán (nếu cầu tốt)
            val1_last = last_row_vals[idx1]
            val2_last = last_row_vals[idx2]
            if val1_last is None or val2_last is None: continue
            
            # Thử 10 offset K
            for k in range(10): 
                total_wins = 0
                check_window = 0
                valid_history = True
                
                # Check history (Backtest nhanh)
                # Dùng data_matrix để truy xuất cực nhanh
                for day_idx in range(scan_len - 1, scan_len - 1 - self.history_check_len, -1):
                    if day_idx < 1: break
                    check_window += 1
                    
                    gdb_today = get_gdb_last_2(all_data_ai[day_idx]) # GĐB vẫn lấy từ raw vì là string "00"-"99"
                    if not gdb_today: continue
                    
                    row_prev_vals = data_matrix[day_idx-1]
                    d1 = row_prev_vals[idx1]
                    d2 = row_prev_vals[idx2]
                    
                    if d1 is None or d2 is None: 
                        valid_history = False; break
                    
                    base_sum = (d1 + d2) % 10
                    touches = get_touches_by_offset(base_sum, k)
                    
                    if check_cham(gdb_today, touches): total_wins += 1
                
                if not valid_history: continue
                
                # Nếu đạt chuẩn history, validate kỹ hơn và lưu
                if total_wins >= self.min_wins_required:
                    if self._validate_bridge(all_data_ai, data_matrix, idx1, idx2, k, "DYNAMIC"):
                        
                        # [FIX] Tính lại streak trên scan_depth (30 kỳ) để khớp với Popup
                        streak_30 = 0
                        total_days_30 = 0
                        for day_idx in range(scan_len - 1, max(0, scan_len - 1 - self.scan_depth), -1):
                            if day_idx < 1: break
                            
                            gdb_today = get_gdb_last_2(all_data_ai[day_idx])
                            if not gdb_today: continue
                            
                            row_prev_vals = data_matrix[day_idx-1]
                            d1 = row_prev_vals[idx1]
                            d2 = row_prev_vals[idx2]
                            
                            if d1 is None or d2 is None: continue
                            
                            # Only count this day if we have valid data
                            total_days_30 += 1
                            
                            base_sum = (d1 + d2) % 10
                            touches = get_touches_by_offset(base_sum, k)
                            
                            if check_cham(gdb_today, touches): streak_30 += 1
                        
                        base_last = (val1_last + val2_last) % 10
                        final_touches = get_touches_by_offset(base_last, k)
                        final_dan = generate_dan_de_from_touches(final_touches)
                        
                        name1 = getPositionName_V17_Shadow(idx1).replace('[', '.').replace(']', '')
                        name2 = getPositionName_V17_Shadow(idx2).replace('[', '.').replace(']', '')
                        
                        results.append({
                            "name": f"DE_DYN_{name1}_{name2}_K{k}",
                            "type": "DE_DYNAMIC_K",
                            "streak": streak_30,
                            "predicted_value": ",".join(map(str, final_touches)),
                            "full_dan": ",".join(final_dan),
                            "win_rate": (streak_30 / total_days_30 * 100) if total_days_30 > 0 else 0,
                            "display_desc": f"Đuôi {name1} + Đuôi {name2} (K={k})",
                            "pos1_idx": idx1,
                            "pos2_idx": idx2,
                            "k_offset": k
                        })
        return results

    def _scan_algorithm_sum(self, all_data_ai: List[List[str]], data_matrix: List[List[Optional[int]]]) -> List[Dict[str, Any]]:
        results = []
        try:
            limit_pos = 117
            scan_len = len(all_data_ai)
            
            for i in range(limit_pos):
                for j in range(i, limit_pos):
                    consecutive_streak = 0
                    wins_10 = 0
                    
                    # Backtest Loop (consecutive wins)
                    for k in range(scan_len - 1, 0, -1):
                        if scan_len - k > self.scan_depth: break
                        
                        gdb = get_gdb_last_2(all_data_ai[k])
                        row_prev_vals = data_matrix[k-1]
                        
                        v1, v2 = row_prev_vals[i], row_prev_vals[j]
                        if not gdb or v1 is None or v2 is None: break
                        
                        pred = (v1 + v2) % 10
                        is_win = check_cham(gdb, [pred])
                        
                        days_ago = scan_len - 1 - k
                        if is_win:
                            if consecutive_streak == days_ago: consecutive_streak += 1 
                            if days_ago < self.history_check_len: wins_10 += 1
                        else:
                            if consecutive_streak > 0: break 
                    
                    if consecutive_streak >= self.min_streak or wins_10 >= self.rescue_wins_10:
                        if self._validate_bridge(all_data_ai, data_matrix, i, j, 0, "DE_POS_SUM"):
                            # [FIX] Tính tổng số kỳ thắng trên 30 ngày để khớp với Popup
                            total_wins_30 = 0
                            total_days_30 = 0
                            for k in range(scan_len - 1, max(0, scan_len - 1 - self.scan_depth), -1):
                                if k < 1: break
                                
                                gdb = get_gdb_last_2(all_data_ai[k])
                                if not gdb: continue
                                
                                row_prev_vals = data_matrix[k-1]
                                v1, v2 = row_prev_vals[i], row_prev_vals[j]
                                if v1 is None or v2 is None: continue
                                
                                # Only count this day if we have valid data
                                total_days_30 += 1
                                
                                pred = (v1 + v2) % 10
                                if check_cham(gdb, [pred]): total_wins_30 += 1
                            
                            # Calc Prediction
                            curr_vals = data_matrix[-1]
                            v1, v2 = curr_vals[i], curr_vals[j]
                            next_val = (v1 + v2) % 10
                            
                            p1_name = getPositionName_V17_Shadow(i).replace('[', '.').replace(']', '')
                            p2_name = getPositionName_V17_Shadow(j).replace('[', '.').replace(']', '')
                            note = f" (Cứu: {wins_10}/10)" if consecutive_streak < self.min_streak else ""
                            
                            results.append({
                                "name": f"DE_POS_{p1_name}_{p2_name}",
                                "type": "DE_POS_SUM",
                                "streak": total_wins_30,
                                "predicted_value": str(next_val),
                                "full_dan": "",
                                "win_rate": (total_wins_30 / total_days_30 * 100) if total_days_30 > 0 else 0,
                                "display_desc": f"Tổng vị trí: {p1_name} + {p2_name}{note}",
                                "pos1_idx": i,
                                "pos2_idx": j
                            })
        except Exception as e:
            print(f">>> [ERROR] Lỗi quét cầu số học: {e}")
        return results

    def _scan_set_bridges(self, all_data_ai: List[List[str]], data_matrix: List[List[Optional[int]]]) -> List[Dict[str, Any]]:
        results = []
        try:
            limit_pos = 117
            scan_len = len(all_data_ai)
            
            for i in range(limit_pos):
                for j in range(i + 1, limit_pos):
                    consecutive_streak = 0
                    wins_10 = 0
                    for k in range(scan_len - 1, 0, -1):
                        if scan_len - k > self.scan_depth: break
                        
                        gdb = get_gdb_last_2(all_data_ai[k])
                        row_prev_vals = data_matrix[k-1]
                        v1, v2 = row_prev_vals[i], row_prev_vals[j]
                        
                        if not gdb or v1 is None or v2 is None: break
                        
                        set_name = get_set_name_of_number(f"{v1}{v2}")
                        if not set_name: break
                        
                        set_nums = BO_SO_DE.get(set_name, [])
                        if not set_nums: break
                        
                        is_win = gdb in set_nums
                        days_ago = scan_len - 1 - k
                        
                        if is_win:
                            if consecutive_streak == days_ago: consecutive_streak += 1
                            if days_ago < self.history_check_len: wins_10 += 1
                        else:
                            if consecutive_streak > 0: break
                            
                    if consecutive_streak >= self.min_streak_bo and wins_10 >= self.min_wins_bo_10:
                        if self._validate_bridge(all_data_ai, data_matrix, i, j, 0, "SET"):
                            # [FIX] Tính tổng số kỳ thắng trên 30 ngày để khớp với Popup
                            total_wins_30 = 0
                            total_days_30 = 0
                            for k in range(scan_len - 1, max(0, scan_len - 1 - self.scan_depth), -1):
                                if k < 1: break
                                
                                gdb = get_gdb_last_2(all_data_ai[k])
                                if not gdb: continue
                                
                                row_prev_vals = data_matrix[k-1]
                                v1, v2 = row_prev_vals[i], row_prev_vals[j]
                                if v1 is None or v2 is None: continue
                                
                                set_name = get_set_name_of_number(f"{v1}{v2}")
                                if not set_name: continue
                                
                                set_nums = BO_SO_DE.get(set_name, [])
                                if not set_nums: continue
                                
                                # Only count this day if we have valid data
                                total_days_30 += 1
                                
                                if gdb in set_nums: total_wins_30 += 1
                            
                            curr_vals = data_matrix[-1]
                            v1_curr, v2_curr = curr_vals[i], curr_vals[j]
                            pred_set_name = get_set_name_of_number(f"{v1_curr}{v2_curr}")
                            
                            if pred_set_name:
                                p1_n = getPositionName_V17_Shadow(i).replace('[', '.').replace(']', '')
                                p2_n = getPositionName_V17_Shadow(j).replace('[', '.').replace(']', '')
                                results.append({
                                    "name": f"DE_SET_{p1_n}_{p2_n}",
                                    "type": "DE_SET",
                                    "streak": total_wins_30,
                                    "predicted_value": pred_set_name,
                                    "full_dan": ",".join(BO_SO_DE.get(pred_set_name, [])),
                                    "win_rate": (total_wins_30 / total_days_30 * 100) if total_days_30 > 0 else 0,
                                    "display_desc": f"Bộ: {p1_n} + {p2_n} (Bộ {pred_set_name})",
                                    "pos1_idx": i,
                                    "pos2_idx": j
                                })
        except Exception as e:
            print(f">>> [ERROR] Lỗi quét cầu bộ: {e}")
        return results

    def _get_standard_prize_name(self, idx: int, total_cols: int) -> str:
        if total_cols <= 11:
            mapping = {2: "GDB", 3: "G1", 4: "G2", 5: "G3", 6: "G4", 7: "G5", 8: "G6", 9: "G7"}
            return mapping.get(idx, f"C{idx}")
        # Map cho list 107 vị trí
        return getPositionName_V17_Shadow(idx).replace('[', '.').replace(']', '')

    # REMOVED: _save_to_db method - Scanner is now read-only (V11.2 K1N-Primary Refactor)
    # DB writes are handled by BridgeImporter after policy-based filtering

def run_de_scanner(data, db_name=DB_NAME):
    """
    V11.2 K1N-Primary: Returns (candidates, meta) instead of (count, bridges).
    
    Args:
        data: Historical lottery data
        db_name: Database path (for reading existing bridges only)
        
    Returns:
        Tuple of (candidates: List[Candidate], meta: Dict)
    """
    return DeBridgeScanner().scan_all(data, db_name)