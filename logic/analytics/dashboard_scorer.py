# Tên file: logic/analytics/dashboard_scorer.py
# (MOVED FROM logic/dashboard_analytics.py - Phase 1 & 2 Refactoring)
from collections import Counter
import itertools

# Import SETTINGS
try:
    from ..config_manager import SETTINGS
except ImportError:
    try:
        from logic.config_manager import SETTINGS
    except ImportError:
        print("LỖI: dashboard_scorer.py không thể import SETTINGS. Sử dụng fallback.")
        SETTINGS = type("obj", (object,), {
            "STATS_DAYS": 7, "GAN_DAYS": 15, "HIGH_WIN_THRESHOLD": 47.0,
            "K2N_RISK_START_THRESHOLD": 6, "K2N_RISK_PENALTY_PER_FRAME": 1.0,
            "AI_PROB_THRESHOLD": 45.0, "AI_SCORE_WEIGHT": 0.2,
            "RECENT_FORM_MIN_LOW": 5, "RECENT_FORM_MIN_MED": 7, "RECENT_FORM_MIN_HIGH": 9,
            "RECENT_FORM_BONUS_LOW": 0.5, "RECENT_FORM_BONUS_MED": 1.0, "RECENT_FORM_BONUS_HIGH": 1.5,
        })

# Import Bridge/DB Logic và Helpers
try:
    from ..backtester import BACKTEST_15_CAU_K2N_V30_AI_V8, BACKTEST_MANAGED_BRIDGES_K2N
    from ..backtester_core import parse_k2n_results as _parse_k2n_results
    from ..bridges.bridges_classic import ALL_15_BRIDGE_FUNCTIONS_V5, checkHitSet_V30_K2N, getAllLoto_V30
    from ..bridges.bridges_memory import calculate_bridge_stl, get_27_loto_names, get_27_loto_positions
    from ..bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    from ..data_repository import get_all_managed_bridges
    from ..db_manager import DB_NAME
    from ..backtester_scoring import LoScorer
except ImportError:
    print("Lỗi: Không thể import bridge/backtester helpers trong dashboard_scorer.py")
    def getAllLoto_V30(r): return []
    def checkHitSet_V30_K2N(p, loto_set): return "Lỗi"
    def getAllPositions_V17_Shadow(r): return []
    def taoSTL_V30_Bong(a, b): return ["00", "00"]
    def get_27_loto_names(): return []
    def get_27_loto_positions(r): return []
    def calculate_bridge_stl(l1, l2, type): return ["00", "00"]
    def _parse_k2n_results(r): return [], {}
    def BACKTEST_MANAGED_BRIDGES_K2N(a, b, c, d, e): return []
    def BACKTEST_15_CAU_K2N_V30_AI_V8(a, b, c, d): return []
    DB_NAME = "xo_so_prizes_all_logic.db"
    def get_all_managed_bridges(d, o): return []

# [PHẦN 1-4: Giữ nguyên toàn bộ code từ dashboard_analytics.py]
# I. HÀM ANALYTICS CƠ BẢN
def get_loto_stats_last_n_days(all_data_ai, n=None):
    """Lấy thống kê tần suất loto (hot/lạnh)."""
    try:
        if n is None:
            n = getattr(SETTINGS, "STATS_DAYS", 7)
        if not all_data_ai or len(all_data_ai) == 0:
            return []
        if len(all_data_ai) < n:
            n = len(all_data_ai)
        last_n_rows = all_data_ai[-n:]
        all_lotos_hits = []
        day_appearance_counter = Counter()
        for row in last_n_rows:
            lotos_in_this_row = getAllLoto_V30(row)
            all_lotos_hits.extend(lotos_in_this_row)
            unique_lotos_in_this_row = set(lotos_in_this_row)
            day_appearance_counter.update(unique_lotos_in_this_row)
        loto_hit_counts = Counter(all_lotos_hits)
        sorted_lotos_by_hits = sorted(loto_hit_counts.items(), key=lambda item: item[1], reverse=True)
        final_stats = []
        for loto, hit_count in sorted_lotos_by_hits:
            day_count = day_appearance_counter.get(loto, 0)
            final_stats.append((loto, hit_count, day_count))
        return final_stats
    except Exception as e:
        print(f"Lỗi get_loto_stats_last_n_days: {e}")
        return []

def get_loto_gan_stats(all_data_ai, n_days=None):
    """Tìm các loto (00-99) đã không xuất hiện trong n_days gần nhất (Lô Gan)."""
    gan_stats = []
    try:
        if n_days is None:
            n_days = getattr(SETTINGS, "GAN_DAYS", 15)
        if not all_data_ai or len(all_data_ai) < n_days:
            return []
        all_100_lotos = {str(i).zfill(2) for i in range(100)}
        recent_lotos = set()
        recent_rows = all_data_ai[-n_days:]
        for row in recent_rows:
            lotos_in_this_row = getAllLoto_V30(row)
            recent_lotos.update(lotos_in_this_row)
        gan_lotos = all_100_lotos - recent_lotos
        if not gan_lotos:
            return []
        full_history = all_data_ai[:]
        full_history.reverse()
        for loto in gan_lotos:
            days_gan = 0
            found = False
            for i, row in enumerate(full_history):
                if i < n_days:
                    days_gan += 1
                    continue
                loto_set_this_day = set(getAllLoto_V30(row))
                if loto in loto_set_this_day:
                    found = True
                    break
                else:
                    days_gan += 1
            if found:
                gan_stats.append((loto, days_gan))
            else:
                gan_stats.append((loto, len(full_history)))
        gan_stats.sort(key=lambda x: x[1], reverse=True)
        return gan_stats
    except Exception as e:
        print(f"Lỗi get_loto_gan_stats: {e}")
        return []

def get_top_memory_bridge_predictions(all_data_ai, last_row, top_n=5):
    """Chạy backtest N1 756 cầu bạc nhớ ngầm và trả về dự đoán của TOP N cầu tốt nhất."""
    print("... (BTH) Bắt đầu chạy backtest 756 cầu Bạc Nhớ ngầm...")
    def _validate_data(data):
        return not data or len(data) < 2
    if _validate_data(all_data_ai):
        return []
    loto_names = get_27_loto_names()
    num_positions = len(loto_names)
    algorithms = []
    for i in range(num_positions):
        for j in range(i, num_positions):
            algorithms.append((i, j, "sum"))
            algorithms.append((i, j, "diff"))
    num_algorithms = len(algorithms)
    processedData = []
    startCheckRow = 2
    offset = 1
    finalEndRow = len(all_data_ai)
    for k in range(startCheckRow, finalEndRow + 1):
        prevRow_idx, actualRow_idx = k - 1 - offset, k - offset
        if actualRow_idx >= len(all_data_ai) or prevRow_idx < 0:
            continue
        prevRow, actualRow = all_data_ai[prevRow_idx], all_data_ai[actualRow_idx]
        if (not prevRow or not actualRow or not actualRow[0] or str(actualRow[0]).strip() == "" or len(actualRow) < 10 or not actualRow[9]):
            continue
        processedData.append({"prevLotos": get_27_loto_positions(prevRow), "actualLotoSet": set(getAllLoto_V30(actualRow))})
    totalTestDays = len(processedData)
    if totalTestDays == 0:
        return []
    win_counts = [0] * num_algorithms
    for dayData in processedData:
        actualLotoSet = dayData["actualLotoSet"]
        prevLotos = dayData["prevLotos"]
        for j in range(num_algorithms):
            alg = algorithms[j]
            idx1, idx2, alg_type = alg[0], alg[1], alg[2]
            loto1, loto2 = prevLotos[idx1], prevLotos[idx2]
            pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
            if pred_stl[0] in actualLotoSet or pred_stl[1] in actualLotoSet:
                win_counts[j] += 1
    bridge_stats = []
    for j in range(num_algorithms):
        rate = (win_counts[j] / totalTestDays) * 100
        bridge_stats.append((rate, j))
    bridge_stats.sort(key=lambda x: x[0], reverse=True)
    top_n_bridges = bridge_stats[:top_n]
    predictions_for_dashboard = []
    last_lotos = get_27_loto_positions(last_row)
    for rate, alg_index in top_n_bridges:
        alg = algorithms[alg_index]
        idx1, idx2, alg_type = alg[0], alg[1], alg[2]
        loto1, loto2 = last_lotos[idx1], last_lotos[idx2]
        pred_stl = calculate_bridge_stl(loto1, loto2, alg_type)
        if alg_type == "sum":
            name = f"Tổng({loto_names[idx1]}+{loto_names[idx2]})"
        else:
            name = f"Hiệu(|{loto_names[idx1]}-{loto_names[idx2]}|)"
        predictions_for_dashboard.append({"name": name, "stl": pred_stl, "prediction": ", ".join(map(str, pred_stl)), "rate": f"{rate:.2f}%"})
    return predictions_for_dashboard

# II. HÀM ANALYTICS NÂNG CAO
def _standardize_pair(stl_list):
    """Hàm nội bộ: Chuẩn hóa 1 cặp STL. Ví dụ ['30', '03'] -> '03-30'"""
    if not stl_list or len(stl_list) != 2:
        return None
    sorted_pair = sorted(stl_list)
    return f"{sorted_pair[0]}-{sorted_pair[1]}"

def get_prediction_consensus(last_row=None, db_name=DB_NAME):
    """Lấy dự đoán từ "15 Cầu" và "Cầu Đã Lưu" để đếm vote THEO CẶP.
    Nếu có last_row, tính toán trực tiếp. Nếu không, lấy từ cache (next_prediction_stl trong DB)."""
    try:
        prediction_sources = {}
        
        def get_pair_key(stl_list):
            """Chuẩn hóa 1 cặp STL. Ví dụ ['30', '03'] -> '03-30'"""
            if not stl_list or len(stl_list) != 2:
                return None
            sorted_pair = sorted(stl_list)
            return f"{sorted_pair[0]}-{sorted_pair[1]}"
        
        # Nếu có last_row, tính toán trực tiếp (ưu tiên)
        if last_row and len(last_row) >= 10:
            try:
                # Import các hàm cần thiết (đã import ở đầu file, chỉ cần dùng)
                # getAllPositions_V16, taoSTL_V30_Bong, calculate_bridge_stl, get_27_loto_positions, ALL_15_BRIDGE_FUNCTIONS_V5 đã có
                import re
                
                # 1. Lấy từ 15 Cầu Cổ Điển
                for i, bridge_func in enumerate(ALL_15_BRIDGE_FUNCTIONS_V5):
                    try:
                        stl = bridge_func(last_row)
                        pair_key = get_pair_key(stl)
                        if pair_key:
                            source_name = f"C{i + 1}"
                            if pair_key not in prediction_sources:
                                prediction_sources[pair_key] = []
                            if source_name not in prediction_sources[pair_key]:
                                prediction_sources[pair_key].append(source_name)
                    except Exception:
                        pass
                
                # 2. Lấy từ Cầu Đã Lưu (tính toán trực tiếp)
                managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
                if managed_bridges:
                    # Dùng getAllPositions_V17_Shadow (đã import) thay vì getAllPositions_V16
                    last_positions = getAllPositions_V17_Shadow(last_row)
                    last_lotos = get_27_loto_positions(last_row)
                    
                    for bridge in managed_bridges:
                        try:
                            idx1, idx2 = bridge.get("pos1_idx"), bridge.get("pos2_idx")
                            
                            # Memory Bridge
                            if idx1 == -1 and idx2 == -1:
                                bridge_name = bridge.get("name", "")
                                stl = None
                                
                                if "Tổng(" in bridge_name:
                                    match = re.search(r'Tổng\((\d+)\+(\d+)\)', bridge_name)
                                    if match:
                                        pos1, pos2 = int(match.group(1)), int(match.group(2))
                                        if pos1 < len(last_lotos) and pos2 < len(last_lotos):
                                            loto1, loto2 = last_lotos[pos1], last_lotos[pos2]
                                            if loto1 and loto2:
                                                stl = calculate_bridge_stl(loto1, loto2, "sum")
                                elif "Hiệu(" in bridge_name:
                                    match = re.search(r'Hiệu\((\d+)-(\d+)\)', bridge_name)
                                    if match:
                                        pos1, pos2 = int(match.group(1)), int(match.group(2))
                                        if pos1 < len(last_lotos) and pos2 < len(last_lotos):
                                            loto1, loto2 = last_lotos[pos1], last_lotos[pos2]
                                            if loto1 and loto2:
                                                stl = calculate_bridge_stl(loto1, loto2, "diff")
                                
                                if stl:
                                    pair_key = get_pair_key(stl)
                                    if pair_key:
                                        source_name = bridge["name"]
                                        if pair_key not in prediction_sources:
                                            prediction_sources[pair_key] = []
                                        if source_name not in prediction_sources[pair_key]:
                                            prediction_sources[pair_key].append(source_name)
                                continue
                            
                            # V17 Bridge
                            if idx1 is not None and idx2 is not None and idx1 >= 0 and idx2 >= 0:
                                if idx1 < len(last_positions) and idx2 < len(last_positions):
                                    a, b = last_positions[idx1], last_positions[idx2]
                                    if a is not None and b is not None:
                                        stl = taoSTL_V30_Bong(a, b)
                                        pair_key = get_pair_key(stl)
                                        if pair_key:
                                            source_name = bridge["name"]
                                            if pair_key not in prediction_sources:
                                                prediction_sources[pair_key] = []
                                            if source_name not in prediction_sources[pair_key]:
                                                prediction_sources[pair_key].append(source_name)
                        except Exception:
                            pass
            except Exception as e:
                print(f"Lỗi tính toán consensus từ last_row: {e}")
                # Fallback: dùng cache
                last_row = None
        
        # Nếu không có last_row hoặc tính toán thất bại, lấy từ cache
        if not last_row or len(prediction_sources) == 0:
            managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
            if managed_bridges:
                for bridge in managed_bridges:
                    try:
                        prediction_stl_str = bridge.get("next_prediction_stl")
                        if (not prediction_stl_str or "N2" in prediction_stl_str or "LỖI" in prediction_stl_str or "," not in prediction_stl_str):
                            continue
                        stl = prediction_stl_str.split(",")
                        pair_key = get_pair_key(stl)
                        if not pair_key:
                            continue
                        source_name = bridge["name"]
                        if source_name.startswith("Cầu "):
                            source_name = f"C{source_name.split(' ')[1]}"
                        if pair_key not in prediction_sources:
                            prediction_sources[pair_key] = []
                        if source_name not in prediction_sources[pair_key]:
                            prediction_sources[pair_key].append(source_name)
                    except Exception as e:
                        print(f"Lỗi dự đoán Cầu (consensus cache) {bridge.get('name')}: {e}")
        
        consensus_list = []
        for pair_key, sources in prediction_sources.items():
            count = len(sources)
            sources_str = ", ".join(sources)
            consensus_list.append((pair_key, count, sources_str))
        consensus_list.sort(key=lambda item: item[1], reverse=True)
        return consensus_list
    except Exception as e:
        print(f"Lỗi get_prediction_consensus: {e}")
        return []

def get_high_win_rate_predictions(last_row=None, threshold=None, db_name=DB_NAME):
    """
    Lấy dự đoán từ Cầu Đã Lưu CÓ TỶ LỆ CAO (dựa trên cache K2N).
    
    - Cầu LÔ (LOTO): Lọc theo win_rate_text >= threshold
    - Cầu ĐỀ (DE): Lọc theo recent_win_count_10 >= DE_HIGH_RATE_MIN_WINS_10
    
    Returns:
        list: List of dicts với keys: {'name': str, 'value': str, 'rate': str, 'type': str}
    """
    try:
        if threshold is None:
            threshold = getattr(SETTINGS, "HIGH_WIN_THRESHOLD", 47.0)
        de_min_wins = getattr(SETTINGS, "DE_HIGH_RATE_MIN_WINS_10", 7)
        
        predictions = []
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if not managed_bridges:
            return []
        
        for bridge in managed_bridges:
            try:
                bridge_type = bridge.get("type", "").upper()
                prediction_stl_str = bridge.get("next_prediction_stl")
                
                if not prediction_stl_str or "N2" in prediction_stl_str or "LỖI" in prediction_stl_str or "," not in prediction_stl_str:
                    continue
                
                stl = prediction_stl_str.split(",")
                
                # Xử lý cầu ĐỀ (DE)
                if bridge_type in ["DE", "DE_DYNAMIC_K", "DE_POS_SUM"]:
                    recent_wins = bridge.get("recent_win_count_10", 0)
                    if isinstance(recent_wins, str):
                        try:
                            recent_wins = int(recent_wins)
                        except ValueError:
                            recent_wins = 0
                    
                    if recent_wins >= de_min_wins:
                        # Chuyển đổi STL sang Dàn Đề
                        try:
                            from logic.de_utils import generate_dan_de_from_touches
                            de_values = generate_dan_de_from_touches(stl)
                            for de_value in de_values:
                                predictions.append({
                                    "name": bridge["name"],
                                    "value": de_value,
                                    "rate": f"{recent_wins}/10",
                                    "type": "DE"
                                })
                        except Exception as e:
                            print(f"Lỗi chuyển đổi DE cho cầu {bridge['name']}: {e}")
                
                # Xử lý cầu LÔ (LOTO)
                else:
                    rate_str = str(bridge.get("win_rate_text", "0%")).replace("%", "")
                    if not rate_str or rate_str == "N/A":
                        continue
                    win_rate = float(rate_str)
                    
                    if win_rate >= threshold:
                        # Thêm từng giá trị STL như một prediction riêng
                        for stl_value in stl:
                            predictions.append({
                                "name": bridge["name"],
                                "value": stl_value.strip(),
                                "rate": f"{win_rate:.2f}%",
                                "type": "LOTO"
                            })
            except Exception as e:
                print(f"Lỗi kiểm tra tỷ lệ cầu {bridge.get('name', 'Unknown')}: {e}")
        
        return predictions
    except Exception as e:
        print(f"Lỗi get_high_win_rate_predictions: {e}")
        return []

def get_pending_k2n_bridges(last_row, prev_row):
    """Lấy các cầu đã trượt N1 ở kỳ trước và đang chờ N2 (Dùng để tính Penalty)."""
    pending_bridges = []
    try:
        if not last_row or not prev_row:
            return []
        actualLotoSet = set(getAllLoto_V30(last_row))
        if not actualLotoSet:
            return []
        for i, bridge_func in enumerate(ALL_15_BRIDGE_FUNCTIONS_V5):
            try:
                stl = bridge_func(prev_row)
                check_result = checkHitSet_V30_K2N(stl, actualLotoSet)
                if "❌" in check_result:
                    pending_bridges.append({"name": f"Cầu {i + 1}", "stl": stl})
            except Exception:
                pass
        managed_bridges = get_all_managed_bridges(DB_NAME, only_enabled=True)
        if managed_bridges:
            prev_positions = getAllPositions_V17_Shadow(prev_row)
            for bridge in managed_bridges:
                try:
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    a, b = prev_positions[idx1], prev_positions[idx2]
                    if a is None or b is None:
                        continue
                    stl = taoSTL_V30_Bong(a, b)
                    check_result = checkHitSet_V30_K2N(stl, actualLotoSet)
                    if "❌" in check_result:
                        pending_bridges.append({"name": bridge["name"], "stl": stl})
                except Exception:
                    pass
        return pending_bridges
    except Exception as e:
        print(f"Lỗi get_pending_k2n_bridges: {e}")
        return []

# III. HÀM CHẤM ĐIỂM CỐT LÕI (V7.5 - GOM NHÓM PHONG ĐỘ & RỦI RO)
def get_top_scored_pairs(stats, consensus, high_win, pending_k2n, gan_stats, top_memory_bridges, ai_predictions=None, recent_data=None):
    """(V7.5) Tính toán, chấm điểm và xếp hạng các cặp số (Using LoScorer)."""
    try:
        # Đảm bảo LoScorer khả dụng
        if 'LoScorer' not in globals() or not LoScorer:
            print("Cảnh báo: LoScorer chưa được load. Trả về rỗng.")
            return []

        # Tải managed_bridges cho logic Phong độ
        try:
            from ..db_manager import DB_NAME as db_name_param
        except ImportError:
            db_name_param = "xo_so_prizes_all_logic.db"
            
        managed_bridges = get_all_managed_bridges(db_name=db_name_param)
        
        # Khởi tạo và tính điểm
        scorer = LoScorer()
        return scorer.score_all_pairs(
            stats, consensus, high_win, pending_k2n, gan_stats, 
            top_memory_bridges, ai_predictions, recent_data, managed_bridges
        )

    except Exception as e:
        import traceback
        print(f"LỖI get_top_scored_pairs (delegated): {e}")
        print(traceback.format_exc())
        return []

# IV. HÀM MÔ PHỎNG LỊCH SỬ
def get_consensus_simulation(data_slice, last_row):
    """Bản sao của get_prediction_consensus (chạy N1 trong bộ nhớ)."""
    prediction_sources = {}
    def _standardize_pair(stl_list):
        if not stl_list or len(stl_list) != 2:
            return None
        sorted_pair = sorted(stl_list)
        return f"{sorted_pair[0]}-{sorted_pair[1]}"
    for i, bridge_func in enumerate(ALL_15_BRIDGE_FUNCTIONS_V5):
        try:
            stl = bridge_func(last_row)
            pair_key = _standardize_pair(stl)
            if not pair_key:
                continue
            source_name = f"C{i + 1}"
            if pair_key not in prediction_sources:
                prediction_sources[pair_key] = []
            prediction_sources[pair_key].append(source_name)
        except Exception:
            pass
    bridges_to_test = get_all_managed_bridges(DB_NAME, only_enabled=True)
    if bridges_to_test:
        last_positions = getAllPositions_V17_Shadow(last_row)
        for bridge in bridges_to_test:
            try:
                idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                if idx1 == -1:
                    continue
                a, b = last_positions[idx1], last_positions[idx2]
                if a is None or b is None:
                    continue
                stl = taoSTL_V30_Bong(a, b)
                pair_key = _standardize_pair(stl)
                if not pair_key:
                    continue
                source_name = bridge["name"]
                if pair_key not in prediction_sources:
                    prediction_sources[pair_key] = []
                if source_name not in prediction_sources[pair_key]:
                    prediction_sources[pair_key].append(source_name)
            except Exception:
                pass
    consensus_list = []
    for pair_key, sources in prediction_sources.items():
        count = len(sources)
        sources_str = ", ".join(sources)
        consensus_list.append((pair_key, count, sources_str))
    consensus_list.sort(key=lambda item: item[1], reverse=True)
    return consensus_list

def get_high_win_simulation(data_slice, last_row, threshold):
    """Bản sao của get_high_win_rate_predictions (chạy K2N trong bộ nhớ)."""
    high_win_bridges = []
    cache_list, _ = _parse_k2n_results(BACKTEST_MANAGED_BRIDGES_K2N(data_slice, 2, len(data_slice) + 1, DB_NAME, history=False))
    cache_list_15, _ = _parse_k2n_results(BACKTEST_15_CAU_K2N_V30_AI_V8(data_slice, 2, len(data_slice) + 1, history=False))
    cache_list.extend(cache_list_15)
    if not cache_list:
        return []
    for win_rate_text, _, next_prediction_stl, _, _, bridge_name in cache_list:
        try:
            win_rate = float(str(win_rate_text).replace("%", ""))
            if win_rate >= threshold:
                if (not next_prediction_stl or "N2" in next_prediction_stl or "LỖI" in next_prediction_stl or "," not in next_prediction_stl):
                    continue
                stl = next_prediction_stl.split(",")
                high_win_bridges.append({"name": bridge_name, "stl": stl, "rate": f"{win_rate:.2f}%"})
        except (ValueError, TypeError):
            continue
    return high_win_bridges

def prepare_daily_features(all_data_ai, day_index):
    """Tính toán tất cả dữ liệu thô (Raw Features) tốn kém cho dashboard một ngày cụ thể."""
    data_slice = all_data_ai[: day_index + 1]
    if len(data_slice) < 2:
        return None
    last_row = data_slice[-1]
    n_days_stats = getattr(SETTINGS, "STATS_DAYS", 7)
    n_days_gan = getattr(SETTINGS, "GAN_DAYS", 15)
    high_win_thresh = getattr(SETTINGS, "HIGH_WIN_THRESHOLD", 47.0)
    stats_n_day = get_loto_stats_last_n_days(data_slice, n=n_days_stats)
    _, pending_k2n_data = _parse_k2n_results(BACKTEST_15_CAU_K2N_V30_AI_V8(data_slice, 2, len(data_slice) + 1, history=False))
    consensus = get_consensus_simulation(data_slice, last_row)
    high_win = get_high_win_simulation(data_slice, last_row, threshold=high_win_thresh)
    top_memory_bridges = get_top_memory_bridge_predictions(data_slice, last_row, top_n=5)
    gan_stats = get_loto_gan_stats(data_slice, n_days=n_days_gan)
    ai_predictions = None
    return {"stats_n_day": stats_n_day, "consensus": consensus, "high_win": high_win, "gan_stats": gan_stats,
            "pending_k2n": pending_k2n_data, "top_memory": top_memory_bridges, "ai_predictions": ai_predictions, "recent_data": data_slice}

def calculate_score_from_features(features_dict, config_dict):
    """Inject config_dict params into SETTINGS before calculating scores."""
    for k, v in config_dict.items():
        try:
            setattr(SETTINGS, k, v)
        except Exception:
            pass
    return get_top_scored_pairs(features_dict["stats_n_day"], features_dict["consensus"], features_dict["high_win"],
            features_dict["pending_k2n"], features_dict["gan_stats"], features_dict["top_memory"],
            features_dict.get("ai_predictions"), features_dict.get("recent_data"))

def get_historical_dashboard_data(all_data_ai, day_index, temp_settings):
    """Hàm "chủ" để mô phỏng Bảng Tổng Hợp tại một ngày trong quá khứ."""
    features = prepare_daily_features(all_data_ai, day_index)
    if not features:
        return None
    return calculate_score_from_features(features, temp_settings)

