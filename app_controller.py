# Tên file: git3/app_controller.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - ĐÃ KHẮC PHỤC LỖI W503, E226)
#
import itertools
import json
import os
import time
import tkinter as tk
import traceback
import pandas as pd

# Import tường minh các hàm cần thiết từ lottery_service
try:
    from lottery_service import (
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_15_CAU_N1_V31_AI_V8,
        BACKTEST_CUSTOM_CAU_V16,
        BACKTEST_MANAGED_BRIDGES_K2N,
        BACKTEST_MANAGED_BRIDGES_N1,
        BACKTEST_MEMORY_BRIDGES,
        TIM_CAU_BAC_NHO_TOT_NHAT,
        TIM_CAU_TOT_NHAT_V16,
        find_and_auto_manage_bridges,
        find_and_auto_manage_bridges_de,
        get_all_managed_bridges,
        get_high_win_rate_predictions,
        get_historical_dashboard_data,
        get_loto_gan_stats,
        get_loto_stats_last_n_days,
        get_prediction_consensus,
        get_top_memory_bridge_predictions,
        get_top_scored_pairs,
        getAllLoto_V30,
        load_data_ai_from_db,
        parse_and_APPEND_data,
        parse_and_insert_data,
        auto_manage_bridges,
        prune_bad_bridges,
        run_ai_prediction_for_dashboard,
        run_ai_training_threaded,
        run_and_update_all_bridge_K2N_cache,
        setup_database,
    )
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Controller không tìm thấy 'lottery_service.py': {e}")
    # Giữ exit() để đảm bảo ứng dụng không chạy nếu thiếu service cốt lõi
    exit()

# Import SETTINGS
try:
    from logic.config_manager import SETTINGS
except ImportError as e:
    print(f"LỖI: Controller không thể import logic.config_manager: {e}")
    # Use centralized constants
    from logic.constants import DEFAULT_SETTINGS
    
    settings_dict = DEFAULT_SETTINGS.copy()
    settings_dict.update({
        "get_all_settings": lambda: {},
        "get": lambda k, d: d,
    })
    SETTINGS = type("obj", (object,), settings_dict)

# ===================================================================
# (PHỤC HỒI) Import hàm bị thiếu trực tiếp từ logic.data_parser
# ===================================================================
try:
    from logic.data_parser import run_and_update_from_text
except ImportError as e_import:
    error_msg = str(e_import)
    print(
        f"LỖI NGHIÊM TRỌNG: app_controller không tìm thấy logic.data_parser.run_and_update_from_text: {error_msg}"
    )

    # Tạo hàm giả để tránh crash ngay lập tức
    def run_and_update_from_text(raw_data):
        return False, "Lỗi: Không tìm thấy module logic.data_parser"

from logic.dashboard_analytics import prepare_daily_features, calculate_score_from_features

class AppController:
    """
    Lớp này chứa TOÀN BỘ logic nghiệp vụ (các hàm _task)
    được tách ra từ ui_main_window.py.
    """

    def __init__(self, app_instance):
        self.app = app_instance  # Tham chiếu đến DataAnalysisApp
        self.root = app_instance.root
        self.db_name = app_instance.db_name
        self.logger = None  # Sẽ được gán từ app_instance

        self.all_data_ai = None  # Cache dữ liệu

    def root_after(self, ms, func, *args):
        """Hàm gọi root.after an toàn (chạy trên luồng chính)."""
        self.root.after(ms, func, *args)

    # ===================================================================
    # LOGIC TẢI DỮ LIỆU (Đã di chuyển)
    # ===================================================================

    def load_data_ai_from_db_controller(self):
        """Tải (hoặc tải lại) dữ liệu A:I từ DB."""
        # (SỬA) Gọi hàm từ lottery_service
        rows_of_lists, message = load_data_ai_from_db(self.db_name)
        if rows_of_lists is None:
            self.logger.log(message)
            self.all_data_ai = None  # Xóa cache nếu lỗi
            return None
        else:
            self.logger.log(message)
            self.all_data_ai = rows_of_lists  # Lưu cache
            return rows_of_lists

    # ===================================================================
    # CÁC HÀM TÁC VỤ (Đã di chuyển từ ui_main_window.py)
    # ===================================================================

    def task_run_parsing(self, input_file):
        conn = None
        try:
            with open(input_file, "r", encoding="utf-8-sig") as f:
                raw_data = f.read()
            self.logger.log(f"Đã đọc tệp tin '{input_file}' thành công.")

            if os.path.exists(self.db_name):
                os.remove(self.db_name)
                self.logger.log(f"Đã xóa database cũ: {self.db_name}")

            conn, cursor = setup_database()
            total_records_ai = parse_and_insert_data(raw_data, conn, cursor)

            if total_records_ai == 0:
                self.logger.log(
                    "LỖI: Không thể phân tích dữ liệu. File có thể không đúng định dạng."
                )
            else:
                self.logger.log("Phân tích và chèn dữ liệu hoàn tất.")
                self.logger.log(f"- Đã chèn {total_records_ai} hàng A:I (backtest).")
                self.logger.log("- Đã xóa mọi Cầu Đã Lưu (do nạp lại).")
                self.logger.log(">>> Sẵn sàng cho Chức Năng Soi Cầu.")
                self.root_after(0, self.app.run_decision_dashboard)

        except Exception as e:
            self.logger.log(f"LỖI trong Bước 1 (Xóa Hết): {e}")
            self.logger.log(traceback.format_exc())
        finally:
            if conn:
                conn.close()
                self.logger.log("Đã đóng kết nối database.")

    def task_run_parsing_append(self, input_file):
        conn = None
        try:
            with open(input_file, "r", encoding="utf-8-sig") as f:
                raw_data = f.read()
            self.logger.log(f"Đã đọc tệp tin '{input_file}' thành công.")

            conn, cursor = setup_database()
            total_keys_added = parse_and_APPEND_data(raw_data, conn, cursor)

            if total_keys_added == 0:
                self.logger.log(
                    "Không có kỳ nào được thêm (có thể do trùng lặp hoặc file rỗng)."
                )
            else:
                self.logger.log("Thêm dữ liệu hoàn tất.")
                self.logger.log(f"- Đã thêm {total_keys_added} kỳ mới vào DB.")
                self.logger.log(">>> Sẵn sàng cho Chức Năng Soi Cầu.")
                self.root_after(0, self.app.run_decision_dashboard)

        except Exception as e:
            self.logger.log(f"LỖI trong Bước 1 (Append): {e}")
            self.logger.log(traceback.format_exc())
        finally:
            if conn:
                conn.close()
                self.logger.log("Đã đóng kết nối database.")

    def task_run_update_from_text(self, raw_data):
        try:
            # Hàm này giờ sẽ được import bởi khối try...except ở trên
            success, message = run_and_update_from_text(raw_data)

            self.logger.log(message)

            if success:
                self.root_after(0, self.app.clear_update_text_area)
                time.sleep(0.5)
                self.root_after(
                    0,
                    self.logger.log,
                    "Đã thêm dữ liệu. Tự động chạy lại Bảng Tổng Hợp...",
                )
                self.root_after(0, self.app.run_decision_dashboard)
            else:
                self.logger.log("(Không có kỳ nào được thêm hoặc có lỗi nghiêm trọng.)")

        except Exception as e:
            self.logger.log(f"LỖI khi cập nhật: {e}")
            self.logger.log(traceback.format_exc())
        finally:
            self.logger.log("Đã hoàn tất tác vụ thêm từ text.")

    def task_run_backtest(self, mode, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)
        self.logger.log(f"Đang chạy backtest trên {len(toan_bo_A_I)} hàng dữ liệu...")

        # LOGIC MỚI: Phân loại dựa trên Title
        func_to_call = None
        
        if "15" in title:
            # Xử lý cho 15 Cầu Cổ Điển
            if mode == "N1":
                func_to_call = BACKTEST_15_CAU_N1_V31_AI_V8
            else:
                func_to_call = BACKTEST_15_CAU_K2N_V30_AI_V8
        else:
            # Xử lý mặc định cho Cầu Đã Lưu (Managed Bridges)
            if mode == "N1":
                func_to_call = BACKTEST_MANAGED_BRIDGES_N1
            else:
                func_to_call = lambda a, b, c: BACKTEST_MANAGED_BRIDGES_K2N(a, b, c, history=True)
        
        results_data = func_to_call(
            toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
        )

        self.logger.log("Backtest hoàn tất. Đang mở cửa sổ kết quả...")
        self.root_after(0, self.app.show_backtest_results, title, results_data)

    def task_run_custom_backtest(self, mode, title, custom_bridge_name):
        allData = self.load_data_ai_from_db_controller()
        if not allData:
            return

        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(allData) + (ky_bat_dau_kiem_tra - 1)

        if (
            "Tổng(" in custom_bridge_name or "Hiệu(" in custom_bridge_name
        ) and mode == "K2N":
            self.logger.log("Lỗi: Cầu Bạc Nhớ chỉ hỗ trợ Backtest N1. Đang chạy N1...")
            mode = "N1"
            title = f"Test Cầu N1: {custom_bridge_name}"

        func_to_call = BACKTEST_CUSTOM_CAU_V16
        if "Tổng(" in custom_bridge_name or "Hiệu(" in custom_bridge_name:
            self.logger.log(
                "Lỗi: Chức năng test cầu Bạc Nhớ tùy chỉnh chưa được hỗ trợ."
            )
            return

        self.logger.log(f"Đã dịch: {custom_bridge_name}. Đang test...")
        results = func_to_call(
            allData, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, custom_bridge_name, mode
        )
        self.root_after(0, self.app.show_backtest_results, title, results)

    def task_run_backtest_managed_n1(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)

        results_data = BACKTEST_MANAGED_BRIDGES_N1(
            toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
        )

        self.logger.log("Backtest Cầu Đã Lưu N1 hoàn tất. Đang mở cửa sổ kết quả...")
        self.root_after(0, self.app.show_backtest_results, title, results_data)

    def task_run_backtest_managed_k2n(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)

        results_data = BACKTEST_MANAGED_BRIDGES_K2N(
            toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, history=True
        )

        self.logger.log("Backtest Cầu Đã Lưu K2N hoàn tất. Đang mở cửa sổ kết quả...")
        self.root_after(0, self.app.show_backtest_results, title, results_data)

    def task_run_decision_dashboard(self, title):
        all_data_ai = self.load_data_ai_from_db_controller()

        if not all_data_ai or len(all_data_ai) < 2:
            self.logger.log("LỖI: Cần ít nhất 2 kỳ dữ liệu để chạy Bảng Tổng Hợp.")
            self.root_after(0, self.app._on_dashboard_close)
            return

        last_row = all_data_ai[-1]

        try:
            SETTINGS.load_settings()
            n_days_stats = SETTINGS.STATS_DAYS
            n_days_gan = SETTINGS.GAN_DAYS
            high_win_thresh = SETTINGS.HIGH_WIN_THRESHOLD
        except Exception as e:
            self.logger.log(
                f"Cảnh báo: Không thể tải config: {e}. Sử dụng giá trị mặc định."
            )
            n_days_stats = 7
            n_days_gan = 15
            high_win_thresh = 47.0

        # Xử lý 'int' object has no attribute 'isdigit'
        try:
            # Thử chuyển ky sang số nguyên
            ky_int = int(last_row[0])
            next_ky = f"Kỳ {ky_int + 1}"
        except (ValueError, TypeError):
            # Nếu không phải số (hoặc là None, v.v.)
            next_ky = f"Kỳ {last_row[0]} (Next)"

        self.logger.log(
            f"... (1/5) Đang thống kê Loto Về Nhiều ({n_days_stats} ngày)..."
        )
        stats_n_day = get_loto_stats_last_n_days(all_data_ai, n=n_days_stats)

        self.logger.log("... (2/5) Đang chạy hàm Cập nhật K2N Cache (tối ưu)...")
        pending_k2n_data, _, cache_message = run_and_update_all_bridge_K2N_cache(
            all_data_ai, self.db_name
        )
        self.logger.log(f"... (Cache K2N) {cache_message}")

        self.logger.log("... (3/5) Đang đọc Consensus và Cầu Tỷ lệ Cao từ cache...")
        consensus = get_prediction_consensus()
        high_win = get_high_win_rate_predictions(threshold=high_win_thresh)

        self.logger.log(f"... (4/5) Đang tìm Lô Gan (trên {n_days_gan} kỳ)...")
        gan_stats = get_loto_gan_stats(all_data_ai, n_days=n_days_gan)

        self.logger.log("... (5/5) Đang chạy dự đoán AI (V7.0)...")
        ai_predictions, ai_message = run_ai_prediction_for_dashboard()
        self.logger.log(f"... (AI) {ai_message}")

        # --- CẬP NHẬT DỮ LIỆU CHO TAB SOI CẦU ĐỀ (V7.8) ---
        try:
            if hasattr(self.app, 'de_dashboard_tab') and self.app.de_dashboard_tab:
                self.logger.log("... (Soi Cầu Đề) Đang chuẩn bị dữ liệu...")
                # 1. Định nghĩa cột (Mapping chuẩn theo DataParser)
                # Index: 0=Ky, 1=Ngay, 2=GDB, 3=G1, ... 9=G7
                cols = ["NB", "NGAY", "GDB", "G1", "G2", "G3", "G4", "G5", "G6", "G7"]

                # 2. Lọc dữ liệu: Chỉ lấy các cột cần thiết để tạo DataFrame nhẹ
                # Lưu ý: all_data_ai là list of lists. Cần slice 10 phần tử đầu.
                data_for_df = [r[:10] for r in all_data_ai if r and len(r) >= 10]

                # 3. Tạo DataFrame
                df_de = pd.DataFrame(data_for_df, columns=cols)

                # 4. Gửi sang UI
                self.root_after(0, self.app.de_dashboard_tab.update_data, df_de)
                self.logger.log(f"... (Soi Cầu Đề) Đã nạp {len(df_de)} kỳ vào hệ thống.")
        except Exception as e_de:
            self.logger.log(f"Cảnh báo: Lỗi cập nhật Tab Soi Cầu Đề: {e_de}")
        # -----------------------------------------------------

        # --- LOGIC CHẤM ĐIỂM & HIỂN THỊ (Đã Bọc Try-Except An Toàn) ---
        try:
            self.logger.log("... (Kết thúc) Đang chấm điểm và tổng hợp quyết định...")
            
            # 1. Tính toán Top Cầu Bạc Nhớ (Có bắt lỗi riêng)
            try:
                top_memory_bridges = get_top_memory_bridge_predictions(
                    all_data_ai, last_row, top_n=5
                )
            except Exception as e_mem:
                self.logger.log(f"Lỗi tính Cầu Bạc Nhớ: {e_mem}")
                top_memory_bridges = []

            # 2. Tính toán Điểm Tổng Lực (Có bắt lỗi riêng)
            try:
                top_scores = get_top_scored_pairs(
                    stats_n_day,
                    consensus,
                    high_win,
                    pending_k2n_data,
                    gan_stats,
                    top_memory_bridges,
                    ai_predictions,
                )
            except Exception as e_score:
                self.logger.log(f"Lỗi tính Điểm Tổng Lực: {e_score}")
                top_scores = []

            self.logger.log("Phân tích hoàn tất. Đang hiển thị Bảng Quyết Định Tối Ưu...")

            # 3. Hiển thị Dashboard (Luôn chạy dù các bước trên có thể lỗi nhẹ)
            self.root_after(
                0,
                self.app._show_dashboard_window,
                next_ky,
                stats_n_day,
                n_days_stats,
                consensus,
                high_win,
                pending_k2n_data,
                gan_stats,
                top_scores,
                top_memory_bridges,
                ai_predictions,
            )
            
        except Exception as e_final:
            self.logger.log(f"LỖI NGHIÊM TRỌNG khi hiển thị Dashboard Lô: {e_final}")
            self.logger.log(traceback.format_exc())
            # Cố gắng hiển thị bảng rỗng để không treo UI
            self.root_after(0, self.app._on_dashboard_close)

    def task_run_update_all_bridge_K2N_cache(self, title):
        all_data_ai = self.load_data_ai_from_db_controller()
        if not all_data_ai:
            return

        _, _, message = run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)

        self.logger.log(message)

        if (
            self.app.bridge_manager_window
            and self.app.bridge_manager_window.winfo_exists()
        ):
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            try:
                self.root_after(
                    0, self.app.bridge_manager_window_instance.refresh_bridge_list
                )
            except Exception as e_refresh:
                self.logger.log(f"Lỗi khi tự động làm mới QL Cầu: {e_refresh}")

    def task_run_auto_find_bridges(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        # 1. Chạy Lô
        msg_loto = find_and_auto_manage_bridges(toan_bo_A_I, self.db_name)
        self.logger.log(f">>> LOTO: {msg_loto}")

        # 2. Chạy Đề (Hệ thống riêng biệt)
        self.logger.log(">>> Đang chuyển sang hệ thống Dò Cầu Đề...")
        msg_de = find_and_auto_manage_bridges_de(toan_bo_A_I, self.db_name)
        self.logger.log(f">>> ĐỀ: {msg_de}")
        self.logger.log(">>> Tác vụ hoàn tất.")

        if (
            self.app.bridge_manager_window
            and self.app.bridge_manager_window.winfo_exists()
        ):
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            self.root_after(
                0, self.app.bridge_manager_window_instance.refresh_bridge_list
            )

    def task_run_auto_prune_bridges(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        result_message = prune_bad_bridges(toan_bo_A_I, self.db_name)

        self.logger.log(f">>> {title} HOÀN TẤT:")
        self.logger.log(result_message)

        if (
            self.app.bridge_manager_window
            and self.app.bridge_manager_window.winfo_exists()
        ):
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            self.root_after(
                0, self.app.bridge_manager_window_instance.refresh_bridge_list
            )

    def task_run_auto_manage_bridges(self, title):
        """Tự động BẬT/TẮT cầu dựa trên tỷ lệ K2N."""
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        result_message = auto_manage_bridges(toan_bo_A_I, self.db_name)

        self.logger.log(f">>> {title} HOÀN TẤT:")
        self.logger.log(result_message)

        if (
            self.app.bridge_manager_window
            and self.app.bridge_manager_window.winfo_exists()
        ):
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            self.root_after(
                0, self.app.bridge_manager_window_instance.refresh_bridge_list
            )

    def task_run_smart_optimization(self, title):
        """
        Gộp chức năng: Lọc cầu yếu + Quản lý tự động + Refresh UI.
        """
        try:
            # Tải dữ liệu một lần dùng chung
            all_data = self.load_data_ai_from_db_controller()
            if not all_data:
                return

            self.logger.log(f"\n--- ⚡ BẮT ĐẦU: {title} ---")

            # BƯỚC 1: Dọn dẹp (Prune)
            self.logger.log("(1/3) Đang quét và TẮT các cầu hiệu quả kém...")
            # Gọi hàm prune từ lottery_service
            msg_prune = prune_bad_bridges(all_data, self.db_name)
            self.logger.log(f"-> Kết quả lọc: {msg_prune}")

            # BƯỚC 2: Cân bằng (Auto Manage)
            self.logger.log("(2/3) Đang kiểm tra và BẬT lại các cầu tiềm năng...")
            # Gọi hàm auto manage từ lottery_service
            msg_manage = auto_manage_bridges(all_data, self.db_name)
            self.logger.log(f"-> Kết quả quản lý: {msg_manage}")

            # BƯỚC 3: Làm mới UI
            self.logger.log("(3/3) Đang làm mới danh sách cầu...")
            if self.app.bridge_manager_window_instance:
                self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list)

            self.logger.log(f"✅ TỐI ƯU HÓA HOÀN TẤT!")

        except Exception as e:
            self.logger.log(f"LỖI TỐI ƯU HÓA: {e}")
            self.logger.log(traceback.format_exc())

    def task_run_train_ai(self, title):

        def train_callback(success, message):
            self.logger.log(f">>> {title} HOÀN TẤT:")
            self.logger.log(message)

        success, message = run_ai_training_threaded(callback=train_callback)

        if not success:
            self.logger.log(f"LỖI KHỞI CHẠY LUỒNG: {message}")
            raise Exception(f"Lỗi khởi chạy luồng Huấn luyện AI: {message}")

    def task_run_backtest_memory(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)

        results_data = BACKTEST_MEMORY_BRIDGES(
            toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra
        )

        self.logger.log("Backtest Cầu Bạc Nhớ hoàn tất. Đang mở cửa sổ kết quả...")
        self.root_after(0, self.app.show_backtest_results, title, results_data)

    def task_run_parameter_tuning(
        self, param_key, val_from, val_to, val_step, tuner_window
    ):

        def log_to_tuner(message):
            self.root_after(0, tuner_window.log, message)

        try:
            log_to_tuner("Đang tải dữ liệu A:I...")
            all_data_ai = self.load_data_ai_from_db_controller()
            if not all_data_ai or len(all_data_ai) < 2:
                log_to_tuner("LỖI: Không thể tải dữ liệu A:I.")
                return
            last_row = all_data_ai[-1]
            log_to_tuner(f"...Tải thành công {len(all_data_ai)} kỳ.")

            def float_range(start, stop, step):
                if step == 0:
                    yield start
                    return
                n = start
                while n < (stop + (step * 0.5)):
                    yield n
                    n += step

            def test_gan_days(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                for i in float_range(v_from, v_to, v_step):
                    n = int(i)
                    if n <= 0:
                        continue
                    gan_stats = get_loto_gan_stats(all_data_ai, n_days=n)
                    log_to_tuner(
                        f"Kiểm thử {p_key} = {n}: Tìm thấy {len(gan_stats)} loto gan."
                    )
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_high_win_threshold(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Cache K2N một lần để lấy dữ liệu mới nhất)...")
                run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
                log_to_tuner("... (Cache K2N hoàn tất. Bắt đầu lặp)...")
                for i in float_range(v_from, v_to, v_step):
                    high_win_bridges = get_high_win_rate_predictions(threshold=i)
                    log_to_tuner(
                        f"Kiểm thử {p_key} >= {i:.1f}%: Tìm thấy {len(high_win_bridges)} cầu đạt chuẩn."
                    )
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_auto_add_rate(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Dò Cầu V17... Rất nặng, vui lòng chờ)...")
                ky_bat_dau = 2
                ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
                results_v17 = TIM_CAU_TOT_NHAT_V16(
                    all_data_ai, ky_bat_dau, ky_ket_thuc, self.db_name
                )
                log_to_tuner("... (Chạy Dò Cầu Bạc Nhớ...)...")
                results_memory = TIM_CAU_BAC_NHO_TOT_NHAT(
                    all_data_ai, ky_bat_dau, ky_ket_thuc
                )
                combined_results = []
                if results_v17 and len(results_v17) > 1:
                    combined_results.extend(
                        [row for row in results_v17[1:] if "---" not in str(row[0])]
                    )
                if results_memory and len(results_memory) > 1:
                    combined_results.extend(
                        [row for row in results_memory[1:] if "---" not in str(row[0])]
                    )
                if not combined_results:
                    log_to_tuner("LỖI: Không dò được cầu nào.")
                    return
                log_to_tuner(
                    f"... (Dò cầu hoàn tất. Tổng cộng {len(combined_results)} cầu. Bắt đầu lặp)..."
                )
                for i in float_range(v_from, v_to, v_step):
                    count = 0
                    for row in combined_results:
                        try:
                            rate = float(str(row[3]).replace("%", ""))
                            if rate >= i:
                                count += 1
                        except (ValueError, IndexError):
                            continue
                    log_to_tuner(
                        f"Kiểm thử {p_key} >= {i:.1f}%: Sẽ thêm/cập nhật {count} cầu."
                    )
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_auto_prune_rate(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Cache K2N một lần để lấy dữ liệu mới nhất)...")
                run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
                log_to_tuner("... (Cache K2N hoàn tất. Bắt đầu lặp)...")
                enabled_bridges = get_all_managed_bridges(
                    self.db_name, only_enabled=True
                )
                if not enabled_bridges:
                    log_to_tuner("LỖI: Không có cầu nào đang Bật để kiểm thử.")
                    return
                for i in float_range(v_from, v_to, v_step):
                    count = 0
                    for bridge in enabled_bridges:
                        try:
                            rate_str = str(bridge.get("win_rate_text", "100%")).replace(
                                "%", ""
                            )
                            if not rate_str or rate_str == "N/A":
                                continue
                            rate = float(rate_str)
                            if rate < i:
                                count += 1
                        except ValueError:
                            continue
                    log_to_tuner(f"Kiểm thử {p_key} < {i:.1f}%: Sẽ TẮT {count} cầu.")
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_k2n_risk_logic(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Cache K2N một lần để lấy dữ liệu nền)...")
                pending_k2n, _, _ = run_and_update_all_bridge_K2N_cache(
                    all_data_ai, self.db_name
                )
                stats_n_day = get_loto_stats_last_n_days(all_data_ai)
                consensus = get_prediction_consensus()
                high_win = get_high_win_rate_predictions()
                gan_stats = get_loto_gan_stats(all_data_ai)
                top_memory = get_top_memory_bridge_predictions(all_data_ai, last_row)
                ai_preds, _ = run_ai_prediction_for_dashboard()
                log_to_tuner("... (Dữ liệu nền hoàn tất. Bắt đầu lặp)...")

                original_value = SETTINGS.get_all_settings().get(p_key)
                for i in float_range(v_from, v_to, v_step):
                    val = i
                    if p_key == "K2N_RISK_START_THRESHOLD":
                        val = int(i)
                    setattr(SETTINGS, p_key, val)
                    top_scores = get_top_scored_pairs(
                        stats_n_day,
                        consensus,
                        high_win,
                        pending_k2n,
                        gan_stats,
                        top_memory,
                        ai_preds,
                    )
                    if not top_scores:
                        log_to_tuner(
                            f"Kiểm thử {p_key} = {val}: Không có cặp nào đạt điểm."
                        )
                    else:
                        top_score_item = top_scores[0]
                        log_to_tuner(
                            f"Kiểm thử {p_key} = {val}: Top 1 là {top_score_item['pair']} (Điểm: {top_score_item['score']})"
                        )
                if original_value is not None:
                    setattr(SETTINGS, p_key, original_value)
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            # --- Bộ điều phối kiểm thử ---
            if param_key == "GAN_DAYS":
                test_gan_days(param_key, val_from, val_to, val_step)
            elif param_key == "HIGH_WIN_THRESHOLD":
                test_high_win_threshold(param_key, val_from, val_to, val_step)
            elif param_key == "AUTO_ADD_MIN_RATE":
                test_auto_add_rate(param_key, val_from, val_to, val_step)
            elif param_key == "AUTO_PRUNE_MIN_RATE":
                test_auto_prune_rate(param_key, val_from, val_to, val_step)
            elif (
                param_key == "K2N_RISK_START_THRESHOLD"
                or param_key == "K2N_RISK_PENALTY_PER_FRAME"
            ):
                test_k2n_risk_logic(param_key, val_from, val_to, val_step)
            else:
                log_to_tuner(f"Lỗi: Chưa định nghĩa logic kiểm thử cho {param_key}")

        except Exception as e:
            log_to_tuner(f"LỖI: {e}")
            log_to_tuner(traceback.format_exc())
        finally:
            self.root_after(0, tuner_window.run_button.config, {"state": tk.NORMAL})

    def task_run_strategy_optimization(
        self, strategy, days_to_test, param_ranges, optimizer_tab
    ):

        def log_to_optimizer(message):
            self.root_after(0, optimizer_tab.log, message)

        def update_tree_results_threadsafe(results_list):
            optimizer_tab.clear_results_tree()
            for i, (rate, hits, params_str, config_dict_str) in enumerate(results_list):
                rate_str = f"{rate * 100:.1f}%"
                tags = ("best",) if i == 0 else ()
                tags_with_data = (config_dict_str,) + tags
                optimizer_tab.tree.insert(
                    "", tk.END, values=(rate_str, hits, params_str), tags=tags_with_data
                )
            optimizer_tab.apply_button.config(state=tk.NORMAL)

        def float_range(start, stop, step):
            if step == 0:
                yield start
                return
            n = start
            while n < (stop + (step * 0.5)):
                yield n
                n += step

        def generate_combinations(param_ranges, original_settings):
            param_lists = []
            config_keys = list(param_ranges.keys())
            static_keys = [k for k in original_settings.keys() if k not in config_keys]

            for key in config_keys:
                v_from, v_to, v_step = param_ranges[key]
                if isinstance(original_settings[key], int):
                    param_lists.append([
                        (key, int(i))
                        for i in float_range(v_from, v_to, v_step)
                        if i >= 0
                    ])
                else:
                    param_lists.append([
                        (key, round(i, 2))
                        for i in float_range(v_from, v_to, v_step)
                        if i >= 0
                    ])
            if not param_lists:
                return []

            combinations = []
            for combo in itertools.product(*param_lists):
                temp_config = {}
                for static_key in static_keys:
                    temp_config[static_key] = original_settings[static_key]
                for key, value in combo:
                    temp_config[key] = value
                combinations.append(temp_config)
            return combinations

        try:
            log_to_optimizer("Đang tải toàn bộ dữ liệu A:I...")
            all_data_ai = self.load_data_ai_from_db_controller()
            if not all_data_ai or len(all_data_ai) < days_to_test + 50:
                log_to_optimizer(f"LỖI: Cần ít nhất {days_to_test + 50} kỳ dữ liệu để kiểm thử.")
                return
            log_to_optimizer(f"...Tải dữ liệu thành công ({len(all_data_ai)} kỳ).")

            original_settings = SETTINGS.get_all_settings()
            combinations = generate_combinations(param_ranges, original_settings)
            total_combos = len(combinations)
            if total_combos == 0:
                log_to_optimizer("Lỗi: Không tạo được tổ hợp kiểm thử.")
                return
            log_to_optimizer(f"Đã tạo {total_combos} tổ hợp. Bắt đầu chuẩn bị features cache...")

            # Phase 1: Precompute features cho từng ngày trong days_to_test
            cached_features = []
            offset = len(all_data_ai) - days_to_test
            for i in range(days_to_test):
                day_index = offset + i
                log_to_optimizer(f"Đang chuẩn bị dữ liệu ngày {day_index + 1 - offset}/{days_to_test} ...")
                try:
                    features = prepare_daily_features(all_data_ai, day_index)
                    cached_features.append(features)
                except Exception as e:
                    log_to_optimizer(f"Lỗi khi prepare features ngày {i+1}: {e}")
                    cached_features.append(None)

            results_list = []
            log_to_optimizer(f"Chuẩn bị xong features. Bắt đầu Loop tối ưu ({total_combos} tổ hợp)...")
            for ci, config in enumerate(combinations):
                log_to_optimizer(f"--- Đang kiểm thử [{ci + 1}/{total_combos}]: {config} ---")
                total_hits = 0
                days_tested = 0
                for fidx, features in enumerate(cached_features):
                    if not features:
                        continue
                    try:
                        top_scores = calculate_score_from_features(features, config)
                    except Exception as e:
                        log_to_optimizer(f"Lỗi tính score ngày {fidx+1}: {e}")
                        continue
                    days_tested += 1
                    # Logic tính hit: lấy top 1 cặp, check xuất hiện trong actual
                    if not top_scores:
                        continue
                    top1 = top_scores[0]
                    # Lấy actual_lotos của ngày đó
                    last_row = features['recent_data'][-1] if 'recent_data' in features else None
                    if last_row:
                        actual_lotos = set(getAllLoto_V30(last_row))
                        loto1, loto2 = top1['pair'].split('-')
                        if loto1 in actual_lotos or loto2 in actual_lotos:
                            total_hits += 1
                rate = total_hits / days_tested if days_tested > 0 else 0
                hits_str = f"{total_hits}/{days_tested}"
                import json
                config_str_json = json.dumps(config)
                params_str_display = ", ".join(
                    [f"{key}: {value}" for key, value in config.items() if key in param_ranges]
                )
                results_list.append((rate, hits_str, params_str_display, config_str_json))
                log_to_optimizer(f"-> Kết quả: {hits_str} ({rate * 100:.1f}%)")
            log_to_optimizer("Đang sắp xếp kết quả...")
            results_list.sort(key=lambda x: x[0], reverse=True)
            self.root_after(0, update_tree_results_threadsafe, results_list)
            log_to_optimizer("--- HOÀN TẤT TỐI ƯU HÓA ---")
        except Exception as e:
            log_to_optimizer(f"LỖI: {e}")
            import traceback
            log_to_optimizer(traceback.format_exc())
        finally:
            self.root_after(0, optimizer_tab.run_button.config, {"state": tk.NORMAL})
