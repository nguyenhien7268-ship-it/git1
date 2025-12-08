# Tên file: CODE5/git1/ui/ui_main_window.py
#
# (PHIÊN BẢN CLEAN UX V7.9 - FIXED LOGGER INITIALIZATION ORDER)
#
import json
import os
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, simpledialog, ttk

# --- IMPORTS AN TOÀN ---
try:
    from lottery_service import DB_NAME, upsert_managed_bridge
except ImportError:
    print("LỖI: Không tìm thấy 'lottery_service.py'.")
    exit()

try:
    from app_controller import AppController
    from core_services import Logger, TaskManager
except ImportError:
    print("LỖI: Không tìm thấy 'core_services.py' hoặc 'app_controller.py'.")
    exit()

try:
    from logic.config_manager import SETTINGS
except ImportError:
    SETTINGS = None

# Import UI Components
try:
    from ui.ui_dashboard import DashboardWindow
    from ui.ui_de_dashboard import UiDeDashboard
    from ui.ui_lookup import LookupWindow
    from ui.ui_optimizer import OptimizerTab
    from ui.ui_results_viewer import ResultsViewerWindow
    from ui.ui_settings import SettingsWindow
    from ui.ui_tuner import TunerWindow
except ImportError as e:
    print(f"LỖI UI IMPORTS: {e}")
    exit()


class DataAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Xổ Số Data Analysis (v7.9 - Giao diện Tinh Gọn)")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        # Kích thước chuẩn HD
        self.root.geometry("1100x800")

        self.db_name = DB_NAME
        
        # --- CÁC BIẾN CONTROLLER CẦN TRUY CẬP (GIỮ NGUYÊN TÊN) ---
        self.bridge_manager_window = None          # Controller cần check biến này
        self.bridge_manager_window_instance = None # Controller cần gọi refresh_bridge_list() từ đây
        self.settings_window = None
        self.tuner_window = None

        # --- STYLE ---
        style = ttk.Style()
        # Nút Hero (Nổi bật)
        style.configure("Hero.TButton", font=("Helvetica", 12, "bold"), padding=10)
        # Nút Action (Màu xanh nhấn)
        style.configure("Accent.TButton", font=("Helvetica", 10, "bold"), foreground="blue")
        # Label nhỏ
        style.configure("Compact.TLabel", font=("Arial", 9), foreground="#555")

        # --- NOTEBOOK CHÍNH ---
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # ======================================================================
        # [QUAN TRỌNG] KHỞI TẠO LOGGER TRƯỚC TIÊN
        # Lý do: Các tab con (Lookup, Dashboard...) cần logger ngay khi init.
        # ======================================================================
        self.tab_log_frame = ttk.Frame(self.notebook, padding="10")
        self._setup_log_tab() # -> Tạo self.logger tại đây

        # 1. Khởi tạo các Tab Chức Năng (Sau khi đã có Logger)
        self.tab1_frame = ttk.Frame(self.notebook, padding="10") # Tab Trang chủ
        
        # Bọc try-except để nếu tab nào lỗi thì không sập cả app
        try:
            self.dashboard_tab = DashboardWindow(self)
        except Exception as e:
            self.logger.log(f"Lỗi khởi tạo Dashboard: {e}")
            self.dashboard_tab = ttk.Frame(self.notebook) # Placeholder

        try:
            self.de_dashboard_tab = UiDeDashboard(self.notebook, None)
        except Exception as e:
            self.logger.log(f"Lỗi khởi tạo Tab Đề: {e}")
            self.de_dashboard_tab = ttk.Frame(self.notebook)

        try:
            self.lookup_tab = LookupWindow(self)
        except Exception as e:
            self.logger.log(f"Lỗi khởi tạo Tab Tra Cứu: {e}")
            self.lookup_tab = ttk.Frame(self.notebook)

        try:
            self.optimizer_tab = OptimizerTab(self.notebook, self)
        except Exception as e:
            self.logger.log(f"Lỗi khởi tạo Tab Optimizer: {e}")
            self.optimizer_tab = ttk.Frame(self.notebook)

        # 2. Add Tabs vào Notebook
        self.notebook.add(self.tab1_frame, text="🏠 Trang Chủ")
        self.notebook.add(self.dashboard_tab, text="📊 Bảng Quyết Định")
        self.notebook.add(self.de_dashboard_tab, text="🔮 Soi Cầu Đề")
        self.notebook.add(self.lookup_tab, text="🔍 Tra Cứu")
        self.notebook.add(self.optimizer_tab, text="🚀 Tối Ưu Hóa")
        self.notebook.add(self.tab_log_frame, text="📝 Log Hệ Thống")

        # --- SETUP GIAO DIỆN TRANG CHỦ ---
        self._setup_home_tab()

        # --- LIST BUTTONS CHO TASK MANAGER ---
        # (Để khóa nút khi đang chạy tác vụ nặng)
        self.all_buttons = [
            self.btn_load_file, self.btn_load_append, self.btn_quick_update,
            self.btn_open_dashboard, self.btn_bridge_manager,
            self.btn_train_ai, self.btn_auto_find, self.btn_vote_stats,
            self.btn_settings, self.btn_tuner, self.btn_refresh_cache,
        ]
        
        # Thêm nút từ optimizer nếu khởi tạo thành công
        if hasattr(self.optimizer_tab, 'run_button'):
            self.all_buttons.append(self.optimizer_tab.run_button)
        if hasattr(self.optimizer_tab, 'apply_button'):
            self.all_buttons.append(self.optimizer_tab.apply_button)

        # --- KHỞI TẠO SERVICES ---
        self.task_manager = TaskManager(self.logger, self.all_buttons, self.root)
        
        if hasattr(self.optimizer_tab, 'apply_button'):
            self.task_manager.optimizer_apply_button = self.optimizer_tab.apply_button
        
        self.controller = AppController(self)
        self.controller.logger = self.logger
        
        # Link controller vào tab Đề (để tab Đề gọi ngược lại controller)
        if hasattr(self.de_dashboard_tab, 'controller'):
            self.de_dashboard_tab.controller = self.controller
        
        self.logger.log("✅ Giao diện (V7.9) đã khởi tạo xong & Logger đã sẵn sàng.")

    def _setup_home_tab(self):
        """Dựng giao diện Trang Chủ: Gọn gàng, tập trung."""
        self.tab1_frame.columnconfigure(0, weight=1)
        
        # === KHU VỰC 1: NHẬP LIỆU (COMPACT) ===
        input_frame = ttk.LabelFrame(self.tab1_frame, text="1. Dữ Liệu Đầu Vào", padding="5")
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        input_frame.columnconfigure(1, weight=1)

        # Hàng 1: Chọn File (Ít dùng -> Nhỏ lại)
        ttk.Label(input_frame, text="File:", style="Compact.TLabel").grid(row=0, column=0, sticky="w", padx=5)
        self.file_path_entry = ttk.Entry(input_frame)
        self.file_path_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(input_frame, text="...", width=4, command=self.browse_file).grid(row=0, column=2, padx=2)
        self.btn_load_file = ttk.Button(input_frame, text="Nạp Mới (Xóa)", command=self.run_parsing)
        self.btn_load_file.grid(row=0, column=3, padx=2)
        self.btn_load_append = ttk.Button(input_frame, text="Nạp Thêm", command=self.run_parsing_append)
        self.btn_load_append.grid(row=0, column=4, padx=2)

        # Hàng 2: Nhập Text (Dùng nhiều -> Text box vừa phải)
        ttk.Label(input_frame, text="Paste KQ:", style="Compact.TLabel").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        
        # [QUAN TRỌNG] Giảm height xuống 4 để tiết kiệm diện tích
        self.update_text_area = tk.Text(input_frame, height=4, width=60, font=("Consolas", 10))
        self.update_text_area.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        
        # Nút Cập Nhật Nổi Bật
        self.btn_quick_update = ttk.Button(input_frame, text="⚡ CẬP NHẬT NGAY", style="Accent.TButton", command=self.run_update_from_text)
        self.btn_quick_update.grid(row=1, column=3, sticky="ew", pady=5, padx=5)

        # [V10.0 NEW] Checkbox chọn chế độ phân tích
        mode_frame = ttk.Frame(input_frame)
        mode_frame.grid(row=2, column=0, columnspan=5, sticky="w", padx=5, pady=5)
        
        self.var_lo_mode = tk.BooleanVar(value=True)
        self.var_de_mode = tk.BooleanVar(value=True)
        
        ttk.Label(mode_frame, text="Chế độ chạy:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(mode_frame, text="Phân tích LÔ", variable=self.var_lo_mode).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(mode_frame, text="Phân tích ĐỀ", variable=self.var_de_mode).pack(side=tk.LEFT, padx=10)

        # === KHU VỰC 2: HERO ACTION (TRUNG TÂM) ===
        # Đây là nơi người dùng thao tác 90% thời gian
        hero_frame = ttk.Frame(self.tab1_frame)
        hero_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        hero_frame.columnconfigure(0, weight=2) # Dashboard to hơn
        hero_frame.columnconfigure(1, weight=1)

        # Nút TO NHẤT: Bảng Quyết Định (Đã đổi tên cho phù hợp ngữ cảnh)
        self.btn_open_dashboard = ttk.Button(
            hero_frame, 
            text="🚀 CHẠY PHÂN TÍCH\n(Theo chế độ đã chọn)", 
            style="Hero.TButton",
            command=self.run_decision_dashboard
        )
        self.btn_open_dashboard.grid(row=0, column=0, sticky="nsew", padx=(0, 10), ipady=25)

        # Nút VỪA: Quản Lý Cầu
        self.btn_bridge_manager = ttk.Button(
            hero_frame, 
            text="🛠️ QUẢN LÝ CẦU\n(Tinh chỉnh & Lọc)", 
            command=self.show_bridge_manager_window
        )
        self.btn_bridge_manager.grid(row=0, column=1, sticky="nsew", ipady=25)


        # === KHU VỰC 3: HỆ THỐNG & AI (ADVANCED) ===
        # Gom nhóm các chức năng ít dùng xuống dưới
        sys_frame = ttk.LabelFrame(self.tab1_frame, text="3. Hệ Thống & Trí Tuệ Nhân Tạo", padding="10")
        sys_frame.grid(row=2, column=0, sticky="ew", pady=15)
        for i in range(4): sys_frame.columnconfigure(i, weight=1)

        # Dòng 1
        self.btn_train_ai = ttk.Button(sys_frame, text="🧠 Huấn Luyện AI", command=self.run_train_ai)
        self.btn_train_ai.grid(row=0, column=0, sticky="ew", padx=5, pady=2)

        self.btn_auto_find = ttk.Button(sys_frame, text="🔍 Quét Cầu Đề Mới", command=self.show_de_scanner_window, style="Accent.TButton")
        self.btn_auto_find.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        self.btn_vote_stats = ttk.Button(sys_frame, text="📈 Thống Kê Vote", command=self.show_vote_statistics_window)
        self.btn_vote_stats.grid(row=0, column=2, sticky="ew", padx=5, pady=2)

        self.btn_settings = ttk.Button(sys_frame, text="⚙️ Cài Đặt", command=self.show_settings_window)
        self.btn_settings.grid(row=0, column=3, sticky="ew", padx=5, pady=2)

        # Dòng 2
        self.btn_tuner = ttk.Button(sys_frame, text="🎛️ Tinh Chỉnh Tham Số", command=self.show_tuner_window)
        self.btn_tuner.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(5,0))

        self.btn_refresh_cache = ttk.Button(sys_frame, text="🔄 Làm Mới Cache K2N", command=self.run_update_all_bridge_K2N_cache_from_main)
        self.btn_refresh_cache.grid(row=1, column=2, columnspan=2, sticky="ew", padx=5, pady=(5,0))

    def _setup_log_tab(self):
        self.tab_log_frame.columnconfigure(0, weight=1)
        self.tab_log_frame.rowconfigure(0, weight=1)
        
        self.output_text = tk.Text(self.tab_log_frame, height=15, width=80, font=("Courier New", 9))
        self.output_text.grid(row=0, column=0, sticky="nsew")
        
        scroll = ttk.Scrollbar(self.tab_log_frame, orient="vertical", command=self.output_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.output_text.config(yscrollcommand=scroll.set, state=tk.DISABLED)
        
        # Logger kết nối vào text box này
        self.logger = Logger(self.output_text, self.root)

    # --- ACTION HANDLERS ---

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=(("Data Files", "*.json;*.txt"), ("All Files", "*.*")))
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)

    def run_parsing(self):
        path = self.file_path_entry.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Lỗi", "Đường dẫn file không hợp lệ!")
            return
        if messagebox.askyesno("Xác nhận", "Hành động này sẽ XÓA HẾT dữ liệu cũ và nạp lại. Tiếp tục?"):
            self.logger.log("\n--- Bắt đầu Nạp Lại Dữ Liệu ---")
            self.task_manager.run_task(self.controller.task_run_parsing, path)

    def run_parsing_append(self):
        path = self.file_path_entry.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Lỗi", "Đường dẫn file không hợp lệ!")
            return
        if messagebox.askyesno("Xác nhận", "Bạn muốn NẠP THÊM dữ liệu từ file này vào Database hiện tại?"):
            self.logger.log("\n--- Bắt đầu Nạp Thêm Dữ Liệu ---")
            self.task_manager.run_task(self.controller.task_run_parsing_append, path)

    def run_update_from_text(self):
        text_data = self.update_text_area.get("1.0", tk.END).strip()
        if not text_data:
            messagebox.showwarning("Chưa nhập liệu", "Vui lòng dán kết quả xổ số vào ô trống.")
            return
        self.logger.log("\n--- Bắt đầu Cập Nhật Nhanh ---")
        self.task_manager.run_task(self.controller.task_run_update_from_text, text_data)

    def run_decision_dashboard(self):
        """
        [V10.1] Chạy Phân Tích & Điều Hướng Thông Minh.
        Tự động chuyển sang tab phù hợp dựa trên chế độ người dùng chọn.
        """
        # 1. Lấy trạng thái từ Checkbox
        lo_mode = self.var_lo_mode.get()
        de_mode = self.var_de_mode.get()
        
        # 2. Validate (Phải chọn ít nhất 1)
        if not lo_mode and not de_mode:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất: LÔ hoặc ĐỀ (hoặc cả hai)!", parent=self.root)
            return

        self.logger.log("\n--- Bắt đầu Phân Tích ---")
        
        # 3. [SMART NAV] Chuyển tab dựa trên nhu cầu
        # Nếu CHỈ chọn Đề -> Chuyển ngay sang tab Đề
        if de_mode and not lo_mode:
             self.notebook.select(self.de_dashboard_tab)
             self.logger.log("-> Chế độ: ĐỀ (Chuyển sang Tab Soi Cầu Đề)")
        
        # Các trường hợp khác (Chỉ Lô hoặc Cả hai) -> Chuyển sang Dashboard Lô
        else:
             self.notebook.select(self.dashboard_tab)
             mode_str = "LÔ & ĐỀ" if (lo_mode and de_mode) else "LÔ"
             self.logger.log(f"-> Chế độ: {mode_str} (Chuyển sang Tab Bảng Quyết Định)")

        # 4. Gửi lệnh xuống Controller
        self.task_manager.run_task(
            self.controller.task_run_decision_dashboard, 
            "Phân Tích Dữ Liệu", 
            lo_mode, 
            de_mode
        )

    def show_bridge_manager_window(self):
        try:
            from ui.ui_bridge_manager import BridgeManagerWindow
        except ImportError as e:
            self.logger.log(f"LỖI NGHIÊM TRỌNG khi mở BridgeManager: {e}")
            messagebox.showerror("Lỗi Import", f"Không thể tải ui_bridge_manager: {e}")
            return

        self.bridge_manager_window_instance = BridgeManagerWindow(self)
    
    def show_de_scanner_window(self):
        """[V11.0 NEW] Mở cửa sổ Quét Cầu Đề Mới"""
        try:
            from ui.ui_de_bridge_scanner import DeBridgeScannerWindow
            DeBridgeScannerWindow(self)
        except Exception as e:
            self.logger.log(f"Lỗi mở cửa sổ Quét Cầu: {e}")
            messagebox.showerror("Lỗi", f"Không thể mở cửa sổ Quét Cầu: {e}")

    # --- CÁC HÀM MÀ CONTROLLER CÓ THỂ GỌI (GIỮ NGUYÊN) ---
    def clear_update_text_area(self):
        self.update_text_area.delete("1.0", tk.END)

    def _show_dashboard_window(self, next_ky, stats_n_day, n_days_stats, consensus, high_win, pending_k2n_data, gan_stats, top_scores, top_memory_bridges, ai_predictions):
        # Hàm callback từ controller để hiển thị dữ liệu
        try:
            self.dashboard_tab.populate_data(
                next_ky, stats_n_day, n_days_stats, consensus, high_win, 
                pending_k2n_data, gan_stats, top_scores, top_memory_bridges, ai_predictions
            )
            
            # [FIX V10.2] Đã xóa dòng lệnh tự động chuyển tab.
            # Lý do: Việc chuyển tab đã được xử lý thông minh ngay khi bấm nút ở hàm run_decision_dashboard.
            # Code cũ gây lỗi: self.notebook.select(self.dashboard_tab) <--- ĐÃ XÓA

        except Exception as e:
            self.logger.log(f"LỖI HIỂN THỊ DASHBOARD: {e}")
            self._on_dashboard_close()

    def _on_dashboard_close(self):
        if hasattr(self.dashboard_tab, 'clear_data'):
            self.dashboard_tab.clear_data()

    # --- CÁC WRAPPER CHO TASK MANAGER (GIỮ NGUYÊN) ---
    def run_train_ai(self):
        self.task_manager.run_task(self.controller.task_run_train_ai, "Huấn luyện AI")

    def run_auto_find_bridges(self):
        self.task_manager.run_task(self.controller.task_run_auto_find_bridges, "Dò Cầu Tự Động")
    
    def run_auto_prune_bridges(self): # Vẫn giữ hàm này cho backward compatibility
        self.task_manager.run_task(self.controller.task_run_auto_prune_bridges, "Lọc Cầu")

    def run_auto_manage_bridges(self): # Vẫn giữ hàm này
        self.task_manager.run_task(self.controller.task_run_auto_manage_bridges, "Quản Lý Cầu")

    def run_update_all_bridge_K2N_cache_from_main(self):
        self.task_manager.run_task(self.controller.task_run_update_all_bridge_K2N_cache, "Cập nhật Cache")

    def show_vote_statistics_window(self):
        from ui.ui_vote_statistics import VoteStatisticsWindow
        VoteStatisticsWindow(self)

    def show_settings_window(self):
        SettingsWindow(self)

    def show_tuner_window(self):
        TunerWindow(self)
    
    def show_lookup_window(self):
        self.notebook.select(self.lookup_tab)

    # --- Optimizer Support ---
    def run_strategy_optimization(self, strategy, days, params, tab):
        self.task_manager.run_task(self.controller.task_run_strategy_optimization, strategy, days, params, tab)

    def apply_optimized_settings(self, config_dict_str, optimizer_window):
        try:
            config = json.loads(config_dict_str)
            if messagebox.askyesno("Áp dụng", f"Áp dụng cấu hình này?\n{config_dict_str}"):
                for k, v in config.items():
                    SETTINGS.update_setting(k, v)
                messagebox.showinfo("OK", "Đã lưu cấu hình!")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    # --- Backtest Support & Results Viewer (Kết nối Bridge Manager) ---
    def show_backtest_results(self, title, data, show_save=False):
        ResultsViewerWindow(self, title, data, show_save)
    
    def run_backtest(self, mode):
        self.task_manager.run_task(self.controller.task_run_backtest, mode, f"Backtest {mode}")
    
    def run_custom_backtest(self, mode):
        # Placeholder nếu cần gọi từ module khác
        pass 

    def run_backtest_memory(self):
        self.task_manager.run_task(self.controller.task_run_backtest_memory, "Backtest Bạc Nhớ")

    def run_backtest_managed_n1(self):
        self.task_manager.run_task(self.controller.task_run_backtest_managed_n1, "Backtest Cầu Lưu N1")

    def run_backtest_managed_k2n(self):
        self.task_manager.run_task(self.controller.task_run_backtest_managed_k2n, "Backtest Cầu Lưu K2N")
    
    def run_parameter_tuning(self, param_key, val_from, val_to, val_step, tuner_window):
        self.task_manager.run_task(self.controller.task_run_parameter_tuning, param_key, val_from, val_to, val_step, tuner_window)

    def trigger_bridge_backtest(self, bridge_name):
        """Kích hoạt backtest 30 ngày cho một cầu cụ thể"""
        if not bridge_name:
            return
        self.logger.log(f"Đang chạy backtest 30 ngày cho cầu: {bridge_name}")
        if self.controller:
            self.controller.trigger_bridge_backtest(bridge_name)
    
    def _save_bridge_from_treeview(self, tree):
        # Hàm hỗ trợ lưu cầu từ bảng kết quả
        try:
            selected_item = tree.focus()
            if not selected_item: return
            item_values = tree.item(selected_item, "values")
            bridge_name, win_rate = item_values[1], item_values[3]
            
            description = simpledialog.askstring("Lưu Cầu", f"Mô tả cho: {bridge_name}", initialvalue=bridge_name)
            if description:
                success, msg = upsert_managed_bridge(bridge_name, description, win_rate)
                if success: messagebox.showinfo("OK", msg)
                else: messagebox.showerror("Lỗi", msg)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))