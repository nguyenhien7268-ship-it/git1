# Tên file: git3/logic/dashboard_analytics.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - FIX LỖI UNPACK TUPLE TRONG get_high_win_simulation)
#
from collections import Counter

# Import SETTINGS
try:
    from .config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    # Chỉ định nghĩa fallback NẾU import thất bại
    except ImportError:
        print(
            "LỖI: dashboard_analytics.py không thể import SETTINGS. Sử dụng fallback."
        )
        SETTINGS = type(
            "obj",
            (object,),
            {
                "STATS_DAYS": 7,
                "GAN_DAYS": 15,
                "HIGH_WIN_THRESHOLD": 47.0,
                "K2N_RISK_START_THRESHOLD": 6,
                "K2N_RISK_PENALTY_PER_FRAME": 1.0,
                "AI_PROB_THRESHOLD": 45.0,
                "AI_SCORE_WEIGHT": 0.2,
                "RECENT_FORM_MIN_LOW": 5,
                "RECENT_FORM_MIN_MED": 7,
                "RECENT_FORM_MIN_HIGH": 9,
                "RECENT_FORM_BONUS_LOW": 0.5,
                "RECENT_FORM_BONUS_MED": 1.0,
                "RECENT_FORM_BONUS_HIGH": 1.5,
            },
        )

# Import Bridge/DB Logic và Helpers
try:
    # Import functions từ backtester.py
    from .backtester import (
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_MANAGED_BRIDGES_K2N,
    )
    # Import parse function from backtester_helpers.py
    from .backtester_helpers import parse_k2n_results as _parse_k2n_results
    from .bridges.bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5,
        checkHitSet_V30_K2N,
        getAllLoto_V30,
    )
    from .bridges.bridges_memory import (
        calculate_bridge_stl,
        get_27_loto_names,
        get_27_loto_positions,
    )
    from .bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    from .data_repository import get_all_managed_bridges
    from .db_manager import DB_NAME

except ImportError:
    print(
        "Lỗi: Không thể import bridge/backtester helpers trong dashboard_analytics.py"
    )

    def getAllLoto_V30(r):
        return []

    # Đổi 'l' thành 'loto_set'
    def checkHitSet_V30_K2N(p, loto_set):
        return "Lỗi"

    def getAllPositions_V17_Shadow(r):
        return []

    def taoSTL_V30_Bong(a, b):
        return ["00", "00"]

    def get_27_loto_names():
        return []

    def get_27_loto_positions(r):
        return []

    def calculate_bridge_stl(l1, l2, type):
        return ["00", "00"]

    def _parse_k2n_results(r):
        return [], {}

    def BACKTEST_MANAGED_BRIDGES_K2N(a, b, c, d, e):
        return []

    def BACKTEST_15_CAU_K2N_V30_AI_V8(a, b, c, d):
        return []

    DB_NAME = "xo_so_prizes_all_logic.db"

    def get_all_managed_bridges(d, o):
        return []


# ===================================================================================
# I. HÀM ANALYTICS CƠ BẢN (CHUYỂN TỪ backtester.py)
# ===================================================================================


def get_loto_stats_last_n_days(all_data_ai, n=None):
    """Lấy thống kê tần suất loto (hot/lạnh)."""
    try:
        # FIX: Sửa truy cập SETTINGS
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
        sorted_lotos_by_hits = sorted(
            loto_hit_counts.items(), key=lambda item: item[1], reverse=True
        )

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
        # FIX: Sửa truy cập SETTINGS
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
        if (
            not prevRow
            or not actualRow
            or not actualRow[0]
            or str(actualRow[0]).strip() == ""
            or len(actualRow) < 10
            or not actualRow[9]
        ):
            continue
        processedData.append(
            {
                "prevLotos": get_27_loto_positions(prevRow),
                "actualLotoSet": set(getAllLoto_V30(actualRow)),
            }
        )

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

        predictions_for_dashboard.append(
            {"name": name, "stl": pred_stl, "rate": f"{rate:.2f}%"}
        )

    return predictions_for_dashboard


# ===================================================================================
# II. HÀM ANALYTICS NÂNG CAO (CHUYỂN TỪ backtester.py)
# ===================================================================================


def _standardize_pair(stl_list):
    """Hàm nội bộ: Chuẩn hóa 1 cặp STL. Ví dụ ['30', '03'] -> '03-30'"""
    if not stl_list or len(stl_list) != 2:
        return None
    sorted_pair = sorted(stl_list)
    return f"{sorted_pair[0]}-{sorted_pair[1]}"  # Key: "03-30"


def get_prediction_consensus(last_row=None, db_name=DB_NAME):
    """Lấy dự đoán từ "15 Cầu" (cache) và "Cầu Đã Lưu" (cache) để đếm vote THEO CẶP."""
    try:
        prediction_sources = {}
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)

        if not managed_bridges:
            return []

        for bridge in managed_bridges:
            try:
                prediction_stl_str = bridge.get("next_prediction_stl")

                if (
                    not prediction_stl_str
                    or "N2" in prediction_stl_str
                    or "LỖI" in prediction_stl_str
                    or "," not in prediction_stl_str
                ):
                    continue

                stl = prediction_stl_str.split(",")
                pair_key = _standardize_pair(stl)
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
    """Lấy dự đoán từ Cầu Đã Lưu CÓ TỶ LỆ CAO (dựa trên cache K2N)."""
    try:
        # FIX: Sửa truy cập SETTINGS
        if threshold is None:
            threshold = getattr(SETTINGS, "HIGH_WIN_THRESHOLD", 47.0)

        high_win_bridges = []
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if not managed_bridges:
            return []

        for bridge in managed_bridges:
            try:
                rate_str = str(bridge.get("win_rate_text", "0%")).replace("%", "")
                if not rate_str or rate_str == "N/A":
                    continue

                win_rate = float(rate_str)

                if win_rate >= threshold:
                    prediction_stl_str = bridge.get("next_prediction_stl")

                    if (
                        not prediction_stl_str
                        or "N2" in prediction_stl_str
                        or "LỖI" in prediction_stl_str
                        or "," not in prediction_stl_str
                    ):
                        continue

                    stl = prediction_stl_str.split(",")

                    high_win_bridges.append(
                        {"name": bridge["name"], "stl": stl, "rate": f"{win_rate:.2f}%"}
                    )
            except Exception as e:
                print(f"Lỗi kiểm tra tỷ lệ cầu {bridge['name']}: {e}")

        return high_win_bridges

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

        # 1. Kiểm tra 15 Cầu Cổ Điển
        for i, bridge_func in enumerate(ALL_15_BRIDGE_FUNCTIONS_V5):
            try:
                stl = bridge_func(prev_row)
                check_result = checkHitSet_V30_K2N(stl, actualLotoSet)
                if "❌" in check_result:
                    pending_bridges.append({"name": f"Cầu {i + 1}", "stl": stl})
            except Exception:
                pass

        # 2. Kiểm tra Cầu Đã Lưu
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


# ===================================================================================
# III. HÀM CHẤM ĐIỂM CỐT LÕI (V7.5 - GOM NHÓM PHONG ĐỘ & RỦI RO)
# ===================================================================================


def get_top_scored_pairs(
    stats,
    consensus,
    high_win,
    pending_k2n,
    gan_stats,
    top_memory_bridges,
    ai_predictions=None,
    recent_data=None,
):
    """
    (V7.5) Tính toán, chấm điểm và xếp hạng các cặp số.
    Đã thêm logic GOM NHÓM cho cả K2N RISK và RECENT FORM.
    (V7.6) IMPROVED: Thêm bonus "Về Gần" để cải thiện hiệu quả.
    """
    try:
        scores = {}

        K2N_RISK_START_THRESHOLD = getattr(SETTINGS, "K2N_RISK_START_THRESHOLD", 6)
        K2N_RISK_PENALTY_FIXED = getattr(SETTINGS, "K2N_RISK_PENALTY_PER_FRAME", 1.0)
        
        ai_score_weight = getattr(SETTINGS, "AI_SCORE_WEIGHT", 0.2)

        loto_prob_map = {}
        if ai_predictions:
            for pred in ai_predictions:
                loto_prob_map[pred["loto"]] = (
                    pred["probability"] / 100.0
                )

        # Helper maps
        top_hot_lotos = {loto for loto, count, days in stats if count > 0}
        gan_map = {loto: days for loto, days in gan_stats}

        # --- 3. Chấm điểm từ 4 nguồn chính ---

        # Nguồn 2: Consensus (IMPROVED: Vote decay với sqrt)
        # IMPROVED V7.6: Giảm từ 0.5 → 0.3 để giảm dominance của vote
        vote_weight = getattr(SETTINGS, "VOTE_SCORE_WEIGHT", 0.3)
        for pair_key, count, _ in consensus:
            if pair_key not in scores:
                scores[pair_key] = {
                    "score": 0.0,
                    "reasons": [],
                    "is_gan": False,
                    "gan_days": 0,
                    "gan_loto": "",  # NEW: Which loto is gan
                    "sources": 0,  # NEW: Đếm số nguồn
                }
            # IMPROVED: Dùng sqrt để giảm dominance của vote cao
            import math
            vote_score = math.sqrt(count) * vote_weight
            scores[pair_key]["score"] += vote_score
            scores[pair_key]["reasons"].append(f"Vote x{count} (+{vote_score:.1f})")
            scores[pair_key]["sources"] += 1

        # Nguồn 3: Cầu Tỷ Lệ Cao (IMPROVED: Tăng từ 2.0 → 2.5)
        high_win_bonus = getattr(SETTINGS, "HIGH_WIN_SCORE_BONUS", 2.5)
        for bridge in high_win:
            pair_key = _standardize_pair(bridge["stl"])
            if pair_key:
                if pair_key not in scores:
                    scores[pair_key] = {
                        "score": 0.0,
                        "reasons": [],
                        "is_gan": False,
                        "gan_days": 0,
                        "gan_loto": "",
                        "sources": 0,
                    }
                scores[pair_key]["score"] += high_win_bonus
                scores[pair_key]["reasons"].append(f"Cao ({bridge['rate']})")
                scores[pair_key]["sources"] += 1

        # Nguồn 4: Cầu K2N Đang Chờ (IMPROVED: Progressive penalty)
        K2N_RISK_PROGRESSIVE = getattr(SETTINGS, "K2N_RISK_PROGRESSIVE", True)
        k2n_risks = {}
        for bridge_name, data in pending_k2n.items():
            pair_key = _standardize_pair(data["stl"].split(","))
            max_lose = data.get("max_lose", 0)
            
            # IMPROVED: Progressive penalty
            if K2N_RISK_PROGRESSIVE:
                # Khung 3-5: -0.5, Khung 6-9: -1.0, Khung 10+: -2.0
                if max_lose >= 10:
                    penalty = 2.0
                elif max_lose >= 6:
                    penalty = 1.0
                elif max_lose >= 3:
                    penalty = 0.5
                else:
                    penalty = 0.0
            else:
                # Original: fixed penalty
                penalty = K2N_RISK_PENALTY_FIXED if max_lose >= K2N_RISK_START_THRESHOLD else 0.0
            
            if pair_key and penalty > 0:
                if pair_key not in k2n_risks:
                    k2n_risks[pair_key] = {"count": 0, "total_penalty": 0.0, "max_frames": 0}
                
                k2n_risks[pair_key]["count"] += 1
                k2n_risks[pair_key]["total_penalty"] += penalty
                k2n_risks[pair_key]["max_frames"] = max(k2n_risks[pair_key]["max_frames"], max_lose)

        for pair_key, info in k2n_risks.items():
             if pair_key not in scores:
                scores[pair_key] = {
                    "score": 0.0,
                    "reasons": [],
                    "is_gan": False,
                    "gan_days": 0,
                    "gan_loto": "",
                    "sources": 0,
                }
             
             total_pen = info["total_penalty"]
             count = info["count"]
             max_frames = info["max_frames"]
             
             scores[pair_key]["score"] -= total_pen
             scores[pair_key]["sources"] += 1
             
             if count > 1:
                 scores[pair_key]["reasons"].append(f"Rủi ro K2N (x{count}, max {max_frames}kh) -{total_pen:.1f}")
             else:
                 scores[pair_key]["reasons"].append(f"Rủi ro K2N ({max_frames}kh) -{total_pen:.1f})")

        # Nguồn 5: Cầu Bạc Nhớ (Top N) - Giữ nguyên 1.5
        for bridge in top_memory_bridges:
            pair_key = _standardize_pair(bridge["stl"])
            if pair_key:
                if pair_key not in scores:
                    scores[pair_key] = {
                        "score": 0.0,
                        "reasons": [],
                        "is_gan": False,
                        "gan_days": 0,
                    "gan_loto": "",
                        "sources": 0,
                    }
                scores[pair_key]["score"] += 1.5
                scores[pair_key]["reasons"].append(f"BN ({bridge['rate']})")
                scores[pair_key]["sources"] += 1

        # Nguồn 6: Phong Độ Gần Đây (GOM NHÓM)
        try:
            try:
                from .db_manager import DB_NAME as db_name_param
            except ImportError:
                db_name_param = "xo_so_prizes_all_logic.db"
            
            managed_bridges = get_all_managed_bridges(db_name=db_name_param)
            
            # IMPROVED: Thêm tier Very High và giảm thresholds
            RF_MIN_LOW = getattr(SETTINGS, "RECENT_FORM_MIN_LOW", 3)
            RF_MIN_MED = getattr(SETTINGS, "RECENT_FORM_MIN_MED", 5)
            RF_MIN_HIGH = getattr(SETTINGS, "RECENT_FORM_MIN_HIGH", 7)
            RF_MIN_VERY_HIGH = getattr(SETTINGS, "RECENT_FORM_MIN_VERY_HIGH", 9)
            
            RF_BONUS_LOW = getattr(SETTINGS, "RECENT_FORM_BONUS_LOW", 1.0)
            RF_BONUS_MED = getattr(SETTINGS, "RECENT_FORM_BONUS_MED", 2.0)
            RF_BONUS_HIGH = getattr(SETTINGS, "RECENT_FORM_BONUS_HIGH", 3.0)
            RF_BONUS_VERY_HIGH = getattr(SETTINGS, "RECENT_FORM_BONUS_VERY_HIGH", 4.0)

            recent_form_groups = {} # pair -> {count, total_bonus, best_wins}

            for bridge in managed_bridges:
                if not bridge.get("is_enabled"):
                    continue
                    
                recent_wins = bridge.get("recent_win_count_10", 0)
                if isinstance(recent_wins, str):
                    try:
                        recent_wins = int(recent_wins)
                    except (ValueError, TypeError):
                        recent_wins = 0
                elif recent_wins is None:
                    recent_wins = 0
                
                prediction_stl_str = bridge.get("next_prediction_stl", "")
                
                if not prediction_stl_str or "," not in prediction_stl_str or "N2" in prediction_stl_str or "LỖI" in prediction_stl_str:
                    continue
                
                stl = prediction_stl_str.split(",")
                pair_key = _standardize_pair(stl)
                
                if pair_key and recent_wins >= RF_MIN_LOW:
                    if pair_key not in scores:
                        scores[pair_key] = {
                            "score": 0.0,
                            "reasons": [],
                            "is_gan": False,
                            "gan_days": 0,
                    "gan_loto": "",
                            "sources": 0,
                        }
                    
                    # IMPROVED: 4 tiers thay vì 3
                    bonus = 0.0
                    if recent_wins >= RF_MIN_VERY_HIGH:
                        bonus = RF_BONUS_VERY_HIGH
                    elif recent_wins >= RF_MIN_HIGH:
                        bonus = RF_BONUS_HIGH
                    elif recent_wins >= RF_MIN_MED:
                        bonus = RF_BONUS_MED
                    elif recent_wins >= RF_MIN_LOW:
                        bonus = RF_BONUS_LOW
                    
                    if bonus > 0:
                        # Gom nhóm thông tin thay vì cộng trực tiếp vào list
                        if pair_key not in recent_form_groups:
                            recent_form_groups[pair_key] = {
                                "count": 0, 
                                "total_bonus": 0.0, 
                                "best_wins": 0
                            }
                        
                        group = recent_form_groups[pair_key]
                        group["count"] += 1
                        group["total_bonus"] += bonus
                        if recent_wins > group["best_wins"]:
                            group["best_wins"] = recent_wins

            # Áp dụng dữ liệu đã gom vào bảng điểm
            for pair_key, info in recent_form_groups.items():
                total_bonus = info["total_bonus"]
                count = info["count"]
                best_wins = info["best_wins"]
                
                scores[pair_key]["score"] += total_bonus
                scores[pair_key]["sources"] += 1
                
                if count > 1:
                    scores[pair_key]["reasons"].append(f"Phong độ (x{count}) +{total_bonus:.1f}")
                else:
                    scores[pair_key]["reasons"].append(f"Phong độ ({best_wins}/10) +{total_bonus:.1f}")

        except Exception as e:
            print(f"Lỗi tính điểm phong độ: {e}")

        # --- 4. Chấm điểm cộng và AI (Trọng số liên tục) ---

        for pair_key in list(scores.keys()):
            loto1, loto2 = pair_key.split("-")

            # Nguồn 1: Loto Hot
            if loto1 in top_hot_lotos or loto2 in top_hot_lotos:
                scores[pair_key]["score"] += 1.0
                scores[pair_key]["reasons"].append("Loto Hot")
                scores[pair_key]["sources"] += 1

            # Nguồn 6: Gắn cờ Gan (IMPROVED: Track which number is gan)
            gan_days_1 = gan_map.get(loto1, 0)
            gan_days_2 = gan_map.get(loto2, 0)
            max_gan = max(gan_days_1, gan_days_2)
            if max_gan > 0:
                scores[pair_key]["is_gan"] = True
                scores[pair_key]["gan_days"] = max_gan
                # NEW: Store which loto is gan
                if gan_days_1 >= gan_days_2:
                    scores[pair_key]["gan_loto"] = loto1
                else:
                    scores[pair_key]["gan_loto"] = loto2

            # Nguồn 7: Chấm điểm AI (IMPROVED: Tăng weight từ 0.2 → 0.3)
            if loto_prob_map:
                prob_1 = loto_prob_map.get(loto1, 0.0)
                prob_2 = loto_prob_map.get(loto2, 0.0)
                max_prob = max(prob_1, prob_2)

                if max_prob > 0:
                    ai_score_contribution = max_prob * ai_score_weight
                    scores[pair_key]["score"] += ai_score_contribution
                    scores[pair_key]["sources"] += 1
                    scores[pair_key]["reasons"].append(
                        f"AI: +{ai_score_contribution:.2f} ({max_prob * 100.0:.1f}%)"
                    )

        # --- 5. Thêm các cặp SẠCH (Chỉ AI phát hiện - STL) ---
        if loto_prob_map:
            for loto1_str in [str(i).zfill(2) for i in range(100)]:
                if loto1_str[0] == loto1_str[1]:
                    continue
                loto2_str = str(int(loto1_str[::-1])).zfill(2)
                stl_pair = _standardize_pair([loto1_str, loto2_str])

                if stl_pair in scores:
                    continue

                prob1 = loto_prob_map.get(loto1_str, 0.0)
                prob2 = loto_prob_map.get(loto2_str, 0.0)
                max_prob = max(prob1, prob2)

                if max_prob > 0.0:
                    ai_score_contribution = max_prob * ai_score_weight

                    if stl_pair not in scores:
                        scores[stl_pair] = {
                            "score": 0.0,
                            "reasons": [],
                            "is_gan": False,
                            "gan_days": 0,
                    "gan_loto": "",
                        }

                    scores[stl_pair]["score"] += ai_score_contribution

                    scores[stl_pair]["reasons"].append(
                        f"AI SẠCH: +{ai_score_contribution:.2f} ({max_prob * 100.0:.1f}%)"
                    )

                    l1, l2 = stl_pair.split("-")
                    max_gan = max(gan_map.get(l1, 0), gan_map.get(l2, 0))
                    if max_gan > 0:
                        scores[stl_pair]["is_gan"] = True
                        scores[stl_pair]["gan_days"] = max_gan

        # --- 5.5. BONUS "VỀ GẦN" (V7.6 - IMPROVED EFFECTIVENESS) ---
        # Thêm điểm bonus cho các cặp đã về trong các kỳ gần đây
        if recent_data and len(recent_data) > 0:
            # Get last 7 periods
            last_7 = recent_data[-7:] if len(recent_data) >= 7 else recent_data
            last_3 = recent_data[-3:] if len(recent_data) >= 3 else recent_data
            
            # Extract all pairs from recent periods
            recent_pairs_3 = set()
            recent_pairs_7 = set()
            
            for row in last_3:
                try:
                    lotos = getAllLoto_V30(row)
                    # Generate all possible pairs from lotos
                    for i, loto1 in enumerate(lotos):
                        for loto2 in lotos[i+1:]:
                            pair_key = _standardize_pair([loto1, loto2])
                            if pair_key:
                                recent_pairs_3.add(pair_key)
                except:
                    pass
            
            for row in last_7:
                try:
                    lotos = getAllLoto_V30(row)
                    for i, loto1 in enumerate(lotos):
                        for loto2 in lotos[i+1:]:
                            pair_key = _standardize_pair([loto1, loto2])
                            if pair_key:
                                recent_pairs_7.add(pair_key)
                except:
                    pass
            
            # Apply bonus to scored pairs
            for pair_key in scores.keys():
                if pair_key in recent_pairs_3:
                    # +2.0 bonus for appearing in last 3 periods
                    scores[pair_key]["score"] += 2.0
                    scores[pair_key]["reasons"].append("Về 3kỳ (+2.0)")
                    scores[pair_key]["sources"] += 1
                elif pair_key in recent_pairs_7:
                    # +1.0 bonus for appearing in last 7 periods
                    scores[pair_key]["score"] += 1.0
                    scores[pair_key]["reasons"].append("Về 7kỳ (+1.0)")
                    scores[pair_key]["sources"] += 1

        # --- 6. Định dạng lại và Sắp xếp (IMPROVED: Thêm confidence score) ---
        final_list = []
        for pair_key, data in scores.items():
            # IMPROVED: Confidence score = số nguồn / 7 nguồn tối đa
            # 7 nguồn: Vote, High Win, K2N Risk, Memory, Recent Form, Loto Hot, AI
            num_sources = data.get("sources", 0)
            confidence = round(num_sources / 7.0, 2)
            
            # NEW: Extract AI probability for this pair
            loto1, loto2 = pair_key.split("-")
            ai_prob = 0.0
            if loto_prob_map:
                prob_1 = loto_prob_map.get(loto1, 0.0)
                prob_2 = loto_prob_map.get(loto2, 0.0)
                ai_prob = max(prob_1, prob_2)
            
            # NEW: Enhancement 3 - Auto-Recommendation System
            # Logic: Score ≥7 + Confidence ≥4 → CHƠI (green)
            #        Score ≥5 OR Confidence ≥3 → XEM XÉT (yellow)
            #        Otherwise → BỎ QUA (gray)
            score_val = data["score"]
            confidence_stars = num_sources  # Confidence stars = number of sources
            
            if score_val >= 7 and confidence_stars >= 4:
                recommendation = "CHƠI"
            elif score_val >= 5 or confidence_stars >= 3:
                recommendation = "XEM XÉT"
            else:
                recommendation = "BỎ QUA"
            
            final_list.append(
                {
                    "pair": pair_key,
                    "score": round(data["score"], 2),
                    "reasons": ", ".join(data["reasons"]),
                    "is_gan": data["is_gan"],
                    "gan_days": data["gan_days"],
                    "gan_loto": data.get("gan_loto", ""),  # NEW: Which loto is gan
                    "confidence": confidence,  # NEW: Confidence score
                    "sources": num_sources,  # NEW: Số nguồn
                    "ai_probability": round(ai_prob, 3),  # NEW: AI probability for this pair
                    "recommendation": recommendation,  # NEW: Enhancement 3 - Auto-recommendation
                }
            )

        final_list.sort(key=lambda x: x["score"], reverse=True)

        return final_list

    except Exception as e:
        import traceback

        print(f"LỖI get_top_scored_pairs: {e}")
        print(traceback.format_exc())
        return []


# ===================================================================================
# IV. HÀM MÔ PHỎNG LỊCH SỬ (V7.1 - CHUYỂN TỪ backtester.py)
# ===================================================================================


def get_consensus_simulation(data_slice, last_row):
    """Bản sao của get_prediction_consensus (chạy N1 trong bộ nhớ)."""
    prediction_sources = {}

    def _standardize_pair(stl_list):
        if not stl_list or len(stl_list) != 2:
            return None
        sorted_pair = sorted(stl_list)
        return f"{sorted_pair[0]}-{sorted_pair[1]}"

    # 1. Lấy từ 15 Cầu Cổ Điển
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

    # 2. Lấy từ Cầu Đã Lưu (chạy N1)
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

    # 1. Chạy K2N Cache Mô phỏng (Cầu Đã Lưu)
    cache_list, _ = _parse_k2n_results(
        BACKTEST_MANAGED_BRIDGES_K2N(
            data_slice,
            2,
            len(data_slice) + 1,
            DB_NAME,
            history=False,
        )
    )

    # Chạy 15 cầu cổ điển
    cache_list_15, _ = _parse_k2n_results(
        BACKTEST_15_CAU_K2N_V30_AI_V8(
            data_slice,
            2,
            len(data_slice) + 1,
            history=False,
        )
    )
    cache_list.extend(cache_list_15)

    if not cache_list:
        return []

    # 2. Lọc kết quả
    for win_rate_text, _, next_prediction_stl, _, _, bridge_name in cache_list:
        try:
            win_rate = float(str(win_rate_text).replace("%", ""))

            if win_rate >= threshold:
                if (
                    not next_prediction_stl
                    or "N2" in next_prediction_stl
                    or "LỖI" in next_prediction_stl
                    or "," not in next_prediction_stl
                ):
                    continue

                stl = next_prediction_stl.split(",")
                high_win_bridges.append(
                    {
                        "name": bridge_name,  # FIX: Dùng bridge_name từ cache
                        "stl": stl,
                        "rate": f"{win_rate:.2f}%",
                    }
                )
        except (ValueError, TypeError):
            continue

    return high_win_bridges


def get_historical_dashboard_data(all_data_ai, day_index, temp_settings):
    """Hàm "chủ" để mô phỏng Bảng Tổng Hợp tại một ngày trong quá khứ."""

    # 1. Cắt lát dữ liệu
    data_slice = all_data_ai[: day_index + 1]
    if len(data_slice) < 2:
        return None

    last_row = data_slice[-1]
    # prev_row = data_slice[-2]

    # 2. Lấy các giá trị cài đặt tạm thời
    n_days_stats = int(temp_settings.get("STATS_DAYS", 7))
    n_days_gan = int(temp_settings.get("GAN_DAYS", 15))
    high_win_thresh = float(temp_settings.get("HIGH_WIN_THRESHOLD", 47.0))

    # 3. Chạy 7 hệ thống (phiên bản mô phỏng)

    # (1) Loto Hot
    stats_n_day = get_loto_stats_last_n_days(data_slice, n=n_days_stats)

    # (2) Cache K2N (để lấy pending - cần dict pending_k2n)
    _, pending_k2n_data = _parse_k2n_results(
        BACKTEST_15_CAU_K2N_V30_AI_V8(
            data_slice,
            2,
            len(data_slice) + 1,
            history=False,
        )
    )

    # (3) Consensus (Vote)
    consensus = get_consensus_simulation(data_slice, last_row)

    # (4) Cầu Tỷ Lệ Cao
    high_win = get_high_win_simulation(data_slice, last_row, threshold=high_win_thresh)

    # (5) Cầu Bạc Nhớ
    top_memory_bridges = get_top_memory_bridge_predictions(
        data_slice, last_row, top_n=5
    )

    # (6) Lô Gan
    gan_stats = get_loto_gan_stats(data_slice, n_days=n_days_gan)

    # (7) Chấm điểm (V7.6: IMPROVED với recent_data cho bonus "Về Gần")
    top_scores = get_top_scored_pairs(
        stats_n_day,
        consensus,
        high_win,
        pending_k2n_data,  # Dữ liệu pending K2N
        gan_stats,
        top_memory_bridges,
        ai_predictions=None,
        recent_data=data_slice,  # NEW: Pass recent data for "Về Gần" bonus
    )

    return top_scores