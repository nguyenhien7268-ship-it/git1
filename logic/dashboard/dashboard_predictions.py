"""
dashboard_predictions.py - Prediction functions

Contains prediction functions extracted from dashboard_analytics.py
Functions: get_top_memory_bridge_predictions, get_prediction_consensus,
           get_high_win_rate_predictions, get_pending_k2n_bridges
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
    from ..backtester import (
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_MANAGED_BRIDGES_K2N,
    )
    from ..backtester_helpers import parse_k2n_results as _parse_k2n_results
    from ..bridges.bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5,
        checkHitSet_V30_K2N,
        getAllLoto_V30,
    )
    from ..bridges.bridges_memory import (
        calculate_bridge_stl,
        get_27_loto_names,
        get_27_loto_positions,
    )
    from ..bridges.bridges_v16 import getAllPositions_V17_Shadow, taoSTL_V30_Bong
    from ..data_repository import get_all_managed_bridges
    from ..db_manager import DB_NAME
except ImportError:
    def getAllLoto_V30(r):
        return []
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
    from ..constants import DB_PATH as DB_NAME
    def get_all_managed_bridges(d, o):
        return []
    ALL_15_BRIDGE_FUNCTIONS_V5 = []

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
    # FIX: Đặt last_row=None để tương thích với cách gọi cũ (vị trí đầu tiên) và mới
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
    # FIX: Đặt last_row=None để tương thích với cách gọi cũ (vị trí đầu tiên)
    try:
        # FIX: Sửa truy cập SETTINGS
        if threshold is None:
            threshold = SETTINGS.HIGH_WIN_THRESHOLD

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
# III. HÀM CHẤM ĐIỂM CỐT LÕI (V7.1 - HOÀN THIỆN LOGIC TRỌNG SỐ)
# ===================================================================================
