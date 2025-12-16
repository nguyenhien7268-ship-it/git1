# Tên file: git3/app_controller.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - ĐÃ KHẮC PHỤC LỖI W503, E226)
#
import time
import tkinter as tk
import traceback
import threading

# Import chỉ các hàm cần thiết cho fallback (nếu services không khả dụng)
try:
    from lottery_service import load_data_ai_from_db
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Controller không tìm thấy 'lottery_service.py': {e}")
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

# Import chỉ các hàm cần thiết cho services

# Import Services Layer (MVC Refactoring Phase 1 & 2)
try:
    from services import DataService, BridgeService, AnalysisService
except ImportError:
    print("Cảnh báo: Không thể import services. Sử dụng fallback mode.")
    DataService = None
    BridgeService = None
    AnalysisService = None

class AppController:
    """
    Lớp này chứa TOÀN BỘ logic nghiệp vụ (các hàm _task)
    được tách ra từ ui_main_window.py.
    Đã được refactor để sử dụng Service Layer (MVC).
    """

    def __init__(self, app_instance):
        self.app = app_instance  # Tham chiếu đến DataAnalysisApp
        self.root = app_instance.root
        self.db_name = app_instance.db_name
        self.logger = None  # Sẽ được gán từ app_instance

        self.all_data_ai = None  # Cache dữ liệu
        self.dashboard_data_cache = {} # [V10.0 NEW] Cache lưu trữ kết quả phân tích để Safe Merge
        
        # Khởi tạo Services (MVC Refactoring)
        # Lưu ý: logger sẽ được cập nhật sau bằng set_logger()
        if DataService:
            self.data_service = DataService(self.db_name, logger=None)
        else:
            self.data_service = None
        
        if BridgeService:
            self.bridge_service = BridgeService(self.db_name, logger=None)
        else:
            self.bridge_service = None
        
        if AnalysisService:
            self.analysis_service = AnalysisService(self.db_name, logger=None)
        else:
            self.analysis_service = None
    
    def set_logger(self, logger):
        """Cập nhật logger cho controller và các services"""
        self.logger = logger
        if self.data_service:
            self.data_service.logger = logger
        if self.bridge_service:
            self.bridge_service.logger = logger
        if self.analysis_service:
            self.analysis_service.logger = logger

    def root_after(self, ms, func, *args):
        """Hàm gọi root.after an toàn (chạy trên luồng chính)."""
        self.root.after(ms, func, *args)
    
    def _refresh_bridge_manager_if_needed(self):
        """Helper: Refresh bridge manager window nếu đang mở"""
        if (self.app.bridge_manager_window and self.app.bridge_manager_window.winfo_exists()):
            self.logger.log("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            try:
                self.root_after(0, self.app.bridge_manager_window_instance.refresh_bridge_list)
            except Exception as e:
                self.logger.log(f"Lỗi khi tự động làm mới QL Cầu: {e}")

    # ===================================================================
    # LOGIC TẢI DỮ LIỆU (Đã di chuyển)
    # ===================================================================

    def load_data_ai_from_db_controller(self):
        """Tải (hoặc tải lại) dữ liệu A:I từ DB."""
        # Sử dụng DataService nếu có, fallback về hàm cũ
        if self.data_service:
            rows_of_lists = self.data_service.load_data()
            if rows_of_lists is None:
                self.all_data_ai = None
                return None
            else:
                self.all_data_ai = rows_of_lists
                return rows_of_lists
        else:
            # Fallback: Gọi hàm từ lottery_service
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
    # CÁC HÀM TÁC VỤ (Đã di chuyển từ ui_main_window.py)
    # ===================================================================

    def task_run_parsing(self, input_file):
        if self.data_service:
            def callback():
                self.root_after(0, self.app.run_decision_dashboard)
            success, message = self.data_service.import_data_from_file(input_file, callback_on_success=callback)
            if not success:
                self.logger.log(f"LỖI: {message}")

    def task_run_parsing_append(self, input_file):
        if self.data_service:
            def callback():
                self.root_after(0, self.app.run_decision_dashboard)
            success, message = self.data_service.append_data_from_file(input_file, callback_on_success=callback)
            if not success:
                self.logger.log(f"LỖI: {message}")

    def task_run_update_from_text(self, raw_data):
        if self.data_service:
            def callback():
                self.root_after(0, self.app.clear_update_text_area)
                time.sleep(0.5)
                self.root_after(0, self.logger.log, "Đã thêm dữ liệu. Tự động chạy lại Bảng Tổng Hợp...")
                self.root_after(0, self.app.run_decision_dashboard)
            success, message = self.data_service.update_from_text(raw_data, callback_on_success=callback)
            if not success:
                self.logger.log("(Không có kỳ nào được thêm hoặc có lỗi nghiêm trọng.)")

    def task_run_backtest(self, mode, title):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.analysis_service:
            results = self.analysis_service.run_backtest(all_data, mode, title)
            if results:
                self.logger.log("Backtest hoàn tất. Đang mở cửa sổ kết quả...")
                self.root_after(0, self.app.show_backtest_results, title, results)

    def task_run_custom_backtest(self, mode, title, custom_bridge_name):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.analysis_service:
            results, adjusted_mode, adjusted_title = self.analysis_service.run_custom_backtest(all_data, mode, custom_bridge_name)
            if results:
                self.root_after(0, self.app.show_backtest_results, adjusted_title or title, results)

    def task_run_backtest_managed_n1(self, title):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.analysis_service:
            results = self.analysis_service.run_backtest_managed_n1(all_data)
            if results:
                self.logger.log("Backtest Cầu Đã Lưu N1 hoàn tất. Đang mở cửa sổ kết quả...")
                self.root_after(0, self.app.show_backtest_results, title, results)

    def task_run_backtest_managed_k2n(self, title):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.analysis_service:
            results = self.analysis_service.run_backtest_managed_k2n(all_data)
            if results:
                self.logger.log("Backtest Cầu Đã Lưu K2N hoàn tất. Đang mở cửa sổ kết quả...")
                self.root_after(0, self.app.show_backtest_results, title, results)

    def task_run_decision_dashboard(self, title, lo_mode=True, de_mode=True):
        """
        Chạy phân tích Dashboard với chế độ tùy chọn (On-Demand).
        """
        all_data = self.load_data_ai_from_db_controller()
        if not all_data or len(all_data) < 2:
            self.logger.log("LỖI: Cần ít nhất 2 kỳ dữ liệu để chạy Bảng Tổng Hợp.")
            self.root_after(0, self.app._on_dashboard_close)
            return
        try:
            limit = getattr(SETTINGS, "DATA_LIMIT_DASHBOARD", 2000)
        except:
            limit = 2000
        
        if self.analysis_service:
            # [V10.0] Gọi Service với tham số mode
            # Hàm này sẽ chỉ trả về những phần dữ liệu được yêu cầu tính toán
            new_partial_data = self.analysis_service.prepare_dashboard_data(
                all_data, 
                data_limit=limit if limit > 0 else None,
                lo_mode=lo_mode,
                de_mode=de_mode
            )
            
            if not new_partial_data:
                self.logger.log("LỖI: Không thể chuẩn bị dữ liệu dashboard.")
                self.root_after(0, self.app._on_dashboard_close)
                return
            
            # [V10.0] SAFE MERGE LOGIC
            # Gộp kết quả mới vào cache, giữ lại kết quả cũ của chế độ không chạy
            if not self.dashboard_data_cache:
                self.dashboard_data_cache = {}
            
            # Cập nhật cache với dữ liệu mới
            self.dashboard_data_cache.update(new_partial_data)
            
            # Sử dụng dữ liệu tổng hợp từ Cache để hiển thị
            final_data = self.dashboard_data_cache

            try:
                # Cập nhật Tab Đề (Chỉ khi có dữ liệu Đề mới hoặc Đề mode bật)
                if hasattr(self.app, 'de_dashboard_tab') and self.app.de_dashboard_tab:
                    if final_data.get('df_de') is not None:
                        # Chỉ log thông báo nếu đang chạy chế độ Đề
                        if de_mode:
                            self.logger.log("... (Soi Cầu Đề) Đang chuẩn bị dữ liệu...")
                        self.root_after(0, self.app.de_dashboard_tab.update_data, final_data['df_de'])
                        
                        if de_mode:
                            self.logger.log(f"... (Soi Cầu Đề) Đã nạp {len(final_data['df_de'])} kỳ vào hệ thống.")
            except Exception as e_de:
                self.logger.log(f"Cảnh báo: Lỗi cập nhật Tab Soi Cầu Đề: {e_de}")
            
            try:
                self.logger.log("Phân tích hoàn tất. Đang hiển thị Bảng Quyết Định Tối Ưu...")
                self.root_after(0, self.app._show_dashboard_window,
                    final_data.get('next_ky', "N/A"), 
                    final_data.get('stats_n_day', []), 
                    final_data.get('n_days_stats', 7),
                    final_data.get('consensus', []), 
                    final_data.get('high_win', []), 
                    final_data.get('pending_k2n_data', {}),
                    final_data.get('gan_stats', []), 
                    final_data.get('top_scores', []), 
                    final_data.get('top_memory_bridges', []),
                    final_data.get('ai_predictions', [])
                )
            except Exception as e_final:
                self.logger.log(f"LỖI NGHIÊM TRỌNG khi hiển thị Dashboard: {e_final}")
                self.logger.log(traceback.format_exc())
                self.root_after(0, self.app._on_dashboard_close)

    def task_run_update_all_bridge_K2N_cache(self, title):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.bridge_service:
            _, _, message = self.bridge_service.update_k2n_cache(all_data)
            self.logger.log(message)
            self._refresh_bridge_manager_if_needed()

    def task_run_auto_find_bridges(self, title):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.bridge_service:
            try:
                SCAN_LIMIT = getattr(SETTINGS, "DATA_LIMIT_SCANNER", 500)
            except:
                SCAN_LIMIT = 500
            self.bridge_service.find_and_scan_bridges(all_data, scan_limit=SCAN_LIMIT)
            self.logger.log(">>> Tác vụ hoàn tất.")
            self._refresh_bridge_manager_if_needed()

    def task_run_auto_prune_bridges(self, title):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.bridge_service:
            result = self.bridge_service.prune_bad_bridges(all_data)
            self.logger.log(f">>> {title} HOÀN TẤT:")
            self.logger.log(result)
            self._refresh_bridge_manager_if_needed()

    def task_run_auto_manage_bridges(self, title):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.bridge_service:
            result = self.bridge_service.auto_manage_bridges(all_data)
            self.logger.log(f">>> {title} HOÀN TẤT:")
            self.logger.log(result)
            self._refresh_bridge_manager_if_needed()
    
    def task_run_prune_bad_de_bridges(self, title):
        """
        Tự động loại bỏ cầu Đề yếu (Phase 4 - Pruning).
        Chạy trong luồng nền để không chặn UI.
        
        Args:
            title: Tiêu đề tác vụ (để log)
        """
        try:
            self.logger.log(f">>> Bắt đầu {title}...")
            
            # Tải dữ liệu
            all_data = self.load_data_ai_from_db_controller()
            if not all_data:
                self.logger.log("LỖI: Không có dữ liệu để kiểm tra.")
                return
            
            # Gọi service để loại bỏ cầu Đề yếu
            if not self.bridge_service:
                self.logger.log("LỖI: BridgeService chưa được khởi tạo.")
                return
            
            result_msg = self.bridge_service.prune_bad_de_bridges(all_data)
            self.logger.log(f">>> {title} HOÀN TẤT:")
            self.logger.log(result_msg)
            
            # Refresh bridge manager nếu cần
            self._refresh_bridge_manager_if_needed()
            
        except Exception as e:
            error_msg = f"LỖI khi loại bỏ cầu Đề yếu: {e}"
            self.logger.log(error_msg)
            self.logger.log(traceback.format_exc())
    
    def task_run_toggle_pin(self, bridge_name):
        """
        Đảo ngược trạng thái ghim của cầu (Phase 4 - Pinning).
        Chạy trong luồng nền để không chặn UI.
        
        Args:
            bridge_name: Tên cầu cần ghim/bỏ ghim
        """
        try:
            if not bridge_name:
                self.logger.log("LỖI: Tên cầu không được để trống.")
                return
            
            # Gọi service để toggle pin
            if not self.bridge_service:
                self.logger.log("LỖI: BridgeService chưa được khởi tạo.")
                return
            
            success, message, new_pin_state = self.bridge_service.toggle_pin_bridge(bridge_name)
            
            if success:
                pin_status = "đã ghim" if new_pin_state else "đã bỏ ghim"
                self.logger.log(f">>> [PIN] Cầu '{bridge_name}' {pin_status}.")
            else:
                self.logger.log(f">>> [PIN] Lỗi: {message}")
            
            # Refresh bridge manager nếu cần
            self._refresh_bridge_manager_if_needed()
            
        except Exception as e:
            error_msg = f"LỖI khi ghim/bỏ ghim cầu '{bridge_name}': {e}"
            self.logger.log(error_msg)
            self.logger.log(traceback.format_exc())

    def task_run_smart_optimization(self, title):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.bridge_service:
            self.logger.log(f"\n--- ⚡ BẮT ĐẦU: {title} ---")
            msg_prune, msg_manage = self.bridge_service.smart_optimization(all_data)
            self.logger.log(f"✅ TỐI ƯU HÓA HOÀN TẤT!")
            self._refresh_bridge_manager_if_needed()

    def task_run_train_ai(self, title):
        def train_callback(success, message):
            self.logger.log(f">>> {title} HOÀN TẤT:")
            self.logger.log(message)
        if self.analysis_service:
            success, message = self.analysis_service.train_ai(callback=train_callback)
            if not success:
                self.logger.log(f"LỖI KHỞI CHẠY LUỒNG: {message}")

    def task_run_backtest_memory(self, title):
        all_data = self.load_data_ai_from_db_controller()
        if not all_data:
            return
        if self.analysis_service:
            results = self.analysis_service.run_backtest_memory(all_data)
            if results:
                self.logger.log("Backtest Cầu Bạc Nhớ hoàn tất. Đang mở cửa sổ kết quả...")
                self.root_after(0, self.app.show_backtest_results, title, results)

    def task_run_parameter_tuning(self, param_key, val_from, val_to, val_step, tuner_window):
        """Wrapper: Chuyển sang AnalysisService"""
        def log_to_tuner(message):
            self.root_after(0, tuner_window.log, message)
        
        try:
            log_to_tuner("Đang tải dữ liệu A:I...")
            all_data_ai = self.load_data_ai_from_db_controller()
            if not all_data_ai or len(all_data_ai) < 2:
                log_to_tuner("LỖI: Không thể tải dữ liệu A:I.")
                return
            
            # Sử dụng AnalysisService
            if self.analysis_service:
                self.analysis_service.run_parameter_tuning(all_data_ai, param_key, val_from, val_to, val_step, log_to_tuner)
            else:
                # Fallback: Giữ nguyên logic cũ (rút gọn)
                log_to_tuner("Cảnh báo: AnalysisService không khả dụng. Sử dụng fallback.")
        except Exception as e:
            log_to_tuner(f"LỖI: {e}")
            log_to_tuner(traceback.format_exc())
        finally:
            self.root_after(0, tuner_window.run_button.config, {"state": tk.NORMAL})

    def task_run_strategy_optimization(self, strategy, days_to_test, param_ranges, optimizer_tab):
        """Wrapper: Chuyển sang AnalysisService"""
        def log_to_optimizer(message):
            self.root_after(0, optimizer_tab.log, message)
        
        def update_tree_results_threadsafe(results_list):
            optimizer_tab.clear_results_tree()
            for i, (rate, hits, params_str, config_dict_str) in enumerate(results_list):
                rate_str = f"{rate * 100:.1f}%"
                tags = ("best",) if i == 0 else ()
                tags_with_data = (config_dict_str,) + tags
                optimizer_tab.tree.insert("", tk.END, values=(rate_str, hits, params_str), tags=tags_with_data)
            optimizer_tab.apply_button.config(state=tk.NORMAL)
        
        try:
            log_to_optimizer("Đang tải toàn bộ dữ liệu A:I...")
            all_data_ai = self.load_data_ai_from_db_controller()
            if not all_data_ai or len(all_data_ai) < days_to_test + 50:
                log_to_optimizer(f"LỖI: Cần ít nhất {days_to_test + 50} kỳ dữ liệu để kiểm thử.")
                return
            
            # Sử dụng AnalysisService
            if self.analysis_service:
                self.analysis_service.run_strategy_optimization(
                    all_data_ai, days_to_test, param_ranges, log_to_optimizer, update_tree_results_threadsafe
                )
            else:
                # Fallback: Giữ nguyên logic cũ (rút gọn)
                log_to_optimizer("Cảnh báo: AnalysisService không khả dụng. Sử dụng fallback.")
        except Exception as e:
            log_to_optimizer(f"LỖI: {e}")
            log_to_optimizer(traceback.format_exc())
        finally:
            self.root_after(0, optimizer_tab.run_button.config, {"state": tk.NORMAL})
    
    def trigger_bridge_backtest(self, bridge_name, is_de=False):
        """
        Kích hoạt backtest 30 ngày cho một cầu cụ thể (Task Launcher).
        Chạy logic backtest trong luồng nền để không chặn UI.
        
        Args:
            bridge_name: Tên cầu cần backtest
            is_de: True nếu là cầu Đề, False nếu là cầu Lô (mặc định)
        """
        print(f"[DEBUG] trigger_bridge_backtest được gọi: bridge_name='{bridge_name}', is_de={is_de}")
        
        if not bridge_name:
            print("[DEBUG] Bridge name rỗng, bỏ qua.")
            return
        
        # Log để debug
        if self.logger:
            self.logger.log(f"Đang khởi động backtest cho cầu '{bridge_name}' ({'Đề' if is_de else 'Lô'})...")
        
        # Khởi tạo Thread để chạy backtest trong luồng nền
        try:
            thread = threading.Thread(
                target=self.task_run_bridge_backtest,
                args=(bridge_name, is_de),
                daemon=True
            )
            thread.start()
            print(f"[DEBUG] Thread đã được khởi động.")
        except Exception as e:
            print(f"[ERROR] Lỗi khi khởi động thread: {e}")
            import traceback
            traceback.print_exc()
            if self.logger:
                self.logger.log(f"LỖI khi khởi động thread backtest: {e}")
    
    def task_run_bridge_backtest(self, bridge_name, is_de=False):
        """
        Chạy backtest 30 ngày cho một cầu cụ thể trong luồng nền.
        
        Args:
            bridge_name: Tên cầu cần backtest
            is_de: True nếu là cầu Đề, False nếu là cầu Lô (mặc định)
        """
        print(f"[DEBUG] task_run_bridge_backtest BẮT ĐẦU: bridge_name='{bridge_name}', is_de={is_de}")
        try:
            # Tải dữ liệu
            print(f"[DEBUG] Đang tải dữ liệu...")
            all_data = self.load_data_ai_from_db_controller()
            if not all_data:
                error_msg = "LỖI: Không có dữ liệu để chạy backtest."
                print(f"[ERROR] {error_msg}")
                if self.logger:
                    self.logger.log(error_msg)
                return
            
            print(f"[DEBUG] Đã tải {len(all_data)} dòng dữ liệu.")
            
            # Gọi service để chạy backtest
            if not self.analysis_service:
                error_msg = "LỖI: AnalysisService chưa được khởi tạo."
                print(f"[ERROR] {error_msg}")
                if self.logger:
                    self.logger.log(error_msg)
                return
            
            print(f"[DEBUG] Đang gọi service để chạy backtest...")
            if is_de:
                backtest_data = self.analysis_service.run_de_backtest_30_days(bridge_name, all_data)
            else:
                backtest_data = self.analysis_service.run_lo_backtest_30_days(bridge_name, all_data)
            
            print(f"[DEBUG] Backtest hoàn tất. Kết quả: {len(backtest_data) if backtest_data else 0} dòng.")
            
            # Hiển thị popup trên UI thread (sử dụng root_after)
            if backtest_data is not None:
                print(f"[DEBUG] Đang gọi _show_backtest_popup với {len(backtest_data)} dòng dữ liệu.")
                self.root_after(0, self._show_backtest_popup, bridge_name, backtest_data)
            else:
                error_msg = f"Không thể chạy backtest cho cầu '{bridge_name}'."
                print(f"[ERROR] {error_msg}")
                if self.logger:
                    self.logger.log(error_msg)
        
        except Exception as e:
            error_msg = f"LỖI khi chạy backtest: {e}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            if self.logger:
                self.logger.log(error_msg)
                self.logger.log(traceback.format_exc())
    
    def _show_backtest_popup(self, bridge_name, backtest_data):
        """
        Hiển thị popup backtest (được gọi trên UI thread).
        
        Args:
            bridge_name: Tên cầu
            backtest_data: Dữ liệu backtest
        """
        print(f"[DEBUG] _show_backtest_popup được gọi: bridge_name='{bridge_name}', data_length={len(backtest_data) if backtest_data else 0}")
        try:
            from ui.popups.ui_backtest_popup import BacktestPopup
            print(f"[DEBUG] Đang tạo BacktestPopup...")
            popup = BacktestPopup(self.root, bridge_name, backtest_data)
            print(f"[DEBUG] BacktestPopup đã được tạo thành công.")
        except ImportError as e:
            error_msg = f"LỖI: Không thể import BacktestPopup: {e}"
            print(f"[ERROR] {error_msg}")
            if self.logger:
                self.logger.log(error_msg)
        except Exception as e:
            error_msg = f"LỖI khi hiển thị popup: {e}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            if self.logger:
                self.logger.log(error_msg)
                self.logger.log(traceback.format_exc())
    
    def execute_batch_bridge_activation(self, bridge_names):
        """
        Phase 1: Execute batch bridge activation in background thread.
        
        Args:
            bridge_names: List of bridge names to activate and recalculate
        """
        if not bridge_names:
            if self.logger:
                self.logger.log("LỖI: Danh sách cầu rỗng.")
            return
        
        if not self.bridge_service:
            if self.logger:
                self.logger.log("LỖI: BridgeService chưa được khởi tạo.")
            return
        
        # Log start
        if self.logger:
            self.logger.log(f">>> Bắt đầu kích hoạt và tính toán {len(bridge_names)} cầu trong nền...")
        
        # Create thread to run activation task
        thread = threading.Thread(
            target=self._run_activation_task,
            args=(bridge_names,),
            daemon=True
        )
        thread.start()
    
    def _run_activation_task(self, bridge_names):
        """
        Internal: Run bridge activation in background thread.
        
        Args:
            bridge_names: List of bridge names to activate
        """
        try:
            # Load data
            all_data = self.load_data_ai_from_db_controller()
            if not all_data:
                if self.logger:
                    self.logger.log("LỖI: Không thể tải dữ liệu để tính toán.")
                return
            
            # Call bridge service to activate and recalculate
            result = self.bridge_service.activate_and_recalc_bridges(bridge_names, all_data)
            
            # Log result
            if result.get('success'):
                if self.logger:
                    self.logger.log(f"✅ {result.get('message')}")
                    
                    # Show details of updated bridges
                    updated = result.get('updated_bridges', [])
                    if updated:
                        self.logger.log(f">>> Chi tiết {len(updated)} cầu đã cập nhật:")
                        for bridge_info in updated[:5]:  # Show max 5
                            metrics = bridge_info.get('metrics', {})
                            self.logger.log(
                                f"  • {bridge_info['name']}: "
                                f"Tỷ lệ {metrics.get('win_rate_text', 'N/A')}, "
                                f"Dự đoán: {metrics.get('prediction', 'N/A')}"
                            )
                        if len(updated) > 5:
                            self.logger.log(f"  ... và {len(updated) - 5} cầu khác.")
            else:
                if self.logger:
                    self.logger.log(f"⚠️ {result.get('message')}")
            
            # Refresh bridge manager if it's open
            self._refresh_bridge_manager_if_needed()
        
        except Exception as e:
            error_msg = f"LỖI trong _run_activation_task: {e}"
            if self.logger:
                self.logger.log(error_msg)
                self.logger.log(traceback.format_exc())
