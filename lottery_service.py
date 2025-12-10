# Tên file: git1/lottery_service.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA LỖI MISSING IMPORT DASHBOARD ANALYTICS)
#
"""
==================================================================================
LOTTERY SERVICE API (BỘ ĐIỀU PHỐI) - (V7.4 - FIXED EXPORTS)
==================================================================================
File này đóng vai trò là API trung tâm, import và phân phối logic từ
các file con trong thư mục /logic.
"""
# 1. LOGIC DB & REPO
try:
    from logic.data_repository import get_all_managed_bridges, load_data_ai_from_db, delete_managed_bridges_batch
    from logic.db_manager import (
        DB_NAME,
        add_managed_bridge,
        delete_managed_bridge,
        delete_ky_from_db,
        get_all_kys_from_db,
        get_results_by_ky,
        setup_database,
        update_bridge_k2n_cache_batch,
        update_bridge_win_rate_batch,
        update_managed_bridge,
        upsert_managed_bridge,
    )

    print(">>> (V7.3) Tải logic.db_manager & data_repository thành công.")
except ImportError as e_db:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic DB/Repo: {e_db}")
    # Fallback for delete_managed_bridges_batch if import fails
    def delete_managed_bridges_batch(names, db_name=None, transactional=False, chunk_size=500):
        return {"requested": len(names or []), "deleted": [], "missing": list(names or []), "failed": [{"error": "delete_managed_bridges_batch not available"}]}

# 2. LOGIC PARSING (XỬ LÝ DỮ LIỆU)
try:
    from logic.data_parser import (
        parse_and_APPEND_data,
        parse_and_APPEND_data_TEXT,
        parse_and_insert_data,
        run_and_update_from_text,
    )

    print(">>> (V7.3) Tải logic.data_parser thành công.")
except ImportError as e_parser:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.data_parser: {e_parser}")

# 3. LOGIC CẦU CỔ ĐIỂN & TIỆN ÍCH
try:
    from logic.bridges.bridges_classic import (
        ALL_15_BRIDGE_FUNCTIONS_V5,
        calculate_loto_stats,
        getAllLoto_V30,
    )

    print(">>> (V7.3) Tải logic.bridges.bridges_classic thành công.")
except ImportError as e_classic:
    print(
        f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridges.bridges_classic: {e_classic}"
    )

# 4. LOGIC BACKTEST
try:
    from logic.backtester import (
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_15_CAU_N1_V31_AI_V8,
        BACKTEST_CUSTOM_CAU_V16,
        BACKTEST_MANAGED_BRIDGES_K2N,
        BACKTEST_MANAGED_BRIDGES_N1,
        BACKTEST_MEMORY_BRIDGES,
        TONGHOP_TOP_CAU_N1_V5,
        TONGHOP_TOP_CAU_RATE_V5,
        run_and_update_all_bridge_K2N_cache,
        run_and_update_all_bridge_rates,
    )

    print(">>> (V7.3) Tải logic.backtester thành công.")
except ImportError as e_backtester:
    print(f"LỖĨ NGHIÊM TRỌNG: Không thể import logic.backtester: {e_backtester}")

# 5. LOGIC QUẢN LÝ CẦU (DÒ, LỌC)
try:
    # Import scanning functions from lo_bridge_scanner
    from logic.bridges.lo_bridge_scanner import (
        TIM_CAU_BAC_NHO_TOT_NHAT,
        TIM_CAU_TOT_NHAT_V16,
        update_fixed_lo_bridges,
    )
    # Import management functions from bridge_manager_core
    from logic.bridges.bridge_manager_core import (
        auto_manage_bridges,
        find_and_auto_manage_bridges,
        prune_bad_bridges,
    )
    from logic.bridges.bridge_manager_de import find_and_auto_manage_bridges_de

    print(">>> (V7.3) Tải logic.bridges.bridge_manager_core & lo_bridge_scanner thành công.")
except ImportError as e_bridge_core:
    print(
        f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridges modules: {e_bridge_core}"
    )

# 6. LOGIC DASHBOARD (CHẤM ĐIỂM)
try:
    from logic.dashboard_analytics import (
        get_high_win_rate_predictions,
        get_historical_dashboard_data,
        get_loto_gan_stats,
        get_loto_stats_last_n_days,
        get_prediction_consensus,
        get_top_memory_bridge_predictions,
        get_top_scored_pairs,
        # [FIXED] Thêm import để phục vụ AppController
        prepare_daily_features,
        calculate_score_from_features
    )

    print(">>> (V7.3) Tải logic.dashboard_analytics thành công.")
except ImportError as e_dashboard:
    print(
        f"LỖI NGHIÊM TRỌNG: Không thể import logic.dashboard_analytics: {e_dashboard}"
    )


# 7. LOGIC AI (HUẤN LUYỆN, DỰ ĐOÁN, ĐA LUỒNG)
try:
    # (SỬA) Import các hàm AI đã được tách biệt
    from logic.ai_feature_extractor import (
        run_ai_prediction_for_dashboard,
        run_ai_training_threaded,
    )

    print(">>> (V7.3) Tải logic.ai_feature_extractor (AI Wrappers) thành công.")
except ImportError as e_ai:
    error_msg = str(e_ai)
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.ai_feature_extractor (AI): {error_msg}")

    # Giả lập hàm nếu lỗi
    def run_ai_training_threaded(callback=None):
        return False, "Lỗi: Không tìm thấy module ai_feature_extractor"

    def run_ai_prediction_for_dashboard():
        return None, "Lỗi: Không tìm thấy module ai_feature_extractor"


# Thêm __all__ để đánh dấu các hàm này là 'được sử dụng' (để export)
__all__ = [
    # DB & Repo (12)
    "get_all_managed_bridges",
    "load_data_ai_from_db",
    "DB_NAME",
    "add_managed_bridge",
    "delete_managed_bridge",
    "delete_managed_bridges_batch",
    "get_all_kys_from_db",
    "get_results_by_ky",
    "setup_database",
    "update_bridge_k2n_cache_batch",
    "update_bridge_win_rate_batch",
    "update_managed_bridge",
    "upsert_managed_bridge",
    # Parsing (4)
    "parse_and_APPEND_data",
    "parse_and_APPEND_data_TEXT",
    "parse_and_insert_data",
    "run_and_update_from_text",
    # Bridges Classic (3)
    "ALL_15_BRIDGE_FUNCTIONS_V5",
    "calculate_loto_stats",
    "getAllLoto_V30",
    # Backtester (10)
    "BACKTEST_15_CAU_K2N_V30_AI_V8",
    "BACKTEST_15_CAU_N1_V31_AI_V8",
    "BACKTEST_CUSTOM_CAU_V16",
    "BACKTEST_MANAGED_BRIDGES_K2N",
    "BACKTEST_MANAGED_BRIDGES_N1",
    "BACKTEST_MEMORY_BRIDGES",
    "TONGHOP_TOP_CAU_N1_V5",
    "TONGHOP_TOP_CAU_RATE_V5",
    "run_and_update_all_bridge_K2N_cache",
    "run_and_update_all_bridge_rates",
    # Bridge Manager (5)
    "TIM_CAU_BAC_NHO_TOT_NHAT",
    "TIM_CAU_TOT_NHAT_V16",
    "auto_manage_bridges",
    "find_and_auto_manage_bridges",
    "prune_bad_bridges",
    "find_and_auto_manage_bridges_de",  # Thêm hàm của Đề
    # Dashboard (7)
    "get_high_win_rate_predictions",
    "get_historical_dashboard_data",
    "get_loto_gan_stats",
    "get_loto_stats_last_n_days",
    "get_prediction_consensus",
    "get_top_memory_bridge_predictions",
    "get_top_scored_pairs",
    # AI (2)
    "run_ai_prediction_for_dashboard",
    "run_ai_training_threaded",
    # Hàm Wrapper (1)
    "get_all_managed_bridges_wrapper",
    # Optimizer functions
    "prepare_daily_features",
    "calculate_score_from_features",
]


# ==========================================================================
# CÁC HÀM HỖ TRỢ CŨ (Đảm bảo chữ ký/logic đúng)
# ==========================================================================


# Wrapper cho get_all_managed_bridges để tương thích
def get_all_managed_bridges_wrapper(db_name=DB_NAME, only_enabled=False):
    """
    Wrapper (Giữ lại hàm này cho tương thích)
    """
    # Gọi hàm mới từ data_repository.py đã được import
    return get_all_managed_bridges(db_name, only_enabled)


print("Lottery Service API (lottery_service.py) đã tải thành công (V7.4).")