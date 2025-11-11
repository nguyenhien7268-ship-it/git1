import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import traceback # Để in lỗi chi tiết
import threading # (MỚI) Import thư viện đa luồng
import time # (MỚI GĐ 9) Thêm time để giả lập
import json # (MỚI GĐ 10) Thêm json để xử lý kết quả
import itertools # (MỚI GĐ 10) Thêm itertools để tạo tổ hợp

# Import toàn bộ logic từ file lottery_service.py
try:
    from lottery_service import *
except ImportError:
    print("LỖI NGHIÊM TRỌNG: Không tìm thấy file 'lottery_service.py' hoặc gói '/logic'.")
    exit()

# (MỚI GĐ 8) Import SETTINGS
try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: ui_main_window.py không thể import logic.config_manager. Sử dụng giá trị mặc định.")
    SETTINGS = type('obj', (object,), {
        'STATS_DAYS': 7, 'GAN_DAYS': 15, 'HIGH_WIN_THRESHOLD': 47.0,
        'AUTO_ADD_MIN_RATE': 50.0, 'AUTO_PRUNE_MIN_RATE': 40.0,
        'K2N_RISK_START_THRESHOLD': 4, 'K2N_RISK_PENALTY_PER_FRAME': 0.5
    })

# Import các cửa sổ con từ gói /ui
try:
    from .ui_lookup import LookupWindow
    from .ui_bridge_manager import BridgeManagerWindow
    from .ui_results_viewer import ResultsViewerWindow
    from .ui_dashboard import DashboardWindow
    from .ui_settings import SettingsWindow # (MỚI GĐ 8) Import Cài đặt
    from .ui_tuner import TunerWindow # (MỚI GĐ 9) Import Tinh chỉnh
    from .ui_optimizer import OptimizerTab # (MỚI GĐ 10) Import Tối ưu hóa
except ImportError:
    print("LỖI NGHIÊM TRỌNG: Không thể import các cửa sổ con từ gói /ui.")
    # Fallback (nếu chạy trực tiếp file này)
    from ui_lookup import LookupWindow
    from ui_bridge_manager import BridgeManagerWindow
    from ui_results_viewer import ResultsViewerWindow
    from ui_dashboard import DashboardWindow
    from ui_settings import SettingsWindow # (MỚI GĐ 8)
    from ui_tuner import TunerWindow # (MỚI GĐ 9)
    from ui_optimizer import OptimizerTab # (MỚI GĐ 10)

class DataAnalysisApp:
    def __init__(self, root):
        self.root = root
        # (SỬA V6.6) Cập nhật tiêu đề
        self.root.title("Xổ Số Data Analysis (v6.6 - Tích hợp AI)") 
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry("800x600")

        self.db_name = DB_NAME
        self.lookup_window = None 
        self.bridge_manager_window = None
        self.bridge_manager_tree = None
        self.bridge_manager_window_instance = None 
        self.dashboard_window = None 
        self.settings_window = None # (MỚI GĐ 8) Quản lý Cài đặt
        self.tuner_window = None # (MỚI GĐ 9) Quản lý Tinh chỉnh
        # (MỚI GĐ 10) Biến cho Tab Tối ưu hóa
        self.optimizer_tab = None 

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        self.tab1_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab1_frame, text='Chức Năng')
        self.tab1_frame.columnconfigure(0, weight=1)
        
        self.tab1_frame.rowconfigure(0, weight=0) # Nhóm 1: Dự đoán
        self.tab1_frame.rowconfigure(1, weight=1) # Nhóm 2: Nạp Dữ Liệu
        self.tab1_frame.rowconfigure(2, weight=0) # Nhóm 3: Quản lý
        self.tab1_frame.rowconfigure(3, weight=0) # Nhóm 4: Backtest

        self.tab2_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab2_frame, text='Log Hệ Thống')
        self.tab2_frame.columnconfigure(0, weight=1)
        self.tab2_frame.rowconfigure(0, weight=1)
        
        # (MỚI GĐ 10) Thêm Tab 3: Tối ưu Hóa
        self.optimizer_tab = OptimizerTab(self.notebook, self)
        self.notebook.add(self.optimizer_tab, text='🚀 Tối ưu Hóa Chiến lược')


        # --- (SỬA GĐ 7) NHÓM 1: PHÂN TÍCH & DỰ ĐOÁN ---
        predict_frame = ttk.Labelframe(self.tab1_frame, text="📈 Phân tích & Dự đoán", padding="10")
        predict_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        predict_frame.columnconfigure(0, weight=1)
        predict_frame.columnconfigure(1, weight=1)
        
        self.dashboard_button = ttk.Button(predict_frame, text="Mở Bảng Tổng Hợp (V6.6 + AI)", command=self.run_decision_dashboard)
        self.dashboard_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.update_cache_button = ttk.Button(predict_frame, text="Cập nhật Cache K2N", command=self.run_update_all_bridge_K2N_cache_from_main)
        self.update_cache_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)


        # --- (SỬA GĐ 5) NHÓM 2: NẠP/CẬP NHẬT DỮ LIỆU ---
        data_frame = ttk.Labelframe(self.tab1_frame, text="💾 Nạp/Cập Nhật Dữ Liệu", padding="10") 
        data_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        data_frame.columnconfigure(1, weight=1) 
        data_frame.rowconfigure(3, weight=1) # Cho Text box co giãn

        ttk.Label(data_frame, text="Input File (JSON/Text):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_path_entry = ttk.Entry(data_frame, width=50)
        self.file_path_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        browse_button = ttk.Button(data_frame, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        self.parse_button = ttk.Button(data_frame, text="Nạp File (Xóa Hết DB)", command=self.run_parsing)
        self.parse_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.parse_append_button = ttk.Button(data_frame, text="Nạp File (Thêm/Append)", command=self.run_parsing_append)
        self.parse_append_button.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(data_frame, text="Dán dữ liệu text (1 hoặc nhiều kỳ) vào đây:").grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        self.update_text_area = tk.Text(data_frame, height=5, width=80)
        self.update_text_area.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        
        self.update_button = ttk.Button(data_frame, text="Thêm 1/Nhiều Kỳ Từ Text (Append)", command=self.run_update_from_text)
        self.update_button.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)


        # --- (SỬA V6.0) NHÓM 3: QUẢN LÝ & DÒ CẦU (THÊM AI) ---
        manage_frame = ttk.Labelframe(self.tab1_frame, text="🛠️ Quản lý & Dò Cầu (Bảo trì)", padding="10")
        manage_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        manage_frame.columnconfigure(0, weight=1)
        manage_frame.columnconfigure(1, weight=1)
        manage_frame.columnconfigure(2, weight=1)

        # (SỬA GĐ 9) Hàng 1
        self.manage_bridges_button = ttk.Button(manage_frame, text="Quản lý Cầu (V17)...", command=self.show_bridge_manager_window)
        self.manage_bridges_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.auto_find_bridges_button = ttk.Button(manage_frame, text="Tự động Dò & Thêm Cầu (V17+BN)", command=self.run_auto_find_bridges)
        self.auto_find_bridges_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.auto_prune_bridges_button = ttk.Button(manage_frame, text="Tự động Lọc/Tắt Cầu Yếu", command=self.run_auto_prune_bridges)
        self.auto_prune_bridges_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        
        # (SỬA V6.0) Hàng 2 (Thêm nút AI)
        self.settings_button = ttk.Button(manage_frame, text="⚙️ Cài đặt Tham số...", command=self.show_settings_window)
        self.settings_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.tuner_button = ttk.Button(manage_frame, text="📈 Tinh chỉnh Tham số...", command=self.show_tuner_window)
        self.tuner_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # (MỚI V6.0) THÊM NÚT HUẤN LUYỆN AI
        self.train_ai_button = ttk.Button(manage_frame, text="🧠 Huấn luyện AI...", command=self.run_train_ai)
        self.train_ai_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)


        # --- (SỬA GĐ 7) NHÓM 4: BACKTEST & TRA CỨU ---
        v25_frame = ttk.Labelframe(self.tab1_frame, text="🔍 Backtest & Tra Cứu (Phân tích sâu)", padding="10")
        v25_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)

        v25_frame.columnconfigure(0, weight=1)
        v25_frame.columnconfigure(1, weight=1)
        v25_frame.columnconfigure(2, weight=1)
        
        # Hàng 1
        self.lookup_button = ttk.Button(v25_frame, text="Tra Cứu Kết Quả", command=self.show_lookup_window)
        self.lookup_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.backtest_n1_15_button = ttk.Button(v25_frame, text="Backtest 15 Cầu (N1)", command=lambda: self.run_backtest('N1'))
        self.backtest_n1_15_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.backtest_k2n_15_button = ttk.Button(v25_frame, text="Backtest 15 Cầu (K2N)", command=lambda: self.run_backtest('K2N'))
        self.backtest_k2n_15_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        # Hàng 2
        self.backtest_memory_button = ttk.Button(v25_frame, text="Backtest 756 Cầu Bạc Nhớ (N1)", command=self.run_backtest_memory)
        self.backtest_memory_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.backtest_managed_button = ttk.Button(v25_frame, text="Backtest Cầu Đã Lưu (N1)", command=self.run_backtest_managed_n1)
        self.backtest_managed_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.backtest_managed_k2n_button = ttk.Button(v25_frame, text="Backtest Cầu Đã Lưu (K2N)", command=self.run_backtest_managed_k2n)
        self.backtest_managed_k2n_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)
        
        # (SỬA GĐ 7) Gỡ bỏ khung Test Cầu Tùy Chỉnh
        # Chúng ta VẪN KHỞI TẠO self.custom_bridge_entry để double-click hoạt động
        self.custom_bridge_entry = ttk.Entry(v25_frame)
        
        # --- Danh sách nút tổng (để Bật/Tắt) ---
        self.all_buttons = [
            self.parse_button, self.parse_append_button, self.update_button,
            self.dashboard_button, self.update_cache_button,
            self.manage_bridges_button, self.auto_find_bridges_button, self.auto_prune_bridges_button,
            self.settings_button, self.tuner_button, 
            self.train_ai_button, # (MỚI V6.0) Thêm nút Huấn luyện AI
            self.lookup_button, self.backtest_n1_15_button, self.backtest_k2n_15_button,
            self.backtest_memory_button, self.backtest_managed_button, self.backtest_managed_k2n_button,
            # (MỚI GĐ 10) Thêm các nút của tab Tối ưu hóa
            self.optimizer_tab.run_button, self.optimizer_tab.apply_button
        ]

        # --- Output Frame (row=0 của Tab 2) ---
        output_frame = ttk.Frame(self.tab2_frame, padding="10")
        output_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output Log:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_text = tk.Text(output_frame, height=25, width=80, font=('Courier New', 10))
        self.output_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        log_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        log_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.output_text.config(yscrollcommand=log_scrollbar.set, state=tk.DISABLED)

    # --- (MỚI) HÀM ĐA LUỒNG ---

    def _run_task_in_thread(self, target_function, *args):
        """
        Hàm bao bọc (wrapper) chung để chạy bất kỳ tác vụ nào trong một luồng riêng.
        Điều này ngăn chặn UI bị "Đơ" (Freeze).
        """
        self.set_buttons_state(tk.DISABLED)

        def _thread_wrapper():
            """Hàm này sẽ chạy trong luồng mới."""
            try:
                target_function(*args)
            except Exception as e:
                self.root.after(0, self._safe_update_output, f"LỖI LUỒNG: {e}")
                self.root.after(0, self._safe_update_output, traceback.format_exc())
            finally:
                self.root.after(0, self.set_buttons_state, tk.NORMAL)

        task_thread = threading.Thread(target=_thread_wrapper, daemon=True)
        task_thread.start()

    # --- Hàm Giao tiếp & Trạng thái ---

    def _safe_update_output(self, message):
        """Hàm cập nhật output an toàn từ các luồng khác."""
        try:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.output_text.config(state=tk.DISABLED)
            self.root.update_idletasks()
        except Exception as e:
            print(f"Lỗi khi cập nhật output: {e}")

    def update_output(self, message):
        """Hàm cập nhật output. Sẽ kiểm tra xem có phải từ luồng chính hay không."""
        if threading.current_thread() is not threading.main_thread():
            self.root.after(0, self._safe_update_output, message)
        else:
            self._safe_update_output(message)


    def browse_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=".",
            title="Select Input File",
            filetypes=(("JSON files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*"))
        )
        if file_path:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)
            self.update_output(f"Selected file: {file_path}")

    def set_buttons_state(self, state):
        for button in self.all_buttons:
            # (MỚI GĐ 10) Đảm bảo nút "Áp dụng" chỉ bật khi có kết quả
            if button == self.optimizer_tab.apply_button and state == tk.NORMAL:
                # Chỉ bật lại nút "Chạy"
                self.optimizer_tab.run_button.config(state=tk.NORMAL)
                # Nút "Áp dụng" sẽ được bật riêng khi có kết quả
                continue
            
            button.config(state=state)
        self.root.update_idletasks()

    def check_file_path(self):
        input_file = self.file_path_entry.get()
        if not input_file:
            self.update_output("Lỗi: Vui lòng chọn một tệp tin đầu vào.")
            return None
        if not os.path.exists(input_file):
             self.update_output(f"Lỗi: Không tìm thấy tệp tin tại '{input_file}'")
             return None
        return input_file

    # --- HÀM NẠP DỮ LIỆU (Callbacks - Đã cập nhật Đa luồng) ---

    def run_parsing(self):
        input_file = self.check_file_path()
        if not input_file: return
        self.update_output(f"\n--- Bắt đầu Bước 1 (Xóa Hết): Phân tích tệp tin ---")
        self._run_task_in_thread(self._task_run_parsing, input_file)

    def _task_run_parsing(self, input_file):
        conn = None 
        try:
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                raw_data = f.read()
            self.update_output(f"Đã đọc tệp tin '{input_file}' thành công.")

            if os.path.exists(self.db_name):
                os.remove(self.db_name)
                self.update_output(f"Đã xóa database cũ: {self.db_name}")

            conn, cursor = setup_database()
            total_records_ai = parse_and_insert_data(raw_data, conn, cursor)
            
            if total_records_ai == 0:
                self.update_output("LỖI: Không thể phân tích dữ liệu. File có thể không đúng định dạng.")
            else:
                self.update_output(f"Phân tích và chèn dữ liệu hoàn tất.")
                self.update_output(f"- Đã chèn {total_records_ai} hàng A:I (backtest).")
                self.update_output(f"- Đã xóa mọi Cầu Đã Lưu (do nạp lại).")
                self.update_output(">>> Sẵn sàng cho Chức Năng Soi Cầu.")

        except Exception as e:
            self.update_output(f"LỖI trong Bước 1 (Xóa Hết): {e}")
            self.update_output(traceback.format_exc())
        finally:
            if conn:
                conn.close()
                self.update_output("Đã đóng kết nối database.")

    def run_parsing_append(self):
        input_file = self.check_file_path()
        if not input_file: return
        self.update_output(f"\n--- Bắt đầu Bước 1 (Append): Thêm dữ liệu từ tệp tin ---")
        self._run_task_in_thread(self._task_run_parsing_append, input_file)

    def _task_run_parsing_append(self, input_file):
        conn = None
        try:
            with open(input_file, 'r', encoding='utf-8-sig') as f:
                raw_data = f.read()
            self.update_output(f"Đã đọc tệp tin '{input_file}' thành công.")
            
            conn, cursor = setup_database()
            total_keys_added = parse_and_APPEND_data(raw_data, conn, cursor)
            
            if total_keys_added == 0:
                self.update_output("Không có kỳ nào được thêm (có thể do trùng lặp hoặc file rỗng).")
            else:
                self.update_output(f"Thêm dữ liệu hoàn tất.")
                self.update_output(f"- Đã thêm {total_keys_added} kỳ mới vào DB.")
                self.update_output(">>> Sẵn sàng cho Chức Năng Soi Cầu.")

        except Exception as e:
            self.update_output(f"LỖI trong Bước 1 (Append): {e}")
            self.update_output(traceback.format_exc())
        finally:
            if conn:
                conn.close()
                self.update_output("Đã đóng kết nối database.")

    def run_update_from_text(self):
        raw_data = self.update_text_area.get("1.0", tk.END)
        if not raw_data.strip():
            self.update_output("LỖI: Không có dữ liệu text để cập nhật.")
            return
        self.update_output(f"\n--- Bắt đầu: Thêm Kỳ Mới Từ Text ---")
        self._run_task_in_thread(self._task_run_update_from_text, raw_data)

    def _task_run_update_from_text(self, raw_data):
        conn = None 
        try:
            conn, cursor = setup_database()
            total_keys_added = parse_and_APPEND_data_TEXT(raw_data, conn, cursor) 
            
            self.update_output(f"Hoàn tất: Đã thêm thành công {total_keys_added} kỳ mới.")
            if total_keys_added > 0:
                self.root.after(0, self.update_text_area.delete, "1.0", tk.END)
            else:
                self.update_output("(Không có kỳ nào được thêm, có thể do dữ liệu đã tồn tại hoặc định dạng sai.)")

        except Exception as e:
            self.update_output(f"LỖI khi cập nhật: {e}")
            self.update_output(traceback.format_exc())
        finally:
            if conn:
                conn.close()
                self.update_output("Đã đóng kết nối database.")

    # --- HÀM LOGIC SOI CẦU (Callbacks - Đã cập nhật Đa luồng) ---

    def load_data_ai_from_db(self):
        """Tải toàn bộ dữ liệu A:I từ DB (qua Service)."""
        rows_of_lists, message = load_data_ai_from_db(self.db_name)
        if rows_of_lists is None:
            self.update_output(message)
            return None
        else:
            self.update_output(message)
            return rows_of_lists

    def run_backtest(self, mode):
        title = f"Backtest 15 Cầu {mode}"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self._run_task_in_thread(self._task_run_backtest, mode, title)

    def _task_run_backtest(self, mode, title):
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)
        self.update_output(f"Đang chạy backtest trên {len(toan_bo_A_I)} hàng dữ liệu...")

        # (SỬA V6.4) Đổi hàm gọi sang hàm hợp nhất
        func_to_call = BACKTEST_MANAGED_BRIDGES_N1 if mode == 'N1' else (lambda a, b, c: BACKTEST_MANAGED_BRIDGES_K2N(a, b, c, history=True))
        results_data = func_to_call(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.update_output(f"Backtest hoàn tất. Đang mở cửa sổ kết quả...")
        self.root.after(0, self.show_backtest_results, title, results_data)
    
    def run_custom_backtest(self, mode):
        custom_bridge_name = self.custom_bridge_entry.get()
        if not custom_bridge_name or ("+" not in custom_bridge_name and "Tổng(" not in custom_bridge_name and "Hiệu(" not in custom_bridge_name):
            self.update_output("LỖI: Tên cầu không hợp lệ để test.")
            return
        title = f"Test Cầu {mode}: {custom_bridge_name}"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self._run_task_in_thread(self._task_run_custom_backtest, mode, title, custom_bridge_name)

    def _task_run_custom_backtest(self, mode, title, custom_bridge_name):
        allData = self.load_data_ai_from_db()
        if not allData:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(allData) + (ky_bat_dau_kiem_tra - 1)
        
        if ("Tổng(" in custom_bridge_name or "Hiệu(" in custom_bridge_name) and mode == 'K2N':
             self.update_output("Lỗi: Cầu Bạc Nhớ chỉ hỗ trợ Backtest N1. Đang chạy N1...")
             mode = 'N1'
             title = f"Test Cầu N1: {custom_bridge_name}"

        func_to_call = BACKTEST_CUSTOM_CAU_V16
        if "Tổng(" in custom_bridge_name or "Hiệu(" in custom_bridge_name:
            self.update_output("Lỗi: Chức năng test cầu Bạc Nhớ tùy chỉnh chưa được hỗ trợ.")
            return 
            
        self.update_output(f"Đã dịch: {custom_bridge_name}. Đang test...")
        results = func_to_call(
            allData, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra,
            custom_bridge_name, mode
        )
        self.root.after(0, self.show_backtest_results, title, results)
            
    def run_backtest_managed_n1(self):
        title = "Backtest Cầu Đã Lưu (N1)"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang tải danh sách cầu và chạy backtest...")
        self._run_task_in_thread(self._task_run_backtest_managed_n1, title)

    def _task_run_backtest_managed_n1(self, title):
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)

        results_data = BACKTEST_MANAGED_BRIDGES_N1(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.update_output(f"Backtest Cầu Đã Lưu N1 hoàn tất. Đang mở cửa sổ kết quả...")
        self.root.after(0, self.show_backtest_results, title, results_data)

    def run_backtest_managed_k2n(self):
        title = "Backtest Cầu Đã Lưu (K2N)"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang tải danh sách cầu và chạy backtest K2N (với Chuỗi)...")
        self._run_task_in_thread(self._task_run_backtest_managed_k2n, title)

    def _task_run_backtest_managed_k2n(self, title):
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)

        results_data = BACKTEST_MANAGED_BRIDGES_K2N(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, history=True)
        
        self.update_output(f"Backtest Cầu Đã Lưu K2N hoàn tất. Đang mở cửa sổ kết quả...")
        self.root.after(0, self.show_backtest_results, title, results_data)
            
    def run_decision_dashboard(self):
        title = "Bảng Tổng Hợp Quyết Định"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        # (SỬA V6.0) Cập nhật log
        self.update_output("Đang chạy 8 hệ thống phân tích... (Bao gồm 3 backtest ngầm + 1 AI)") 
        self._run_task_in_thread(self._task_run_decision_dashboard, title)

    def _task_run_decision_dashboard(self, title):
        """(CẬP NHẬT V6.6) Tích hợp AI vào chấm điểm VÀ hiển thị riêng."""
        all_data_ai = self.load_data_ai_from_db()
        
        if not all_data_ai or len(all_data_ai) < 2:
            self.update_output("LỖI: Cần ít nhất 2 kỳ dữ liệu để chạy Bảng Tổng Hợp.")
            return
        
        last_row = all_data_ai[-1]
        
        try:
            from logic.config_manager import SETTINGS
            SETTINGS.load_settings() # Đảm bảo tải lại giá trị mới nhất từ file
            # FIX: Sửa truy cập SETTINGS
            n_days_stats = SETTINGS.STATS_DAYS
            n_days_gan = SETTINGS.GAN_DAYS
            high_win_thresh = SETTINGS.HIGH_WIN_THRESHOLD
        except Exception as e:
             self.update_output(f"Cảnh báo: Không thể tải config: {e}. Sử dụng giá trị mặc định.")
             n_days_stats = 7
             n_days_gan = 15
             high_win_thresh = 47.0
             
        next_ky = f"Kỳ {int(last_row[0]) + 1}" if last_row[0].isdigit() else f"Kỳ {last_row[0]} (Next)"

        # --- 1. Thống kê N ngày ---
        self.update_output(f"... (1/8) Đang thống kê Loto Về Nhiều ({n_days_stats} ngày)...")
        stats_n_day = get_loto_stats_last_n_days(all_data_ai, n=n_days_stats)
        
        # --- 2. Chạy hàm K2N Cache TRƯỚC ---
        self.update_output("... (2/8) Đang chạy hàm Cập nhật K2N Cache (tối ưu)...")
        pending_k2n_data, cache_message = run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
        self.update_output(f"... (Cache K2N) {cache_message}")
        
        # --- 3. Thống kê "Vote" (ĐỌC TỪ CACHE) ---
        self.update_output("... (3/8) Đang thống kê Cặp Số Dự Đoán (đọc cache)...")
        # FIX V7.1: Sửa cách gọi hàm để phù hợp với signature mới (đã bỏ last_row)
        consensus = get_prediction_consensus()
        
        # --- 4. Thống kê "Cầu Tỷ Lệ Cao" (ĐỌC TỪ CACHE) ---
        self.update_output(f"... (4/8) Đang lọc Cầu Tỷ Lệ Cao (>= {high_win_thresh}%, đọc cache)...")
        # FIX V7.1: Sửa cách gọi hàm để phù hợp với signature mới (đã bỏ last_row)
        high_win = get_high_win_rate_predictions(threshold=high_win_thresh)

        # --- 5. Chạy Backtest Bạc Nhớ ngầm ---
        self.update_output("... (5/8) Đang chạy Backtest 756 Cầu Bạc Nhớ ngầm...")
        top_memory_bridges = get_top_memory_bridge_predictions(all_data_ai, last_row, top_n=5)
        
        # --- 6. Thống kê Lô Gan ---
        self.update_output(f"... (6/8) Đang tìm Lô Gan (trên {n_days_gan} kỳ)...")
        gan_stats = get_loto_gan_stats(all_data_ai, n_days=n_days_gan)
        
        # --- (MỚI V6.0) 7. CHẠY DỰ ĐOÁN AI ---
        self.update_output("... (7/8) Đang chạy dự đoán AI (V6.0)...")
        # FIX V7.1: Sửa lỗi gọi hàm, gọi hàm wrapper run_ai_prediction_for_dashboard()
        ai_predictions, ai_message = run_ai_prediction_for_dashboard()
        self.update_output(f"... (AI) {ai_message}")

        # --- (SỬA V6.2) 8. HỆ THỐNG CHẤM ĐIỂM (LOGIC V5 + V6) ---
        self.update_output("... (8/8) Đang chấm điểm và tổng hợp quyết định (Logic V6.2)...")
        
        # (SỬA V6.2) Truyền `ai_predictions` vào đây
        top_scores = get_top_scored_pairs(
            stats_n_day,
            consensus, 
            high_win, 
            pending_k2n_data, 
            gan_stats,
            top_memory_bridges,
            ai_predictions # (MỚI V6.2) Tích hợp AI vào chấm điểm
        )
        
        self.update_output("Phân tích hoàn tất. Đang hiển thị Bảng Tổng Hợp...")
        
        # (SỬA V6.6) TRẢ LẠI `ai_predictions` cho hàm hiển thị
        self.root.after(0, self._show_dashboard_window, 
            next_ky, stats_n_day, n_days_stats, 
            consensus, high_win, pending_k2n_data, 
            gan_stats, top_scores, top_memory_bridges,
            ai_predictions # (MỚI V6.6)
        )

    # (SỬA V6.6) TRẢ LẠI `ai_predictions`
    def _show_dashboard_window(self, next_ky, stats_n_day, n_days_stats, consensus, high_win, pending_k2n_data, gan_stats, top_scores, top_memory_bridges, ai_predictions):
        try:
            if self.dashboard_window and self.dashboard_window.window.winfo_exists():
                self.dashboard_window.window.lift()
                self.dashboard_window.clear_data()
            else:
                self.dashboard_window = DashboardWindow(self) 
            
            # (SỬA V6.6) TRẢ LẠI `ai_predictions`
            self.dashboard_window.populate_data(
                next_ky, stats_n_day, n_days_stats, 
                consensus, high_win, pending_k2n_data, 
                gan_stats, top_scores, top_memory_bridges,
                ai_predictions # (MỚI V6.6)
            )
        except Exception as e:
            self.update_output(f"LỖI khi hiển thị Bảng Tổng Hợp: {e}")
            self.update_output(traceback.format_exc())

    # ===================================================================================
    # (MỚI GĐ 5) HÀM CẬP NHẬT K2N CACHE (Từ nút bấm chính)
    # ===================================================================================
    
    def run_update_all_bridge_K2N_cache_from_main(self):
        """(MỚI GĐ 5) Bước 1: Gọi hàm chạy đa luồng từ Cửa sổ CHÍNH."""
        title = "Cập nhật Cache K2N Hàng Loạt"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang chạy Backtest K2N (tối ưu) cho 15 Cầu CĐ + Cầu Đã Lưu...")
        self._run_task_in_thread(self._task_run_update_all_bridge_K2N_cache, title)

    def _task_run_update_all_bridge_K2N_cache(self, title):
        """(MỚI GĐ 5) Bước 2: Logic Cập nhật K2N Cache chạy trong luồng riêng."""
        all_data_ai = self.load_data_ai_from_db()
        if not all_data_ai:
            return # Lỗi đã được in

        # Hàm này sẽ chạy backtest, cập nhật CSDL VÀ trả về dict K2N
        _, message = run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
        
        self.update_output(message) # In kết quả
        
        # Tự động làm mới cửa sổ Quản lý Cầu (nếu đang mở)
        if self.bridge_manager_window and self.bridge_manager_window.winfo_exists():
            self.update_output("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            try:
                self.root.after(0, self.bridge_manager_window_instance.refresh_bridge_list)
            except Exception as e_refresh:
                self.update_output(f"Lỗi khi tự động làm mới QL Cầu: {e_refresh}")

    # ===================================================================================
    # CÁC HÀM TỰ ĐỘNG HÓA DÒ CẦU (Callbacks)
    # ===================================================================================

    def run_auto_find_bridges(self):
        title = "Tự động Dò & Thêm Cầu V17 + Bạc Nhớ" 
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        
        # (SỬA GĐ 8) Lấy giá trị từ SETTINGS
        try:
            from logic.config_manager import SETTINGS
            auto_add_rate = SETTINGS.AUTO_ADD_MIN_RATE
        except Exception:
             auto_add_rate = 50.0
             
        self.update_output("CẢNH BÁO: Tác vụ này RẤT NẶNG (23.005 + 756 cầu). Vui lòng chờ...")
        self.update_output(f"Các cầu có Tỷ lệ > {auto_add_rate}% sẽ được tự động thêm/cập nhật...")
        self._run_task_in_thread(self._task_run_auto_find_bridges, title)

    def _task_run_auto_find_bridges(self, title):
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return

        result_message = find_and_auto_manage_bridges(toan_bo_A_I, self.db_name)
        
        self.update_output(f">>> {title} HOÀN TẤT:")
        self.update_output(result_message)
        
        if self.bridge_manager_window and self.bridge_manager_window.winfo_exists():
            self.update_output("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            self.root.after(0, self.bridge_manager_window_instance.refresh_bridge_list)

    def run_auto_prune_bridges(self):
        title = "Tự động Lọc/Tắt Cầu Yếu"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        
        # (SỬA GĐ 8) Lấy giá trị từ SETTINGS
        try:
            from logic.config_manager import SETTINGS
            auto_prune_rate = SETTINGS.AUTO_PRUNE_MIN_RATE
        except Exception:
             auto_prune_rate = 40.0
             
        self.update_output("Đang kiểm tra cache K2N của các Cầu Đã Lưu...")
        self.update_output(f"Các cầu có Tỷ lệ < {auto_prune_rate}% sẽ bị TẮT (vô hiệu hóa)...")
        self._run_task_in_thread(self._task_run_auto_prune_bridges, title)

    def _task_run_auto_prune_bridges(self, title):
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return

        result_message = prune_bad_bridges(toan_bo_A_I, self.db_name)
        
        self.update_output(f">>> {title} HOÀN TẤT:")
        self.update_output(result_message)
        
        if self.bridge_manager_window and self.bridge_manager_window.winfo_exists():
            self.update_output("Đang tự động làm mới cửa sổ Quản lý Cầu...")
            self.root.after(0, self.bridge_manager_window_instance.refresh_bridge_list)

    # ===================================================================================
    # (MỚI V6.0) HÀM HUẤN LUYỆN AI
    # ===================================================================================
    
    def run_train_ai(self):
        """
        (MỚI V6.0) Bước 1: Gọi hàm chạy đa luồng cho Huấn luyện AI.
        FIX: Bỏ _task_train_ai và gọi trực tiếp threaded wrapper.
        """
        title = "Huấn luyện Mô hình AI (V6.0)"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("CẢNH BÁO: Tác vụ này RẤT NẶNG và có thể mất vài phút.")
        self.update_output("Đang tải toàn bộ CSDL và trích xuất đặc trưng...")
        
        # Hàm callback được gọi từ luồng phụ sau khi hoàn tất
        def train_callback(success, message):
            self.update_output(f">>> {title} HOÀN TẤT:")
            self.update_output(message)
            self.root.after(0, self.set_buttons_state, tk.NORMAL)

        # Tắt nút và gọi hàm threaded wrapper từ lottery_service.py
        self.set_buttons_state(tk.DISABLED)
        # run_ai_training_threaded đã tự tạo luồng, không cần _run_task_in_thread
        success, message = run_ai_training_threaded(callback=train_callback)
        
        if not success:
            self.update_output(f"LỖI KHỞI CHẠY LUỒNG: {message}")
            self.set_buttons_state(tk.NORMAL)


    # ===================================================================================
    # (MỚI) HÀM CALLBACK CẦU BẠC NHỚ
    # ===================================================================================
    
    def run_backtest_memory(self):
        title = "Backtest 756 Cầu Bạc Nhớ (N1)"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang chạy backtest 756 thuật toán (Tổng/Hiệu của 27 vị trí lô)...")
        self._run_task_in_thread(self._task_run_backtest_memory, title)

    def _task_run_backtest_memory(self, title):
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)
        
        results_data = BACKTEST_MEMORY_BRIDGES(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.update_output(f"Backtest Cầu Bạc Nhớ hoàn tất. Đang mở cửa sổ kết quả...")
        self.root.after(0, self.show_backtest_results, title, results_data)

    # ===================================================================================
    # (MỚI GĐ 9) HÀM TINH CHỈNH THAM SỐ
    # ===================================================================================
    
    def run_parameter_tuning(self, param_key, val_from, val_to, val_step, tuner_window):
        """(MỚI GĐ 9) Bước 1: Gọi hàm chạy đa luồng cho Tinh chỉnh."""
        # Chuyển cửa sổ tuner vào luồng để luồng có thể log lại
        self._run_task_in_thread(self._task_run_parameter_tuning, 
                                 param_key, val_from, val_to, val_step, tuner_window)

    def _task_run_parameter_tuning(self, param_key, val_from, val_to, val_step, tuner_window):
        """(CẬP NHẬT GĐ 9) Bước 2: Logic Tinh chỉnh thực tế."""
        
        # Hàm log an toàn từ luồng
        def log_to_tuner(message):
            self.root.after(0, tuner_window.log, message)
            
        try:
            log_to_tuner("Đang tải dữ liệu A:I...")
            all_data_ai = self.load_data_ai_from_db()
            if not all_data_ai or len(all_data_ai) < 2:
                log_to_tuner("LỖI: Không thể tải dữ liệu A:I.")
                return
            last_row = all_data_ai[-1]
            log_to_tuner(f"...Tải thành công {len(all_data_ai)} kỳ.")

            # --- (MỚI GĐ 9) Hàm tạo vòng lặp (thay thế numpy) ---
            def float_range(start, stop, step):
                if step == 0:
                    yield start
                    return
                n = start
                while n < (stop + (step * 0.5)): 
                    yield n
                    n += step

            # --- (MỚI GĐ 9) Các hàm kiểm thử chuyên biệt ---

            def test_gan_days(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                for i in float_range(v_from, v_to, v_step):
                    n = int(i) # GAN_DAYS phải là số nguyên
                    if n <= 0: continue
                    gan_stats = get_loto_gan_stats(all_data_ai, n_days=n)
                    log_to_tuner(f"Kiểm thử {p_key} = {n}: Tìm thấy {len(gan_stats)} loto gan.")
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_high_win_threshold(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Cache K2N một lần để lấy dữ liệu mới nhất)...")
                run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name) # Chạy 1 lần
                log_to_tuner("... (Cache K2N hoàn tất. Bắt đầu lặp)...")
                
                for i in float_range(v_from, v_to, v_step):
                    # FIX: Bỏ last_row để tương thích với signature mới
                    high_win_bridges = get_high_win_rate_predictions(threshold=i)
                    log_to_tuner(f"Kiểm thử {p_key} >= {i:.1f}%: Tìm thấy {len(high_win_bridges)} cầu đạt chuẩn.")
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_auto_add_rate(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Dò Cầu V17... Rất nặng, vui lòng chờ)...")
                ky_bat_dau = 2
                ky_ket_thuc = len(all_data_ai) + (ky_bat_dau - 1)
                results_v17 = TIM_CAU_TOT_NHAT_V16(all_data_ai, ky_bat_dau, ky_ket_thuc, self.db_name)
                log_to_tuner("... (Chạy Dò Cầu Bạc Nhớ...)...")
                results_memory = TIM_CAU_BAC_NHO_TOT_NHAT(all_data_ai, ky_bat_dau, ky_ket_thuc)
                
                combined_results = []
                if results_v17 and len(results_v17) > 1:
                    combined_results.extend([row for row in results_v17[1:] if "---" not in str(row[0])])
                if results_memory and len(results_memory) > 1:
                    combined_results.extend([row for row in results_memory[1:] if "---" not in str(row[0])])
                
                if not combined_results:
                    log_to_tuner("LỖI: Không dò được cầu nào.")
                    return

                log_to_tuner(f"... (Dò cầu hoàn tất. Tổng cộng {len(combined_results)} cầu. Bắt đầu lặp)...")

                for i in float_range(v_from, v_to, v_step):
                    count = 0
                    for row in combined_results:
                        try:
                            rate = float(str(row[3]).replace('%', ''))
                            if rate >= i:
                                count += 1
                        except (ValueError, IndexError):
                            continue
                    log_to_tuner(f"Kiểm thử {p_key} >= {i:.1f}%: Sẽ thêm/cập nhật {count} cầu.")
                log_to_tuner(f"--- Hoàn tất kiểm thử {p_key} ---")

            def test_auto_prune_rate(p_key, v_from, v_to, v_step):
                log_to_tuner(f"--- Bắt đầu kiểm thử: {p_key} ---")
                log_to_tuner("... (Chạy Cache K2N một lần để lấy dữ liệu mới nhất)...")
                run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
                log_to_tuner("... (Cache K2N hoàn tất. Bắt đầu lặp)...")
                
                enabled_bridges = get_all_managed_bridges(self.db_name, only_enabled=True)
                if not enabled_bridges:
                    log_to_tuner("LỖI: Không có cầu nào đang Bật để kiểm thử.")
                    return

                for i in float_range(v_from, v_to, v_step):
                    count = 0
                    for bridge in enabled_bridges:
                        try:
                            rate_str = str(bridge.get('win_rate_text', '100%')).replace('%', '')
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
                # Fix: Cần đảm bảo hàm này trả về dict pending_k2n_data
                pending_k2n, _ = run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name) 
                # Tải các dữ liệu khác cho Bảng Chấm Điểm
                stats_n_day = get_loto_stats_last_n_days(all_data_ai)
                # FIX: Bỏ last_row
                consensus = get_prediction_consensus() 
                # FIX: Bỏ last_row
                high_win = get_high_win_rate_predictions() 
                gan_stats = get_loto_gan_stats(all_data_ai)
                top_memory = get_top_memory_bridge_predictions(all_data_ai, last_row)
                
                # (SỬA V6.2) Lấy cả dự đoán AI
                ai_preds, _ = run_ai_prediction_for_dashboard()
                
                log_to_tuner("... (Dữ liệu nền hoàn tất. Bắt đầu lặp)...")
                
                # Lưu giá trị gốc
                original_value = SETTINGS.get_all_settings().get(p_key)

                for i in float_range(v_from, v_to, v_step):
                    val = i
                    if p_key == "K2N_RISK_START_THRESHOLD":
                        val = int(i) # Phải là số nguyên
                    
                    # Tạm thời thay đổi SETTINGS
                    setattr(SETTINGS, p_key, val)
                    
                    # (SỬA V6.2) Chạy lại hàm chấm điểm V6.2
                    top_scores = get_top_scored_pairs(
                        stats_n_day, consensus, high_win, 
                        pending_k2n, gan_stats, top_memory,
                        ai_preds # Thêm AI
                    )
                    
                    if not top_scores:
                        log_to_tuner(f"Kiểm thử {p_key} = {val}: Không có cặp nào đạt điểm.")
                    else:
                        top_score_item = top_scores[0]
                        log_to_tuner(f"Kiểm thử {p_key} = {val}: Top 1 là {top_score_item['pair']} (Điểm: {top_score_item['score']})")

                # Khôi phục giá trị gốc
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
            elif param_key == "K2N_RISK_START_THRESHOLD" or param_key == "K2N_RISK_PENALTY_PER_FRAME":
                test_k2n_risk_logic(param_key, val_from, val_to, val_step)
            else:
                log_to_tuner(f"Lỗi: Chưa định nghĩa logic kiểm thử cho {param_key}")

        except Exception as e:
            log_to_tuner(f"LỖI: {e}")
            log_to_tuner(traceback.format_exc())
        finally:
            # Bật lại nút "Chạy" trên cửa sổ Tuner từ luồng chính
            self.root.after(0, tuner_window.run_button.config, {"state": tk.NORMAL})
            
            
    # ===================================================================================
    # (MỚI GĐ 10) HÀM TỐI ƯU HÓA CHIẾN LƯỢC
    # ===================================================================================

    def run_strategy_optimization(self, strategy, days_to_test, param_ranges, optimizer_tab):
        """(MỚI GĐ 10) Bước 1: Gọi hàm chạy đa luồng cho Tối ưu hóa."""
        self._run_task_in_thread(self._task_run_strategy_optimization, 
                                 strategy, days_to_test, param_ranges, optimizer_tab)
                                 
    def _task_run_strategy_optimization(self, strategy, days_to_test, param_ranges, optimizer_tab):
        """(CẬP NHẬT GĐ 10) Bước 2: Logic Tối ưu hóa Thực tế."""
        
        # Hàm log an toàn từ luồng
        def log_to_optimizer(message):
            self.root.after(0, optimizer_tab.log, message)
            
        # Hàm cập nhật UI an toàn từ luồng
        def update_tree_results_threadsafe(results_list):
            optimizer_tab.clear_results_tree()
            for i, (rate, hits, params_str, config_dict_str) in enumerate(results_list):
                rate_str = f"{rate * 100:.1f}%"
                tags = ('best',) if i == 0 else ()
                
                # Thêm dict config (dạng chuỗi) vào tag
                tags_with_data = (config_dict_str,) + tags
                
                optimizer_tab.tree.insert("", tk.END, values=(
                    rate_str, hits, params_str
                ), tags=tags_with_data)
            
            # Bật nút Áp dụng
            optimizer_tab.apply_button.config(state=tk.NORMAL)

        # --- (MỚI GĐ 10) Hàm tạo vòng lặp (thay thế numpy) ---
        def float_range(start, stop, step):
            if step == 0:
                yield start
                return
            n = start
            while n < (stop + (step * 0.5)): # Thêm 1/2 bước nhảy
                yield n
                n += step
        
        # --- (MỚI GĐ 10) Hàm tạo tổ hợp ---
        def generate_combinations(param_ranges, original_settings):
            """Tạo tất cả các tổ hợp cài đặt."""
            param_lists = []
            
            # Giữ lại các key không thay đổi
            config_keys = list(param_ranges.keys())
            static_keys = [k for k in original_settings.keys() if k not in config_keys]
            
            # Tạo các dải giá trị
            for key in config_keys:
                v_from, v_to, v_step = param_ranges[key]
                # Chuyển đổi sang Int nếu cần
                if isinstance(original_settings[key], int):
                    param_lists.append([(key, int(i)) for i in float_range(v_from, v_to, v_step) if i >= 0])
                else:
                    param_lists.append([(key, round(i, 2)) for i in float_range(v_from, v_to, v_step) if i >= 0])

            if not param_lists:
                return []

            # Tạo các tổ hợp
            combinations = []
            for combo in itertools.product(*param_lists):
                temp_config = {}
                # Thêm các giá trị tĩnh
                for static_key in static_keys:
                    temp_config[static_key] = original_settings[static_key]
                # Thêm các giá trị động
                for key, value in combo:
                    temp_config[key] = value
                combinations.append(temp_config)
                
            return combinations

        try:
            log_to_optimizer("Đang tải toàn bộ dữ liệu A:I...")
            all_data_ai = self.load_data_ai_from_db()
            if not all_data_ai or len(all_data_ai) < days_to_test + 50: # Cần 50 ngày làm mốc
                log_to_optimizer(f"LỖI: Cần ít nhất {days_to_test + 50} kỳ dữ liệu để kiểm thử.")
                return
            log_to_optimizer(f"...Tải dữ liệu thành công ({len(all_data_ai)} kỳ).")
            
            # 1. Lấy cài đặt gốc (để điền vào các tham số không đổi)
            original_settings = SETTINGS.get_all_settings()
            
            # 2. Tạo tất cả tổ hợp
            combinations = generate_combinations(param_ranges, original_settings)
            total_combos = len(combinations)
            if total_combos == 0:
                log_to_optimizer("Lỗi: Không tạo được tổ hợp kiểm thử.")
                return
                
            log_to_optimizer(f"Đã tạo {total_combos} tổ hợp. Bắt đầu kiểm thử...")
            
            # 3. Lặp qua từng tổ hợp
            results_list = []
            
            # (MỚI GĐ 10) Lưu giá trị SETTINGS gốc
            original_settings_backup = original_settings.copy()
            
            for i, config in enumerate(combinations):
                log_to_optimizer(f"--- Đang kiểm thử [{i+1}/{total_combos}]: {config} ---")
                
                # Tạm thời gán SETTINGS (cho các hàm con)
                for key, value in config.items():
                    setattr(SETTINGS, key, value)
                
                total_hits = 0
                days_tested = 0
                
                # 4. Lặp qua N ngày lịch sử (lùi dần)
                for day_offset in range(days_to_test):
                    # day_index: chỉ số của ngày tạo dự đoán (D)
                    # actual_index: chỉ số của ngày kết quả (D+1)
                    actual_index = len(all_data_ai) - 1 - day_offset
                    day_index = actual_index - 1
                    
                    if day_index < 50: # Cần ít nhất 50 ngày để backtest
                        continue
                    
                    days_tested += 1 # Đếm số ngày đã thực sự test
                    
                    # Dữ liệu để kiểm tra (D+1)
                    actual_row = all_data_ai[actual_index]
                    actual_loto_set = set(getAllLoto_V30(actual_row))
                    
                    # 5. Chạy mô phỏng Bảng Tổng Hợp cho ngày D
                    # (SỬA V6.2) Tạm thời không thể mô phỏng AI trong hàm này
                    top_scores = get_historical_dashboard_data(
                        all_data_ai, 
                        day_index, 
                        config # Truyền config tạm thời
                    )
                    
                    if not top_scores:
                        # log_to_optimizer(f" - Ngày {day_index}: Không có cặp nào đạt điểm.")
                        continue
                        
                    # 6. Kiểm tra kết quả
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
                                total_hits += 1
                                break # Chỉ tính 1 lần trúng
                                
                # 7. Ghi lại kết quả cho tổ hợp này
                rate = total_hits / days_tested if days_tested > 0 else 0
                hits_str = f"{total_hits}/{days_tested}"
                config_str_display = ", ".join([f"{k.split('_')[0]}:{v}" for k,v in param_ranges.items()])
                config_str_json = json.dumps(config) # Chuyển dict thành chuỗi JSON
                
                # (SỬA GĐ 10) Sửa lại params_str để dễ đọc hơn
                params_str_display = ", ".join([f"{key}: {value}" for key, value in config.items() if key in param_ranges])

                results_list.append((rate, hits_str, params_str_display, config_str_json))
                
                log_to_optimizer(f"-> Kết quả: {hits_str} ({rate*100:.1f}%)")

            # 8. Sắp xếp và Hiển thị
            log_to_optimizer("Đang sắp xếp kết quả...")
            results_list.sort(key=lambda x: x[0], reverse=True)
            
            # (MỚI GĐ 10) Khôi phục SETTINGS về ban đầu
            for key, value in original_settings_backup.items():
                setattr(SETTINGS, key, value)
            log_to_optimizer("Đã khôi phục cài đặt gốc.")
            
            self.root.after(0, update_tree_results_threadsafe, results_list)
            log_to_optimizer("--- HOÀN TẤT TỐI ƯU HÓA ---")

        except Exception as e:
            log_to_optimizer(f"LỖI: {e}")
            log_to_optimizer(traceback.format_exc())
            # (MỚI GĐ 10) Khôi phục SETTINGS về ban đầu nếu có lỗi
            try:
                original_settings_backup
                for key, value in original_settings_backup.items():
                    setattr(SETTINGS, key, value)
                log_to_optimizer("Đã khôi phục cài đặt gốc sau lỗi.")
            except NameError:
                pass # Lỗi xảy ra trước khi backup
        finally:
            # Bật lại nút "Chạy" trên cửa sổ Optimizer từ luồng chính
            self.root.after(0, optimizer_tab.run_button.config, {"state": tk.NORMAL})
            
    def apply_optimized_settings(self, config_dict_str, optimizer_window):
        """(MỚI GĐ 10) Áp dụng cấu hình đã chọn từ Tab Tối ưu hóa."""
        try:
            # Hàm log an toàn từ luồng
            def log_to_optimizer(message):
                self.root.after(0, optimizer_window.log, message)
            
            config_dict = json.loads(config_dict_str) # Chuyển chuỗi JSON thành dict
            
            # (SỬA LỖI) parent=optimizer_window
            if not messagebox.askyesno("Xác nhận Áp dụng", 
                                       f"Bạn có chắc chắn muốn áp dụng cấu hình này và lưu vào 'config.json' không?\n\n{config_dict_str}",
                                       parent=optimizer_window):
                return
            
            log_to_optimizer("Đang áp dụng cấu hình mới...")
            
            # Lặp qua và lưu từng cài đặt
            for key, value in config_dict.items():
                success, msg = SETTINGS.update_setting(key, value)
                if success:
                    log_to_optimizer(f" - Đã lưu: {key} = {value}")
                else:
                    log_to_optimizer(f" - LỖI LƯU: {msg}")
                    
            log_to_optimizer("--- Áp dụng hoàn tất! ---")
            messagebox.showinfo("Thành công", "Đã áp dụng và lưu cấu hình mới!", parent=optimizer_window)

        except Exception as e:
             messagebox.showerror("Lỗi", f"Lỗi khi áp dụng cấu hình: {e}", parent=optimizer_window)


    # ===================================================================================
    # CÁC HÀM GỌI CỬA SỔ CON (Đã Tách)
    # ===================================================================================

    def show_lookup_window(self):
        """Mở cửa sổ Tra cứu từ ui/ui_lookup.py"""
        self.lookup_window = LookupWindow(self)

    def show_bridge_manager_window(self):
        """Mở cửa sổ Quản lý Cầu từ ui/ui_bridge_manager.py"""
        self.bridge_manager_window_instance = BridgeManagerWindow(self)

    # (MỚI GĐ 8)
    def show_settings_window(self):
        """Mở cửa sổ Cài đặt từ ui/ui_settings.py"""
        self.settings_window = SettingsWindow(self)

    # (MỚI GĐ 9)
    def show_tuner_window(self):
        """Mở cửa sổ Tinh chỉnh từ ui/ui_tuner.py"""
        self.tuner_window = TunerWindow(self)

    def show_backtest_results(self, title, results_data, show_save_button=False):
        """Mở cửa sổ Hiển thị Kết quả từ ui/ui_results_viewer.py"""
        if "V17" in title or "Bạc Nhớ" in title: 
            show_save_button = True
        
        self.results_window = ResultsViewerWindow(self, title, results_data, show_save_button)

    # ===================================================================================
    # HÀM TRIGGER TỪ BẢNG TỔNG HỢP
    # ===================================================================================
    
    def trigger_bridge_backtest(self, bridge_name):
        """
        (SỬA GĐ 7) Cập nhật logic double-click
        """
        if not bridge_name:
            return
            
        if bridge_name.startswith("Cầu "):
            self.update_output(f"--- Trigger: Mở Backtest K2N cho 15 Cầu Cổ Điển (focus vào {bridge_name})...")
            self.run_backtest('K2N')
            
        elif "+" in bridge_name or "Bong(" in bridge_name:
            # (SỬA GĐ 7) Hàm tùy chỉnh N1 vẫn chạy
            self.update_output(f"--- Trigger: Chạy Backtest N1 tùy chỉnh cho {bridge_name}...")
            self.custom_bridge_entry.delete(0, "end") # Dùng biến ẩn
            self.custom_bridge_entry.insert(0, bridge_name)
            self.run_custom_backtest('N1') 
            self.notebook.select(self.tab1_frame)

        elif "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
            self.update_output(f"--- Trigger: Mở Backtest N1 cho 756 Cầu Bạc Nhớ (focus vào {bridge_name})...")
            self.run_backtest_memory()
            
        else:
            self.update_output(f"Lỗi trigger: Không nhận dạng được loại cầu '{bridge_name}'")

    # ===================================================================================
    # HÀM LOGIC CẦN THIẾT (phải ở lại app chính)
    # ===================================================================================

    def _save_bridge_from_treeview(self, tree):
        """
        Logic này phải ở lại app chính vì nó cần:
        1. Giao tiếp với service (add_managed_bridge)
        2. Cập nhật output (self.update_output)
        3. Cập nhật cửa sổ Quản lý Cầu (self.bridge_manager_tree)
        """
        try:
            selected_item = tree.focus()
            if not selected_item:
                messagebox.showwarning("Chưa chọn cầu", "Vui lòng chọn một cầu từ danh sách trước.", parent=tree.master)
                return
                
            item_values = tree.item(selected_item, 'values')
            bridge_name = item_values[1] # Cột "Tên Cầu"
            win_rate = item_values[3]    # Cột "Tỷ lệ"
            
            # (SỬA GĐ 5) Cho phép lưu cả V17 và Bạc Nhớ
            if not ("+" in bridge_name or "Bong(" in bridge_name or "Tổng(" in bridge_name or "Hiệu(" in bridge_name):
                # (SỬA V6.4) Bỏ qua Cầu Cổ Điển
                if bridge_name.startswith("Cầu "):
                    messagebox.showerror("Lỗi Lưu Cầu", "Không thể lưu Cầu Cổ Điển (Chúng đã được lưu tự động).", parent=tree.master)
                else:
                    messagebox.showerror("Lỗi Lưu Cầu", "Chức năng này chỉ hỗ trợ lưu Cầu V17 hoặc Cầu Bạc Nhớ.", parent=tree.master)
                return

            description = simpledialog.askstring("Lưu Cầu Mới", 
                                                 f"Nhập mô tả cho cầu:\n{bridge_name}",
                                                 initialvalue=bridge_name, 
                                                 parent=tree.master)
            
            if description is None: return

            success, message = upsert_managed_bridge(bridge_name, description, win_rate)
            
            if success:
                self.update_output(f"LƯU/CẬP NHẬT CẦU: {message}")
                messagebox.showinfo("Thành công", message, parent=tree.master)
                if self.bridge_manager_window and self.bridge_manager_window.winfo_exists():
                    try:
                        self.bridge_manager_window_instance.refresh_bridge_list()
                    except Exception as e_refresh:
                        self.update_output(f"Lỗi khi tự động làm mới QL Cầu: {e_refresh}")
            else:
                self.update_output(f"LỖI LƯU CẦU: {message}")
                messagebox.showerror("Lỗi", message, parent=tree.master)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi _save_bridge_from_treeview: {e}", parent=tree.master)

# (Khối __main__ đã được chuyển sang main_app.py)