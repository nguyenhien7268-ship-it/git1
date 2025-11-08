"""
==================================================================================
LOTTERY SERVICE API (BỘ ĐIỀU PHỐI)
==================================================================================
Vai trò: 
- File này là "cầu nối" duy nhất giữa Giao diện (app.py) và Gói Logic (/logic).
- Nó import tất cả các hàm cần thiết từ 6 file logic chuyên biệt.
- Nó "tái xuất" (re-export) tất cả các hàm này để app.py có thể gọi 
  một cách đơn giản.

Bất kỳ logic nghiệp vụ phức tạp nào (như logic Bảng Tổng Hợp) 
đều được xử lý BÊN TRONG gói /logic trước khi được đưa ra đây.
"""

# 1. Từ logic.db_manager
# (Các hàm CRUD cơ bản với CSDL)
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
        update_bridge_win_rate_batch # (MỚI) Đã thêm ở Giai đoạn 3
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.db_manager: {e}")

# 2. Từ logic.data_parser
# (Các hàm nạp dữ liệu JSON/Text)
try:
    from logic.data_parser import (
        parse_and_insert_data,
        parse_and_APPEND_data,
        parse_and_APPEND_data_TEXT
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.data_parser: {e}")

# 3. Từ logic.bridges_classic
# (Các hàm hỗ trợ mà app.py cần, ví dụ: để hiển thị Cửa sổ Tra Cứu)
try:
    from logic.bridges_classic import (
        getAllLoto_V30,
        calculate_loto_stats
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.bridges_classic: {e}")

# 4. Từ logic.backtester
# (Các hàm phân tích Backtest nặng)
try:
    from logic.backtester import (
        TONGHOP_TOP_CAU_N1_V5,
        TONGHOP_TOP_CAU_RATE_V5,
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_15_CAU_N1_V31_AI_V8,
        TIM_CAU_TOT_NHAT_V16,
        BACKTEST_CUSTOM_CAU_V16,
        BACKTEST_MANAGED_BRIDGES_N1,
        BACKTEST_MANAGED_BRIDGES_K2N, # <-- (ĐÃ SỬA LỖI: Thêm dấu phẩy ở đây)
        run_and_update_all_bridge_rates
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.backtester: {e}")

# 5. Từ logic.analytics
# (Các hàm phân tích cho Bảng Tổng Hợp)
try:
    from logic.analytics import (
        get_loto_stats_last_n_days,
        get_prediction_consensus,
        get_high_win_rate_predictions,
        get_loto_gan_stats,  # <-- (THÊM DÒNG NÀY)
        get_top_scored_pairs  # <-- (THÊM DÒNG NÀY)
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import logic.analytics: {e}")

print("Lottery Service API (lottery_service.py) đã tải thành công.")