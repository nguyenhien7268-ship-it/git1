# Tên file: ui/ui_main_window.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - TÁI CẤU TRÚC GIAO DIỆN UX V8.1 - Đảo vị trí nút Thêm Text)
#
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import traceback 
import json 

# Import toàn bộ logic từ file lottery_service.py (Giữ nguyên)
try:
    from lottery_service import *
except ImportError:
    print("LỖI NGHIÊM TRỌNG: Không tìm thấy file 'lottery_service.py' hoặc gói '/logic'.")
    exit()

# (GIỮ NGUYÊN) Import các dịch vụ lõi và controller
try:
    from core_services import Logger, TaskManager
    from app_controller import AppController
except ImportError:
    print("LỖI NGHIÊM TRỌNG: Không tìm thấy 'core_services.py' hoặc 'app_controller.py'.")
    exit()

# (GIỮ NGUYÊN) Import SETTINGS
try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: ui_main_window.py không thể import logic.config_manager. Sử dụng giá trị mặc định.")
    # Cung cấp một đối tượng SETTINGS giả để tránh lỗi
    SETTINGS = type('obj', (object,), {
        'STATS_DAYS': 7, 'GAN_DAYS': 15, 'HIGH_WIN_THRESHOLD': 47.0,
        'AUTO_ADD_MIN_RATE': 50.0, 'AUTO_PRUNE_MIN_RATE': 40.0,
        'K2N_RISK_START_THRESHOLD': 4, 'K2N_RISK_PENALTY_PER_FRAME': 0.5
    })

# (GIỮ NGUYÊN) Import các cửa sổ con/tabs
try:
    from .ui_lookup import LookupWindow
    from .ui_bridge_manager import BridgeManagerWindow
    from .ui_results_viewer import ResultsViewerWindow
    from .ui_dashboard import DashboardWindow
    from .ui_settings import SettingsWindow 
    from .ui_tuner import TunerWindow 
    from .ui_optimizer import OptimizerTab 
except ImportError:
    print("LỖI NGHIÊM TRỌNG: Không thể import các cửa sổ con từ gói /ui.")
    # Fallback (nếu cấu trúc thư mục bị sai)
    from ui_lookup import LookupWindow
    from ui_bridge_manager import BridgeManagerWindow
    from ui_results_viewer import ResultsViewerWindow
    from ui_dashboard import DashboardWindow
    from ui_settings import SettingsWindow 
    from ui_tuner import TunerWindow 
    from ui_optimizer import OptimizerTab 

class DataAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Xổ Số Data Analysis (v8.1 - Tối ưu UX)") 
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry("1024x768") 
        
        self.bridge_manager_window = None
        self.bridge_manager_window_instance = None 
        self.settings_window = None 
        self.tuner_window = None 
        
        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # (GIỮ NGUYÊN) THỨ TỰ KHỞI TẠO ĐÚNG
        
        # 1. Tạo Khung Tab Log (LUÔN CHẠY TRƯỚC)
        self.tab_log_frame = ttk.Frame(self.notebook, padding="10")
        self.tab_log_frame.columnconfigure(0, weight=1)
        self.tab_log_frame.rowconfigure(0, weight=1)
        
        output_frame = ttk.Frame(self.tab_log_frame, padding="10")
        output_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)
        ttk.Label(output_frame, text="Output Log:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_text = tk.Text(output_frame, height=25, width=80, font=('Courier New', 10))
        self.output_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        log_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        log_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.output_text.config(yscrollcommand=log_scrollbar.set, state=tk.DISABLED)

        # 2. Khởi tạo Logger (NGAY SAU KHI CÓ output_text)
        self.logger = Logger(self.output_text, self.root)
        
        # 3. Khởi tạo CONTROLLER (TRƯỚC KHI CÓ BẤT KỲ VIEW NÀO KHÁC)
        self.controller = AppController(self)
        self.controller.logger = self.logger
        
        # 4. Khởi tạo các Tab (dưới dạng class)
        self.dashboard_tab = DashboardWindow(self) # Tab "Bảng Quyết Định"
        self.optimizer_tab = OptimizerTab(self.notebook, self) # Tab "Tối ưu Hóa"
        
        # ====================================================================
        # (MỚI) TÁI CẤU TRÚC "LÀM PHẲNG" GIAO DIỆN
        # ====================================================================
        
        self.all_buttons = [] # Danh sách nút sẽ được cập nhật khi tạo

        # --- Tab 1: 🏠 Chức Năng Chính ---
        self.tab_home_frame = ttk.Frame(self.notebook, padding="20")
        self.tab_home_frame.columnconfigure(0, weight=1)
        
        home_labelframe = ttk.Labelframe(self.tab_home_frame, text="📈 Chức Năng Chính", padding="20")
        home_labelframe.grid(row=0, column=0, sticky="ew")
        home_labelframe.columnconfigure(0, weight=1)
        
        self.dashboard_button = ttk.Button(home_labelframe, text="Mở / Làm Mới Bảng Quyết Định Tối Ưu", command=self.run_decision_dashboard)
        self.dashboard_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5, ipady=10)
        self.all_buttons.append(self.dashboard_button)
        
        # --- Tab 2: 💾 Nạp Dữ Liệu ---
        self.tab_data_load_frame = ttk.Frame(self.notebook, padding="10")
        self.tab_data_load_frame.columnconfigure(0, weight=1)
        self.tab_data_load_frame.rowconfigure(1, weight=1) # Cho Text Area co giãn
        
        # Khung Nạp File (An toàn hơn)
        data_frame = ttk.Labelframe(self.tab_data_load_frame, text="💾 Nạp Dữ Liệu Từ File (JSON/Text)", padding="10") 
        data_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10)) 
        data_frame.columnconfigure(1, weight=1)
        
        ttk.Label(data_frame, text="Input File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_path_entry = ttk.Entry(data_frame, width=50)
        self.file_path_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        browse_button = ttk.Button(data_frame, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        # Radio Button An Toàn
        self.load_mode_var = tk.StringVar(value="append")
        mode_frame = ttk.Frame(data_frame)
        mode_frame.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        ttk.Radiobutton(mode_frame, text="Thêm vào dữ liệu (Append)", variable=self.load_mode_var, value="append").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="XÓA HẾT và nạp lại (Overwrite)", variable=self.load_mode_var, value="overwrite").pack(side=tk.LEFT, padx=20)
        
        self.parse_button = ttk.Button(data_frame, text="Thực Hiện Nạp File", command=self.run_parsing)
        self.parse_button.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.all_buttons.append(self.parse_button)
        
        # Khung Nạp Text
        text_frame = ttk.Labelframe(self.tab_data_load_frame, text="📝 Thêm Nhanh (Từ Text Copy/Paste)", padding="10")
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.columnconfigure(0, weight=1)
        # (SỬA V8.1) Chuyển weight sang row 1 cho Text Area
        text_frame.rowconfigure(1, weight=1) 
        
        # (SỬA V8.1) Chuyển nút lên row 0
        self.update_button = ttk.Button(text_frame, text="Thêm 1/Nhiều Kỳ Từ Text (Append)", command=self.run_update_from_text)
        self.update_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5) # <-- Button on row 0
        
        # (SỬA V8.1) Chuyển text area xuống row 1
        self.update_text_area = tk.Text(text_frame, height=5, width=80)
        self.update_text_area.grid(row=1, column=0, sticky="nsew", padx=5, pady=5) # <-- Text area on row 1
        
        self.all_buttons.append(self.update_button)

        # --- Tab 3: 📊 Bảng Quyết Định ---
        # (Giữ nguyên, chỉ add)
        
        # --- Tab 4: 🔍 Phân tích & Backtest ---
        self.tab_analysis_frame = ttk.Frame(self.notebook, padding="5")
        self.tab_analysis_frame.columnconfigure(0, weight=1)
        self.tab_analysis_frame.rowconfigure(0, weight=1)
        
        analysis_notebook = ttk.Notebook(self.tab_analysis_frame)
        analysis_notebook.grid(row=0, column=0, sticky="nsew")
        
        # 1. Tab con Tra Cứu (Sử dụng lại class LookupWindow)
        self.lookup_tab = LookupWindow(self) 
        analysis_notebook.add(self.lookup_tab, text='Tra Cứu Kết Quả Kỳ')
        
        # 2. Tab con Backtest
        backtest_frame_tab = ttk.Frame(analysis_notebook, padding=(10, 5))
        backtest_frame_tab.columnconfigure(0, weight=1)
        
        v25_frame = ttk.Labelframe(backtest_frame_tab, text="🔍 Backtest (Phân tích sâu)", padding="10")
        v25_frame.grid(row=0, column=0, sticky="nsew")
        v25_frame.columnconfigure(0, weight=1); v25_frame.columnconfigure(1, weight=1); v25_frame.columnconfigure(2, weight=1)
        
        self.backtest_n1_15_button = ttk.Button(v25_frame, text="Backtest 15 Cầu (N1)", command=lambda: self.run_backtest('N1'))
        self.backtest_n1_15_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.backtest_k2n_15_button = ttk.Button(v25_frame, text="Backtest 15 Cầu (K2N)", command=lambda: self.run_backtest('K2N'))
        self.backtest_k2n_15_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.backtest_memory_button = ttk.Button(v25_frame, text="Backtest 756 Cầu Bạc Nhớ (N1)", command=self.run_backtest_memory)
        self.backtest_memory_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        
        self.backtest_managed_button = ttk.Button(v25_frame, text="Backtest Cầu Đã Lưu (N1)", command=self.run_backtest_managed_n1)
        self.backtest_managed_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.backtest_managed_k2n_button = ttk.Button(v25_frame, text="Backtest Cầu Đã Lưu (K2N)", command=self.run_backtest_managed_k2n)
        self.backtest_managed_k2n_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.all_buttons.extend([
            self.backtest_n1_15_button, self.backtest_k2n_15_button,
            self.backtest_memory_button, self.backtest_managed_button, self.backtest_managed_k2n_button
        ])
        
        analysis_notebook.add(backtest_frame_tab, text='Chạy Backtest')
        
        # --- Tab 5: 🚀 Tối ưu Hóa ---
        # (Giữ nguyên, chỉ add)
        
        # --- Tab 6: 🛠️ Cài đặt & Bảo trì ---
        self.tab_maintenance_frame = ttk.Frame(self.notebook, padding="10")
        self.tab_maintenance_frame.columnconfigure(0, weight=1)
        
        # Khung Quản lý Cầu
        manage_frame = ttk.Labelframe(self.tab_maintenance_frame, text="🛠️ Quản lý & Dò Cầu", padding="10")
        manage_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        manage_frame.columnconfigure(0, weight=1); manage_frame.columnconfigure(1, weight=1); manage_frame.columnconfigure(2, weight=1)
        
        self.manage_bridges_button = ttk.Button(manage_frame, text="Quản lý Cầu (V17)...", command=self.show_bridge_manager_window)
        self.manage_bridges_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.auto_find_bridges_button = ttk.Button(manage_frame, text="Tự động Dò & Thêm Cầu (V17+BN)", command=self.run_auto_find_bridges)
        self.auto_find_bridges_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.auto_prune_bridges_button = ttk.Button(manage_frame, text="Tự động Lọc/Tắt Cầu Yếu", command=self.run_auto_prune_bridges)
        self.auto_prune_bridges_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        
        # Khung Cài đặt & AI
        ai_settings_frame = ttk.Labelframe(self.tab_maintenance_frame, text="⚙️ Cài đặt & Huấn luyện AI", padding="10")
        ai_settings_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        ai_settings_frame.columnconfigure(0, weight=1); ai_settings_frame.columnconfigure(1, weight=1); ai_settings_frame.columnconfigure(2, weight=1)

        self.settings_button = ttk.Button(ai_settings_frame, text="⚙️ Cài đặt Tham số...", command=self.show_settings_window)
        self.settings_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.tuner_button = ttk.Button(ai_settings_frame, text="📈 Tinh chỉnh Tham số...", command=self.show_tuner_window)
        self.tuner_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.train_ai_button = ttk.Button(ai_settings_frame, text="🧠 Huấn luyện AI...", command=self.run_train_ai)
        self.train_ai_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        
        # Khung Cache
        cache_frame = ttk.Labelframe(self.tab_maintenance_frame, text="🗄️ Quản lý Cache", padding="10")
        cache_frame.grid(row=2, column=0, sticky="nsew")
        cache_frame.columnconfigure(0, weight=1)
        
        self.update_cache_button = ttk.Button(cache_frame, text="Cập nhật Cache K2N", command=self.run_update_all_bridge_K2N_cache_from_main)
        self.update_cache_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.all_buttons.extend([
            self.manage_bridges_button, self.auto_find_bridges_button, self.auto_prune_bridges_button,
            self.settings_button, self.tuner_button, self.train_ai_button,
            self.update_cache_button
        ])
        
        # --- Tab 7: Log Hệ Thống ---
        # (Đã tạo ở đầu)
        
        # ====================================================================
        # ADD CÁC TAB CHÍNH VÀO NOTEBOOK
        # ====================================================================
        self.notebook.add(self.tab_home_frame, text='🏠 Chính')
        self.notebook.add(self.tab_data_load_frame, text='💾 Nạp Dữ Liệu')
        self.notebook.add(self.dashboard_tab, text='📊 Bảng Quyết Định')
        self.notebook.add(self.tab_analysis_frame, text='🔍 Phân tích & Backtest')
        self.notebook.add(self.optimizer_tab, text='🚀 Tối ưu Hóa')
        self.notebook.add(self.tab_maintenance_frame, text='🛠️ Cài đặt & Bảo trì')
        self.notebook.add(self.tab_log_frame, text='Log Hệ Thống')
        
        
        # --- CẬP NHẬT DANH SÁCH NÚT TỔNG ---
        self.all_buttons.append(self.optimizer_tab.run_button)
        if hasattr(self.optimizer_tab, 'generate_cache_button'): # Nút mới
             self.all_buttons.append(self.optimizer_tab.generate_cache_button)
        self.all_buttons.append(self.optimizer_tab.apply_button)

        # --- KHỞI TẠO TASK MANAGER ---
        self.task_manager = TaskManager(self.logger, self.all_buttons, self.root)
        self.task_manager.optimizer_apply_button = self.optimizer_tab.apply_button
        
        self.logger.log("Hệ thống (v8.1 Tối ưu UX) sẵn sàng.")
        
    # --- (MỚI) HÀM XÓA TEXT (Callback cho Controller) ---
    def clear_update_text_area(self):
        """Hàm này được gọi từ controller để xóa text box (an toàn)."""
        if self.update_text_area and self.update_text_area.winfo_exists():
            self.update_text_area.delete("1.0", tk.END)

    # --- (GIỮ NGUYÊN) CÁC HÀM CALLBACK CHO CONTROLLER ---
    def _log_to_optimizer(self, message, optimizer_window):
        if optimizer_window and optimizer_window.winfo_exists():
            optimizer_window.log(message)

    def _show_save_success_dialog(self, title, message, parent_widget):
        messagebox.showinfo(title, message, parent=parent_widget)
        if self.bridge_manager_window and self.bridge_manager_window_instance and self.bridge_manager_window_instance.winfo_exists():
            try:
                self.bridge_manager_window_instance.refresh_bridge_list()
            except Exception as e_refresh:
                self.logger.log(f"Lỗi khi tự động làm mới QL Cầu: {e_refresh}")

    def _show_error_dialog(self, title, message, parent_widget):
        messagebox.showerror(title, message, parent=parent_widget)
    
    def _show_warning_dialog(self, title, message, parent_widget):
        messagebox.showwarning(title, message, parent=parent_widget)

    # --- CÁC HÀM XỬ LÝ SỰ KIỆN GIAO DIỆN (Đại diện lệnh) ---
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=".", title="Select Input File",
            filetypes=(("JSON files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*"))
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

    # --- (CẬP NHẬT) HÀM NẠP FILE MỚI (AN TOÀN HƠN) ---
    def run_parsing(self):
        input_file = self.check_file_path()
        if not input_file: return
        
        mode = self.load_mode_var.get()
        
        if mode == "overwrite":
            # Hiển thị hộp thoại xác nhận CỰC KỲ RÕ RÀNG
            if not messagebox.askyesno("XÁC NHẬN XÓA", 
                                       "CẢNH BÁO: Bạn đã chọn chế độ 'XÓA HẾT'.\n\nToàn bộ dữ liệu trong database sẽ bị xóa trước khi nạp file mới.\n\nBạn có chắc chắn muốn tiếp tục?",
                                       icon='warning', parent=self.root):
                self.logger.log("HỦY BỎ: Tác vụ Nạp (Xóa Hết) đã bị hủy.")
                return

            self.logger.log(f"\n--- Bắt đầu Bước 1 (Xóa Hết): Phân tích tệp tin ---")
            self.task_manager.run_task(self.controller.task_run_parsing, input_file)
        
        else: # mode == "append"
            self.logger.log(f"\n--- Bắt đầu Bước 1 (Append): Thêm dữ liệu từ tệp tin ---")
            self.task_manager.run_task(self.controller.task_run_parsing_append, input_file)

    def run_update_from_text(self):
        raw_data = self.update_text_area.get("1.0", tk.END)
        if not raw_data.strip():
            self.logger.log("LỖI: Không có dữ liệu text để cập nhật.")
            return
        self.logger.log(f"\n--- Bắt đầu: Thêm Kỳ Mới Từ Text ---")
        self.task_manager.run_task(self.controller.task_run_update_from_text, raw_data)

    def run_backtest(self, mode):
        title = f"Backtest 15 Cầu {mode}"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        self.task_manager.run_task(self.controller.task_run_backtest, mode, title)
            
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
        self.task_manager.run_task(self.controller.task_run_update_all_bridge_K2N_cache, title)

    def run_auto_find_bridges(self):
        title = "Tự động Dò & Thêm Cầu V17 + Bạc Nhớ" 
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        try: auto_add_rate = SETTINGS.AUTO_ADD_MIN_RATE
        except Exception: auto_add_rate = 50.0
        self.logger.log("CẢNH BÁO: Tác vụ này RẤT NẶNG. Vui lòng chờ...")
        self.logger.log(f"Các cầu có Tỷ lệ > {auto_add_rate}% sẽ được tự động thêm/cập nhật...")
        self.task_manager.run_task(self.controller.task_run_auto_find_bridges, title)

    def run_auto_prune_bridges(self):
        title = "Tự động Lọc/Tắt Cầu Yếu"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        try: auto_prune_rate = SETTINGS.AUTO_PRUNE_MIN_RATE
        except Exception: auto_prune_rate = 40.0
        self.logger.log("Đang kiểm tra cache K2N của các Cầu Đã Lưu...")
        self.logger.log(f"Các cầu có Tỷ lệ < {auto_prune_rate}% sẽ bị TẮT (vô hiệu hóa)...")
        self.task_manager.run_task(self.controller.task_run_auto_prune_bridges, title)
    
    def run_train_ai(self):
        title = "Huấn luyện Mô hình AI (V7.1)"
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
        self.task_manager.run_task(self.controller.task_run_parameter_tuning, 
                                 param_key, val_from, val_to, val_step, tuner_window)

    def run_strategy_optimization(self, strategy, days_to_test, param_ranges, optimizer_tab):
        self.task_manager.run_task(self.controller.task_run_strategy_optimization, 
                                 strategy, days_to_test, param_ranges, optimizer_tab)
            
    def apply_optimized_settings(self, config_dict_str, optimizer_window):
        try:
            config_dict = json.loads(config_dict_str)
            if not messagebox.askyesno("Xác nhận Áp dụng", 
                                       f"Bạn có chắc chắn muốn áp dụng cấu hình này và lưu vào 'config.json' không?\n\n{config_dict_str}",
                                       parent=optimizer_window):
                return
            
            self.task_manager.run_task(self.controller.task_apply_optimized_settings, 
                                       config_dict, optimizer_window)
            
        except json.JSONDecodeError:
             messagebox.showerror("Lỗi", "Lỗi: Chuỗi cấu hình không phải định dạng JSON hợp lệ.", parent=optimizer_window)
        except Exception as e:
             messagebox.showerror("Lỗi", f"Lỗi khi áp dụng cấu hình: {e}", parent=optimizer_window)

    def run_decision_dashboard(self):
        title = "Bảng Quyết Định Tối Ưu"
        self.logger.log(f"\n--- Bắt đầu: {title} ---")
        if self.dashboard_tab.title_label.cget("text") != "Đang tải...":
            self.logger.log("Đang chạy lại 5 hệ thống phân tích cốt lõi để cập nhật...")
        else:
            self.logger.log("Đang chạy 5 hệ thống phân tích cốt lõi... (Bao gồm 1 AI và 1 Cache K2N)") 
        
        # (QUAN TRỌNG) Tự động chuyển sang tab Bảng Quyết Định
        self.notebook.select(self.dashboard_tab) 
        
        self.task_manager.run_task(self.controller.task_run_decision_dashboard, title)

    def _on_dashboard_close(self):
        if self.dashboard_tab and self.dashboard_tab.winfo_exists():
            self.dashboard_tab.clear_data()

    def _show_dashboard_window(self, next_ky, stats_n_day, n_days_stats, consensus, high_win, pending_k2n_data, gan_stats, top_scores, top_memory_bridges, ai_predictions, gan_threshold, risk_threshold):
        try:
            self.dashboard_tab.populate_data(
                next_ky, stats_n_day, n_days_stats, 
                consensus, high_win, pending_k2n_data, 
                gan_stats, top_scores, top_memory_bridges,
                ai_predictions,
                gan_threshold, 
                risk_threshold
            )
        except Exception as e:
            self.logger.log(f"LỖI khi hiển thị Bảng Tổng Hợp: {e}")
            self.logger.log(traceback.format_exc())
            self._on_dashboard_close()

    def show_bridge_manager_window(self):
        self.bridge_manager_window_instance = BridgeManagerWindow(self)

    def show_settings_window(self):
        self.settings_window = SettingsWindow(self)

    def show_tuner_window(self):
        self.tuner_window = TunerWindow(self)

    def show_backtest_results(self, title, results_data, show_save_button=False):
        if "V17" in title or "Bạc Nhớ" in title: 
            show_save_button = True
        self.results_window = ResultsViewerWindow(self, title, results_data, show_save_button)

    def trigger_bridge_backtest(self, bridge_name):
        if not bridge_name: return
        
        # (MỚI) Tự động chuyển tab Phân tích
        self.notebook.select(self.tab_analysis_frame)
        
        if bridge_name.startswith("Cầu "):
            self.logger.log(f"--- Trigger: Mở Backtest K2N cho 15 Cầu Cổ Điển (focus vào {bridge_name})...")
            self.run_backtest('K2N')
        elif "+" in bridge_name or "Bong(" in bridge_name:
            self.logger.log(f"--- Trigger: Chạy Backtest N1 tùy chỉnh cho {bridge_name}...")
            self.logger.log("Lỗi: Nút 'Test Cầu Tùy Chỉnh' đã bị ẩn trong bản V8.0. Vui lòng chạy 'Backtest Cầu Đã Lưu'.")
        elif "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
            self.logger.log(f"--- Trigger: Mở Backtest N1 cho 756 Cầu Bạc Nhớ (focus vào {bridge_name})...")
            self.run_backtest_memory()
        else:
            self.logger.log(f"Lỗi trigger: Không nhận dạng được loại cầu '{bridge_name}'")

    def _save_bridge_from_treeview(self, tree):
        try:
            selected_item = tree.focus()
            if not selected_item:
                messagebox.showwarning("Chưa chọn cầu", "Vui lòng chọn một cầu từ danh sách trước.", parent=tree.master)
                return
            item_values = tree.item(selected_item, 'values')
            bridge_name, win_rate = item_values[1], item_values[3]
            
            if not ("+" in bridge_name or "Bong(" in bridge_name or "Tổng(" in bridge_name or "Hiệu(" in bridge_name):
                if bridge_name.startswith("Cầu "):
                    messagebox.showerror("Lỗi Lưu Cầu", "Không thể lưu Cầu Cổ Điển.", parent=tree.master)
                else:
                    messagebox.showerror("Lỗi Lưu Cầu", "Chỉ hỗ trợ lưu Cầu V17 hoặc Cầu Bạc Nhớ.", parent=tree.master)
                return

            description = simpledialog.askstring("Lưu Cầu Mới", 
                                                 f"Nhập mô tả cho cầu:\n{bridge_name}",
                                                 initialvalue=bridge_name, 
                                                 parent=tree.master)
            if description is None: return

            self.task_manager.run_task(self.controller.task_save_bridge, 
                                       bridge_name, description, win_rate, tree.master)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi _save_bridge_from_treeview: {e}", parent=tree.master)