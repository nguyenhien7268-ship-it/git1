# Tên file: du-an-backup/ui/ui_main_window.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - TỐI ƯU UX GIAO DIỆN CHÍNH)
#
import json
import os
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, simpledialog, ttk

# (GIỮ NGUYÊN)
try:
    from lottery_service import DB_NAME, upsert_managed_bridge, add_managed_bridge_adapter
except ImportError:
    print(
        "LỖI NGHIÊM TRỌNG: Không tìm thấy file 'lottery_service.py' hoặc gói '/logic'."
    )
    exit()

# (GIỮ NGUYÊN)
try:
    from app_controller import AppController
    from core_services import Logger, TaskManager
except ImportError:
    print(
        "LỖI NGHIÊM TRỌNG: Không tìm thấy 'core_services.py' hoặc 'app_controller.py'."
    )
    exit()

# (GIỮ NGUYÊN)
try:
    from logic.config_manager import SETTINGS
except ImportError:
    print(
        "LỖI: ui_main_window.py không thể import logic.config_manager. Sử dụng giá trị mặc định."
    )
    SETTINGS = type(
        "obj",
        (object,),
        {
            "STATS_DAYS": 7,
            "GAN_DAYS": 15,
            "HIGH_WIN_THRESHOLD": 47.0,
            "AUTO_ADD_MIN_RATE": 50.0,
            "AUTO_PRUNE_MIN_RATE": 40.0,
            "K2N_RISK_START_THRESHOLD": 4,
            "K2N_RISK_PENALTY_PER_FRAME": 0.5,
        },
    )

# (SỬA LỖI CIRCULAR IMPORT)
try:
    from ui.ui_dashboard import DashboardWindow
    from ui.ui_lookup import LookupWindow
    from ui.ui_optimizer import OptimizerTab
    from ui.ui_results_viewer import ResultsViewerWindow
    from ui.ui_settings import SettingsWindow
    from ui.ui_tuner import TunerWindow
except ImportError as e:
    print(f"LỖI NGHIÊM TRỌNG: Không thể import các cửa sổ con (trừ BridgeManager): {e}")
    exit()


class DataAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Xổ Số Data Analysis (v7.5 - Giao diện Tối ưu)")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry("1024x768")

        self.db_name = DB_NAME

        self.bridge_manager_window = None
        self.bridge_manager_window_instance = None
        self.settings_window = None
        self.tuner_window = None

        self.dashboard_tab = None
        self.lookup_tab = None
        self.optimizer_tab = None

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5
        )

        # --- KHỞI TẠO CÁC TAB ---

        # 1. Tạo Khung Tab Log
        self.tab_log_frame = ttk.Frame(self.notebook, padding="10")
        self.tab_log_frame.columnconfigure(0, weight=1)
        self.tab_log_frame.rowconfigure(0, weight=1)

        # 2. Tạo Khung Output và self.output_text
        output_frame = ttk.Frame(self.tab_log_frame, padding="10")
        output_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)
        ttk.Label(output_frame, text="Output Log:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.output_text = tk.Text(
            output_frame, height=25, width=80, font=("Courier New", 10)
        )
        self.output_text.grid(
            row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5
        )
        log_scrollbar = ttk.Scrollbar(
            output_frame, orient=tk.VERTICAL, command=self.output_text.yview
        )
        log_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.output_text.config(yscrollcommand=log_scrollbar.set, state=tk.DISABLED)

        # 3. Khởi tạo Logger
        self.logger = Logger(self.output_text, self.root)

        # 4. Khởi tạo các Tab còn lại
        self.tab1_frame = ttk.Frame(self.notebook, padding="10")
        self.tab1_frame.columnconfigure(0, weight=1)
        self.tab1_frame.rowconfigure(0, weight=0)
        self.tab1_frame.rowconfigure(1, weight=1)

        self.dashboard_tab = DashboardWindow(self)
        self.lookup_tab = LookupWindow(self)
        self.optimizer_tab = OptimizerTab(self.notebook, self)

        # 5. ADD CÁC TAB VÀO NOTEBOOK
        self.notebook.add(self.tab1_frame, text="⚙️ Điều Khiển")
        self.notebook.add(self.dashboard_tab, text="📊 Bảng Quyết Định")
        self.notebook.add(self.lookup_tab, text="🔍 Tra Cứu")
        self.notebook.add(self.optimizer_tab, text="🚀 Tối ưu Hóa")
        self.notebook.add(self.tab_log_frame, text="Log Hệ Thống")

        # --- TÁI CẤU TRÚC TAB "ĐIỀU KHIỂN" ---

        # 1. Khung Chức Năng Chính (Hàng 0)
        predict_frame = ttk.Labelframe(
            self.tab1_frame, text="📈 Chức Năng Chính", padding="10"
        )
        predict_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=5)
        predict_frame.columnconfigure(0, weight=1)
        predict_frame.columnconfigure(1, weight=1)
        self.dashboard_button = ttk.Button(
            predict_frame,
            text="Mở/Làm Mới Bảng Quyết Định",
            command=self.run_decision_dashboard,
        )
        self.dashboard_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.update_cache_button = ttk.Button(
            predict_frame,
            text="Cập nhật Cache K2N",
            command=self.run_update_all_bridge_K2N_cache_from_main,
        )
        self.update_cache_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # 2. Tạo Notebook con (Hàng 1)
        sub_notebook = ttk.Notebook(self.tab1_frame)
        sub_notebook.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 0))

        # 3. Tạo các Tab con cho Notebook con
        data_frame_tab = ttk.Frame(sub_notebook, padding=(10, 5))
        manage_frame_tab = ttk.Frame(sub_notebook, padding=(10, 5))
        backtest_frame_tab = ttk.Frame(sub_notebook, padding=(10, 5))
        sub_notebook.add(data_frame_tab, text="💾 Nạp/Cập Nhật Dữ Liệu")
        sub_notebook.add(manage_frame_tab, text="🛠️ Quản lý & Dò Cầu")
        sub_notebook.add(backtest_frame_tab, text="🔍 Backtest (Phân tích sâu)")

        # 4. Di chuyển các Khung (Frame) vào các Tab con

        # --- TỐI ƯU HÓA GIAO DIỆN TAB NẠP DỮ LIỆU ---
        data_frame_tab.columnconfigure(0, weight=1)
        data_frame_tab.rowconfigure(0, weight=1)
        data_frame = ttk.Labelframe(
            data_frame_tab, text="💾 Nạp/Cập Nhật Dữ Liệu", padding="10"
        )
        data_frame.grid(row=0, column=0, sticky="nsew")
        data_frame.columnconfigure(1, weight=1)
        data_frame.rowconfigure(4, weight=1)  # Text box expand

        # Phần 1: File Import
        ttk.Label(data_frame, text="File Đầu Vào:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.file_path_entry = ttk.Entry(data_frame, width=50)
        self.file_path_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        browse_button = ttk.Button(data_frame, text="Chọn File...", command=self.browse_file)
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        self.parse_button = ttk.Button(
            data_frame, text="Xóa Hết & Nạp Lại DB", command=self.run_parsing
        )
        self.parse_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.parse_append_button = ttk.Button(
            data_frame, text="Nạp Thêm Dữ Liệu (Append)", command=self.run_parsing_append
        )
        self.parse_append_button.grid(
            row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5
        )

        # Đường phân cách
        ttk.Separator(data_frame, orient='horizontal').grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=10
        )

        # Phần 2: Manual Text Input (Giao diện tối ưu)
        # Tạo frame chứa Label và Button trên cùng 1 hàng
        manual_header_frame = ttk.Frame(data_frame)
        manual_header_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=(0, 5))
        
        ttk.Label(manual_header_frame, text="Dán dữ liệu text (1 hoặc nhiều kỳ):", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        
        # Nút bấm nằm ngay bên phải (Action Button)
        self.update_button = ttk.Button(
            manual_header_frame,
            text="⚡ Cập Nhật Ngay",
            command=self.run_update_from_text,
        )
        self.update_button.pack(side=tk.RIGHT)

        # Text area
        self.update_text_area = tk.Text(data_frame, height=8, width=80) # Tăng chiều cao chút
        self.update_text_area.grid(
            row=4, column=0, columnspan=3, sticky="nsew", padx=5, pady=5
        )

        # --- Khung QUẢN LÝ ---
        manage_frame_tab.columnconfigure(0, weight=1)
        manage_frame_tab.rowconfigure(0, weight=1)
        manage_frame = ttk.Labelframe(
            manage_frame_tab, text="🛠️ Quản lý & Dò Cầu (Bảo trì)", padding="10"
        )
        manage_frame.grid(row=0, column=0, sticky="nsew")
        manage_frame.columnconfigure(0, weight=1)
        manage_frame.columnconfigure(1, weight=1)
        manage_frame.columnconfigure(2, weight=1)
        self.manage_bridges_button = ttk.Button(
            manage_frame,
            text="Quản lý Cầu (V17)...",
            command=self.show_bridge_manager_window,
        )
        self.manage_bridges_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.auto_find_bridges_button = ttk.Button(
            manage_frame,
            text="Tự động Dò & Thêm Cầu (V17+BN)",
            command=self.run_auto_find_bridges,
        )
        self.auto_find_bridges_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.auto_prune_bridges_button = ttk.Button(
            manage_frame,
            text="Tự động Lọc/Tắt Cầu Yếu",
            command=self.run_auto_prune_bridges,
        )
        self.auto_prune_bridges_button.grid(
            row=0, column=2, sticky="ew", padx=5, pady=5
        )
        self.auto_manage_bridges_button = ttk.Button(
            manage_frame,
            text="🔄 Quản Lý Cầu Tự Động (Bật+Tắt)",
            command=self.run_auto_manage_bridges,
        )
        self.auto_manage_bridges_button.grid(
            row=0, column=3, sticky="ew", padx=5, pady=5
        )
        self.vote_stats_button = ttk.Button(
            manage_frame,
            text="📊 Thống Kê Vote",
            command=self.show_vote_statistics_window,
        )
        self.vote_stats_button.grid(
            row=1, column=0, sticky="ew", padx=5, pady=5
        )
        self.settings_button = ttk.Button(
            manage_frame, text="⚙️ Cài đặt Tham số...", command=self.show_settings_window
        )
        self.settings_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.tuner_button = ttk.Button(
            manage_frame,
            text="📈 Tinh chỉnh Tham số...",
            command=self.show_tuner_window,
        )
        self.tuner_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)
        self.train_ai_button = ttk.Button(
            manage_frame, text="🧠 Huấn luyện AI...", command=self.run_train_ai
        )
        self.train_ai_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        # --- Khung BACKTEST ---
        backtest_frame_tab.columnconfigure(0, weight=1)
        backtest_frame_tab.rowconfigure(0, weight=1)
        v25_frame = ttk.Labelframe(
            backtest_frame_tab,
            text="🔍 Backtest & Tra Cứu (Phân tích sâu)",
            padding="10",
        )
        v25_frame.grid(row=0, column=0, sticky="nsew")
        v25_frame.columnconfigure(0, weight=1)
        v25_frame.columnconfigure(1, weight=1)
        v25_frame.columnconfigure(2, weight=1)
        self.lookup_button = ttk.Button(
            v25_frame, text="Tra Cứu Kết Quả (Mở Tab)", command=self.show_lookup_window
        )
        self.lookup_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.backtest_n1_15_button = ttk.Button(
            v25_frame,
            text="Backtest 15 Cầu (N1)",
            command=lambda: self.run_backtest("N1"),
        )
        self.backtest_n1_15_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.backtest_k2n_15_button = ttk.Button(
            v25_frame,
            text="Backtest 15 Cầu (K2N)",
            command=lambda: self.run_backtest("K2N"),
        )
        self.backtest_k2n_15_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        self.backtest_memory_button = ttk.Button(
            v25_frame,
            text="Backtest 756 Cầu Bạc Nhớ (N1)",
            command=self.run_backtest_memory,
        )
        self.backtest_memory_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.backtest_managed_button = ttk.Button(
            v25_frame,
            text="Backtest Cầu Đã Lưu (N1)",
            command=self.run_backtest_managed_n1,
        )
        self.backtest_managed_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.backtest_managed_k2n_button = ttk.Button(
            v25_frame,
            text="Backtest Cầu Đã Lưu (K2N)",
            command=self.run_backtest_managed_k2n,
        )
        self.backtest_managed_k2n_button.grid(
            row=1, column=2, sticky="ew", padx=5, pady=5
        )
        self.custom_bridge_entry = ttk.Entry(v25_frame)

        # --- Danh sách nút tổng ---
        self.all_buttons = [
            self.parse_button,
            self.parse_append_button,
            self.update_button,
            self.dashboard_button,
            self.update_cache_button,
            self.manage_bridges_button,
            self.auto_find_bridges_button,
            self.auto_prune_bridges_button,
            self.auto_manage_bridges_button,
            self.vote_stats_button,
            self.settings_button,
            self.tuner_button,
            self.train_ai_button,
            self.lookup_button,
            self.backtest_n1_15_button,
            self.backtest_k2n_15_button,
            self.backtest_memory_button,
            self.backtest_managed_button,
            self.backtest_managed_k2n_button,
            self.optimizer_tab.run_button,
            self.optimizer_tab.apply_button,
        ]

        # --- KHỞI TẠO CÁC DỊCH VỤ LÕI & CONTROLLER ---
        self.task_manager = TaskManager(self.logger, self.all_buttons, self.root)
        self.task_manager.optimizer_apply_button = self.optimizer_tab.apply_button

        self.controller = AppController(self)
        self.controller.logger = self.logger

        self.logger.log("Hệ thống sẵn sàng (UI Tối Ưu).")

    # --- HÀM XÓA TEXT (Callback cho Controller) ---
    def clear_update_text_area(self):
        """Hàm này được gọi từ controller để xóa text box (an toàn)."""
        if self.update_text_area:
            self.update_text_area.delete("1.0", tk.END)

    def update_output(self, msg):
        """Cập nhật output log. Được gọi từ các cửa sổ phụ."""
        self.logger.log(msg)

    # --- CÁC HÀM LOGIC (GIỮ NGUYÊN) ---

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=".",
            title="Select Input File",
            filetypes=(
                ("JSON files", "*.json"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*"),
            ),
        )
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)
            self.logger.log(f"Selected file: {file_path}")

    def check_file_path(self):
        input_file = self.file_path_entry.get()
        if not input_file:
            self.logger.log("Lỗi: Vui lòng chọn một tệp tin đầu vào.")
            return None
        if not os.path.exists(input_file):
            self.logger.log(f"Lỗi: Không tìm thấy tệp tin tại '{input_file}'")
            return None
        return input_file

    def run_parsing(self):
        input_file = self.check_file_path()
        if not input_file:
            return
        self.logger.log("\n--- Bắt đầu Bước 1 (Xóa Hết): Phân tích tệp tin ---")
        self.task_manager.run_task(self.controller.task_run_parsing, input_file)

    def run_parsing_append(self):
        input_file = self.check_file_path()
        if not input_file:
            return
        self.logger.log("\n--- Bắt đầu Bước 1 (Append): Thêm dữ liệu từ tệp tin ---")
        self.task_manager.run_task(self.controller.task_run_parsing_append, input_file)

    def run_update_from_text(self):
        raw_data = self.update_text_area.get("1.0", tk.END)
        if not raw_data.strip():
            self.logger.log("LỖI: Không có dữ liệu text để cập nhật.")
            return
        self.logger.log("\n--- Bắt đầu: Thêm Kỳ Mới Từ Text ---")
        self.task_manager.run_task(self.controller.task_run_update_from_text, raw_data)

    def run_backtest(self, mode):
        title = f"Backtest 15 Cầu {mode}"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        self.task_manager.run_task(self.controller.task_run_backtest, mode, title)

    def run_custom_backtest(self, mode):
        custom_bridge_name = self.custom_bridge_entry.get()
        if not custom_bridge_name or (
            "+" not in custom_bridge_name
            and "Bong(" not in custom_bridge_name
            and "Tổng(" not in custom_bridge_name
            and "Hiệu(" not in custom_bridge_name
        ):
            self.logger.log("LỖI: Tên cầu không hợp lệ để test.")
            return
        title = f"Test Cầu {mode}: {custom_bridge_name}"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        self.task_manager.run_task(
            self.controller.task_run_custom_backtest, mode, title, custom_bridge_name
        )

    def run_backtest_managed_n1(self):
        title = "Backtest Cầu Đã Lưu (N1)"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        self.logger.log("Đang tải danh sách cầu và chạy backtest...")
        self.task_manager.run_task(self.controller.task_run_backtest_managed_n1, title)

    def run_backtest_managed_k2n(self):
        title = "Backtest Cầu Đã Lưu (K2N)"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        self.logger.log("Đang tải danh sách cầu và chạy backtest K2N (với Chuỗi)...")
        self.task_manager.run_task(self.controller.task_run_backtest_managed_k2n, title)

    def run_update_all_bridge_K2N_cache_from_main(self):
        title = "Cập nhật Cache K2N Hàng Loạt"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        self.logger.log("Đang chạy Backtest K2N (tối ưu) cho 15 Cầu CĐ + Cầu Đã Lưu...")
        self.task_manager.run_task(
            self.controller.task_run_update_all_bridge_K2N_cache, title
        )

    def run_auto_find_bridges(self):
        title = "Tự động Dò & Thêm Cầu V17 + Bạc Nhớ"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        try:
            auto_add_rate = SETTINGS.AUTO_ADD_MIN_RATE
        except Exception:
            auto_add_rate = 50.0
        self.logger.log("CẢNH BÁO: Tác vụ này RẤT NẶNG. Vui lòng chờ...")
        self.logger.log(
            f"Các cầu có Tỷ lệ > {auto_add_rate}% sẽ được tự động thêm/cập nhật..."
        )
        self.task_manager.run_task(self.controller.task_run_auto_find_bridges, title)

    def run_auto_prune_bridges(self):
        title = "Tự động Lọc/Tắt Cầu Yếu"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        try:
            auto_prune_rate = SETTINGS.AUTO_PRUNE_MIN_RATE
        except Exception:
            auto_prune_rate = 40.0
        self.logger.log("Đang kiểm tra cache K2N của các Cầu Đã Lưu...")
        self.logger.log(
            f"Các cầu có Tỷ lệ < {auto_prune_rate}% sẽ bị TẮT (vô hiệu hóa)..."
        )
        self.task_manager.run_task(self.controller.task_run_auto_prune_bridges, title)

    def run_auto_manage_bridges(self):
        title = "Quản Lý Cầu Tự Động (BẬT/TẮT)"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        try:
            auto_add_rate = SETTINGS.AUTO_ADD_MIN_RATE
            auto_prune_rate = SETTINGS.AUTO_PRUNE_MIN_RATE
        except Exception:
            auto_add_rate = 50.0
            auto_prune_rate = 40.0
        self.logger.log("Đang kiểm tra cache K2N của TẤT CẢ Cầu Đã Lưu...")
        self.logger.log(
            f"✅ Cầu có Tỷ lệ >= {auto_add_rate}% sẽ được BẬT\n"
            f"❌ Cầu có Tỷ lệ < {auto_prune_rate}% sẽ bị TẮT"
        )
        self.task_manager.run_task(self.controller.task_run_auto_manage_bridges, title)

    def run_train_ai(self):
        title = "Huấn luyện Mô hình AI (V6.0)"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        self.logger.log("CẢNH BÁO: Tác vụ này RẤT NẶNG và có thể mất vài phút.")
        self.logger.log("Đang tải toàn bộ CSDL và trích xuất đặc trưng...")
        self.task_manager.run_task(self.controller.task_run_train_ai, title)

    def run_backtest_memory(self):
        title = "Backtest 756 Cầu Bạc Nhớ (N1)"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        self.logger.log("Đang chạy backtest 756 thuật toán...")
        self.task_manager.run_task(self.controller.task_run_backtest_memory, title)

    def run_parameter_tuning(self, param_key, val_from, val_to, val_step, tuner_window):
        self.task_manager.run_task(
            self.controller.task_run_parameter_tuning,
            param_key,
            val_from,
            val_to,
            val_step,
            tuner_window,
        )

    def run_strategy_optimization(
        self, strategy, days_to_test, param_ranges, optimizer_tab
    ):
        self.task_manager.run_task(
            self.controller.task_run_strategy_optimization,
            strategy,
            days_to_test,
            param_ranges,
            optimizer_tab,
        )

    def apply_optimized_settings(self, config_dict_str, optimizer_window):
        try:

            def log_to_optimizer(message):
                self.root.after(0, optimizer_window.log, message)

            config_dict = json.loads(config_dict_str)
            if not messagebox.askyesno(
                "Xác nhận Áp dụng",
                f"Bạn có chắc chắn muốn áp dụng cấu hình này và lưu vào 'config.json' không?\n\n{config_dict_str}",
                parent=optimizer_window,
            ):
                return
            log_to_optimizer("Đang áp dụng cấu hình mới...")
            for key, value in config_dict.items():
                success, msg = SETTINGS.update_setting(key, value)
                if success:
                    log_to_optimizer(f" - Đã lưu: {key} = {value}")
                else:
                    log_to_optimizer(f" - LỖI LƯU: {msg}")
            log_to_optimizer("--- Áp dụng hoàn tất! ---")
            messagebox.showinfo(
                "Thành công", "Đã áp dụng và lưu cấu hình mới!", parent=optimizer_window
            )
        except Exception as e:
            messagebox.showerror(
                "Lỗi", f"Lỗi khi áp dụng cấu hình: {e}", parent=optimizer_window
            )

    def run_decision_dashboard(self):
        title = "Bảng Quyết Định Tối Ưu"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        if self.dashboard_tab.title_label.cget("text") != "Đang tải...":
            self.logger.log("Đang chạy lại 5 hệ thống phân tích cốt lõi để cập nhật...")
        else:
            self.logger.log(
                "Đang chạy 5 hệ thống phân tích cốt lõi... (Bao gồm 1 AI và 1 Cache K2N)"
            )
        self.task_manager.run_task(self.controller.task_run_decision_dashboard, title)

    def _on_dashboard_close(self):
        if self.dashboard_tab:
            self.dashboard_tab.clear_data()

    def _show_dashboard_window(
        self,
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
    ):
        try:
            self.dashboard_tab.populate_data(
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
            self.notebook.select(self.dashboard_tab)
        except Exception as e:
            self.logger.log(f"LỖI khi hiển thị Bảng Tổng Hợp: {e}")
            self.logger.log(traceback.format_exc())
            self._on_dashboard_close()

    def show_lookup_window(self):
        self.logger.log("Đang chuyển sang Tab Tra Cứu...")
        try:
            self.lookup_tab.refresh_lookup_list()
        except Exception as e:
            self.logger.log(f"Lỗi tự động làm mới Tra Cứu: {e}")
        self.notebook.select(self.lookup_tab)

    def show_bridge_manager_window(self):
        try:
            from ui.ui_bridge_manager import BridgeManagerWindow
        except ImportError as e:
            self.logger.log(f"LỖI NGHIÊM TRỌNG khi mở BridgeManager: {e}")
            messagebox.showerror("Lỗi Import", f"Không thể tải ui_bridge_manager: {e}")
            return

        self.bridge_manager_window_instance = BridgeManagerWindow(self)

    def show_settings_window(self):
        self.settings_window = SettingsWindow(self)

    def show_tuner_window(self):
        self.tuner_window = TunerWindow(self)

    def show_vote_statistics_window(self):
        """Hiển thị cửa sổ Thống Kê Vote."""
        from ui.ui_vote_statistics import VoteStatisticsWindow
        self.vote_stats_window_instance = VoteStatisticsWindow(self)

    def show_backtest_results(self, title, results_data, show_save_button=False):
        if "V17" in title or "Bạc Nhớ" in title:
            show_save_button = True
        self.results_window = ResultsViewerWindow(
            self, title, results_data, show_save_button
        )

    def trigger_bridge_backtest(self, bridge_name):
        if not bridge_name:
            return
        if bridge_name.startswith("Cầu "):
            self.logger.log(
                f"--- Trigger: Mở Backtest K2N cho 15 Cầu Cổ Điển (focus vào {bridge_name})..."
            )
            self.run_backtest("K2N")
            self.notebook.select(self.tab1_frame)
        elif "+" in bridge_name or "Bong(" in bridge_name:
            self.logger.log(
                f"--- Trigger: Chạy Backtest N1 tùy chỉnh cho {bridge_name}..."
            )
            self.custom_bridge_entry.delete(0, "end")
            self.custom_bridge_entry.insert(0, bridge_name)
            self.run_custom_backtest("N1")
            self.notebook.select(self.tab1_frame)
        elif "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
            self.logger.log(
                f"--- Trigger: Mở Backtest N1 cho 756 Cầu Bạc Nhớ (focus vào {bridge_name})..."
            )
            self.run_backtest_memory()
            self.notebook.select(self.tab1_frame)
        else:
            self.logger.log(
                f"Lỗi trigger: Không nhận dạng được loại cầu '{bridge_name}'"
            )

    def _save_bridge_from_treeview(self, tree):
        try:
            selected_item = tree.focus()
            if not selected_item:
                messagebox.showwarning(
                    "Chưa chọn cầu",
                    "Vui lòng chọn một cầu từ danh sách trước.",
                    parent=tree.master,
                )
                return
            item_values = tree.item(selected_item, "values")
            bridge_name, win_rate = item_values[1], item_values[3]

            if not (
                "+" in bridge_name
                or "Bong(" in bridge_name
                or "Tổng(" in bridge_name
                or "Hiệu(" in bridge_name
            ):
                if bridge_name.startswith("Cầu "):
                    messagebox.showerror(
                        "Lỗi Lưu Cầu", "Không thể lưu Cầu Cổ Điển.", parent=tree.master
                    )
                else:
                    messagebox.showerror(
                        "Lỗi Lưu Cầu",
                        "Chỉ hỗ trợ lưu Cầu V17 hoặc Cầu Bạc Nhớ.",
                        parent=tree.master,
                    )
                return

            description = simpledialog.askstring(
                "Lưu Cầu Mới",
                f"Nhập mô tả cho cầu:\n{bridge_name}",
                initialvalue=bridge_name,
                parent=tree.master,
            )
            if description is None:
                return

            # (SỬA F405) Giờ đã được import tường minh
            # Use adapter for normalization and validation
            success, message = add_managed_bridge_adapter(
                bridge_name=bridge_name,
                description=description,
                win_rate=win_rate
            )

            if success:
                self.logger.log(f"LƯU/CẬP NHẬT CẦU: {message}")
                messagebox.showinfo("Thành công", message, parent=tree.master)
                if (
                    self.bridge_manager_window
                    and self.bridge_manager_window.winfo_exists()
                ):
                    try:
                        self.bridge_manager_window_instance.refresh_bridge_list()
                    except Exception as e_refresh:
                        self.logger.log(f"Lỗi khi tự động làm mới QL Cầu: {e_refresh}")
            else:
                self.logger.log(f"LỖI LƯU CẦU: {message}")
                messagebox.showerror("Lỗi", message, parent=tree.master)

        except Exception as e:
            messagebox.showerror(
                "Lỗi", f"Lỗi _save_bridge_from_treeview: {e}", parent=tree.master
            )