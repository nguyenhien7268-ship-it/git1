# Tên file: code6/logic/bridges/de_bridge_scanner.py
# (PHIÊN BẢN V3.3 FIX - ĐÃ BỔ SUNG HÀM _validate_bridge)

import sqlite3
from collections import Counter
from typing import List, Dict, Any, Optional, Tuple, Set

# Fallback imports
try:
    from logic.db_manager import DB_NAME
    from logic.bridges.bridges_v16 import getAllPositions_V17_Shadow, getPositionName_V17_Shadow
    from logic.de_utils import (
        get_gdb_last_2, check_cham, get_touches_by_offset, 
        generate_dan_de_from_touches, get_set_name_of_number, BO_SO_DE
    )
except ImportError:
    DB_NAME = "lottery.db"
    pass 

class DeBridgeScanner:
    """
    Bộ quét cầu Đề tự động (Automated DE Bridge Scanner)
    Phiên bản: V3.3 (Final Fixed - Full Stack Strategies)
    """

    def __init__(self):
        # [CONFIGURATION]
        self.min_streak = 3        # Cầu Lô/Vị trí
        self.min_streak_bo = 2     # Cầu Bộ
        self.scan_depth = 30       # Số kỳ quét (Short-term)
        self.memory_depth = 90     # Số kỳ quét Bạc Nhớ (Long-term)
        
        self.history_check_len = 10 
        self.min_wins_required = 4  
        self.validation_len = 15   
        self.min_val_wins = 2      
        
        # Cấu hình Killer & Memory
        self.min_killer_streak = 12 
        self.min_memory_confidence = 60.0 # % Xuất hiện tối thiểu để báo Bạc Nhớ

        # Cứu Cầu
        self.rescue_wins_10 = 7    
        self.min_wins_bo_10 = 2    

    def scan_all(self, all_data_ai: List[List[str]]) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Hàm điều phối chính (Orchestrator).
        """
        if not self._validate_input_data(all_data_ai):
            return 0, []

        last_row_idx = len(all_data_ai[-1])
        print(f">>> [DE SCANNER V3.3] Bắt đầu quét trên {last_row_idx} cột dữ liệu...")
        
        found_bridges: List[Dict[str, Any]] = []

        # 1. CHIẾN THUẬT TOÁN HỌC (MATH BRIDGES)
        found_bridges.extend(self._scan_dynamic_offset(all_data_ai))
        found_bridges.extend(self._scan_algorithm_sum(all_data_ai))
        found_bridges.extend(self._scan_set_bridges(all_data_ai))
        found_bridges.extend(self._scan_pascal_topology(all_data_ai))

        # 2. CHIẾN THUẬT KHAI PHÁ DỮ LIỆU (DATA MINING)
        # Bạc nhớ (Memory) - V3.3
        bridges_memory = self._scan_memory_pattern(all_data_ai)
        print(f">>> [DE SCANNER] Bạc Nhớ tìm thấy: {len(bridges_memory)}")
        found_bridges.extend(bridges_memory)

        # 3. CHIẾN THUẬT LOẠI TRỪ (KILLER)
        bridges_killer = self._scan_killer_bridges(all_data_ai)
        print(f">>> [DE SCANNER] Cầu Loại tìm thấy: {len(bridges_killer)}")
        found_bridges.extend(bridges_killer)

        # 4. TỔNG HỢP & LƯU TRỮ
        self._rank_bridges(found_bridges)
        self._save_to_db(found_bridges)
        
        print(f">>> [DE SCANNER] Tổng cộng: {len(found_bridges)} cầu.")
        return len(found_bridges), found_bridges

    # --- CORE HELPERS ---

    def _validate_input_data(self, data: List[List[str]]) -> bool:
        required_len = self.scan_depth + self.validation_len
        if not data or len(data) < required_len:
            if data and len(data) >= self.scan_depth:
                self.validation_len = 0 
                return True
            return False
        return True

    def _extract_digit(self, value: Any) -> Optional[int]:
        try:
            s = str(value)
            digits = ''.join(filter(str.isdigit, s))
            return int(digits[-1]) if digits else None
        except Exception:
            return None

    def _clean_str(self, raw_val) -> str:
        if not raw_val: return ""
        return ''.join(filter(str.isdigit, str(raw_val)))

    def _calculate_ranking_score(self, streak: int, wins_10: int, bridge_type: str) -> float:
        """Hệ thống điểm số (Ranking System)."""
        type_bonus = 0.0
        if bridge_type == 'DE_SET': type_bonus = 2.0
        elif bridge_type == 'DE_PASCAL': type_bonus = 1.0
        elif bridge_type == 'DE_MEMORY': return 15.0 + (wins_10 / 2) # Bạc nhớ luôn ưu tiên cao nếu tìm thấy
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

    def _validate_bridge(self, all_data_ai, idx1, idx2, k_param, mode) -> bool:
        """
        Kiểm tra độ ổn định của cầu trong quá khứ xa hơn (Validation Phase).
        """
        if self.validation_len <= 0: return True
        start_idx = len(all_data_ai) - self.scan_depth - self.validation_len
        end_idx = len(all_data_ai) - self.scan_depth
        if start_idx < 1: return True

        val_wins = 0
        scan_slice = all_data_ai[start_idx:end_idx]
        for i, row_curr in enumerate(scan_slice):
            real_idx = start_idx + i
            row_prev = all_data_ai[real_idx - 1]
            gdb = get_gdb_last_2(row_curr)
            if not gdb: continue
            try:
                is_win = False
                if mode == "DYNAMIC":
                    d1, d2 = self._extract_digit(row_prev[idx1]), self._extract_digit(row_prev[idx2])
                    if d1 is None or d2 is None: continue
                    touches = get_touches_by_offset((d1 + d2) % 10, k_param)
                    is_win = check_cham(gdb, touches)
                elif mode == "DE_POS_SUM":
                    p_prev = getAllPositions_V17_Shadow(row_prev)
                    if p_prev[idx1] is None or p_prev[idx2] is None: continue
                    pred = (int(p_prev[idx1]) + int(p_prev[idx2])) % 10
                    is_win = check_cham(gdb, [pred])
                elif mode == "SET":
                    p_prev = getAllPositions_V17_Shadow(row_prev)
                    if p_prev[idx1] is None or p_prev[idx2] is None: continue
                    s_name = get_set_name_of_number(f"{p_prev[idx1]}{p_prev[idx2]}")
                    if s_name:
                        is_win = gdb in BO_SO_DE.get(s_name, [])
                if is_win: val_wins += 1
            except Exception: continue
        return val_wins >= self.min_val_wins

    # =========================================================================
    # MODULE 1: BẠC NHỚ (MEMORY PATTERN) - V3.3 NEW
    # =========================================================================
    
    def _scan_memory_pattern(self, all_data_ai: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Quét các mẫu hình Bạc Nhớ (Pattern Recognition).
        Ví dụ: Khi G1 có đuôi 5, Đề hôm sau thường về chạm mấy?
        """
        results = []
        # Cần dữ liệu dài hơn để mining
        mining_depth = min(len(all_data_ai) - 1, self.memory_depth)
        mining_data = all_data_ai[-mining_depth:]
        
        # Các vị trí "Tín hiệu" (Trigger) quan trọng
        triggers = [
            (2, "GDB_Tail", "Đuôi ĐB"), 
            (2, "GDB_Head", "Đầu ĐB"),
            (3, "G1_Tail", "Đuôi G1"),
        ]

        last_row = all_data_ai[-1]

        for col_idx, trigger_code, trigger_name in triggers:
            # 1. Lấy giá trị tín hiệu của ngày hôm nay
            current_signal = self._get_signal_value(last_row, col_idx, trigger_code)
            if current_signal is None: continue

            # 2. Quét quá khứ
            matching_next_days_gdb = []
            
            for k in range(len(mining_data) - 2):
                row_k = mining_data[k]
                hist_signal = self._get_signal_value(row_k, col_idx, trigger_code)
                
                if hist_signal == current_signal:
                    row_next = mining_data[k+1]
                    gdb_next = get_gdb_last_2(row_next)
                    if gdb_next:
                        matching_next_days_gdb.append(gdb_next)

            # 3. Thống kê kết quả
            if len(matching_next_days_gdb) < 5: continue

            touch_counts = Counter()
            for gdb in matching_next_days_gdb:
                if len(gdb) == 2:
                    touch_counts[int(gdb[0])] += 1
                    touch_counts[int(gdb[1])] += 1
            
            total_matches = len(matching_next_days_gdb)
            best_touch, count = touch_counts.most_common(1)[0]
            confidence = (count / total_matches) * 100

            # 4. Lưu nếu độ tin cậy cao
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
    # MODULE 2: CẦU LOẠI (KILLER) - V3.2
    # =========================================================================

    def _scan_killer_bridges(self, all_data_ai: List[List[str]]) -> List[Dict[str, Any]]:
        results = []
        try:
            sample_pos = getAllPositions_V17_Shadow(all_data_ai[-1])
            limit_pos = min(len(sample_pos), 40)
            scan_data = all_data_ai[-self.scan_depth:]
            
            for i in range(limit_pos):
                for j in range(i, limit_pos):
                    killer_streak = 0
                    for k in range(len(scan_data) - 1, 0, -1):
                        row_curr = scan_data[k]
                        row_prev = scan_data[k-1]
                        gdb = get_gdb_last_2(row_curr)
                        pos_prev = getAllPositions_V17_Shadow(row_prev)
                        if not gdb or pos_prev[i] is None or pos_prev[j] is None: break
                        try:
                            val_i, val_j = int(pos_prev[i]), int(pos_prev[j])
                            pred_touch = (val_i + val_j) % 10
                            has_touch = check_cham(gdb, [pred_touch])
                            if not has_touch: killer_streak += 1
                            else: break
                        except ValueError: break

                    if killer_streak >= self.min_killer_streak:
                        p_curr = getAllPositions_V17_Shadow(all_data_ai[-1])
                        v1, v2 = int(p_curr[i]), int(p_curr[j])
                        next_killer_touch = (v1 + v2) % 10
                        p1_n = getPositionName_V17_Shadow(i).strip('[]')
                        p2_n = getPositionName_V17_Shadow(j).strip('[]')
                        
                        results.append({
                            "name": f"DE_KILLER_{p1_n}_{p2_n}",
                            "type": "DE_KILLER",
                            "streak": killer_streak,
                            "predicted_value": f"LOẠI CHẠM {next_killer_touch}",
                            "full_dan": "",
                            "win_rate": 0,
                            "display_desc": f"LOẠI Chạm {next_killer_touch} (Thông {killer_streak} kỳ). Từ: {p1_n}+{p2_n}"
                        })
        except Exception as e:
            print(f">>> [ERROR] Lỗi quét Cầu Loại: {e}")
        
        results.sort(key=lambda x: x['streak'], reverse=True)
        return results[:15]

    # =========================================================================
    # MODULE 3: CẦU PASCAL (TOPOLOGY) - V3.1
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
            streak = 0
            wins_10 = 0
            for k in range(len(scan_data) - 1, 0, -1):
                row_curr = scan_data[k]
                row_prev = scan_data[k-1]
                gdb = get_gdb_last_2(row_curr)
                if not gdb: break
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
                    if streak == days_ago: streak += 1
                    if days_ago < self.history_check_len: wins_10 += 1
                else:
                    if streak > 0: break 
            
            if streak >= self.min_streak or wins_10 >= self.rescue_wins_10:
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
                        "streak": streak,
                        "predicted_value": display_val,
                        "full_dan": display_val,
                        "win_rate": (wins_10 / 10) * 100,
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
    # MODULE 4: DYNAMIC & SUM (CLASSIC)
    # =========================================================================

    def _scan_dynamic_offset(self, all_data_ai: List[List[str]]) -> List[Dict[str, Any]]:
        results = []
        scan_data = all_data_ai[-self.scan_depth:]
        last_row = all_data_ai[-1]
        num_cols = len(last_row)
        pairs = []
        for i in range(2, num_cols):
            for j in range(i + 1, num_cols):
                pairs.append((i, j))
        for idx1, idx2 in pairs:
            name1 = self._get_standard_prize_name(idx1, num_cols)
            name2 = self._get_standard_prize_name(idx2, num_cols)
            val1_last = self._extract_digit(last_row[idx1])
            val2_last = self._extract_digit(last_row[idx2])
            if val1_last is None or val2_last is None: continue
            for k in range(10): 
                total_wins = 0
                check_window = 0
                history_range = range(len(scan_data) - 1, len(scan_data) - 1 - self.history_check_len, -1)
                valid_history = True
                for day_idx in history_range:
                    if day_idx < 1: break
                    check_window += 1
                    row_curr = scan_data[day_idx]
                    row_prev = scan_data[day_idx-1]
                    gdb_today = get_gdb_last_2(row_curr)
                    if not gdb_today: continue
                    d1 = self._extract_digit(row_prev[idx1])
                    d2 = self._extract_digit(row_prev[idx2])
                    if d1 is None or d2 is None: 
                        valid_history = False; break
                    base_sum = (d1 + d2) % 10
                    touches = get_touches_by_offset(base_sum, k)
                    if check_cham(gdb_today, touches): total_wins += 1
                if not valid_history: continue
                if total_wins >= self.min_wins_required:
                    if self._validate_bridge(all_data_ai, idx1, idx2, k, "DYNAMIC"):
                        base_last = (val1_last + val2_last) % 10
                        final_touches = get_touches_by_offset(base_last, k)
                        final_dan = generate_dan_de_from_touches(final_touches)
                        results.append({
                            "name": f"DE_DYN_{name1}_{name2}_K{k}",
                            "type": "DE_DYNAMIC_K",
                            "streak": total_wins,
                            "predicted_value": ",".join(map(str, final_touches)),
                            "full_dan": ",".join(final_dan),
                            "win_rate": (total_wins / check_window * 100) if check_window > 0 else 0,
                            "display_desc": f"Đuôi {name1} + Đuôi {name2} (K={k})"
                        })
        return results

    def _scan_algorithm_sum(self, all_data_ai: List[List[str]]) -> List[Dict[str, Any]]:
        results = []
        try:
            sample_pos = getAllPositions_V17_Shadow(all_data_ai[-1])
            limit_pos = min(len(sample_pos), 50)
            scan_data = all_data_ai[-self.scan_depth:]
            for i in range(limit_pos):
                for j in range(i, limit_pos):
                    streak = 0
                    wins_10 = 0
                    for k in range(len(scan_data) - 1, 0, -1):
                        row_curr = scan_data[k]
                        row_prev = scan_data[k-1]
                        gdb = get_gdb_last_2(row_curr)
                        pos_prev = getAllPositions_V17_Shadow(row_prev)
                        if not gdb or pos_prev[i] is None or pos_prev[j] is None: break
                        try:
                            val_i, val_j = int(pos_prev[i]), int(pos_prev[j])
                            pred = (val_i + val_j) % 10
                            is_win = check_cham(gdb, [pred])
                            days_ago = len(scan_data) - 1 - k
                            if is_win:
                                if streak == days_ago: streak += 1 
                                if days_ago < self.history_check_len: wins_10 += 1
                            else:
                                if streak > 0: break 
                        except ValueError: break
                    if streak >= self.min_streak or wins_10 >= self.rescue_wins_10:
                        if self._validate_bridge(all_data_ai, i, j, 0, "DE_POS_SUM"):
                            p_curr = getAllPositions_V17_Shadow(all_data_ai[-1])
                            v1, v2 = int(p_curr[i]), int(p_curr[j])
                            next_val = (v1 + v2) % 10
                            p1_name = getPositionName_V17_Shadow(i).strip('[]')
                            p2_name = getPositionName_V17_Shadow(j).strip('[]')
                            note = f" (Cứu: {wins_10}/10)" if streak < self.min_streak else ""
                            results.append({
                                "name": f"DE_POS_{p1_name}_{p2_name}",
                                "type": "DE_POS_SUM",
                                "streak": streak,
                                "predicted_value": str(next_val),
                                "full_dan": "",
                                "win_rate": (wins_10 / 10) * 100,
                                "display_desc": f"Tổng vị trí: {p1_name} + {p2_name}{note}"
                            })
        except Exception as e:
            print(f">>> [ERROR] Lỗi quét cầu số học: {e}")
        return results

    def _scan_set_bridges(self, all_data_ai: List[List[str]]) -> List[Dict[str, Any]]:
        results = []
        try:
            sample_pos = getAllPositions_V17_Shadow(all_data_ai[-1])
            limit_pos = min(len(sample_pos), 50)
            scan_data = all_data_ai[-self.scan_depth:]
            for i in range(limit_pos):
                for j in range(i + 1, limit_pos):
                    streak = 0
                    wins_10 = 0
                    for k in range(len(scan_data) - 1, 0, -1):
                        row_curr = scan_data[k]
                        row_prev = scan_data[k-1]
                        gdb = get_gdb_last_2(row_curr)
                        pos_prev = getAllPositions_V17_Shadow(row_prev)
                        if not gdb or pos_prev[i] is None or pos_prev[j] is None: break
                        try:
                            v1, v2 = int(pos_prev[i]), int(pos_prev[j])
                            set_name = get_set_name_of_number(f"{v1}{v2}")
                            if not set_name: break
                            set_nums = set(BO_SO_DE.get(set_name, []))
                            if not set_nums: break
                            is_win = gdb in set_nums
                            days_ago = len(scan_data) - 1 - k
                            if is_win:
                                if streak == days_ago: streak += 1
                                if days_ago < self.history_check_len: wins_10 += 1
                            else:
                                if streak > 0: break
                        except ValueError: break
                    if streak >= self.min_streak_bo and wins_10 >= self.min_wins_bo_10:
                        if self._validate_bridge(all_data_ai, i, j, 0, "SET"):
                            p_curr = getAllPositions_V17_Shadow(all_data_ai[-1])
                            v1_curr, v2_curr = int(p_curr[i]), int(p_curr[j])
                            pred_set_name = get_set_name_of_number(f"{v1_curr}{v2_curr}")
                            if pred_set_name:
                                p1_n = getPositionName_V17_Shadow(i).strip('[]')
                                p2_n = getPositionName_V17_Shadow(j).strip('[]')
                                results.append({
                                    "name": f"DE_SET_{p1_n}_{p2_n}",
                                    "type": "DE_SET",
                                    "streak": streak,
                                    "predicted_value": pred_set_name,
                                    "full_dan": ",".join(BO_SO_DE.get(pred_set_name, [])),
                                    "win_rate": (wins_10 / 10) * 100,
                                    "display_desc": f"Bộ: {p1_n} + {p2_n} (Bộ {pred_set_name})"
                                })
        except Exception as e:
            print(f">>> [ERROR] Lỗi quét cầu bộ: {e}")
        return results

    def _get_standard_prize_name(self, idx: int, total_cols: int) -> str:
        if total_cols <= 11:
            mapping = {2: "GDB", 3: "G1", 4: "G2", 5: "G3", 6: "G4", 7: "G5", 8: "G6", 9: "G7"}
            return mapping.get(idx, f"C{idx}")
        if idx == 2: return "GDB"
        if idx == 3: return "G1"
        if 4 <= idx <= 5: return f"G2.{idx-3}"
        if 6 <= idx <= 11: return f"G3.{idx-5}"
        if 12 <= idx <= 15: return f"G4.{idx-11}"
        if 16 <= idx <= 21: return f"G5.{idx-15}"
        if 22 <= idx <= 24: return f"G6.{idx-21}"
        if 25 <= idx <= 28: return f"G7.{idx-24}"
        return f"Pos{idx}"

    def _save_to_db(self, bridges: List[Dict[str, Any]]):
        if not bridges: return
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ManagedBridges WHERE type IN ('DE_DYNAMIC_K', 'DE_POS_SUM', 'DE_SET', 'DE_PASCAL', 'DE_KILLER', 'DE_MEMORY')")
            
            count = 0
            # [CONFIG] Lưu tối đa 50 cầu TỐT NHẤT (Đã tăng để chứa thêm Bạc Nhớ)
            for b in bridges[:150]: 
                desc = b.get('display_desc', '')
                full_dan = b.get('full_dan', '')
                final_desc = f"{desc}. Dàn: {full_dan}" if full_dan else desc
                final_desc += f". Thông {b['streak']} kỳ."
                
                cursor.execute("""
                    INSERT INTO ManagedBridges 
                    (name, type, description, win_rate_text, current_streak, next_prediction_stl, is_enabled) 
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (b['name'], b['type'], final_desc, f"{b['win_rate']:.0f}%", b['streak'], b['predicted_value']))
                count += 1
            conn.commit(); conn.close()
            print(f">>> [DB] Đã lưu thành công {count} cầu vào bảng ManagedBridges.")
        except Exception as e: print(f"Lỗi lưu DB: {e}")

def run_de_scanner(data):
    return DeBridgeScanner().scan_all(data)