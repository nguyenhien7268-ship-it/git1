"""
==================================================================================
LOTTERY SERVICE API (BỘ ĐIỀU PHỐI)
==================================================================================
"""

# 1. Từ logic.db_manager
try:
    from logic.db_manager import (
        DB_NAME,
        setup_database,
        get_all_kys_from_db,
        get_results_by_ky,
        add_managed_bridge,
        get_all_managed_bridges,
        update_managed_bridge,
        delete_managed_bridge,
        load_data_ai_from_db,
        update_bridge_win_rate_batch,
        upsert_managed_bridge 
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.db_manager: {e}")

# 2. Từ logic.data_parser
try:
    from logic.data_parser import (
        parse_and_insert_data,
        parse_and_APPEND_data,
        parse_and_APPEND_data_TEXT
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.data_parser: {e}")

# 3. Từ logic.bridges_classic
try:
    from logic.bridges_classic import (
        getAllLoto_V30,
        calculate_loto_stats
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridges_classic: {e}")

# 4. Từ logic.backtester
try:
    from logic.backtester import (
        TONGHOP_TOP_CAU_N1_V5,
        TONGHOP_TOP_CAU_RATE_V5,
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_15_CAU_N1_V31_AI_V8,
        TIM_CAU_TOT_NHAT_V16,
        BACKTEST_CUSTOM_CAU_V16,
        BACKTEST_MANAGED_BRIDGES_N1,
        BACKTEST_MANAGED_BRIDGES_K2N, 
        run_and_update_all_bridge_rates,
        find_and_auto_manage_bridges,
        prune_bad_bridges,
        
        # Logic Bạc Nhớ
        BACKTEST_MEMORY_BRIDGES,
        get_top_memory_bridge_predictions, # (MỚI) Hỗ trợ BTH

        # Logic Analytics
        get_loto_stats_last_n_days,
        get_prediction_consensus,
        get_high_win_rate_predictions,
        get_loto_gan_stats,
        get_top_scored_pairs
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.backtester: {e}")

print("Lottery Service API (lottery_service.py) đã tải thành công.")