"""
dashboard_simulation.py - Simulation and historical data functions

Contains simulation functions extracted from dashboard_analytics.py
Functions: get_consensus_simulation, get_high_win_simulation, get_historical_dashboard_data
"""

from collections import Counter

# Import SETTINGS
try:
    from ..config_manager import SETTINGS
except ImportError:
    try:
        from config_manager import SETTINGS
    except ImportError:
        from ..constants import DEFAULT_SETTINGS
        SETTINGS = type("obj", (object,), DEFAULT_SETTINGS)

# Import from other dashboard modules
try:
    from .dashboard_predictions import (
        get_prediction_consensus,
        get_high_win_rate_predictions,
    )
    from .dashboard_stats import get_loto_stats_last_n_days
except ImportError:
    def get_prediction_consensus(last_row=None, db_name=None):
        return []
    def get_high_win_rate_predictions(last_row=None, threshold=None, db_name=None):
        return []
    def get_loto_stats_last_n_days(all_data_ai, n=None):
        return []

try:
    from ..bridges.bridges_classic import getAllLoto_V30
except ImportError:
    def getAllLoto_V30(r):
        return []

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
    for win_rate_text, _, next_prediction_stl, _, bridge_name in cache_list:
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
    from ..constants import DEFAULT_SETTINGS
    n_days_stats = int(temp_settings.get("STATS_DAYS", DEFAULT_SETTINGS["STATS_DAYS"]))
    n_days_gan = int(temp_settings.get("GAN_DAYS", DEFAULT_SETTINGS["GAN_DAYS"]))
    high_win_thresh = float(temp_settings.get("HIGH_WIN_THRESHOLD", DEFAULT_SETTINGS["HIGH_WIN_THRESHOLD"]))

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

    # (7) Chấm điểm
    top_scores = get_top_scored_pairs(
        stats_n_day,
        consensus,
        high_win,
        pending_k2n_data,  # Dữ liệu pending K2N
        gan_stats,
        top_memory_bridges,
        ai_predictions=None,
    )

    return top_scores
