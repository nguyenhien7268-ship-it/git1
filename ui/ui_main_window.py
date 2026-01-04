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
except Exception as e:
    print(f"ERROR: Could not import lottery_service. Details: {e}")
    # Print sys.path to debug
    import sys
    print(f"DEBUG PATH: {sys.path}")
    exit()

try:
    from app_controller import AppController
    from core_services import Logger, TaskManager
except ImportError as e:
    print(f"ERROR: Could not import core_services/app_controller. Details: {e}")
    exit()

try:
    from logic.config_manager import SETTINGS
except ImportError:
    SETTINGS = None

# Import Theme Engine
try:
    from ui.styles import ThemeColor, AppFont, LayoutConfig
except ImportError:
    # Fallback minimal theme
    class ThemeColor:
        BG_MAIN = "#f0f0f0"
        BG_WHITE = "#ffffff"
        PRIMARY = "#0078d7"
        TEXT_MAIN = "#000000"
        TEXT_WHITE = "#ffffff"
        PRIMARY_DARK = "#005a9e"
    class AppFont:
        BODY_NORMAL = ("Arial", 10)
        TITLE_NORMAL = ("Arial", 12, "bold")
        TITLE_LARGE = ("Arial", 16, "bold")
        BODY_BOLD = ("Arial", 10, "bold")
    class LayoutConfig:
        PAD_M = 10
        PAD_S = 5

# Import UI Components
try:
    from ui.ui_dashboard import DashboardWindow
    from ui.ui_de_dashboard import UiDeDashboard
    from ui.ui_lookup import LookupWindow
    from ui.ui_optimizer import OptimizerTab
    from ui.ui_results_viewer import ResultsViewerWindow
    from ui.ui_settings import SettingsWindow
    from ui.ui_tuner import TunerWindow
    # NEW: Bridge Scanner and Management tabs
    from ui.ui_bridge_scanner import BridgeScannerTab
    from ui.ui_bridge_management import BridgeManagementTab
except ImportError as e:
    print(f"LỖI UI IMPORTS: {e}")
    exit()


class DataAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Xổ Số Data Analysis (v8.0 - Clean UX)")
        self.root.geometry("1300x850") # Larger default size
        
        # Apply Theme
        self.root.configure(bg=ThemeColor.BG_MAIN)
        self._apply_global_styles()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.db_name = DB_NAME
        
        # --- CÁC BIẾN CONTROLLER ---
        self.bridge_manager_window = None
        self.bridge_manager_window_instance = None
        self.settings_window = None
        self.tuner_window = None
        self.de_dashboard_tab = None

        # --- NOTEBOOK CHÍNH ---
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=LayoutConfig.PAD_S, pady=LayoutConfig.PAD_S)

        # ======================================================================
        # [QUAN TRỌNG] KHỞI TẠO LOGGER TRƯỚC TIÊN
        # ======================================================================
        self.tab_log_frame = ttk.Frame(self.notebook, padding=str(LayoutConfig.PAD_M))
        self._setup_log_tab()
        
        # Init Controller (Pass logger immediately)
        if AppController:
            self.controller = AppController(self)
            self.controller.set_logger(self.logger)
        else:
            self.controller = None
            self.logger.log("CRITICAL ERROR: AppController not found!")

        # Đồng bộ DB Name
        if self.controller:
            self.db_name = self.controller.db_name

        # --- SETUP TABS ---
        self._setup_tabs()

        # --- SETUP MENU ---
        self._setup_menu()

        # --- SERVICES ---
        # Buttons list for blocking when busy
        self.all_buttons = [] # Populated in _setup_home_tab and other tabs
        
        # Init Task Manager
        self.task_manager = TaskManager(self.logger, self.all_buttons, self.root)
        
        # Add extra buttons from tabs
        if hasattr(self, 'optimizer_tab') and hasattr(self.optimizer_tab, 'run_button'):
             self.task_manager.all_buttons.append(self.optimizer_tab.run_button)

        self.logger.log("✅ Giao diện (V8.0) khởi tạo thành công.")
        self.logger.log(f"Database: {self.db_name}")

    def _apply_global_styles(self):
        style = ttk.Style()
        style.theme_use('clam')  # Base theme
        
        # Configure TFrame
        style.configure("TFrame", background=ThemeColor.BG_MAIN)
        style.configure("TLabelframe", background=ThemeColor.BG_MAIN, foreground=ThemeColor.TEXT_MAIN)
        style.configure("TLabelframe.Label", background=ThemeColor.BG_MAIN, foreground=ThemeColor.PRIMARY, font=AppFont.BODY_BOLD)
        
        # Configure TButton (Default style with better borders)
        style.configure("TButton", 
            font=AppFont.BODY_NORMAL,
            background="#F8F8F9",  # Softer white
            foreground=ThemeColor.TEXT_MAIN,
            borderwidth=1,
            relief="solid",
            focusthickness=0
        )
        style.map("TButton",
            background=[('active', "#E8E8ED"), ('pressed', "#D1D1D6"), ('disabled', "#F0F0F2")],
            foreground=[('disabled', ThemeColor.TEXT_SECONDARY)],
            relief=[('pressed', 'sunken')]
        )
        
        # Configure Hero.TButton (Large, Soft Gray - Elegant)
        style.configure("Hero.TButton", 
            font=AppFont.TITLE_NORMAL,
            background="#E8E8ED",  # Soft gray like old design
            foreground=ThemeColor.TEXT_MAIN,
            borderwidth=2,
            relief="solid",
            padding=15
        )
        style.map("Hero.TButton",
            background=[('active', "#D1D1D6"), ('pressed', "#C0C0C8")],
            relief=[('pressed', 'sunken')]
        )

        # Configure Accent.TButton (Vibrant accent for important actions)
        style.configure("Accent.TButton",
            font=AppFont.BODY_BOLD,
            background=ThemeColor.PRIMARY,
            foreground=ThemeColor.TEXT_WHITE,
            borderwidth=0,
            relief="flat"
        )
        style.map("Accent.TButton",
            background=[('active', ThemeColor.PRIMARY_DARK), ('pressed', "#0056b3")],
            relief=[('pressed', 'sunken')]
        )
        
        # Configure Compact.TLabel
        style.configure("Compact.TLabel",
            background=ThemeColor.BG_MAIN,
            foreground=ThemeColor.TEXT_SECONDARY,
            font=AppFont.SMALL
        )

    def _setup_tabs(self):
        # 1. Dashboard (Table Home)
        self.tab1_frame = ttk.Frame(self.notebook, padding=str(LayoutConfig.PAD_M))
        
        try: self.dashboard_tab = DashboardWindow(self)
        except Exception as e: 
            self.logger.log(f"Err Dashboard: {e}")
            self.dashboard_tab = ttk.Frame(self.notebook)

        try: self.de_dashboard_tab = UiDeDashboard(self.notebook, self.controller)
        except Exception as e:
            self.logger.log(f"Err DeDashboard: {e}")
            self.de_dashboard_tab = ttk.Frame(self.notebook)

        try: self.bridge_scanner_tab = BridgeScannerTab(self.notebook, self)
        except Exception as e:
            self.logger.log(f"Err Scanner: {e}")
            self.bridge_scanner_tab = ttk.Frame(self.notebook)

        try: self.bridge_management_tab = BridgeManagementTab(self.notebook, self)
        except Exception as e:
            self.logger.log(f"Err Manager: {e}")
            self.bridge_management_tab = ttk.Frame(self.notebook)
            
        try: self.lookup_tab = LookupWindow(self)
        except: self.lookup_tab = ttk.Frame(self.notebook)
        
        try: self.optimizer_tab = OptimizerTab(self.notebook, self)
        except: self.optimizer_tab = ttk.Frame(self.notebook)

        # Add to Notebook
        self.notebook.add(self.tab1_frame, text="🏠 Trang Chủ")
        self.notebook.add(self.dashboard_tab, text="📊 Bảng Quyết Định")
        self.notebook.add(self.de_dashboard_tab, text="🔮 Soi Cầu Đề")
        self.notebook.add(self.bridge_scanner_tab, text="🔍 Dò Tìm Cầu")
        self.notebook.add(self.bridge_management_tab, text="🛠️ Quản Lý Cầu")
        self.notebook.add(self.lookup_tab, text="📖 Tra Cứu")
        self.notebook.add(self.optimizer_tab, text="🚀 Tối Ưu")
        self.notebook.add(self.tab_log_frame, text="📝 Logs")
        
        # Setup Home Tab Content (This was missing!)
        self._setup_home_tab()
    
    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hệ Thống", menu=file_menu)
        file_menu.add_command(label="Mở File Dữ Liệu", command=self.browse_file)
        file_menu.add_separator()
        file_menu.add_command(label="Cài Đặt", command=self.show_settings_window)
        file_menu.add_command(label="Thoát", command=self.root.quit)

    def _setup_home_tab(self):
        """Dựng giao diện Trang Chủ: Gọn gàng, tập trung."""
        self.tab1_frame.columnconfigure(0, weight=1)
        
        # === KHU VỰC 1: NHẬP LIỆU (COMPACT) ===
        input_frame = ttk.LabelFrame(self.tab1_frame, text="1. Dữ Liệu Đầu Vào", padding=str(LayoutConfig.PAD_S))
        input_frame.grid(row=0, column=0, sticky="ew", pady=(0, LayoutConfig.PAD_M))
        input_frame.columnconfigure(1, weight=1)

        # Hàng 1: Chọn File
        ttk.Label(input_frame, text="File:", style="Compact.TLabel").grid(row=0, column=0, sticky="w", padx=LayoutConfig.PAD_S)
        self.file_path_entry = ttk.Entry(input_frame)
        self.file_path_entry.grid(row=0, column=1, sticky="ew", padx=LayoutConfig.PAD_S)
        ttk.Button(input_frame, text="...", width=4, command=self.browse_file).grid(row=0, column=2, padx=LayoutConfig.PAD_XS)
        self.btn_load_file = ttk.Button(input_frame, text="Nạp Mới", command=self.run_parsing)
        self.btn_load_file.grid(row=0, column=3, padx=LayoutConfig.PAD_XS)
        self.btn_load_append = ttk.Button(input_frame, text="Nạp Thêm", command=self.run_parsing_append)
        self.btn_load_append.grid(row=0, column=4, padx=LayoutConfig.PAD_XS)

        # Hàng 2: Nhập Text
        ttk.Label(input_frame, text="Paste KQ:", style="Compact.TLabel").grid(row=1, column=0, sticky="nw", padx=LayoutConfig.PAD_S, pady=LayoutConfig.PAD_S)
        
        self.update_text_area = tk.Text(input_frame, height=4, width=60, font=AppFont.MONO)
        self.update_text_area.grid(row=1, column=1, columnspan=2, sticky="ew", pady=LayoutConfig.PAD_S, padx=LayoutConfig.PAD_S)
        
        # Nút Cập Nhật Nổi Bật
        self.btn_quick_update = ttk.Button(input_frame, text="⚡ CẬP NHẬT NGAY", style="Accent.TButton", command=self.run_update_from_text)
        self.btn_quick_update.grid(row=1, column=3, sticky="ew", pady=LayoutConfig.PAD_S, padx=LayoutConfig.PAD_S)

        # Checkbox chọn chế độ phân tích
        mode_frame = ttk.Frame(input_frame)
        mode_frame.grid(row=2, column=0, columnspan=5, sticky="w", padx=LayoutConfig.PAD_S, pady=LayoutConfig.PAD_S)
        
        self.var_lo_mode = tk.BooleanVar(value=True)
        self.var_de_mode = tk.BooleanVar(value=True)
        
        ttk.Label(mode_frame, text="Chế độ chạy:", font=AppFont.BODY_BOLD).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(mode_frame, text="Phân tích LÔ", variable=self.var_lo_mode).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(mode_frame, text="Phân tích ĐỀ", variable=self.var_de_mode).pack(side=tk.LEFT, padx=10)

        # === KHU VỰC 2: HERO ACTION (TRUNG TÂM) ===
        hero_frame = ttk.Frame(self.tab1_frame)
        hero_frame.grid(row=1, column=0, sticky="nsew", pady=LayoutConfig.PAD_M)
        hero_frame.columnconfigure(0, weight=2)
        hero_frame.columnconfigure(1, weight=1)

        self.btn_open_dashboard = ttk.Button(
            hero_frame, 
            text="🚀 CHẠY PHÂN TÍCH\n(Theo chế độ đã chọn)", 
            style="Hero.TButton",
            command=self.run_decision_dashboard
        )
        self.btn_open_dashboard.grid(row=0, column=0, columnspan=2, sticky="nsew", ipady=20)

        # === KHU VỰC 3: HỆ THỐNG & AI ===
        sys_frame = ttk.LabelFrame(self.tab1_frame, text="3. Toolset", padding=str(LayoutConfig.PAD_M))
        sys_frame.grid(row=2, column=0, sticky="ew", pady=LayoutConfig.PAD_L)
        for i in range(4): sys_frame.columnconfigure(i, weight=1)

        # Dòng 1
        self.btn_train_ai = ttk.Button(sys_frame, text="🧠 Huấn Luyện AI", command=self.run_train_ai)
        self.btn_train_ai.grid(row=0, column=0, sticky="ew", padx=5, pady=2)

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
        """Switch to Bridge Management tab (old method kept for compatibility)."""
        try:
            # Switch to the new Bridge Management tab
            self.notebook.select(self.bridge_management_tab)
            # Refresh the list
            if hasattr(self.bridge_management_tab, 'refresh_bridge_list'):
                self.bridge_management_tab.refresh_bridge_list()
        except Exception as e:
            self.logger.log(f"Lỗi chuyển tab Quản Lý Cầu: {e}")
            messagebox.showerror("Lỗi", f"Không thể mở tab Quản Lý Cầu: {e}")

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
        """Switch to Bridge Scanner tab (old method kept for compatibility)."""
        try:
            # Switch to the new Bridge Scanner tab
            self.notebook.select(self.bridge_scanner_tab)
            self.logger.log("Đã chuyển sang tab Dò Tìm Cầu Mới. Vui lòng chọn loại quét.")
        except Exception as e:
            self.logger.log(f"Lỗi chuyển tab Dò Tìm Cầu: {e}")
            messagebox.showerror("Lỗi", f"Không thể mở tab Dò Tìm Cầu: {e}")
    
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