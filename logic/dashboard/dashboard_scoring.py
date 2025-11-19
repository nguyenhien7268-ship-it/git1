"""
dashboard_scoring.py - Scoring functions

Contains the large get_top_scored_pairs function extracted from dashboard_analytics.py
"""

# Import SETTINGS
try:
    from ..config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    except ImportError:
        from ..constants import DEFAULT_SETTINGS
        SETTINGS = type("obj", (object,), DEFAULT_SETTINGS)

try:
    from .dashboard_stats import get_loto_stats_last_n_days
except ImportError:
    def get_loto_stats_last_n_days(all_data_ai, n=None):
        return []

try:
    from ..bridges.bridges_classic import getAllLoto_V30
except ImportError:
    def getAllLoto_V30(r):
        return []


def _standardize_pair(stl_list):
    """Standardize a pair of lottery numbers to sorted format."""
    if not stl_list or len(stl_list) != 2:
        return None
    sorted_pair = sorted(stl_list)
    return f"{sorted_pair[0]}-{sorted_pair[1]}"


def get_top_scored_pairs(
    stats,
    consensus,
    high_win,
    pending_k2n,
    gan_stats,
    top_memory_bridges,
    ai_predictions=None,
):
    """
    (V7.1) Tính toán, chấm điểm và xếp hạng các cặp số.
    Hoàn thiện việc sử dụng Trọng số AI liên tục (loại bỏ kiểm tra ngưỡng cứng).
    """
    try:
        scores = {}

        # FIX: Sửa truy cập SETTINGS
        K2N_RISK_START_THRESHOLD = SETTINGS.K2N_RISK_START_THRESHOLD
        K2N_RISK_PENALTY_PER_FRAME = SETTINGS.K2N_RISK_PENALTY_PER_FRAME
        # ai_prob_threshold = SETTINGS.AI_PROB_THRESHOLD # Đã loại bỏ việc dùng ngưỡng này cho logic
        ai_score_weight = SETTINGS.AI_SCORE_WEIGHT

        loto_prob_map = {}
        if ai_predictions:
            for pred in ai_predictions:
                loto_prob_map[pred["loto"]] = (
                    pred["probability"] / 100.0
                )  # Chuẩn hóa 0-1

        # Helper maps
        top_hot_lotos = {loto for loto, count, days in stats if count > 0}
        gan_map = {loto: days for loto, days in gan_stats}

        # --- 3. Chấm điểm từ 4 nguồn chính (Điểm truyền thống) ---

        # Nguồn 2: Consensus
        for pair_key, count, _ in consensus:
            if pair_key not in scores:
                scores[pair_key] = {
                    "score": 0.0,
                    "reasons": [],
                    "is_gan": False,
                    "gan_days": 0,
                }
            scores[pair_key]["score"] += count * 0.5
            scores[pair_key]["reasons"].append(f"Vote x{count}")

        # Nguồn 3: Cầu Tỷ Lệ Cao
        for bridge in high_win:
            pair_key = _standardize_pair(bridge["stl"])
            if pair_key:
                if pair_key not in scores:
                    scores[pair_key] = {
                        "score": 0.0,
                        "reasons": [],
                        "is_gan": False,
                        "gan_days": 0,
                    }
                scores[pair_key]["score"] += 2.0
                scores[pair_key]["reasons"].append(f"Cao ({bridge['rate']})")

        # Nguồn 4: Cầu K2N Đang Chờ (Trừ điểm rủi ro K2N)
        for bridge_name, data in pending_k2n.items():
            pair_key = _standardize_pair(data["stl"].split(","))
            if pair_key and data["max_lose"] >= K2N_RISK_START_THRESHOLD:
                if pair_key not in scores:
                    scores[pair_key] = {
                        "score": 0.0,
                        "reasons": [],
                        "is_gan": False,
                        "gan_days": 0,
                    }

                penalty = (
                    data["max_lose"] - K2N_RISK_START_THRESHOLD + 1
                ) * K2N_RISK_PENALTY_PER_FRAME
                scores[pair_key]["score"] -= penalty
                scores[pair_key]["reasons"].append(f"Rủi ro K2N (-{penalty})")

        # Nguồn 5: Cầu Bạc Nhớ (Top N)
        for bridge in top_memory_bridges:
            pair_key = _standardize_pair(bridge["stl"])
            if pair_key:
                if pair_key not in scores:
                    scores[pair_key] = {
                        "score": 0.0,
                        "reasons": [],
                        "is_gan": False,
                        "gan_days": 0,
                    }
                scores[pair_key]["score"] += 1.5
                scores[pair_key]["reasons"].append(f"BN ({bridge['rate']})")

        # --- 4. Chấm điểm cộng và AI (Trọng số liên tục) ---

        for pair_key in list(scores.keys()):
            loto1, loto2 = pair_key.split("-")

            # Nguồn 1: Loto Hot
            if loto1 in top_hot_lotos or loto2 in top_hot_lotos:
                scores[pair_key]["score"] += 1.0
                scores[pair_key]["reasons"].append("Loto Hot")

            # Nguồn 6: Gắn cờ Gan
            gan_days_1 = gan_map.get(loto1, 0)
            gan_days_2 = gan_map.get(loto2, 0)
            max_gan = max(gan_days_1, gan_days_2)
            if max_gan > 0:
                scores[pair_key]["is_gan"] = True
                scores[pair_key]["gan_days"] = max_gan

            # Nguồn 7: Chấm điểm AI (TRỌNG SỐ LIÊN TỤC) - Sửa V7.1: Luôn hiển thị xác suất
            if loto_prob_map:
                prob_1 = loto_prob_map.get(loto1, 0.0)
                prob_2 = loto_prob_map.get(loto2, 0.0)
                max_prob = max(prob_1, prob_2)

                ai_score_contribution = max_prob * ai_score_weight
                scores[pair_key]["score"] += ai_score_contribution

                # Sửa E226
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
                        }

                    scores[stl_pair]["score"] += ai_score_contribution

                    # Sửa V7.1: Luôn hiển thị xác suất
                    # Sửa E226
                    scores[stl_pair]["reasons"].append(
                        f"AI SẠCH: +{ai_score_contribution:.2f} ({max_prob * 100.0:.1f}%)"
                    )

                    l1, l2 = stl_pair.split("-")
                    max_gan = max(gan_map.get(l1, 0), gan_map.get(l2, 0))
                    if max_gan > 0:
                        scores[stl_pair]["is_gan"] = True
                        scores[stl_pair]["gan_days"] = max_gan

        # --- 6. Định dạng lại và Sắp xếp ---
        final_list = []
        for pair_key, data in scores.items():
            final_list.append(
                {
                    "pair": pair_key,
                    "score": round(data["score"], 2),
                    "reasons": ", ".join(data["reasons"]),
                    "is_gan": data["is_gan"],
                    "gan_days": data["gan_days"],
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
