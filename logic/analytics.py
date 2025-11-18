# Tên file: git3/logic/analytics.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA E226)
#
from collections import Counter

# Import các hàm DB
try:
    from .db_manager import DB_NAME, get_all_managed_bridges
except ImportError:
    try:
        from db_manager import DB_NAME, get_all_managed_bridges
    except ImportError:
        print("Lỗi: Không thể import db_manager trong analytics.py")
        DB_NAME = "xo_so_prizes_all_logic.db"

        def get_all_managed_bridges(d, o):
            return []


# Import các hàm cầu cổ điển
try:
    from .bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5,
        checkHitSet_V30_K2N,
        getAllLoto_V30,
    )
except ImportError:
    try:
        from bridges_classic import (
            ALL_15_BRIDGE_FUNCTIONS_V5,
            checkHitSet_V30_K2N,
            getAllLoto_V30,
        )
    except ImportError:
        print("Lỗi: Không thể import bridges_classic trong analytics.py")
        ALL_15_BRIDGE_FUNCTIONS_V5 = []

        def getAllLoto_V30(r):
            return []

        # Đổi tên 'l' thành 'loto_set' cho rõ nghĩa
        def checkHitSet_V30_K2N(p, loto_set):
            return "Lỗi"


# Import các hàm cầu V16
try:
    from .bridges_v16 import getAllPositions_V16, taoSTL_V30_Bong
except ImportError:
    try:
        from bridges_v16 import getAllPositions_V16, taoSTL_V30_Bong
    except ImportError:
        print("Lỗi: Không thể import bridges_v16 trong analytics.py")

        def getAllPositions_V16(r):
            return []

        def taoSTL_V30_Bong(a, b):
            return ["00", "00"]


# ===================================================================================
# (MỚI) CÁC HÀM CHO BẢNG TỔNG HỢP QUYẾT ĐỊNH
# ===================================================================================


def get_loto_stats_last_n_days(all_data_ai, n=7):
    """
    (MỚI) Lấy thống kê tần suất loto trong N ngày gần nhất.
    Trả về: list[('loto', count_nhay, count_ky)],
             ví dụ: [('33', 4, 3), ('01', 3, 3)]
             (Loto 33 về 4 nháy, xuất hiện trong 3/7 kỳ)
    """
    try:
        if not all_data_ai or len(all_data_ai) == 0:
            return []

        if len(all_data_ai) < n:
            n = len(all_data_ai)

        last_n_rows = all_data_ai[-n:]

        all_lotos_hits = []  # Để đếm tổng số nháy
        day_appearance_counter = Counter()  # Để đếm tổng số kỳ (ngày)

        for row in last_n_rows:
            lotos_in_this_row = getAllLoto_V30(row)

            # 1. Đếm tổng số nháy (giống như cũ)
            all_lotos_hits.extend(lotos_in_this_row)

            # 2. Đếm số kỳ xuất hiện (mới)
            unique_lotos_in_this_row = set(lotos_in_this_row)
            day_appearance_counter.update(
                unique_lotos_in_this_row
            )  # update 1 lần cho mỗi loto/kỳ

        # Đếm tổng số nháy
        loto_hit_counts = Counter(all_lotos_hits)

        # Sắp xếp theo tổng số nháy (ưu tiên)
        sorted_lotos_by_hits = sorted(
            loto_hit_counts.items(), key=lambda item: item[1], reverse=True
        )

        # Kết hợp dữ liệu
        final_stats = []
        for loto, hit_count in sorted_lotos_by_hits:
            day_count = day_appearance_counter.get(loto, 0)  # Lấy số kỳ đã xuất hiện
            final_stats.append(
                (loto, hit_count, day_count)
            )  # (loto, tổng_nháy, tổng_kỳ)

        return final_stats

    except Exception as e:
        print(f"Lỗi get_loto_stats_last_n_days (mới): {e}")
        return []


def get_prediction_consensus(last_row, db_name=DB_NAME):
    """
    (MỚI) Lấy dự đoán từ "15 Cầu" và "Cầu Đã Lưu" để đếm vote THEO CẶP.
    Trả về: list[('cap_so', count, 'sources')]
    ví dụ: [('03-30', 2, 'C1, G5.6[3]')]
    """
    try:
        if not last_row or len(last_row) < 10:
            return []

        prediction_sources = {}  # { 'pair_key': ['C1', 'GDB[0]...'] }

        def get_pair_key(stl_list):
            """Chuẩn hóa 1 cặp STL. Ví dụ ['30', '03'] -> '03-30'"""
            if not stl_list or len(stl_list) != 2:
                return None
            # Sắp xếp để chuẩn hóa, ví dụ ['30', '03'] -> ['03', '30']
            sorted_pair = sorted(stl_list)
            return f"{sorted_pair[0]}-{sorted_pair[1]}"  # Key: "03-30"

        # 1. Lấy từ 15 Cầu Cổ Điển
        for i, bridge_func in enumerate(ALL_15_BRIDGE_FUNCTIONS_V5):
            try:
                stl = bridge_func(last_row)
                pair_key = get_pair_key(stl)
                if not pair_key:
                    continue

                source_name = f"C{i + 1}"
                if pair_key not in prediction_sources:
                    prediction_sources[pair_key] = []
                prediction_sources[pair_key].append(source_name)
            except Exception as e:
                print(f"Lỗi dự đoán 15 Cầu (consensus): {e}")

        # 2. Lấy từ Cầu Đã Lưu
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if managed_bridges:
            last_positions = getAllPositions_V16(last_row)
            for bridge in managed_bridges:
                try:
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    a, b = last_positions[idx1], last_positions[idx2]
                    if a is None or b is None:
                        continue

                    stl = taoSTL_V30_Bong(a, b)
                    pair_key = get_pair_key(stl)
                    if not pair_key:
                        continue

                    source_name = bridge["name"]
                    if pair_key not in prediction_sources:
                        prediction_sources[pair_key] = []
                    # Chỉ thêm 1 lần cho 1 cầu (tránh trùng lặp)
                    if source_name not in prediction_sources[pair_key]:
                        prediction_sources[pair_key].append(source_name)
                except Exception as e:
                    print(f"Lỗi dự đoán Cầu Đã Lưu (consensus): {e}")

        # 3. Tổng hợp và Sắp xếp
        consensus_list = []
        for pair_key, sources in prediction_sources.items():
            count = len(sources)
            sources_str = ", ".join(sources)
            consensus_list.append((pair_key, count, sources_str))

        consensus_list.sort(key=lambda item: item[1], reverse=True)
        return consensus_list

    except Exception as e:
        print(f"Lỗi get_prediction_consensus (mới): {e}")
        return []


def get_high_win_rate_predictions(last_row, threshold=80.0, db_name=DB_NAME):
    """
    (MỚI) Lấy dự đoán từ các cầu CÓ TỶ LỆ CAO (dựa trên Cầu Đã Lưu).
    Trả về: list[ {'name': str, 'stl': list, 'rate': str} ]
    """
    try:
        if not last_row or len(last_row) < 10:
            return []

        high_win_bridges = []
        managed_bridges = get_all_managed_bridges(db_name, only_enabled=True)
        if not managed_bridges:
            return []

        last_positions = getAllPositions_V16(last_row)

        for bridge in managed_bridges:
            try:
                # 1. Kiểm tra tỷ lệ
                rate_str = str(bridge.get("win_rate_text", "0%")).replace("%", "")
                if not rate_str or rate_str == "N/A":
                    continue

                win_rate = float(rate_str)

                # 2. Nếu đạt ngưỡng
                if win_rate >= threshold:
                    idx1, idx2 = bridge["pos1_idx"], bridge["pos2_idx"]
                    a, b = last_positions[idx1], last_positions[idx2]
                    if a is None or b is None:
                        continue

                    stl = taoSTL_V30_Bong(a, b)
                    high_win_bridges.append(
                        {"name": bridge["name"], "stl": stl, "rate": f"{win_rate:.2f}%"}
                    )
            except Exception as e:
                print(f"Lỗi kiểm tra tỷ lệ cầu {bridge['name']}: {e}")

        return high_win_bridges

    except Exception as e:
        print(f"Lỗi get_high_win_rate_predictions: {e}")
        return []


def get_loto_gan_stats(all_data_ai, n_days=15):
    """
    (MỚI) Tìm các loto (00-99) đã không xuất hiện trong n_days gần nhất.
    Trả về: list[('loto', so_ngay_gan)]
    Ví dụ: [('22', 18), ('01', 15)]
    """
    gan_stats = []
    try:
        if not all_data_ai or len(all_data_ai) < n_days:
            print(f"Cảnh báo Lô Gan: Không đủ dữ liệu (cần {n_days} kỳ).")
            return []

        # 1. Tạo danh sách 100 loto
        all_100_lotos = {str(i).zfill(2) for i in range(100)}

        # 2. Tìm loto xuất hiện trong N ngày gần nhất
        recent_lotos = set()
        recent_rows = all_data_ai[-n_days:]
        for row in recent_rows:
            lotos_in_row = getAllLoto_V30(row)
            recent_lotos.update(lotos_in_row)

        # 3. Lấy danh sách loto gan (loto không có trong danh sách gần đây)
        gan_lotos = all_100_lotos - recent_lotos

        if not gan_lotos:
            return []  # Không có loto nào gan > n_days

        # 4. Tính toán số ngày gan chính xác cho từng loto
        full_history = all_data_ai[:]  # Copy
        full_history.reverse()  # Đảo ngược, [0] là ngày gần nhất

        for loto in gan_lotos:
            days_gan = 0
            found = False
            for i, row in enumerate(full_history):
                if i < n_days:  # Bỏ qua N ngày gần nhất (vì ta biết nó không về)
                    days_gan += 1
                    continue

                loto_set_this_day = set(getAllLoto_V30(row))
                if loto in loto_set_this_day:
                    found = True
                    break  # Tìm thấy rồi, dừng đếm
                else:
                    days_gan += 1  # Cộng thêm ngày gan

            if found:
                gan_stats.append((loto, days_gan))
            else:
                # Gan cực đại (chưa về trong toàn bộ lịch sử)
                gan_stats.append((loto, len(full_history)))

        # 5. Sắp xếp: Gan lâu nhất lên đầu
        gan_stats.sort(key=lambda x: x[1], reverse=True)
        return gan_stats

    except Exception as e:
        print(f"Lỗi get_loto_gan_stats: {e}")
        return []


def _standardize_pair(stl_list):
    """Hàm nội bộ: Chuẩn hóa 1 cặp STL. Ví dụ ['30', '03'] -> '03-30'"""
    if not stl_list or len(stl_list) != 2:
        return None
    sorted_pair = sorted(stl_list)
    return f"{sorted_pair[0]}-{sorted_pair[1]}"  # Key: "03-30"


# ===================================================================================
# (MỚI) HÀM TÍNH ĐIỂM TỔNG LỰC (GIAI ĐOẠN 2)
# ===================================================================================


def get_top_scored_pairs(stats, consensus, high_win, pending_k2n, gan_stats):
    """
    (MỚI) Tính toán, chấm điểm và xếp hạng các cặp số dựa trên 5 nguồn dữ liệu.
    """
    try:
        # { '03-30': {'score': 0, 'reasons': [], 'is_gan': False, 'gan_days': 0} }
        scores = {}

        # --- 1. Tạo danh sách Loto Về Nhiều (Top 5) để tra cứu ---
        top_hot_lotos = {loto for loto, nhay, ky in stats[:5]}

        # --- 2. Tạo danh sách Loto Gan để tra cứu ---
        gan_map = {loto: days for loto, days in gan_stats}

        # --- 3. Chấm điểm từ 3 nguồn chính (Consensus, High Win, K2N) ---

        # Nguồn 2: Consensus (Dự đoán nhiều)
        for pair_key, count, sources in consensus[:3]:  # Top 3
            if pair_key not in scores:
                scores[pair_key] = {
                    "score": 0,
                    "reasons": [],
                    "is_gan": False,
                    "gan_days": 0,
                }
            scores[pair_key]["score"] += 3
            scores[pair_key]["reasons"].append(f"Top {len(scores)} Dự Đoán")

        # Nguồn 3: Cầu Tỷ Lệ Cao (>=47%)
        for bridge in high_win:
            pair_key = _standardize_pair(bridge["stl"])
            if not pair_key:
                continue
            if pair_key not in scores:
                scores[pair_key] = {
                    "score": 0,
                    "reasons": [],
                    "is_gan": False,
                    "gan_days": 0,
                }
            scores[pair_key]["score"] += 2
            scores[pair_key]["reasons"].append(f"Cầu {bridge['rate']}")

        # Nguồn 4: Cầu K2N Đang Chờ
        for item in pending_k2n:
            pair_key = _standardize_pair(item["stl"])
            if not pair_key:
                continue
            if pair_key not in scores:
                scores[pair_key] = {
                    "score": 0,
                    "reasons": [],
                    "is_gan": False,
                    "gan_days": 0,
                }
            scores[pair_key]["score"] += 2
            scores[pair_key]["reasons"].append(f"Chờ K2N (Chuỗi {item['streak']})")

        # --- 4. Chấm điểm cộng (Loto Về Nhiều) và Gắn cờ (Lô Gan) ---

        # Duyệt qua tất cả các cặp đã có điểm
        for pair_key in list(scores.keys()):
            loto1, loto2 = pair_key.split("-")

            # Điểm cộng (Nguồn 1: Loto Về Nhiều)
            if loto1 in top_hot_lotos or loto2 in top_hot_lotos:
                scores[pair_key]["score"] += 1
                scores[pair_key]["reasons"].append("Loto Hot")

            # Gắn cờ Gan (Nguồn 5: Lô Gan)
            gan_days_1 = gan_map.get(loto1, 0)
            gan_days_2 = gan_map.get(loto2, 0)
            max_gan = max(gan_days_1, gan_days_2)

            if max_gan > 0:
                scores[pair_key]["is_gan"] = True
                scores[pair_key]["gan_days"] = max_gan

        # --- 5. Định dạng lại và Sắp xếp ---
        final_list = []
        for pair_key, data in scores.items():
            final_list.append(
                {
                    "pair": pair_key,
                    "score": data["score"],
                    "reasons": ", ".join(data["reasons"]),
                    "is_gan": data["is_gan"],
                    "gan_days": data["gan_days"],
                }
            )

        # Sắp xếp theo Điểm (cao -> thấp)
        final_list.sort(key=lambda x: x["score"], reverse=True)

        return final_list

    except Exception as e:
        print(f"LỖI get_top_scored_pairs: {e}")
        return []
