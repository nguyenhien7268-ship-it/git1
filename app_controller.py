# Tên file: code1/app_controller.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - V7.2 MP & MLOps & Caching UPGRADE)
#
import traceback
import time
import json
import itertools
import os # Cần cho việc lấy số lõi CPU

# (V7.2 MP) Thêm import cho Multi-Processing
import multiprocessing 
from multiprocessing import Process, Queue
from multiprocessing.queues import Empty
from concurrent.futures import ProcessPoolExecutor, as_completed

# (MỚI) Import tkinter chỉ để lấy hằng số, nhưng cách tốt hơn là không import
import tkinter as tk # Cần để sử dụng tk.NORMAL/tk.END trong các hàm cũ.

# Import toàn bộ logic từ file lottery_service.py
try:
    from lottery_service import *
except ImportError:
    print("LỖI NGHIÊM TRỌNG: Controller không tìm thấy 'lottery_service.py'.")
    exit()

# Import SETTINGS
try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: Controller không thể import logic.config_manager.")
    # Sử dụng giá trị mặc định (Fallback)
    SETTINGS = type('obj', (object,), {
        'STATS_DAYS': 7, 'GAN_DAYS': 15, 'HIGH_WIN_THRESHOLD': 47.0,
        'AUTO_ADD_MIN_RATE': 50.0, 'AUTO_PRUNE_MIN_RATE': 40.0,
        'K2N_RISK_START_THRESHOLD': 4, 'K2N_RISK_PENALTY_PER_FRAME': 0.5,
        'get_all_settings': lambda: {},
        'get': lambda k, d: d,
        'update_setting': lambda k, v: (False, "SETTINGS object not initialized")
    })

# ===================================================================
# (V7.2 MP) HÀM HỖ TRỢ VÀ HÀM MỤC TIÊU CHO TỐI ƯU HÓA (Đa tiến trình)
# ĐƯỢC ĐỊNH NGHĨA Ở TOP-LEVEL (NGOÀI CLASS) ĐỂ CÓ THỂ PICKLE
# ===================================================================

def _float_range(start, stop, step):
    """Hàm helper (top-level) để tạo range cho số thực."""
    if step == 0: yield start; return
    n = start
    while n < (stop + (step * 0.5)):
        yield n
        n += step

def _generate_combinations(param_ranges, original_settings):
    """Hàm helper (top-level) để tạo các tổ hợp tham số."""
    param_lists = []
    config_keys = list(param_ranges.keys())
    static_keys = [k for k in original_settings.keys() if k not in config_keys]
    
    for key in config_keys:
        v_from, v_to, v_step = param_ranges[key]
        if isinstance(original_settings[key], int):
            param_lists.append([(key, int(i)) for i in _float_range(v_from, v_to, v_step) if i >= 0])
        else:
            param_lists.append([(key, round(i, 2)) for i in _float_range(v_from, v_to, v_step) if i >= 0])
    if not param_lists: return []

    combinations = []
    for combo in itertools.product(*param_lists):
        temp_config = {}
        for static_key in static_keys:
            temp_config[static_key] = original_settings[static_key]
        for key, value in combo:
            temp_config[key] = value
        combinations.append(temp_config)
    return combinations

def _run_single_config_test(job_payload):
    """
    (V7.2 MP) HÀM LÕI (WORKER)
    Hàm này được thực thi bởi các tiến trình con trong ProcessPoolExecutor.
    Nó chạy backtest cho MỘT tổ hợp 'config'.
    (V7.2 Caching) Nâng cấp để nhận cache.
    """
    try:
        # Giải nén payload (MỚI: thêm optimization_cache)
        all_data_ai, strategy, days_to_test, config, param_ranges, optimization_cache = job_payload
        
        # *** QUAN TRỌNG: Import logic nghiệp vụ BÊN TRONG HÀM WORKER ***
        from logic.dashboard_analytics import get_historical_dashboard_data
        from logic.bridges.bridges_classic import getAllLoto_V30
        
        # 1. Sao chép logic chạy backtest cho 1 config
        total_hits = 0
        days_tested = 0
        
        for day_offset in range(days_to_test):
            actual_index = len(all_data_ai) - 1 - day_offset
            day_index = actual_index - 1
            if day_index < 50: continue
            days_tested += 1
            
            actual_row = all_data_ai[actual_index]
            actual_loto_set = set(getAllLoto_V30(actual_row))
            
            # (MỚI V7.2 Caching) Truyền cache vào hàm worker
            top_scores = get_historical_dashboard_data(
                all_data_ai, 
                day_index, 
                config, 
                optimization_cache=optimization_cache # <-- SỬ DỤNG CACHE
            )
            
            if not top_scores: continue
                
            if strategy == "Tối ưu Top 1 (N1)":
                top_1_pair_str = top_scores[0]['pair']
                loto1, loto2 = top_1_pair_str.split('-')
                if loto1 in actual_loto_set or loto2 in actual_loto_set:
                    total_hits += 1
            
            elif strategy == "Tối ưu Top 3 (N1)":
                top_3_pairs = {item['pair'] for item in top_scores[:3]}
                for pair_str in top_3_pairs:
                    loto1, loto2 = pair_str.split('-')
                    if loto1 in actual_loto_set or loto2 in actual_loto_set:
                        total_hits += 1; break 
                        
        # 2. Chuẩn bị kết quả
        rate = total_hits / days_tested if days_tested > 0 else 0
        hits_str = f"{total_hits}/{days_tested}"
        config_str_json = json.dumps(config)
        params_str_display = ", ".join([f"{key}: {value}" for key, value in config.items() if key in param_ranges])
        
        return (rate, hits_str, params_str_display, config_str_json)
        
    except Exception as e:
        error_msg = f"Lỗi worker: {e}\n{traceback.format_exc()}"
        return ("error", error_msg, str(config), "{}")


def _strategy_optimization_process_target(result_queue, all_data_ai, strategy, days_to_test, param_ranges, original_settings_backup):
    """
    (V7.2 MP) HÀM QUẢN LÝ (MANAGER PROCESS)
    (V7.2 Caching) Nâng cấp để TẢI cache và TRUYỀN cache cho worker.
    """
    
    def log_to_queue(message):
        """Gửi log về UI thread qua Queue."""
        result_queue.put(('log', message))

    try:
        # (MỚI V7.2 Caching) Tải cache trước khi bắt đầu
        import joblib
        from logic.dashboard_analytics import CACHE_FILE_PATH # Import path
        
        log_to_queue(f"Đang tải Cache Tối ưu hóa từ {CACHE_FILE_PATH}...")
        if not os.path.exists(CACHE_FILE_PATH):
            log_to_queue("LỖI NGHIÊM TRỌNG: Không tìm thấy file 'optimization_cache.joblib'.")
            log_to_queue(">>> Vui lòng chạy tác vụ 'Tạo Cache Tối ưu hóa' trước.")
            result_queue.put(('error', "Không tìm thấy file cache."))
            return
            
        optimization_cache = joblib.load(CACHE_FILE_PATH)
        log_to_queue("Tải Cache thành công. Đang tạo các tổ hợp kiểm thử...")

        combinations = _generate_combinations(param_ranges, original_settings_backup)
        total_combos = len(combinations)
        
        if total_combos == 0:
            result_queue.put(('error', "Lỗi: Không tạo được tổ hợp kiểm thử."))
            return
            
        log_to_queue(f"Đã tạo {total_combos} tổ hợp. Chuẩn bị Process Pool...")
        
        # Tạo danh sách các "job" (payload) - (MỚI: Thêm optimization_cache)
        jobs = []
        for config in combinations:
            jobs.append((all_data_ai, strategy, days_to_test, config, param_ranges, optimization_cache))

        results_list = []
        jobs_completed = 0
        
        num_workers = max(1, (os.cpu_count() or 4) - 1)
        log_to_queue(f"Khởi chạy {num_workers} tiến trình con để xử lý {total_combos} jobs (nhanh)...")

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_job = {executor.submit(_run_single_config_test, job): job for job in jobs}
            
            for future in as_completed(future_to_job):
                result_tuple = future.result()
                
                if result_tuple[0] == "error":
                    log_to_queue(f"LỖI JOB: {result_tuple[2]}\n{result_tuple[1]}")
                else:
                    results_list.append(result_tuple)
                    
                jobs_completed += 1
                
                if jobs_completed % 100 == 0 or jobs_completed == total_combos: # Cập nhật nhanh hơn
                     result_queue.put(('progress', jobs_completed, total_combos))

        log_to_queue("Tất cả jobs đã hoàn thành. Đang sắp xếp kết quả...")
        results_list.sort(key=lambda x: x[0], reverse=True)
        
        log_to_queue("Khôi phục cài đặt gốc...")
        try:
            from logic.config_manager import SETTINGS
            for key, value in original_settings_backup.items():
                setattr(SETTINGS, key, value)
            log_to_queue("Đã khôi phục cài đặt (trong bộ nhớ process).")
        except Exception as e_cfg:
            log_to_queue(f"Lỗi khôi phục settings: {e_cfg}")

        result_queue.put(('result', results_list))

    except Exception as e:
        error_msg = f"Lỗi nghiêm trọng trong Process Quản lý:\n{e}\n{traceback.format_exc()}"
        result_queue.put(('error', error_msg))

# ===================================================================
# CLASS APP CONTROLLER
# ===================================================================

class AppController:
    """
    Lớp này chứa TOÀN BỘ logic nghiệp vụ (các hàm _task) 
    """
    def __init__(self, app_instance):
        self.app = app_instance # Tham chiếu đến DataAnalysisApp
        self.root = app_instance.root
        self.db_name = DB_NAME if 'DB_NAME' in globals() else "xo_so_prizes_all_logic.db"
        self.logger = None 
        
        self.all_data_ai = None # Cache dữ liệu
        
        # (V7.2 MP) Biến theo dõi tiến trình
        self.optimization_process = None
        self.cache_gen_process = None # (MỚI V7.2 Caching)

    def root_after(self, ms, func, *args):
        """Hàm gọi root.after an toàn (chạy trên luồng chính)."""
        self.root.after(ms, func, *args)
        
    # ===================================================================
    # LOGIC TẢI DỮ LIỆU
    # ===================================================================

    def load_data_ai_from_db_controller(self):
        """Tải (hoặc tải lại) dữ liệu A:I từ DB."""
        rows_of_lists, message = load_data_ai_from_db(self.db_name) 
        if rows_of_lists is None:
            self.logger.log(message)
            self.all_data_ai = None 
            return None
        else:
            self.logger.log(message)
            self.all_data_ai = rows_of_lists 
            return rows_of_lists

    # ===================================================================
    # CÁC HÀM TÁC VỤ
    # ===================================================================

    def task_run_parsing(self, input_file):
        conn = None 
        try:
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                raw_data = f.read()
            self.logger.log(f"Đã đọc tệp tin '{input_file}' thành công.")
            
            if os.path.exists(DB_NAME):
                os.remove(DB_NAME)
                self.logger.log(f"Đã xóa database cũ: {DB_NAME}")

            conn, cursor = setup_database()
            total_records_ai = parse_and_insert_data(raw_data, conn, cursor)
            
            if total_records_ai == 0:
                self.logger.log("LỖI: Không thể phân tích dữ liệu. File có thể không đúng định dạng.")
            else:
                self.logger.log(f"Phân tích và chèn dữ liệu hoàn tất.")
                self.logger.log(f"- Đã chèn {total_records_ai} hàng A:I (backtest).")
                self.logger.log(f"- Đã xóa mọi Cầu Đã Lưu (do nạp lại).")
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
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                raw_data = f.read()
            self.logger.log(f"Đã đọc tệp tin '{input_file}' thành công.")
            
            conn, cursor = setup_database()
            total_keys_added = parse_and_APPEND_data(raw_data, conn, cursor)
            
            if total_keys_added == 0:
                self.logger.log("Không có kỳ nào được thêm (có thể do trùng lặp hoặc file rỗng).")
            else:
                self.logger.log(f"Thêm dữ liệu hoàn tất.")
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

    # (MỚI V7.2 MLOps) Hàm helper để kiểm tra AI sau khi thêm dữ liệu
    def _check_model_drift_after_update(self):
        """
        (MLOps) Được gọi sau khi thêm dữ liệu mới để kiểm tra Model Drift.
        """
        self.logger.log("[Kiểm tra AI] Đang đánh giá mô hình sau khi thêm dữ liệu...")
        
        # run_model_evaluation được import từ lottery_service
        eval_status, eval_msg = run_model_evaluation() 
        
        self.logger.log(f"[Kiểm tra AI] {eval_msg}")
        
        if eval_status == 'WARN':
            # Nếu phát hiện sụt giảm, ghi log cảnh báo lớn
            self.logger.log("======================================")
            self.logger.log("CẢNH BÁO: ĐỘ CHÍNH XÁC AI GIẢM!")
            self.logger.log("Phát hiện độ chính xác AI có thể đã giảm sau khi thêm dữ liệu mới (Model Drift).")
            self.logger.log(">>> ĐỀ XUẤT: Chạy lại 'Huấn luyện AI' để cập nhật mô hình.")
            self.logger.log("======================================")

    def task_run_update_from_text(self, raw_data):
        try:
            success, message = run_and_update_from_text(raw_data)
            
            self.logger.log(message) 
            
            if success:
                self.root_after(0, self.app.clear_update_text_area) 
                time.sleep(0.5) 
                self.root_after(0, self.logger.log, "Đã thêm dữ liệu. Tự động chạy lại Bảng Tổng Hợp...")
                self.root_after(0, self.app.run_decision_dashboard) 
                
                # (MỚI V7.2 MLOps) Lên lịch kiểm tra AI sau 1.5s (để dashboard chạy xong)
                self.root_after(1500, self._check_model_drift_after_update)
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

        func_to_call = BACKTEST_MANAGED_BRIDGES_N1 if mode == 'N1' else (lambda a, b, c: BACKTEST_MANAGED_BRIDGES_K2N(a, b, c, history=True))
        results_data = func_to_call(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.logger.log(f"Backtest hoàn tất. Đang mở cửa sổ kết quả...")
        self.root_after(0, self.app.show_backtest_results, title, results_data) 

    def task_run_custom_backtest(self, mode, title, custom_bridge_name):
        allData = self.load_data_ai_from_db_controller() 
        if not allData:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(allData) + (ky_bat_dau_kiem_tra - 1)
        
        if ("Tổng(" in custom_bridge_name or "Hiệu(" in custom_bridge_name) and mode == 'K2N':
             self.logger.log("Lỗi: Cầu Bạc Nhớ chỉ hỗ trợ Backtest N1. Đang chạy N1...")
             mode = 'N1'
             title = f"Test Cầu N1: {custom_bridge_name}"

        func_to_call = BACKTEST_CUSTOM_CAU_V16
        if "Tổng(" in custom_bridge_name or "Hiệu(" in custom_bridge_name:
            self.logger.log("Lỗi: Chức năng test cầu Bạc Nhớ tùy chỉnh chưa được hỗ trợ.")
            return 
            
        self.logger.log(f"Đã dịch: {custom_bridge_name}. Đang test...")
        results = func_to_call(
            allData, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra,
            custom_bridge_name, mode
        )
        self.root_after(0, self.app.show_backtest_results, title, results) 

    def task_run_backtest_managed_n1(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller() 
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)

        results_data = BACKTEST_MANAGED_BRIDGES_N1(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.logger.log(f"Backtest Cầu Đã Lưu N1 hoàn tất. Đang mở cửa sổ kết quả...")
        self.root_after(0, self.app.show_backtest_results, title, results_data) 

    def task_run_backtest_managed_k2n(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller() 
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)

        results_data = BACKTEST_MANAGED_BRIDGES_K2N(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, history=True)
        
        self.logger.log(f"Backtest Cầu Đã Lưu K2N hoàn tất. Đang mở cửa sổ kết quả...")
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
            k2n_risk_start_threshold = SETTINGS.K2N_RISK_START_THRESHOLD 
        except Exception as e:
             self.logger.log(f"Cảnh báo: Không thể tải config: {e}. Sử dụng giá trị mặc định.")
             n_days_stats = 7
             n_days_gan = 15
             high_win_thresh = 47.0
             k2n_risk_start_threshold = 4 
             
        next_ky = f"Kỳ {int(last_row[0]) + 1}" if last_row[0].isdigit() else f"Kỳ {last_row[0]} (Next)"

        self.logger.log(f"... (1/5) Đang thống kê Loto Về Nhiều ({n_days_stats} ngày)...")
        stats_n_day = get_loto_stats_last_n_days(all_data_ai, n=n_days_stats)
        
        self.logger.log("... (2/5) Đang chạy hàm Cập nhật K2N Cache (tối ưu)...")
        pending_k2n_data, cache_message = run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
        self.logger.log(f"... (Cache K2N) {cache_message}")
        
        self.logger.log("... (3/5) Đang đọc Consensus và Cầu Tỷ lệ Cao từ cache...")
        consensus = get_prediction_consensus()
        high_win = get_high_win_rate_predictions(threshold=high_win_thresh)

        self.logger.log(f"... (4/5) Đang tìm Lô Gan (trên {n_days_gan} kỳ)...")
        gan_stats = get_loto_gan_stats(all_data_ai, n_days=n_days_gan)
        
        self.logger.log("... (5/5) Đang chạy dự đoán AI (V7.0)...")
        ai_predictions, ai_message = run_ai_prediction_for_dashboard()
        self.logger.log(f"... (AI) {ai_message}")

        self.logger.log("... (MLOps) Đang kiểm tra độ chính xác mô hình AI...")
        eval_status, eval_msg = run_model_evaluation() 
        self.logger.log(f"... (MLOps) {eval_msg}")

        self.logger.log("... (Kết thúc) Đang chấm điểm và tổng hợp quyết định...")
        top_memory_bridges = get_top_memory_bridge_predictions(all_data_ai, last_row, top_n=5) 
        top_scores = get_top_scored_pairs(
            stats_n_day, consensus, high_win, 
            pending_k2n_data, gan_stats,
            top_memory_bridges, ai_predictions
        )
        
        self.logger.log("Phân tích hoàn tất. Đang hiển thị Bảng Quyết Định Tối Ưu...")
        
        self.root_after(0, self.app._show_dashboard_window, 
            next_ky, stats_n_day, n_days_stats, 
            consensus, high_win, pending_k2n_data, 
            gan_stats, top_scores, top_memory_bridges,
            ai_predictions,
            n_days_gan, 
            k2n_risk_start_threshold
        )

    def task_run_update_all_bridge_K2N_cache(self, title):
        all_data_ai = self.load_data_ai_from_db_controller()
        if not all_data_ai:
            return 

        _, message = run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
        
        self.logger.log(message)
        
        if self.app.bridge_manager_window and self.app.bridge_manager_window.winfo_exists():
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            try:
                self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list) 
            except Exception as e_refresh:
                self.logger.log(f"Lỗi khi tự động làm mới QL Cầu: {e_refresh}")

    def task_run_auto_find_bridges(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        result_message = find_and_auto_manage_bridges(toan_bo_A_I, self.db_name)
        
        self.logger.log(f">>> {title} HOÀN TẤT:")
        self.logger.log(result_message)
        
        if self.app.bridge_manager_window and self.app.bridge_manager_window.winfo_exists():
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list)

    def task_run_auto_prune_bridges(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        result_message = prune_bad_bridges(toan_bo_A_I, self.db_name)
        
        self.logger.log(f">>> {title} HOÀN TẤT:")
        self.logger.log(result_message)
        
        if self.app.bridge_manager_window and self.app.bridge_manager_window.winfo_exists():
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list)

    # (V7.2 MP) HÀM KIỂM TRA TRẠNG THÁI (Huấn luyện AI)
    def _check_ai_training_status(self, process, queue, title):
        """
        Kiểm tra trạng thái của tiến trình huấn luyện AI.
        """
        try:
            while True:
                message = queue.get_nowait()
                msg_type, payload = message[0], message[1:]
                
                if msg_type == 'done':
                    success, message = payload
                    self.logger.log(f">>> {title} HOÀN TẤT:")
                    self.logger.log(message)
                    try:
                        queue.close(); process.join()
                    except Exception as e:
                        self.logger.log(f"Cảnh báo: Lỗi khi đóng Process/Queue AI: {e}")
                    return # Dừng
        except Empty:
            pass
        except Exception as e:
            self.logger.log(f"Lỗi đọc Queue AI: {e}")

        if process.is_alive():
            self.root_after(500, self._check_ai_training_status, process, queue, title)
        else:
            self.logger.log("LỖI: Tiến trình Huấn luyện AI đã dừng đột ngột.")
            try: queue.close(); process.join()
            except: pass

    def task_run_train_ai(self, title):
        process, queue, success, message = run_ai_training_threaded()
        
        if not success:
            self.logger.log(f"LỖI KHỞI CHẠY TIẾN TRÌNH: {message}")
            return 

        self.logger.log(message)
        self.root_after(500, self._check_ai_training_status, process, queue, title)
        
    def task_run_backtest_memory(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)
        
        results_data = BACKTEST_MEMORY_BRIDGES(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.logger.log(f"Backtest Cầu Bạc Nhớ hoàn tất. Đang mở cửa sổ kết quả...")
        self.root_after(0, self.app.show_backtest_results, title, results_data)
        
    # ===================================================================
    # CÁC HÀM ĐIỀU KHIỂN LOGIC (MVC Delegation)
    # ===================================================================
    
    def get_current_setting_value(self, setting_key):
        try:
            return SETTINGS.get_all_settings().get(setting_key)
        except Exception:
            self.logger.log(f"Cảnh báo: Không thể đọc giá trị hiện tại của setting '{setting_key}'.")
            return None

    def task_load_all_settings(self, settings_view):
        try:
            settings_data = SETTINGS.get_all_settings()
            self.root_after(0, settings_view.populate_settings, settings_data)
        except Exception as e:
            self.logger.log(f"LỖI trong task_load_all_settings: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, self.app._show_error_dialog, 
                            "Lỗi Tải Cấu Hình", 
                            f"Lỗi khi tải cấu hình: {e}", 
                            settings_view.window)

    def task_save_all_settings(self, new_settings_dict, parent_widget):
        try:
            success_count = 0
            for key, value in new_settings_dict.items():
                success, msg = SETTINGS.update_setting(key, value)
                if success: 
                    self.logger.log(f" - Đã lưu: {key} = {value}")
                    success_count += 1
                else: 
                    self.logger.log(f" - LỖI LƯU: {msg}")
            
            if success_count > 0:
                 self.root_after(0, self.app._show_save_success_dialog, 
                                 "Thành công", 
                                 f"Đã lưu thành công {success_count} tham số!", 
                                 parent_widget)
            else:
                 self.root_after(0, self.app._show_error_dialog, 
                                 "Thất bại", 
                                 "Không có tham số nào được lưu thành công.", 
                                 parent_widget)

        except Exception as e:
             self.root_after(0, self.app._show_error_dialog, 
                             "Lỗi", 
                             f"Lỗi khi lưu cấu hình: {e}", 
                             parent_widget)
             self.logger.log(f"LỖI trong task_save_all_settings: {e}")
             self.logger.log(traceback.format_exc())
        finally:
            if hasattr(self.app, 'settings_window') and self.app.settings_window:
                self.root_after(0, self.app.settings_window._re_enable_save_button)
            
    def task_apply_optimized_settings(self, config_dict, optimizer_window):
        """Áp dụng và lưu cấu hình tối ưu hóa vào config.json."""
        def log_to_optimizer(message):
            self.root_after(0, self.app._log_to_optimizer, message, optimizer_window)

        try:
            log_to_optimizer("Đang áp dụng cấu hình mới...")
            
            success_count = 0
            for key, value in config_dict.items():
                success, msg = SETTINGS.update_setting(key, value)
                if success: 
                    log_to_optimizer(f" - Đã lưu: {key} = {value}")
                    success_count += 1
                else: 
                    log_to_optimizer(f" - LỖI LƯU: {msg}")
            
            log_to_optimizer("--- Áp dụng hoàn tất! ---")
            
            if success_count > 0:
                 self.root_after(0, self.app._show_save_success_dialog, 
                                 "Thành công", 
                                 "Đã áp dụng và lưu cấu hình mới!", 
                                 optimizer_window)
            else:
                 self.root_after(0, self.app._show_error_dialog, 
                                 "Thất bại", 
                                 "Không có cấu hình nào được lưu thành công.", 
                                 optimizer_window)

        except Exception as e:
             self.root_after(0, self.app._show_error_dialog, 
                             "Lỗi", 
                             f"Lỗi khi áp dụng cấu hình: {e}", 
                             optimizer_window)
             self.logger.log(f"LỖI trong task_apply_optimized_settings: {e}")
             self.logger.log(traceback.format_exc())

    def task_save_bridge(self, bridge_name, description, win_rate, parent_widget):
        try:
            success, message = upsert_managed_bridge(bridge_name, description, win_rate) 
            
            if success:
                self.logger.log(f"LƯU/CẬP NHẬT CẦU: {message}")
                self.root_after(0, self.app._show_save_success_dialog, 
                                "Thành công", 
                                message, 
                                parent_widget)
            else:
                self.logger.log(f"LỖI LƯU CẦU: {message}")
                self.root_after(0, self.app._show_error_dialog, 
                                "Lỗi", 
                                message, 
                                parent_widget)

        except Exception as e:
            self.logger.log(f"LỖI trong task_save_bridge: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, self.app._show_error_dialog, 
                            "Lỗi", 
                            f"Lỗi nghiêm trọng khi lưu cầu: {e}", 
                            parent_widget)

    def task_load_managed_bridges(self, bridge_manager_view):
        try:
            bridges_data = get_all_managed_bridges() 
            self.logger.log(f"Đã tải {len(bridges_data)} cầu từ DB.")
            self.root_after(0, bridge_manager_view.populate_bridge_list, bridges_data)
        except Exception as e:
            self.logger.log(f"LỖI trong task_load_managed_bridges: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, self.app._show_error_dialog, 
                            "Lỗi Tải Cầu", 
                            f"Lỗi khi tải danh sách cầu: {e}", 
                            bridge_manager_view.window)

    def task_add_managed_bridge(self, bridge_name, description, parent_widget):
        try:
            success, message = add_managed_bridge(bridge_name, description, "Tự thêm")
            
            if success:
                self.logger.log(f"THÊM CẦU THÀNH CÔNG: {message}")
                self.root_after(0, self.app._show_save_success_dialog, 
                                "Thành công", 
                                message, 
                                parent_widget)
            else:
                self.logger.log(f"LỖI THÊM CẦU: {message}")
                self.root_after(0, self.app._show_error_dialog, 
                                "Lỗi", 
                                message, 
                                parent_widget)

            if hasattr(self.app, 'bridge_manager_window_instance') and self.app.bridge_manager_window_instance:
                self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list)

        except Exception as e:
            self.logger.log(f"LỖI trong task_add_managed_bridge: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, self.app._show_error_dialog, 
                            "Lỗi", 
                            f"Lỗi nghiêm trọng khi thêm cầu: {e}", 
                            parent_widget)

    def task_update_managed_bridge(self, bridge_id, new_description, new_status, parent_widget):
        try:
            success, message = update_managed_bridge(bridge_id, new_description, new_status)
            
            if success:
                action = "Cập nhật mô tả" if new_description else "Bật/Tắt trạng thái"
                self.logger.log(f"{action} THÀNH CÔNG: {message}")
                self.root_after(0, self.app._show_save_success_dialog, 
                                "Thành công", 
                                message, 
                                parent_widget)
            else:
                self.logger.log(f"LỖI CẬP NHẬT CẦU: {message}")
                self.root_after(0, self.app._show_error_dialog, 
                                "Lỗi", 
                                message, 
                                parent_widget)
                                
            if hasattr(self.app, 'bridge_manager_window_instance') and self.app.bridge_manager_window_instance:
                self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list)

        except Exception as e:
            self.logger.log(f"LỖI trong task_update_managed_bridge: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, self.app._show_error_dialog, 
                            "Lỗi", 
                            f"Lỗi nghiêm trọng khi cập nhật cầu: {e}", 
                            parent_widget)

    def task_delete_managed_bridge(self, bridge_id, parent_widget):
        try:
            success, message = delete_managed_bridge(bridge_id)
            
            if success:
                self.logger.log(f"XÓA CẦU THÀNH CÔNG: {message}")
                self.root_after(0, self.app._show_save_success_dialog, 
                                "Thành công", 
                                message, 
                                parent_widget)
            else:
                self.logger.log(f"LỖI XÓA CẦU: {message}")
                self.root_after(0, self.app._show_error_dialog, 
                                "Lỗi", 
                                message, 
                                parent_widget)
                                
            if hasattr(self.app, 'bridge_manager_window_instance') and self.app.bridge_manager_window_instance:
                self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list)

        except Exception as e:
            self.logger.log(f"LỖI trong task_delete_managed_bridge: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, self.app._show_error_dialog, 
                            "Lỗi", 
                            f"Lỗi nghiêm trọng khi xóa cầu: {e}", 
                            parent_widget)

    def task_load_ky_list(self, lookup_view):
        try:
            ky_data_list = get_all_kys_from_db() 
            self.root_after(0, lookup_view.populate_ky_list, ky_data_list)
        except Exception as e:
            self.logger.log(f"LỖI trong task_load_ky_list: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, lookup_view.update_detail_text, f"LỖI TẢI DANH SÁCH KỲ: {e}")

    def _format_ky_details(self, ma_so_ky, row):
        try:
            loto_list = getAllLoto_V30(row)
            dau_stats, duoi_stats = calculate_loto_stats(loto_list)

            output = f"KẾT QUẢ KỲ: {ma_so_ky}\n"
            output += "=" * 46 + "\n\n"
            giai_ten = ["Đặc Biệt", "Nhất", "Nhì", "Ba", "Bốn", "Năm", "Sáu", "Bảy"]
            LABEL_WIDTH, NUMBER_WIDTH = 10, 33 
            
            for i in range(len(giai_ten)):
                giai_name = giai_ten[i].ljust(LABEL_WIDTH)
                giai_data_str = str(row[i+2] or "")
                numbers = [n.strip() for n in giai_data_str.split(',') if n.strip()]
                num_count = len(numbers)

                if num_count == 0:
                    output += f"{giai_name} : {''.center(NUMBER_WIDTH)}\n"
                elif num_count <= 3:
                    line_str = " - ".join(numbers)
                    output += f"{giai_name} : {line_str.center(NUMBER_WIDTH)}\n"
                elif num_count == 4:
                    line1_str, line2_str = " - ".join(numbers[:2]), " - ".join(numbers[2:])
                    output += f"{giai_name} : {line1_str.center(NUMBER_WIDTH)}\n"
                    output += f"{''.ljust(LABEL_WIDTH)} : {line2_str.center(NUMBER_WIDTH)}\n"
                elif num_count == 6:
                    line1_str, line2_str = " - ".join(numbers[:3]), " - ".join(numbers[3:])
                    output += f"{giai_name} : {line1_str.center(NUMBER_WIDTH)}\n"
                    output += f"{''.ljust(LABEL_WIDTH)} : {line2_str.center(NUMBER_WIDTH)}\n"
                else:
                    output += f"{giai_name} : {" - ".join(numbers)}\n"

            output += "\n" + "=" * 46 + "\n"
            output += "THỐNG KÊ LOTO (Đầu - Đuôi)\n"
            output += "-" * 46 + "\n"
            COL_DAU_W, COL_LOTO_W, COL_DUOI_W = 3, 12, 4
            output += f"{'Đầu'.ljust(COL_DAU_W)} | {'Loto'.ljust(COL_LOTO_W)} | {'Đuôi'.ljust(COL_DUOI_W)} | {'Loto'.ljust(COL_LOTO_W)}\n" 
            output += f"{'-'*COL_DAU_W} | {'-'*COL_LOTO_W} | {'-'*COL_DUOI_W} | {'-'*COL_LOTO_W}\n"
            
            for i in range(10):
                dau_val_str = ",".join(dau_stats.get(i, []))
                duoi_val_str = ",".join(duoi_stats.get(i, []))
                output += f"{str(i).ljust(COL_DAU_W)} | {dau_val_str.ljust(COL_LOTO_W)} | {str(i).ljust(COL_DUOI_W)} | {duoi_val_str.ljust(COL_LOTO_W)}\n"
            
            return output
            
        except Exception as e:
            self.logger.log(f"LỖI ĐỊNH DẠNG CHI TIẾT: {e}")
            return f"LỖI ĐỊNH DẠNG KẾT QUẢ KỲ: {ma_so_ky}. Lỗi chi tiết: {e}"

    def task_load_ky_details(self, ma_so_ky, lookup_view):
        try:
            row = get_results_by_ky(ma_so_ky)
            
            if not row:
                output = f"Không tìm thấy dữ liệu chi tiết cho kỳ: {ma_so_ky}"
            else:
                output = self._format_ky_details(ma_so_ky, row)

            self.root_after(0, lookup_view.populate_ky_details, output)
        except Exception as e:
            self.logger.log(f"LỖI trong task_load_ky_details: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, lookup_view.populate_ky_details, f"LỖI TẢI CHI TIẾT KỲ: {e}")

    def task_run_parameter_tuning(self, param_key, val_from, val_to, val_step, tuner_window):
        
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

            def test_gan_days(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                for i in _float_range(v_from, v_to, v_step):
                    n = int(i);
                    if n <= 0: continue
                    gan_stats = get_loto_gan_stats(all_data_ai, n_days=n)
                    log_to_tuner(f"Kiểm thử {p_key} = {n}: Tìm thấy {len(gan_stats)} loto gan.")
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_high_win_threshold(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Cache K2N một lần để lấy dữ liệu mới nhất)...")
                run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name) 
                log_to_tuner("... (Cache K2N hoàn tất. Bắt đầu lặp)...")
                for i in _float_range(v_from, v_to, v_step):
                    high_win_bridges = get_high_win_rate_predictions(threshold=i)
                    log_to_tuner(f"Kiểm thử {p_key} >= {i:.1f}%: Tìm thấy {len(high_win_bridges)} cầu đạt chuẩn.")
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_auto_add_rate(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Dò Cầu V17... Rất nặng, vui lòng chờ)...")
                ky_bat_dau = 2; ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
                results_v17 = TIM_CAU_TOT_NHAT_V16(all_data_ai, ky_bat_dau, ky_ket_thuc, self.db_name)
                log_to_tuner("... (Chạy Dò Cầu Bạc Nhớ...)...")
                results_memory = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, ky_bat_dau, ky_ket_thuc)
                combined_results = []
                if results_v17 and len(results_v17) > 1: combined_results.extend([row for row in results_v17[1:] if "---" not in str(row[0])])
                if results_memory and len(results_memory) > 1: combined_results.extend([row for row in results_memory[1:] if "---" not in str(row[0])])
                if not combined_results:
                    log_to_tuner("LỖI: Không dò được cầu nào."); return
                log_to_tuner(f"... (Dò cầu hoàn tất. Tổng cộng {len(combined_results)} cầu. Bắt đầu lặp)...")
                for i in _float_range(v_from, v_to, v_step):
                    count = 0
                    for row in combined_results:
                        try:
                            rate = float(str(row[3]).replace('%', ''))
                            if rate >= i: count += 1
                        except (ValueError, IndexError): continue
                    log_to_tuner(f"Kiểm thử {p_key} >= {i:.1f}%: Sẽ thêm/cập nhật {count} cầu.")
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_auto_prune_rate(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Cache K2N một lần để lấy dữ liệu mới nhất)...")
                run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
                log_to_tuner("... (Cache K2N hoàn tất. Bắt đầu lặp)...")
                enabled_bridges = get_all_managed_bridges(self.db_name, only_enabled=True)
                if not enabled_bridges:
                    log_to_tuner("LỖI: Không có cầu nào đang Bật để kiểm thử."); return
                for i in _float_range(v_from, v_to, v_step):
                    count = 0
                    for bridge in enabled_bridges:
                        try:
                            rate_str = str(bridge.get('win_rate_text', '100%')).replace('%', '')
                            if not rate_str or rate_str == "N/A": continue
                            rate = float(rate_str)
                            if rate < i: count += 1
                        except ValueError: continue
                    log_to_tuner(f"Kiểm thử {p_key} < {i:.1f}%: Sẽ TẮT {count} cầu.")
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_k2n_risk_logic(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Cache K2N một lần để lấy dữ liệu nền)...")
                pending_k2n, _ = run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name) 
                stats_n_day = get_loto_stats_last_n_days(all_data_ai)
                consensus = get_prediction_consensus() 
                high_win = get_high_win_rate_predictions() 
                gan_stats = get_loto_gan_stats(all_data_ai)
                top_memory = get_top_memory_bridge_predictions(all_data_ai, last_row)
                ai_preds, _ = run_ai_prediction_for_dashboard()
                log_to_tuner("... (Dữ liệu nền hoàn tất. Bắt đầu lặp)...")
                
                original_value = SETTINGS.get_all_settings().get(p_key)
                for i in _float_range(v_from, v_to, v_step):
                    val = i
                    if p_key == "K2N_RISK_START_THRESHOLD": val = int(i)
                    setattr(SETTINGS, p_key, val)
                    top_scores = get_top_scored_pairs(
                        stats_n_day, consensus, high_win, 
                        pending_k2n, gan_stats, top_memory, ai_preds
                    )
                    if not top_scores:
                        log_to_tuner(f"Kiểm thử {p_key} = {val}: Không có cặp nào đạt điểm.")
                    else:
                        top_score_item = top_scores[0]
                        log_to_tuner(f"Kiểm thử {p_key} = {val}: Top 1 là {top_score_item['pair']} (Điểm: {top_score_item['score']})")
                if original_value is not None:
                    setattr(SETTINGS, p_key, original_value)
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            # --- Bộ điều phối kiểm thử ---
            if param_key == "GAN_DAYS": test_gan_days(param_key, val_from, val_to, val_step)
            elif param_key == "HIGH_WIN_THRESHOLD": test_high_win_threshold(param_key, val_from, val_to, val_step)
            elif param_key == "AUTO_ADD_MIN_RATE": test_auto_add_rate(param_key, val_from, val_to, val_step)
            elif param_key == "AUTO_PRUNE_MIN_RATE": test_auto_prune_rate(param_key, val_from, val_to, val_step)
            elif param_key == "K2N_RISK_START_THRESHOLD" or param_key == "K2N_RISK_PENALTY_PER_FRAME":
                test_k2n_risk_logic(param_key, val_from, val_to, val_step)
            else:
                log_to_tuner(f"Lỗi: Chưa định nghĩa logic kiểm thử cho {param_key}")

        except Exception as e:
            log_to_tuner(f"LỖI: {e}")
            log_to_tuner(traceback.format_exc())
            try:
                current_settings = SETTINGS.get_all_settings()
                for key in current_settings.keys():
                    if key in locals() and locals()[key] is not None:
                        setattr(SETTINGS, key, locals()[key])
                log_to_tuner("Đã khôi phục cài đặt gốc sau lỗi.")
            except: pass
        finally:
            self.root_after(0, tuner_window.run_button.config, {"state": tk.NORMAL})
            
    # ===================================================================
    # (MỚI V7.2 Caching) LOGIC TẠO CACHE TỐI ƯU HÓA
    # ===================================================================

    def _check_cache_generation_status(self, process, queue, optimizer_tab):
        """
        (V7.2 Caching) Kiểm tra Queue để lấy log và tiến độ từ tiến trình Tạo Cache.
        """
        try:
            while True: 
                message = queue.get_nowait()
                msg_type, payload = message[0], message[1:]
                
                if msg_type == 'progress':
                    # Cập nhật tiến độ
                    current, total = payload
                    if current % 100 == 0: # Chỉ log mỗi 100 ngày
                        optimizer_tab.log(f"Đang tạo cache... {current}/{total} ngày")
                    
                elif msg_type == 'done':
                    # Tác vụ hoàn tất
                    success, msg = payload
                    optimizer_tab.log(f"--- TẠO CACHE HOÀN TẤT ---")
                    optimizer_tab.log(msg)
                    
                    # Bật lại các nút
                    optimizer_tab.run_button.config(state=tk.NORMAL)
                    optimizer_tab.generate_cache_button.config(state=tk.NORMAL) # (Sẽ thêm ở Giai đoạn 3)
                    
                    try:
                        queue.close(); process.join()
                    except Exception as e:
                        self.logger.log(f"Cảnh báo: Lỗi khi đóng Process/Queue Tạo Cache: {e}")
                    self.cache_gen_process = None
                    return # Dừng

        except Empty:
            pass 
        except Exception as e:
            optimizer_tab.log(f"Lỗi đọc Queue Tạo Cache: {e}")
            
        if process.is_alive():
            self.root_after(1000, self._check_cache_generation_status, process, queue, optimizer_tab)
        else:
            if self.cache_gen_process: 
                optimizer_tab.log("LỖI: Tiến trình Tạo Cache đã dừng đột ngột.")
                optimizer_tab.run_button.config(state=tk.NORMAL)
                if hasattr(optimizer_tab, 'generate_cache_button'):
                     optimizer_tab.generate_cache_button.config(state=tk.NORMAL)
                self.cache_gen_process = None
            try: queue.close(); process.join()
            except: pass

    def task_run_generate_cache(self, optimizer_tab):
        """
        (MỚI V7.2 Caching) Khởi chạy tác vụ Tạo Cache (rất nặng) trong tiến trình riêng.
        """
        # Hủy tiến trình cũ nếu đang chạy
        if self.cache_gen_process and self.cache_gen_process.is_alive():
            try:
                self.cache_gen_process.terminate()
                optimizer_tab.log("Đã hủy tác vụ tạo cache cũ.")
            except Exception as e:
                optimizer_tab.log(f"Lỗi khi hủy tác vụ cache cũ: {e}")
        
        # run_optimization_cache_generation được import từ lottery_service
        process, queue, success, message = run_optimization_cache_generation()
        
        if not success:
            optimizer_tab.log(f"LỖI KHỞI CHẠY TIẾN TRÌNH: {message}")
            return 

        self.cache_gen_process = process
        optimizer_tab.log(message)
        
        # Bắt đầu vòng lặp kiểm tra trạng thái
        self.root_after(1000, self._check_cache_generation_status, process, queue, optimizer_tab)

    # ===================================================================
    # (V7.2 MP) LOGIC TỐI ƯU HÓA CHIẾN LƯỢC (ĐA TIẾN TRÌNH)
    # ===================================================================

    def _check_optimization_status(self, process, queue, optimizer_tab):
        """
        (V7.2 MP) Kiểm tra Queue để lấy log và kết quả từ tiến trình Tối ưu hóa.
        """
        try:
            while True: 
                message = queue.get_nowait()
                msg_type, payload = message[0], message[1:]
                
                if msg_type == 'log':
                    optimizer_tab.log(payload[0])
                
                elif msg_type == 'progress':
                    jobs_done, total_jobs = payload
                    optimizer_tab.log(f"Đã hoàn thành {jobs_done}/{total_jobs} tổ hợp...")
                    
                elif msg_type == 'result':
                    optimizer_tab.log("--- HOÀN TẤT TỐI ƯU HÓA ---")
                    
                    results_list = payload[0]
                    optimizer_tab.clear_results_tree()
                    for i, (rate, hits, params_str, config_dict_str) in enumerate(results_list):
                        rate_str = f"{rate * 100:.1f}%"
                        tags = ('best',) if i == 0 else ()
                        tags_with_data = (config_dict_str,) + tags
                        optimizer_tab.tree.insert("", tk.END, values=(
                            rate_str, hits, params_str
                        ), tags=tags_with_data)
                    
                    optimizer_tab.apply_button.config(state=tk.NORMAL)
                    optimizer_tab.run_button.config(state=tk.NORMAL)
                    if hasattr(optimizer_tab, 'generate_cache_button'):
                         optimizer_tab.generate_cache_button.config(state=tk.NORMAL)
                    
                    try:
                        queue.close(); process.join()
                    except Exception as e:
                        self.logger.log(f"Cảnh báo: Lỗi khi đóng Process/Queue Tối ưu hóa: {e}")
                    self.optimization_process = None 
                    return 

                elif msg_type == 'error':
                    optimizer_tab.log(f"LỖI NGHIÊM TRỌNG: {payload[0]}")
                    optimizer_tab.run_button.config(state=tk.NORMAL)
                    if hasattr(optimizer_tab, 'generate_cache_button'):
                         optimizer_tab.generate_cache_button.config(state=tk.NORMAL)
                    try:
                        queue.close(); process.join()
                    except Exception: pass
                    self.optimization_process = None
                    return 

        except Empty:
            pass 
        except Exception as e:
            optimizer_tab.log(f"Lỗi đọc Queue Tối ưu hóa: {e}")
            
        if process.is_alive():
            self.root_after(500, self._check_optimization_status, process, queue, optimizer_tab)
        else:
            if self.optimization_process: 
                optimizer_tab.log("LỖI: Tiến trình Tối ưu hóa đã dừng đột ngột.")
                optimizer_tab.run_button.config(state=tk.NORMAL)
                if hasattr(optimizer_tab, 'generate_cache_button'):
                     optimizer_tab.generate_cache_button.config(state=tk.NORMAL)
                self.optimization_process = None
            try: queue.close(); process.join()
            except: pass


    def task_run_strategy_optimization(self, strategy, days_to_test, param_ranges, optimizer_tab):
        """
        (V7.2 MP & Caching) Khởi chạy tác vụ Tối ưu hóa Chiến lược.
        """
        
        if self.optimization_process and self.optimization_process.is_alive():
            try:
                self.optimization_process.terminate() 
                optimizer_tab.log("Đã hủy tác vụ tối ưu hóa cũ.")
            except Exception as e:
                optimizer_tab.log(f"Lỗi khi hủy tác vụ cũ: {e}")

        def log_to_optimizer(message):
            self.root_after(0, optimizer_tab.log, message)
            
        try:
            log_to_optimizer("Đang tải toàn bộ dữ liệu A:I...")
            all_data_ai = self.load_data_ai_from_db_controller() 
            if not all_data_ai or len(all_data_ai) < days_to_test + 50:
                log_to_optimizer(f"LỖI: Cần ít nhất {days_to_test + 50} kỳ dữ liệu để kiểm thử.")
                self.root_after(0, optimizer_tab.run_button.config, {"state": tk.NORMAL})
                return
            log_to_optimizer(f"...Tải dữ liệu thành công ({len(all_data_ai)} kỳ).")
            
            original_settings = SETTINGS.get_all_settings()
            original_settings_backup = original_settings.copy()
            
            result_queue = Queue()
            self.optimization_process = Process(
                target=_strategy_optimization_process_target, # (Hàm manager đã được sửa để TẢI cache)
                args=(
                    result_queue, 
                    all_data_ai, 
                    strategy, 
                    days_to_test, 
                    param_ranges, 
                    original_settings_backup
                )
            )
            
            self.optimization_process.start()
            
            self.root_after(100, self._check_optimization_status, self.optimization_process, result_queue, optimizer_tab)
            
        except Exception as e:
            log_to_optimizer(f"LỖI KHỞI CHẠY TIẾN TRÌNH: {e}")
            log_to_optimizer(traceback.format_exc())
            self.root_after(0, optimizer_tab.run_button.config, {"state": tk.NORMAL})