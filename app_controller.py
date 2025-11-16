# TÊN FILE: app_controller.py
# NỘI DUNG THAY THẾ TOÀN BỘ (HOÀN TRẢ VỀ .GET())
# (SỬA LỖI THEO YÊU CẦU: Thêm cột "Dự Đoán Kế Tiếp" vào Backtest N1)

import traceback
import time
import json
import itertools
import os 
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional, Callable

import multiprocessing 
from multiprocessing import Process, Queue
from multiprocessing.queues import Empty
from concurrent.futures import ProcessPoolExecutor, as_completed

import tkinter as tk 
from tkinter import messagebox

# (FIX LỖI MP) Thêm import DataService
try:
    from logic.data_service import DataService
except ImportError:
    print("LỖI: Controller không tìm thấy 'logic/data_service.py'.")
    pass 

try:
    from lottery_service import *
except ImportError:
    print("LỖI NGHIÊM TRỌNG: Controller không tìm thấy 'lottery_service.py'.")
    exit()

try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: Controller không thể import logic.config_manager.")
    SETTINGS = type('obj', (object,), {
        'STATS_DAYS': 7, 'GAN_DAYS': 15, 'HIGH_WIN_THRESHOLD': 47.0,
        'AUTO_ADD_MIN_RATE': 50.0, 'AUTO_PRUNE_MIN_RATE': 40.0,
        'K2N_RISK_START_THRESHOLD': 4, 'K2N_RISK_PENALTY_PER_FRAME': 0.5,
        'get_all_settings': lambda: {},
        'get': lambda k, d: d, # (SỬA LỖI) Thêm .get()
        'update_setting': lambda k, v: (False, "SETTINGS object not initialized")
    })

# Import các hàm Backtest/Analytics cần thiết cho Controller
try:
    # (SỬA LỖI GĐ 4) Các hàm này đã được refactor/lỗi thời
    # Chúng ta import các Wrapper GĐ 4 mới
    from logic.backtester import (
        run_and_update_all_bridge_rates,
        run_and_update_all_bridge_K2N_cache,
        
        # (SỬA LỖI GĐ 4) Các hàm V6 cũ (đã bị xóa/làm rỗng)
        # Giữ lại import nếu các tác vụ cũ (Menu Backtest) vẫn gọi chúng
        BACKTEST_MANAGED_BRIDGES_K2N, TONGHOP_TOP_CAU_RATE_V5,
        TONGHOP_TOP_CAU_N1_V5, BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_MEMORY_BRIDGES, 
        BACKTEST_CUSTOM_CAU_V16,
        BACKTEST_MANAGED_BRIDGES_N1
    )
    from logic.dashboard_analytics import (
        get_loto_gan_stats, get_loto_stats_last_n_days,
        get_prediction_consensus, get_high_win_rate_predictions,
        get_top_memory_bridge_predictions, get_historical_dashboard_data,
        
        # (SỬA LỖI GĐ 4) Import hàm tạo cache cho Tối ưu hóa
        generate_full_optimization_cache,
    )
    from logic.bridges.bridge_manager_core import (
        find_and_auto_manage_bridges, prune_bad_bridges,
        TIM_CAU_TOT_NHAT_V16
    )
    # (SỬA LỖI NAMEERROR) Thêm import cho cả 2 hàm tra cứu DB
    from logic.db_manager import get_all_kys_from_db, get_results_by_ky
except ImportError as e:
    print(f"CẢNH BÁO: Lỗi import module logic trong controller: {e}")
    # Fallback cho các hàm nếu lỗi
    def BACKTEST_MANAGED_BRIDGES_K2N(*args): return {}, "Lỗi import"
    def TONGHOP_TOP_CAU_RATE_V5(*args): return {}, "Lỗi import"
    def find_and_auto_manage_bridges(*args): return False, "Lỗi import"
    def prune_bad_bridges(*args): return "Lỗi import"
    # Fallback cho hàm bị lỗi
    def get_all_kys_from_db(*args): 
        print("LỖI: Không thể import 'get_all_kys_from_db'.")
        return []
    def get_results_by_ky(*args):
        print("LỖI: Không thể import 'get_results_by_ky'.")
        return None
    # (SỬA LỖI GĐ 4) Thêm Fallback
    def run_and_update_all_bridge_rates(*args): return {}, "Lỗi Import GĐ 4"
    def run_and_update_all_bridge_K2N_cache(*args): return {}, "Lỗi Import GĐ 4"
    def generate_full_optimization_cache(*args): return False, "Lỗi Import GĐ 4"
    def BACKTEST_MEMORY_BRIDGES(*args): return {}
    def BACKTEST_CUSTOM_CAU_V16(*args): return {}
    def BACKTEST_MANAGED_BRIDGES_N1(*args): return {}

# ===================================================================
# (V7.2 MP) HÀM HỖ TRỢ VÀ HÀM MỤC TIÊU CHO TỐI ƯU HÓA (Đa tiến trình)
# ===================================================================

def _float_range(start, stop, step):
    if step == 0: yield start; return
    n = start
    while n < (stop + (step * 0.5)):
        yield n
        n += step

def _generate_combinations(param_ranges, original_settings):
    param_lists = []
    config_keys = list(param_ranges.keys())
    static_keys = [k for k in original_settings.keys() if k not in config_keys]
    
    for key in config_keys:
        v_from, v_to, v_step = param_ranges[key]
        if isinstance(original_settings.get(key, 0), int): # Sửa lỗi nếu key không có
            param_lists.append([(key, int(i)) for i in _float_range(v_from, v_to, v_step) if i >= 0])
        else:
            param_lists.append([(key, round(i, 2)) for i in _float_range(v_from, v_to, v_step) if i >= 0])
    if not param_lists: return []

    combinations = []
    for combo in itertools.product(*param_lists):
        temp_config = {}
        for static_key in static_keys:
            temp_config[static_key] = original_settings.get(static_key) # Sửa lỗi nếu key không có
        for key, value in combo:
            temp_config[key] = value
        combinations.append(temp_config)
    return combinations

def _run_single_config_test(job_payload):
    try:
        all_data_ai, strategy, days_to_test, config, param_ranges, optimization_cache = job_payload
        
        # ======================================================
        # (SỬA LỖI TỐI ƯU HÓA) Ép SETTINGS của worker này sử dụng config mới
        # ======================================================
        try:
            from logic.config_manager import SETTINGS
            for key, value in config.items():
                if hasattr(SETTINGS, key):
                    setattr(SETTINGS, key, value)
        except Exception as e_cfg:
            # Ghi lỗi vào kết quả nếu không thể set config
            return ("error", f"Loi worker khi set config: {e_cfg}", str(config), "{}")
        # ======================================================
        
        from logic.dashboard_analytics import get_historical_dashboard_data
        
        # (SỬA LỖI GĐ 4) Import hàm tiện ích từ DataService
        # (Hàm này phải được DataService cung cấp)
        try:
            from logic.data_service import DataService
            # (SỬA LỖI GĐ 4) Hàm tiện ích nằm trong file bridge, không phải dataservice
            from logic.bridges.bridges_classic import getAllLoto_V30
        except Exception:
            # Fallback nếu DataService lỗi trong worker
            def getAllLoto_V30(r): return []
            
        
        total_hits = 0
        days_tested = 0
        
        for day_offset in range(days_to_test):
            actual_index = len(all_data_ai) - 1 - day_offset
            day_index = actual_index - 1
            if day_index < 50: continue
            days_tested += 1
            
            actual_row = all_data_ai[actual_index]
            actual_loto_set = set(getAllLoto_V30(actual_row))
            
            # Hàm này giờ sẽ sử dụng SETTINGS đã được cập nhật ở trên
            top_scores = get_historical_dashboard_data(
                all_data_ai, 
                day_index, 
                config, 
                optimization_cache=optimization_cache 
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
                        
        rate = total_hits / days_tested if days_tested > 0 else 0
        hits_str = f"{total_hits}/{days_tested}"
        config_str_json = json.dumps(config)
        params_str_display = ", ".join([f"{key}: {value}" for key, value in config.items() if key in param_ranges])
        
        return (rate, hits_str, params_str_display, config_str_json)
        
    except Exception as e:
        error_msg = f"Lỗi worker: {e}\n{traceback.format_exc()}"
        return ("error", error_msg, str(config), "{}")


def _strategy_optimization_process_target(result_queue: multiprocessing.Queue, all_data_ai: List[List[Any]], strategy: str, days_to_test: int, param_ranges: Dict[str, Tuple[float, float, float]], original_settings_backup: Dict[str, Any]):
    
    def log_to_queue(message):
        result_queue.put(('log', message))

    try:
        import joblib
        from logic.dashboard_analytics import CACHE_FILE_PATH 
        
        log_to_queue(f"Đang tải Cache Tối ưu hóa từ {CACHE_FILE_PATH}...")
        if not os.path.exists(CACHE_FILE_PATH):
            log_to_queue("LỖI NGHIÊM TRỌNG: Không tìm thấy file 'optimization_cache.joblib'.")
            log_to_queue(">>> Vui lòng chạy tác vụ '1. Tạo Cache Tối ưu hóa' trước.")
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
        
        jobs = []
        for config in combinations:
            jobs.append((all_data_ai, strategy, days_to_test, config, param_ranges, optimization_cache))

        results_list = []
        jobs_completed = 0
        
        num_workers = max(1, (os.cpu_count() or 4) - 1)
        log_to_queue(f"Khởi chạy {num_workers} tiến trình con để xử lý {total_combos} jobs (nhanh)...")

        # (FIX LỖI MP) THÊM initializer VÀO ProcessPoolExecutor
        with ProcessPoolExecutor(
            max_workers=num_workers,
            initializer=DataService.initialize_for_worker # <--- FIX LỖI BROKEN PROCESS POOL
        ) as executor:
            future_to_job = {executor.submit(_run_single_config_test, job): job for job in jobs}
            
            for future in as_completed(future_to_job):
                result_tuple = future.result()
                
                if result_tuple[0] == "error":
                    log_to_queue(f"LỖI JOB: {result_tuple[2]}\n{result_tuple[1]}")
                else:
                    results_list.append(result_tuple)
                    
                jobs_completed += 1
                
                if jobs_completed % 100 == 0 or jobs_completed == total_combos: 
                     result_queue.put(('progress', jobs_completed, total_combos))

        log_to_queue("Tất cả jobs đã hoàn thành. Đang sắp xếp kết quả...")
        results_list.sort(key=lambda x: x[0], reverse=True)
        
        log_to_queue("Khôi phục cài đặt gốc...")
        try:
            from logic.config_manager import SETTINGS
            for key, value in original_settings_backup.items():
                if hasattr(SETTINGS, key):
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
        self.app = app_instance 
        self.root = app_instance.root
        self.db_name = DB_NAME if 'DB_NAME' in globals() else "xo_so_prizes_all_logic.db"
        self.logger = None 
        
        self.all_data_ai = None 
        
        self.optimization_process = None
        self.cache_gen_process = None 

    def root_after(self, ms, func, *args):
        self.root.after(ms, func, *args)
        
    # ===================================================================
    # LOGIC TẢI DỮ LIỆU
    # ===================================================================

    def load_data_ai_from_db_controller(self):
        # (SỬA LỖI GĐ 1) Gọi DataService (Singleton) thay vì hàm V6
        try:
            rows_of_lists, message = DataService.get_instance().load_data_ai_from_db() 
        except Exception as e:
             rows_of_lists = None
             message = f"Lỗi nghiêm trọng khi gọi DataService: {e}"
             
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
        """(SỬA LỖI WINERROR 32 Lần 3 - Xóa dữ liệu, không xóa file)"""
        conn = None 
        try:
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                raw_data = f.read()
            self.logger.log(f"Đã đọc tệp tin '{input_file}' thành công.")
            
            # =======================================================
            # (SỬA LỖI WINERROR 32)
            # KHÔNG XÓA FILE (os.remove)
            # Thay vào đó, chúng ta sẽ KẾT NỐI VỚI FILE
            # và XÓA TẤT CẢ DỮ LIỆU BÊN TRONG NÓ.
            # =======================================================
            self.logger.log("... (GĐ 1) Đang kết nối CSDL để xóa dữ liệu cũ...")
            
            # Bước 1: Kết nối (an toàn, thread này sẽ tự tạo conn)
            # (Chúng ta KHÔNG dùng DataService, mà dùng hàm gốc
            # từ lottery_service.py)
            conn, cursor = setup_database()
            if not conn:
                raise Exception("Không thể kết nối CSDL để xóa.")
                
            # Bước 2: Xóa dữ liệu (DROP tables)
            # (db_manager.py's setup_database sẽ tạo lại chúng)
            try:
                self.logger.log("... Đang xóa DuLieu_AI...")
                cursor.execute("DROP TABLE IF EXISTS DuLieu_AI;")
                self.logger.log("... Đang xóa ManagedBridges...")
                cursor.execute("DROP TABLE IF EXISTS ManagedBridges;")
                self.logger.log("... Đang xóa AI_Data_Cache...")
                cursor.execute("DROP TABLE IF EXISTS AI_Data_Cache;")
                # (Thêm bất kỳ bảng nào khác nếu có)
                conn.commit()
                self.logger.log("... Đã xóa thành công bảng (tables) cũ.")
            except Exception as e_drop:
                 self.logger.log(f"Lỗi khi xóa bảng (tables): {e_drop}")
                 # Vẫn tiếp tục, vì setup_database sẽ tạo lại (CREATE IF NOT EXISTS)
            
            # Bước 3: Đóng kết nối này lại
            conn.close()
            conn = None # Đặt lại
            
            self.logger.log("... Đang tạo lại CSDL và chèn dữ liệu...")
            
            # Bước 4: Chạy lại setup_database (để TẠO LẠI bảng)
            # và chèn dữ liệu
            conn, cursor = setup_database()

            total_records_ai = parse_and_insert_data(raw_data, conn, cursor)
            
            if total_records_ai == 0:
                self.logger.log("LỖI: Không thể phân tích dữ liệu. File có thể không đúng định dạng.")
            else:
                self.logger.log(f"Phân tích và chèn dữ liệu hoàn tất.")
                self.logger.log(f"- Đã chèn {total_records_ai} hàng A:I (backtest).")
                self.logger.log(f"- Đã tạo lại bảng ManagedBridges (trống).")
                self.logger.log(">>> Sẵn sàng cho Chức Năng Soi Cầu.")
                
                # (SỬA LỖI WINERROR 32)
                # Chúng ta phải đóng kết nối CSDL của thread này
                # TRƯỚC KHI cố gắng chạy dashboard (nơi DataService
                # của Main Thread sẽ truy cập lại)
                if conn:
                    conn.close()
                    conn = None # Rất quan trọng
                
                # Yêu cầu Main Thread chạy dashboard
                self.root_after(0, self.app.run_decision_dashboard) 
                self.root_after(1500, self._check_model_drift_after_update, True)

        except Exception as e:
            self.logger.log(f"LỖI trong Bước 1 (Xóa Hết): {e}")
            self.logger.log(traceback.format_exc())
        finally:
            if conn:
                conn.close()
                self.logger.log("Đã đóng kết nối database (cuối cùng).")

    def task_run_parsing_append(self, input_file):
        """(SỬA V7.3.1) Thêm cờ auto_retrain=True cho MLOps"""
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
                
                # (SỬA V7.3.1) Tự động hóa AI khi nạp file LỚN
                self.root_after(1500, self._check_model_drift_after_update, True) # auto_retrain = True

        except Exception as e:
            self.logger.log(f"LỖI trong Bước 1 (Append): {e}")
            self.logger.log(traceback.format_exc())
        finally:
            if conn:
                conn.close()
                self.logger.log("Đã đóng kết nối database.")

    # (SỬA V7.3.1) Thêm tham số 'auto_retrain_on_drift'
    def _check_model_drift_after_update(self, auto_retrain_on_drift=False):
        """
        (MLOps) Được gọi sau khi thêm dữ liệu mới.
        Nếu auto_retrain_on_drift=True, sẽ tự động huấn luyện lại nếu phát hiện drift.
        """
        self.logger.log("[Kiểm tra AI] Đang đánh giá mô hình sau khi thêm dữ liệu...")
        
        eval_status, eval_msg = run_model_evaluation() 
        
        self.logger.log(f"[Kiểm tra AI] {eval_msg}")
        
        if eval_status == 'WARN':
            self.logger.log("======================================")
            self.logger.log("CẢNH BÁO: ĐỘ CHÍNH XÁC AI GIẢM!")
            self.logger.log("Phát hiện độ chính xác AI có thể đã giảm (Model Drift).")
            
            if auto_retrain_on_drift:
                # (SỬA V7.3.1) TỰ ĐỘNG HUẤN LUYỆN LẠI
                self.logger.log(">>> [TỰ ĐỘNG] Kích hoạt huấn luyện AI chạy nền...")
                self.logger.log("======================================")
                self.task_run_train_ai("Tự động Huấn luyện AI (do Model Drift)")
            else:
                # Chỉ cảnh báo
                self.logger.log(">>> ĐỀ XUẤT: Chạy lại 'Huấn luyện AI' để cập nhật mô hình.")
                self.logger.log("======================================")

    def task_run_update_from_text(self, raw_data):
        """(SỬA V7.3.1) Thêm cờ auto_retrain=False cho MLOps"""
        try:
            success, message = run_and_update_from_text(raw_data)
            
            self.logger.log(message) 
            
            if success:
                self.root_after(0, self.app.clear_update_text_area) 
                time.sleep(0.5) 
                self.root_after(0, self.logger.log, "Đã thêm dữ liệu. Tự động chạy lại Bảng Tổng Hợp...")
                self.root_after(0, self.app.run_decision_dashboard) 
                
                # (SỬA V7.3.1) KHÔNG tự động hóa AI khi nạp từ text
                self.root_after(1500, self._check_model_drift_after_update, False) # auto_retrain = False
            else:
                self.logger.log("(Không có kỳ nào được thêm hoặc có lỗi nghiêm trọng.)")

        except Exception as e:
            self.logger.log(f"LỖI khi cập nhật: {e}")
            self.logger.log(traceback.format_exc())
        finally:
            self.logger.log("Đã hoàn tất tác vụ thêm từ text.")

    def task_run_backtest(self, mode, title):
        """ (FIX GĐ 4.1) Sửa lỗi V6 lỗi thời."""
        toan_bo_A_I = self.load_data_ai_from_db_controller() 
        if not toan_bo_A_I:
            return
        
        self.logger.log(f"Đang chạy backtest V6 (Cổ điển) trên {len(toan_bo_A_I)} hàng dữ liệu...")

        # (FIX GĐ 4.1) Các hàm V6 này đã lỗi thời.
        # Trả về một List (với tiêu đề) để UI không bị crash (KeyError: 0).
        results_data = [
            ["Tên Cầu", "Tỷ lệ", "Ghi chú"],
            ["LỖI", "N/A", "Chức năng Backtest V6 này đã lỗi thời (GĐ 4) và bị vô hiệu hóa."]
        ]
        
        self.logger.log("CẢNH BÁO: Chức năng Backtest V6 (Cổ điển) đã lỗi thời và bị vô hiệu hóa.")
        self.root_after(0, self.app.show_backtest_results, title, results_data) 

    def task_run_custom_backtest(self, mode, title, custom_bridge_name):
        """ (FIX GĐ 4.1) Sửa lỗi V6 lỗi thời."""
        allData = self.load_data_ai_from_db_controller() 
        if not allData:
            return

        # (FIX GĐ 4.1) Các hàm V6 này đã lỗi thời.
        # Trả về một List (với tiêu đề) để UI không bị crash (KeyError: 0).
        results_data = [
            ["Tên Cầu", "Tỷ lệ", "Ghi chú"],
            ["LỖI", "N/A", "Chức năng Backtest V6 Tùy chỉnh này đã lỗi thời (GĐ 4) và bị vô hiệu hóa."]
        ]
        
        self.logger.log("CẢNH BÁO: Chức năng Backtest V6 Tùy chỉnh đã lỗi thời và bị vô hiệu hóa.")
        self.root_after(0, self.app.show_backtest_results, title, results_data) 

    def task_run_backtest_managed_n1(self, title):
        """ (FIX GĐ 4.1) Tái cấu trúc để gọi BridgeManager (N1).
            (SỬA LỖI THEO YÊU CẦU) Thêm cột "Dự Đoán Kế Tiếp".
        """
        toan_bo_A_I = self.load_data_ai_from_db_controller() 
        if not toan_bo_A_I:
            return
        
        self.logger.log(f"Đang chạy backtest GĐ 4 (N1) trên {len(toan_bo_A_I)} hàng dữ liệu...")
        
        # (GĐ 1) Tải danh sách cầu
        managed_bridges_list = DataService.get_instance().get_all_managed_bridges(only_enabled=True)
        if not managed_bridges_list:
            self.logger.log("Lỗi: Không tìm thấy Cầu Đã Lưu nào để chạy backtest N1.")
            return

        # ===================================================================
        # (SỬA LỖI THEO YÊU CẦU) TÍNH TOÁN 2 BƯỚC
        # ===================================================================

        # 1. Chạy N1 (Tỷ lệ) trước (như cũ)
        n1_results_dict, message_n1 = run_and_update_all_bridge_rates(
            toan_bo_A_I, 
            managed_bridges_list, 
            write_to_db=False 
        )
        self.logger.log(f"(Backtest N1) {message_n1}")

        # 2. Chạy K2N (Cache) để lấy "Dự Đoán Kế Tiếp" (Giống K2N backtest)
        #    (Chúng ta cần cập nhật list cầu với tỷ lệ N1 mới trước)
        managed_bridges_updated = []
        for bridge_data in managed_bridges_list:
            bridge_name = bridge_data['name']
            if bridge_name in n1_results_dict:
                # Cập nhật win_rate_text từ kết quả N1 MỚI NHẤT
                bridge_data['win_rate_text'] = n1_results_dict[bridge_name].get('win_rate_text', '0.00%')
            managed_bridges_updated.append(bridge_data)
        
        k2n_results_dict, message_k2n = run_and_update_all_bridge_K2N_cache(
            toan_bo_A_I, 
            managed_bridges_updated, # <--- Truyền danh sách đã cập nhật N1
            write_to_db=False 
        )
        self.logger.log(f"(Backtest N1 - Lấy dự đoán) {message_k2n}")
        
        # ===================================================================
        # (SỬA LỖI HIỂN THỊ N1)
        # Sửa lại Header và Dữ liệu
        # ===================================================================
        headers = ["Tên Cầu", "Dự Đoán Kế Tiếp", "Tỷ lệ N1", "Thắng/Tổng"] # <-- THÊM CỘT MỚI
        results_list_for_ui = [headers]
        
        # Sắp xếp theo Tỷ lệ N1 giảm dần (lấy từ n1_results_dict)
        try:
            sorted_results = sorted(
                n1_results_dict.items(), # <-- Sắp xếp dict N1
                key=lambda item: float(str(item[1].get('win_rate_text', '0%')).replace('%', '')),
                reverse=True
            )
        except Exception:
             sorted_results = list(n1_results_dict.items()) # Fallback
        
        for bridge_name, n1_data in sorted_results:
            # Lấy dữ liệu dự đoán từ k2n_results_dict
            k2n_data = k2n_results_dict.get(bridge_name, {})
            
            results_list_for_ui.append([
                bridge_name,
                k2n_data.get('next_prediction_stl', 'N/A'), # <-- DỮ LIỆU MỚI
                n1_data.get('win_rate_text', 'N/A'),
                f"{n1_data.get('total_wins', 0)}/{n1_data.get('total_days', 0)}"
            ])
        # ===================================================================

        self.logger.log(f"Backtest Cầu Đã Lưu N1 (GĐ 4) hoàn tất. Đang mở cửa sổ kết quả...")
        self.root_after(0, self.app.show_backtest_results, title, results_list_for_ui)

    def task_run_backtest_managed_k2n(self, title):
        """ (FIX GĐ 4.1) Tái cấu trúc để gọi BridgeManager (K2N) và CHUYỂN ĐỔI kết quả."""
        toan_bo_A_I = self.load_data_ai_from_db_controller() 
        if not toan_bo_A_I:
            return

        self.logger.log(f"Đang chạy backtest GĐ 4 (K2N) trên {len(toan_bo_A_I)} hàng dữ liệu...")
        
        # (GĐ 1) Tải danh sách cầu
        managed_bridges_list = DataService.get_instance().get_all_managed_bridges(only_enabled=True)
        if not managed_bridges_list:
            self.logger.log("Lỗi: Không tìm thấy Cầu Đã Lưu nào để chạy backtest K2N.")
            return

        # ===================================================================
        # (SỬA LỖI HIỂN THỊ K2N)
        # 1. Chạy N1 và *lấy* kết quả (n1_results_dict)
        # 2. *Hợp nhất* (merge) kết quả N1 vào danh sách cầu (managed_bridges)
        # 3. Chạy K2N với danh sách cầu đã được cập nhật tỷ lệ N1
        # ===================================================================
        
        # 1. Chạy N1 (Tỷ lệ) trước (nhưng không cập nhật DB, chỉ để lấy tỷ lệ)
        n1_results_dict, _ = run_and_update_all_bridge_rates(
            toan_bo_A_I, 
            managed_bridges_list, 
            write_to_db=False 
        )
        
        # 2. Hợp nhất N1 vào danh sách cầu
        # (Tải lại danh sách cầu (đã có Tỷ lệ N1 mới))
        # (SỬA LỖI) Không tải lại từ DB, mà cập nhật thủ công
        managed_bridges_updated = []
        for bridge_data in managed_bridges_list:
            bridge_name = bridge_data['name']
            if bridge_name in n1_results_dict:
                # Cập nhật win_rate_text từ kết quả N1 MỚI NHẤT
                bridge_data['win_rate_text'] = n1_results_dict[bridge_name].get('win_rate_text', '0.00%')
            managed_bridges_updated.append(bridge_data)

        # 3. Gọi hàm cache mới (chỉ đọc, không ghi DB)
        #    truyền vào danh sách cầu đã được cập nhật N1
        results_dict, message = run_and_update_all_bridge_K2N_cache(
            toan_bo_A_I, 
            managed_bridges_updated, # <--- Truyền danh sách đã cập nhật
            write_to_db=False 
        )
        self.logger.log(f"(Backtest K2N) {message}")
        
        # (FIX GĐ 4.1) Chuyển đổi DICT (mới) sang LIST (cũ) mà UI Results Viewer yêu cầu
        headers = ["Tên Cầu", "STL Kế tiếp", "Chuỗi K2N", "Gãy Max K2N", "Tỷ lệ N1 (tham khảo)"]
        results_list_for_ui = [headers]
        
        # Sắp xếp theo Chuỗi K2N giảm dần (giống Dashboard)
        try:
            sorted_results = sorted(
                results_dict.items(), 
                key=lambda item: (
                    int(str(item[1].get('current_streak', 0)).split(' ')[0]), 
                    -int(item[1].get('max_lose_streak_k2n', 0))
                ), 
                reverse=True
            )
        except Exception:
             sorted_results = list(results_dict.items()) # Fallback
        
        for bridge_name, data in sorted_results:
            results_list_for_ui.append([
                bridge_name,
                data.get('next_prediction_stl', 'N/A'),
                f"{data.get('current_streak', 0)} ngày",
                data.get('max_lose_streak_k2n', 0),
                data.get('win_rate_text', 'N/A') # <--- Giờ sẽ hiển thị đúng
            ])
        # ===================================================================

        self.logger.log(f"Backtest Cầu Đã Lưu K2N (GĐ 4) hoàn tất. Đang mở cửa sổ kết quả...")
        self.root_after(0, self.app.show_backtest_results, title, results_list_for_ui) 

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
        
        # ===================================================================
        # (SỬA LỖI GĐ 4) Tái cấu trúc quy trình chạy N1 và K2N
        # ===================================================================
        
        # (GĐ 1) Tải danh sách cầu từ DataService (Singleton)
        managed_bridges_list = DataService.get_instance().get_all_managed_bridges(only_enabled=True)

        self.logger.log("... (2/5) Đang chạy Backtest N1 (Cập nhật Tỷ lệ)...")
        # (GĐ 4) Chạy N1 (Tỷ lệ) trước
        total_results_dict, message_n1 = run_and_update_all_bridge_rates(
            all_data_ai, 
            managed_bridges_list, 
            write_to_db=True # Cập nhật DB
        )
        self.logger.log(f"... (Backtest N1) {message_n1}")
        
        # (GĐ 1) Tải lại danh sách cầu (đã có Tỷ lệ N1 mới)
        managed_bridges_updated = DataService.get_instance().get_all_managed_bridges(only_enabled=True)

        self.logger.log("... (3/5) Đang chạy hàm Cập nhật K2N Cache (tối ưu)...")
        # (GĐ 4) Chạy K2N (Cache) sau, sử dụng danh sách cầu đã cập nhật N1
        pending_k2n_data, cache_message = run_and_update_all_bridge_K2N_cache(
            all_data_ai, 
            managed_bridges_updated,
            write_to_db=True # Cập nhật DB
        )
        self.logger.log(f"... (Cache K2N) {cache_message}")
        
        # ===================================================================
        
        self.logger.log("... (4/5) Đang đọc Consensus và Cầu Tỷ lệ Cao từ cache...")
        consensus = get_prediction_consensus()
        high_win = get_high_win_rate_predictions(threshold=high_win_thresh)

        self.logger.log(f"... (5/5) Đang tìm Lô Gan (trên {n_days_gan} kỳ)...")
        gan_stats = get_loto_gan_stats(all_data_ai, n_days=n_days_gan)
        
        self.logger.log("... (6/5) Đang chạy dự đoán AI (V7.0)...") # Sửa 5/5 -> 6/5
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

        # ===================================================================
        # (SỬA LỖI HIỂN THỊ K2N)
        # Sửa lại logic giống hệt task_run_backtest_managed_k2n
        # ===================================================================
        
        # (GĐ 1) Tải danh sách cầu
        managed_bridges_list = DataService.get_instance().get_all_managed_bridges(only_enabled=True)

        # 1. Chạy N1 (Tỷ lệ) trước (nhưng không cập nhật DB, chỉ để lấy tỷ lệ)
        n1_results_dict, _ = run_and_update_all_bridge_rates(
            all_data_ai, 
            managed_bridges_list, 
            write_to_db=False # Không cần ghi DB khi chỉ làm mới cache
        )
        
        # 2. Hợp nhất N1 vào danh sách cầu
        managed_bridges_updated = []
        for bridge_data in managed_bridges_list:
            bridge_name = bridge_data['name']
            if bridge_name in n1_results_dict:
                bridge_data['win_rate_text'] = n1_results_dict[bridge_name].get('win_rate_text', '0.00%')
            managed_bridges_updated.append(bridge_data)

        # 3. (GĐ 4) Chạy K2N (Cache) sau, sử dụng danh sách cầu đã cập nhật N1
        #    (Lần này write_to_db=True là mặc định)
        _, message = run_and_update_all_bridge_K2N_cache(
            all_data_ai, 
            managed_bridges_updated
        )
        # ===================================================================
        
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

        # NOTE: DB_NAME đã được loại bỏ khỏi hàm này, nhưng giữ lại chữ ký ở đây
        success, result_message = find_and_auto_manage_bridges(toan_bo_A_I, self.db_name)
        
        self.logger.log(f">>> {title} HOÀN TẤT:")
        self.logger.log(result_message)
        
        if self.app.bridge_manager_window and self.app.bridge_manager_window.winfo_exists():
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list)

    def task_run_auto_prune_bridges(self, title):
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return

        # NOTE: DB_NAME đã được loại bỏ khỏi hàm này, nhưng giữ lại chữ ký ở đây
        result_message = prune_bad_bridges(self.db_name)
        
        self.logger.log(f">>> {title} HOÀN TẤT:")
        self.logger.log(result_message)
        
        if self.app.bridge_manager_window and self.app.bridge_manager_window.winfo_exists():
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list)

    def _check_ai_training_status(self, process, queue, title):
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
                    return 
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
        """ (FIX GĐ 4.1) Sửa lỗi V6 lỗi thời."""
        toan_bo_A_I = self.load_data_ai_from_db_controller()
        if not toan_bo_A_I:
            return
        
        # (FIX GĐ 4.1) Các hàm V6 này đã lỗi thời.
        # Trả về một List (với tiêu đề) để UI không bị crash (KeyError: 0).
        results_data = [
            ["Tên Cầu", "Tỷ lệ", "Ghi chú"],
            ["LỖI", "N/A", "Chức năng Backtest Cầu Bạc Nhớ (V6) đã lỗi thời (GĐ 4) và bị vô hiệu hóa."]
        ]
        
        self.logger.log("CẢNH BÁO: Chức năng Backtest Cầu Bạc Nhớ (V6) đã lỗi thời và bị vô hiệu hóa.")
        self.root_after(0, self.app.show_backtest_results, title, results_data)
        
    # ===================================================================
    # LOGIC TẠO CACHE VÀ TỐI ƯU HÓA (V7.2 Caching)
    # ===================================================================

    def _check_cache_generation_status(self, process, queue, optimizer_tab):
        try:
            while True: 
                message = queue.get_nowait()
                msg_type, payload = message[0], message[1:]
                
                if msg_type == 'progress':
                    current, total = payload
                    if current % 100 == 0: 
                        optimizer_tab.log(f"Đang tạo cache... {current}/{total} ngày")
                    
                elif msg_type == 'done':
                    success, msg = payload
                    optimizer_tab.log(f"--- TẠO CACHE HOÀN TẤT ---")
                    optimizer_tab.log(msg)
                    
                    optimizer_tab.run_button.config(state=tk.NORMAL)
                    if hasattr(optimizer_tab, 'generate_cache_button'):
                        optimizer_tab.generate_cache_button.config(state=tk.NORMAL)
                    
                    try:
                        queue.close(); process.join()
                    except Exception as e:
                        self.logger.log(f"Cảnh báo: Lỗi khi đóng Process/Queue Tạo Cache: {e}")
                    self.cache_gen_process = None
                    return 

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
        if self.cache_gen_process and self.cache_gen_process.is_alive():
            try:
                self.cache_gen_process.terminate()
                optimizer_tab.log("Đã hủy tác vụ tạo cache cũ.")
            except Exception as e:
                optimizer_tab.log(f"Lỗi khi hủy tác vụ cache cũ: {e}")
        
        # (SỬA LỖI GĐ 4)
        # Hàm này cần (all_data_ai)
        all_data_ai = self.load_data_ai_from_db_controller()
        if not all_data_ai:
             optimizer_tab.log("LỖI: Không thể tải dữ liệu A:I để tạo cache.")
             return
             
        process, queue, success, message = run_optimization_cache_generation(all_data_ai)
        
        if not success:
            optimizer_tab.log(f"LỖI KHỞI CHẠY TIẾN TRÌNH: {message}")
            return 

        self.cache_gen_process = process
        optimizer_tab.log(message)
        
        self.root_after(1000, self._check_cache_generation_status, process, queue, optimizer_tab)

    def _check_optimization_status(self, process, queue, optimizer_tab):
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
                        
                        # (SỬA LỖI HIỂN THỊ TỪ LẦN TRƯỚC)
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
                target=_strategy_optimization_process_target, 
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
            
    # ===================================================================
    # (MỚI) BỔ SUNG CÁC HÀM CHO TINH CHỈNH THAM SỐ (TUNER)
    # ===================================================================

    def task_run_parameter_tuning(self, param_key, val_from, val_to, val_step, tuner_view):
        """
        [CONTROLLER TASK] Chạy kiểm thử cho 1 tham số duy nhất.
        Hàm này được chạy trong 1 thread riêng bởi TaskManager của main_app.
        """
        def log_to_view(message):
            # Sử dụng root_after để đảm bảo an toàn thread cho Tkinter
            self.root_after(0, tuner_view.log, message)
        
        try:
            log_to_view("Đang tải dữ liệu A:I và Cache Tối ưu hóa...")
            
            # 1. Tải dữ liệu
            all_data_ai = self.load_data_ai_from_db_controller()
            if not all_data_ai:
                log_to_view("LỖI: Không thể tải dữ liệu.")
                return

            # 2. Tải cache
            from logic.dashboard_analytics import CACHE_FILE_PATH
            import joblib
            if not os.path.exists(CACHE_FILE_PATH):
                log_to_view(f"LỖI: Không tìm thấy file cache: {CACHE_FILE_PATH}")
                log_to_view(">>> Vui lòng chạy '1. Tạo Cache Tối ưu hóa' trước.")
                return
            optimization_cache = joblib.load(CACHE_FILE_PATH)
            log_to_view("... Tải dữ liệu và cache thành công.")

            # 3. Lấy cài đặt gốc
            original_settings = SETTINGS.get_all_settings()
            original_settings_backup = original_settings.copy()

            # 4. Tạo dải tham số CHỈ cho 1 key
            param_ranges = {param_key: (val_from, val_to, val_step)}
            
            # 5. Tạo các tổ hợp (combinations)
            combinations = _generate_combinations(param_ranges, original_settings_backup)
            total_combos = len(combinations)
            if total_combos == 0:
                log_to_view("LỖI: Không tạo được tổ hợp kiểm thử.")
                return
            
            log_to_view(f"Đã tạo {total_combos} tổ hợp. Bắt đầu kiểm thử...")
            
            # Sử dụng các giá trị mặc định cho tuner
            days_to_test = 30 
            strategy = "Tối ưu Top 1 (N1)" 
            
            results_list = []
            
            # 6. Lặp và chạy test (Không cần ProcessPool vì đã ở trong thread riêng)
            for i, config in enumerate(combinations):
                current_value = config.get(param_key)
                log_to_view(f"Đang chạy {i+1}/{total_combos}: {param_key} = {current_value}")
                
                job_payload = (all_data_ai, strategy, days_to_test, config, param_ranges, optimization_cache)
                
                # Gọi trực tiếp hàm worker
                result_tuple = _run_single_config_test(job_payload)
                
                if result_tuple[0] == "error":
                    log_to_view(f"LỖI JOB: {result_tuple[1]}")
                else:
                    results_list.append(result_tuple)

            log_to_view("... Kiểm thử hoàn tất. Đang sắp xếp kết quả.")
            results_list.sort(key=lambda x: x[0], reverse=True)
            
            log_to_view("\n" + "="*30)
            log_to_view("--- KẾT QUẢ TỐT NHẤT ---")
            if results_list:
                rate, hits, params, _ = results_list[0]
                log_to_view(f"Tỷ lệ: {rate*100:.1f}% ({hits})")
                log_to_view(f"Tham số: {params}")
            
            log_to_view("\n--- Toàn bộ kết quả (từ cao đến thấp) ---")
            for (rate, hits, params, _) in results_list:
                 log_to_view(f" - {params} -> {rate*100:.1f}% ({hits})")
                 
            log_to_view("="*30)
            log_to_view("--- HOÀN TẤT ---")
            
            # 7. Khôi phục cài đặt gốc (RẤT QUAN TRỌNG)
            for key, value in original_settings_backup.items():
                if hasattr(SETTINGS, key):
                    setattr(SETTINGS, key, value)
            log_to_view("Đã khôi phục cài đặt gốc.")

        except Exception as e:
            log_to_view(f"LỖI NGHIÊM TRỌNG TRONG LUỒNG KIỂM THỬ: {e}")
            log_to_view(traceback.format_exc())
        finally:
            # 8. Bật lại nút (luôn luôn chạy)
            self.root_after(0, tuner_view.run_button.config, {"state": tk.NORMAL})
            
    # ===================================================================
    # CÁC HÀM MVC (VIEW-CONTROLLER) KHÁC
    # ===================================================================

    # ===================================================================
    # CÁC HÀM XỬ LÝ CHO CÀI ĐẶT (SETTINGS)
    # ===================================================================

    def task_load_all_settings(self, settings_view):
        """
        [CONTROLLER TASK] Tải tất cả cài đặt từ Model (SETTINGS) và
        gọi callback của View (populate_settings) để hiển thị.
        """
        try:
            self.logger.log("Đang tải cài đặt (config.json) từ Model...")
            # 1. Tải cài đặt từ Model
            current_settings = SETTINGS.get_all_settings() 
            
            if not current_settings:
                self.logger.log("Lỗi: Không thể tải cài đặt từ config_manager.")
                current_settings = {} # Gửi dict rỗng để tránh lỗi
                
            # 2. Gọi callback của View để điền dữ liệu
            self.root_after(0, settings_view.populate_settings, current_settings)

        except Exception as e:
            self.logger.log(f"LỖI trong task_load_all_settings: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, self.app._show_error_dialog, 
                            "Lỗi Tải Cài Đặt", 
                            f"Lỗi khi tải cài đặt: {e}", 
                            settings_view.window)

    def task_save_all_settings(self, new_settings_dict, parent_widget):
        """
        [CONTROLLER TASK] Nhận dữ liệu cài đặt mới từ View và
        ủy quyền cho Model (SETTINGS) để lưu vào file config.json.
        """
        try:
            self.logger.log("Đang lưu cài đặt mới (config.json)...")
            
            success_count = 0
            error_messages = []
            
            # 1. Ủy quyền cho Model (SETTINGS) để lưu từng cài đặt
            for key, value in new_settings_dict.items():
                success, msg = SETTINGS.update_setting(key, value)
                if success: 
                    self.logger.log(f" - Đã lưu: {key} = {value}")
                    success_count += 1
                else: 
                    self.logger.log(f" - LỖI LƯU {key}: {msg}")
                    error_messages.append(msg)
            
            self.logger.log("--- Lưu cài đặt hoàn tất! ---")
            
            # 2. Hiển thị thông báo kết quả (qua main_app)
            if success_count == len(new_settings_dict):
                self.root_after(0, self.app._show_save_success_dialog, 
                                "Thành công", 
                                f"Đã lưu thành công {success_count} tham số.", 
                                parent_widget)
            elif success_count > 0:
                 self.root_after(0, self.app._show_warning_dialog, 
                                "Lưu một phần", 
                                f"Đã lưu {success_count} tham số.\nLỗi: {'; '.join(error_messages)}", 
                                parent_widget)
            else:
                 self.root_after(0, self.app._show_error_dialog, 
                                "Thất bại", 
                                f"Không có tham số nào được lưu thành công.\nLỗi: {'; '.join(error_messages)}", 
                                parent_widget)

        except Exception as e:
            self.logger.log(f"LỖI trong task_save_all_settings: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, self.app._show_error_dialog, 
                            "Lỗi", 
                            f"Lỗi nghiêm trọng khi lưu cài đặt: {e}", 
                            parent_widget)
        finally:
            # 3. (QUAN TRỌNG) Gọi callback để bật lại nút Save trên View
            if hasattr(self.app, 'settings_window') and self.app.settings_window and self.app.settings_window.window == parent_widget:
                self.root_after(0, self.app.settings_window._re_enable_save_button)

    def get_current_setting_value(self, key):
        """
        [CONTROLLER] Lấy một giá trị cài đặt cụ thể từ Model (SETTINGS).
        (Hàm này được ui_tuner.py gọi)
        """
        try:
            # ===================================================================
            # (SỬA LỖI KIẾN TRÚC) Hoàn trả về .get()
            return SETTINGS.get(key, None) 
            # ===================================================================
        except Exception as e:
            self.logger.log(f"Lỗi khi get_current_setting_value cho {key}: {e}")
            return None
            
    # ===================================================================
    # (Kết thúc phần bổ sung)
    # ===================================================================

    def task_apply_optimized_settings(self, config_dict, optimizer_window):
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
            # (SỬA LỖI GĐ 1) Gọi DataService
            success, message = DataService.get_instance().upsert_managed_bridge(bridge_name, description, win_rate) 
            
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
            # (SỬA LỖI GĐ 1) Gọi DataService
            bridges_data = DataService.get_instance().get_all_managed_bridges() 
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
            # (SỬA LỖI GĐ 1) Gọi DataService
            success, message = DataService.get_instance().add_managed_bridge(bridge_name, description, "Tự thêm")
            
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
            # (SỬA LỖI GĐ 1) Gọi DataService
            success, message = DataService.get_instance().update_managed_bridge(bridge_id, new_description, new_status)
            
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
            # (SỬA LỖI GĐ 1) Gọi DataService
            success, message = DataService.get_instance().delete_managed_bridge(bridge_id)
            
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
            # (SỬA LỖI GĐ 1) Gọi DataService
            ky_data_list = DataService.get_instance().get_all_kys_from_db() 
            self.root_after(0, lookup_view.populate_ky_list, ky_data_list)
        except Exception as e:
            self.logger.log(f"LỖI trong task_load_ky_list: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, lookup_view.update_detail_text, f"LỖI TẢI DANH SÁCH KỲ: {e}")

    def _format_ky_details(self, ma_so_ky, row):
        try:
            # (SỬA LỖI TRA CỨU) Import hàm calculate_loto_stats từ file đúng
            # (Nó đã được sửa trong logic/bridges/bridges_classic.py)
            from logic.bridges.bridges_classic import getAllLoto_V30, calculate_loto_stats # Import local
            
            loto_list = getAllLoto_V30(row)
            # (SỬA LỖI TRA CỨU) Hàm này giờ đã đúng
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
            
            # (FIX LỖI HIỂN THỊ ĐẦU/ĐUÔI)
            # Lặp qua 10 dòng (0-9)
            for i in range(10):
                # Lấy loto cho Đầu i
                dau_val_str = ",".join(dau_stats.get(i, []))
                # Lấy loto cho Đuôi i (thay vì Đuôi 0 cho dòng 0, Đuôi 1 cho dòng 1)
                duoi_val_str = ",".join(duoi_stats.get(i, []))
                
                # In Đầu i và Đuôi i trên cùng một dòng
                output += f"{str(i).ljust(COL_DAU_W)} | {dau_val_str.ljust(COL_LOTO_W)} | {str(i).ljust(COL_DUOI_W)} | {duoi_val_str.ljust(COL_LOTO_W)}\n"
            
            return output
            
        except Exception as e:
            self.logger.log(f"LỖI ĐỊNH DẠNG CHI TIẾT: {e}")
            return f"LỖI ĐỊNH DẠNG KẾT QUẢ KỲ: {ma_so_ky}. Lỗi chi tiết: {e}"

    def task_load_ky_details(self, ma_so_ky, lookup_view):
        try:
            # (SỬA LỖI GĐ 1) Gọi DataService
            row = DataService.get_instance().get_results_by_ky(ma_so_ky)
            
            if not row:
                output = f"Không tìm thấy dữ liệu chi tiết cho kỳ: {ma_so_ky}"
            else:
                output = self._format_ky_details(ma_so_ky, row)

            self.root_after(0, lookup_view.populate_ky_details, output)
        except Exception as e:
            self.logger.log(f"LỖI trong task_load_ky_details: {e}")
            self.logger.log(traceback.format_exc())
            self.root_after(0, lookup_view.populate_ky_details, f"LỖI TẢI CHI TIẾT KỲ: {e}")