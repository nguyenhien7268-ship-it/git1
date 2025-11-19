# Tên file: du-an-backup/ui/ui_main_window.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA LỖI FLAKE8 F541, W292)

import json
import os
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, simpledialog, ttk

# (GIỮ NGUYÊN)
try:
    from lottery_service import DB_NAME, upsert_managed_bridge
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
        "Lỗi: ui_main_window.py không thể import logic.config_manager. Sử dụng giá trị mặc định."
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
# Di chuyển import 'BridgeManagerWindow' vào BÊN TRONG hàm show_bridge_manager_window
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
        self.root.title("Xổ Số Data Analysis (v7.2 - Giao diện Sắp xếp)")
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

        # --- (SỬA) THỨ TỰ KHỞI TẠO ĐÚNG ---

        # 1. (SỬA) Tạo Khung Tab Log (nhưng chưa add)
        self.tab_log_frame = ttk.Frame(self.notebook, padding="10")
        self.tab_log_frame.columnconfigure(0, weight=1)
        self.tab_log_frame.rowconfigure(0, weight=1)

        # 2. (SỬA) Tạo Khung Output và self.output_text
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

        # 3. (SỬA) Khởi tạo Logger (NGAY SAU KHI CÓ output_text)
        self.logger = Logger(self.output_text, self.root)

        # 4. (SỬA) Khởi tạo các Tab còn lại (BÂY GIỜ CHÚNG CÓ THỂ DÙNG LOGGER)
        self.tab1_frame = ttk.Frame(self.notebook, padding="10")
        self.tab1_frame.columnconfigure(0, weight=1)
        self.tab1_frame.rowconfigure(0, weight=0)
        self.tab1_frame.rowconfigure(1, weight=1)

        self.dashboard_tab = DashboardWindow(self)  # Logger đã tồn tại
        self.lookup_tab = LookupWindow(self)  # Logger đã tồn tại (FIX LỖI)
        self.optimizer_tab = OptimizerTab(self.notebook, self)

        # 5. (SỬA) ADD CÁC TAB VÀO NOTEBOOK (theo đúng thứ tự)
        self.notebook.add(self.tab1_frame, text="⚙️ Điều Khiển")
        self.notebook.add(self.dashboard_tab, text="📊 Bảng Quyết Định")
        self.notebook.add(self.lookup_tab, text="🔍 Tra Cứu")
        self.notebook.add(self.optimizer_tab, text="🚀 Tối Ưu Hóa")
        self.notebook.add(
            self.tab_log_frame, text="Log Hệ Thống"
        )  # Add Tab Log vào cuối

        # --- TÁI CẤU TRÚC TAB "ĐIỀU KHIỂN" (Giữ nguyên) ---

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
        sub_notebook.add(manage_frame_tab, text="🛠 Quản lý & Dò Cầu")
        sub_notebook.add(backtest_frame_tab, text="🔍 Backtest (Phân tích sâu)")

        # 4. Di chuyển các Khung (Frame) vào các Tab con

        # Khung NẠP DỮ LIỆU
        data_frame_tab.columnconfigure(0, weight=1)
        data_frame_tab.rowconfigure(0, weight=1)
        data_frame = ttk.Labelframe(
            data_frame_tab, text="💾 Nạp/Cập Nhật Dữ Liệu", padding="10"
        )
        data_frame.grid(row=0, column=0, sticky="nsew")
        data_frame.columnconfigure(1, weight=1)
        data_frame.rowconfigure(3, weight=1)
        ttk.Label(data_frame, text="Input File (JSON/Text):").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.file_path_entry = ttk.Entry(data_frame, width=50)
        self.file_path_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        browse_button = ttk.Button(data_frame, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.parse_button = ttk.Button(
            data_frame, text="Nạp File (Xóa Hết DB)", command=self.run_parsing
        )
        self.parse_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.parse_append_button = ttk.Button(
            data_frame, text="Nạp File (Thêm/Append)", command=self.run_parsing_append
        )
        self.parse_append_button.grid(
            row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5
        )
        ttk.Label(data_frame, text="Dán dữ liệu text (1 hoặc nhiều kỳ) vào đây:").grid(
            row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5
        )
        self.update_text_area = tk.Text(data_frame, height=5, width=80)
        self.update_text_area.grid(
            row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5
        )
        self.update_button = ttk.Button(
            data_frame,
            text="Thêm 1/Nhiều Kỳ Từ Text (Append)",
            command=self.run_update_from_text,
        )
        self.update_button.grid(
            row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5
        )

        # Khung QUẢN LÝ
        manage_frame_tab.columnconfigure(0, weight=1)
        manage_frame_tab.rowconfigure(0, weight=1)
        manage_frame = ttk.Labelframe(
            manage_frame_tab, text="🛠 Quản lý & Dò Cầu (Bảo trì)", padding="10"
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
        self.settings_button = ttk.Button(
            manage_frame, text="⚙️ Cài đặt Tham số...", command=self.show_settings_window
        )
        self.settings_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.tuner_button = ttk.Button(
            manage_frame,
            text="📈 Tinh chỉnh Tham số...",
            command=self.show_tuner_window,
        )
        self.tuner_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.train_ai_button = ttk.Button(
            manage_frame, text="🤖 Huấn luyện AI...", command=self.run_train_ai
        )
        self.train_ai_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        # Khung BACKTEST
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
            row=1, column=2, sticky="ew", padx=5, pady=5)
        self.custom_bridge_entry = ttk.Entry(v25_frame)

        # --- Danh sách nút tổng (Giữ nguyên) ---
        self.all_buttons = [
            self.parse_button,
            self.parse_append_button,
            self.update_button,
            self.dashboard_button,
            self.update_cache_button,
            self.manage_bridges_button,
            self.auto_find_bridges_button,
            self.auto_prune_bridges_button,
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

        # --- KHỞI TẠO CÁC DỊCH VỤ LỖI & CONTROLLER (Giữ nguyên) ---
        self.task_manager = TaskManager(self.logger, self.all_buttons, self.root)
        self.task_manager.optimizer_apply_button = self.optimizer_tab.apply_button

        self.controller = AppController(self)
        self.controller.logger = self.logger

        self.logger.log("Hệ thống (GĐ 5.3: Đã sửa lỗi Logger) sẵn sàng.")

    def update_output(self, msg):
        """Cập nhật output log. Được gọi từ các cửa sổ phụ."""
        self.logger.log(msg)

    # ... (other methods unchanged) ...

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

            # Safer extraction: guard against short rows and provide clear error
            bridge_name = item_values[1] if len(item_values) > 1 else ""
            win_rate = item_values[3] if len(item_values) > 3 else ""

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

            success, message = upsert_managed_bridge(bridge_name, description, win_rate)

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
