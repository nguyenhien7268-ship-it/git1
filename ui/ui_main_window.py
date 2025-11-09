import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import traceback # Để in lỗi chi tiết
import threading # (MỚI) Import thư viện đa luồng

# Import toàn bộ logic từ file lottery_service.py
try:
    from lottery_service import *
except ImportError:
    print("LỖI NGHIÊM TRỌNG: Không tìm thấy file 'lottery_service.py' hoặc gói '/logic'.")
    exit()

# Import các cửa sổ con từ gói /ui
try:
    from .ui_lookup import LookupWindow
    from .ui_bridge_manager import BridgeManagerWindow
    from .ui_results_viewer import ResultsViewerWindow
    from .ui_dashboard import DashboardWindow # (MỚI) IMPORT BẢNG TỔNG HỢP TƯƠNG TÁC
except ImportError:
    print("LỖI NGHIÊM TRỌNG: Không thể import các cửa sổ con từ gói /ui.")
    # Fallback (nếu chạy trực tiếp file này)
    from ui_lookup import LookupWindow
    from ui_bridge_manager import BridgeManagerWindow
    from ui_results_viewer import ResultsViewerWindow
    from ui_dashboard import DashboardWindow

# (MỚI) ĐỊNH NGHĨA NGƯỠNG TỰ ĐỘNG (để hiển thị log)
AUTO_ADD_MIN_RATE = 46.0
AUTO_PRUNE_MIN_RATE = 42.0

class DataAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Xổ Số Data Analysis (v4.2 - Bạc Nhớ)") # (SỬA) Đổi tên
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.geometry("800x600")

        self.db_name = DB_NAME
        self.lookup_window = None 
        self.bridge_manager_window = None
        self.bridge_manager_tree = None
        self.bridge_manager_window_instance = None 
        self.dashboard_window = None # (MỚI) Quản lý cửa sổ Bảng Tổng Hợp

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        self.tab1_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab1_frame, text='Chức Năng')
        self.tab1_frame.columnconfigure(0, weight=1)

        self.tab2_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab2_frame, text='Log Hệ Thống')
        self.tab2_frame.columnconfigure(0, weight=1)
        self.tab2_frame.rowconfigure(0, weight=1)

        # --- Input Frame (row=0) ---
        input_frame = ttk.Frame(self.tab1_frame, padding="10") 
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        input_frame.columnconfigure(1, weight=1) 

        ttk.Label(input_frame, text="Input File (JSON/Text):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_path_entry = ttk.Entry(input_frame, width=50)
        self.file_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        browse_button = ttk.Button(input_frame, text="Browse", command=self.browse_file)
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        self.parse_button = ttk.Button(input_frame, text="Nạp File (Xóa Hết DB)", command=self.run_parsing)
        self.parse_button.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.parse_append_button = ttk.Button(input_frame, text="Nạp File (Thêm/Append)", command=self.run_parsing_append)
        self.parse_append_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)

        self.all_buttons = [self.parse_button, self.parse_append_button]

        # --- V25/V16 Control Frame (row=1) ---
        v25_frame = ttk.Labelframe(self.tab1_frame, text="Chức Năng Soi Cầu & Tra Cứu", padding="10")
        v25_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)

        # Hàng 1
        self.manage_bridges_button = ttk.Button(v25_frame, text="Quản lý Cầu (V17)...", command=self.show_bridge_manager_window)
        self.manage_bridges_button.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.backtest_n1_15_button = ttk.Button(v25_frame, text="Backtest 15 Cầu (N1)", command=lambda: self.run_backtest('N1'))
        self.backtest_n1_15_button.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.backtest_k2n_15_button = ttk.Button(v25_frame, text="Backtest 15 Cầu (K2N)", command=lambda: self.run_backtest('K2N'))
        self.backtest_k2n_15_button.grid(row=0, column=2, sticky="ew", padx=5, pady=5)

        # Hàng 2
        self.auto_find_bridges_button = ttk.Button(v25_frame, text="Tự động Dò & Thêm Cầu V17", command=self.run_auto_find_bridges)
        self.auto_find_bridges_button.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.backtest_managed_button = ttk.Button(v25_frame, text="Backtest Cầu Đã Lưu (N1)", command=self.run_backtest_managed_n1)
        self.backtest_managed_button.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.backtest_managed_k2n_button = ttk.Button(v25_frame, text="Backtest Cầu Đã Lưu (K2N)", command=self.run_backtest_managed_k2n)
        self.backtest_managed_k2n_button.grid(row=1, column=2, sticky="ew", padx=5, pady=5)
        
        # Hàng 3 (Cột 3)
        self.lookup_button = ttk.Button(v25_frame, text="Tra Cứu Kết Quả", command=self.show_lookup_window)
        self.lookup_button.grid(row=0, column=3, sticky="nsew", padx=5, pady=5)
        
        self.dashboard_button = ttk.Button(v25_frame, text="Bảng Tổng Hợp", command=self.run_decision_dashboard)
        self.dashboard_button.grid(row=2, column=3, sticky="nsew", padx=5, pady=5)
        
        self.tonghop_rate_button = ttk.Button(v25_frame, text="Tổng Hợp Top 3 (15 Cầu)", command=lambda: self.run_tonghop('rate'))
        self.tonghop_rate_button.grid(row=3, column=3, sticky="ew", padx=5, pady=5) # Chuyển xuống row 3

        self.auto_prune_bridges_button = ttk.Button(v25_frame, text="Tự động Lọc/Tắt Cầu Yếu", command=self.run_auto_prune_bridges)
        self.auto_prune_bridges_button.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        # (MỚI) Hàng 4 (Cầu Bạc Nhớ)
        self.backtest_memory_button = ttk.Button(v25_frame, text="Backtest 756 Cầu Bạc Nhớ (N1)", command=self.run_backtest_memory)
        self.backtest_memory_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5) # (MỚI)

        # Hàng 3 (Cột 0-2) -> Di chuyển xuống Hàng 5
        custom_frame = ttk.Frame(v25_frame, padding="5")
        custom_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5) # (SỬA) row=4, colspan=4
        
        ttk.Label(custom_frame, text="Tên Cầu Tùy Chỉnh (V17):").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.custom_bridge_entry = ttk.Entry(custom_frame, width=40)
        self.custom_bridge_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        self.test_custom_n1_button = ttk.Button(custom_frame, text="Test Cầu N1", command=lambda: self.run_custom_backtest('N1'))
        self.test_custom_n1_button.grid(row=0, column=2, sticky=tk.W, padx=5)
        
        self.test_custom_k2n_button = ttk.Button(custom_frame, text="Test Cầu K2N", command=lambda: self.run_custom_backtest('K2N'))
        self.test_custom_k2n_button.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        custom_frame.columnconfigure(1, weight=1)
        
        self.v25_buttons = [
            self.auto_find_bridges_button, 
            self.auto_prune_bridges_button, 
            self.backtest_n1_15_button,
            self.backtest_k2n_15_button,
            self.test_custom_n1_button, 
            self.test_custom_k2n_button,
            self.tonghop_rate_button,
            self.lookup_button,
            self.manage_bridges_button,
            self.backtest_managed_button,
            self.backtest_managed_k2n_button, 
            self.dashboard_button,
            self.backtest_memory_button # (MỚI) Thêm nút
        ]
        self.all_buttons.extend(self.v25_buttons)
        
        v25_frame.columnconfigure(0, weight=1)
        v25_frame.columnconfigure(1, weight=1)
        v25_frame.columnconfigure(2, weight=1)
        v25_frame.columnconfigure(3, weight=1)

        # --- KHUNG CẬP NHẬT DỮ LIỆU (row=2) ---
        update_frame = ttk.Labelframe(self.tab1_frame, text="Cập Nhật Dữ Liệu Mới (Dán Text)", padding="10")
        update_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        update_frame.columnconfigure(0, weight=1)
        update_frame.rowconfigure(1, weight=1)
        
        ttk.Label(update_frame, text="Dán dữ liệu text (1 hoặc nhiều kỳ) vào đây:").grid(row=0, column=0, sticky=tk.W)
        
        self.update_text_area = tk.Text(update_frame, height=8, width=80)
        self.update_text_area.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        self.update_button = ttk.Button(update_frame, text="Thêm 1/Nhiều Kỳ Từ Text (Append)", command=self.run_update_from_text)
        self.update_button.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.all_buttons.append(self.update_button)


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
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng."""
        input_file = self.check_file_path()
        if not input_file: return
        self.update_output(f"\n--- Bắt đầu Bước 1 (Xóa Hết): Phân tích tệp tin ---")
        self._run_task_in_thread(self._task_run_parsing, input_file)

    def _task_run_parsing(self, input_file):
        """(MỚI) Bước 2: Logic Nạp File (Xóa Hết) chạy trong luồng riêng."""
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
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng."""
        input_file = self.check_file_path()
        if not input_file: return
        self.update_output(f"\n--- Bắt đầu Bước 1 (Append): Thêm dữ liệu từ tệp tin ---")
        self._run_task_in_thread(self._task_run_parsing_append, input_file)

    def _task_run_parsing_append(self, input_file):
        """(MỚI) Bước 2: Logic Nạp File (Append) chạy trong luồng riêng."""
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
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng."""
        raw_data = self.update_text_area.get("1.0", tk.END)
        if not raw_data.strip():
            self.update_output("LỖI: Không có dữ liệu text để cập nhật.")
            return
        self.update_output(f"\n--- Bắt đầu: Thêm Kỳ Mới Từ Text ---")
        self._run_task_in_thread(self._task_run_update_from_text, raw_data)

    def _task_run_update_from_text(self, raw_data):
        """(MỚI) Bước 2: Logic Thêm Text chạy trong luồng riêng."""
        conn = None 
        try:
            conn, cursor = setup_database()
            total_keys_added = parse_and_APPEND_data_TEXT(raw_data, conn, cursor) 
            
            self.update_output(f"Hoàn tất: Đã thêm thành công {total_keys_added} kỳ mới.")
            if total_keys_added > 0:
                # Phải cập nhật UI từ luồng chính
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
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng."""
        title = f"Backtest 15 Cầu {mode}"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self._run_task_in_thread(self._task_run_backtest, mode, title)

    def _task_run_backtest(self, mode, title):
        """(MỚI) Bước 2: Logic Backtest 15 Cầu chạy trong luồng riêng."""
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return # Lỗi đã được in bởi load_data_ai_from_db
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)
        self.update_output(f"Đang chạy backtest trên {len(toan_bo_A_I)} hàng dữ liệu...")

        # (SỬA LỖI GĐ 1) Truyền 'history=True' cho K2N
        func_to_call = BACKTEST_15_CAU_N1_V31_AI_V8 if mode == 'N1' else (lambda a, b, c: BACKTEST_15_CAU_K2N_V30_AI_V8(a, b, c, history=True))
        results_data = func_to_call(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.update_output(f"Backtest hoàn tất. Đang mở cửa sổ kết quả...")
        # (MỚI) Phải gọi hiển thị UI từ luồng chính
        self.root.after(0, self.show_backtest_results, title, results_data)
    
    def run_custom_backtest(self, mode):
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng."""
        custom_bridge_name = self.custom_bridge_entry.get()
        if not custom_bridge_name or "+" not in custom_bridge_name:
            self.update_output("LỖI: Vui lòng nhập tên cầu hợp lệ (ví dụ: GDB[1] + Bong(G3.1[4])).")
            return
        title = f"Test Cầu {mode}: {custom_bridge_name}"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self._run_task_in_thread(self._task_run_custom_backtest, mode, title, custom_bridge_name)

    def _task_run_custom_backtest(self, mode, title, custom_bridge_name):
        """(MỚI) Bước 2: Logic Test Cầu Tùy Chỉnh chạy trong luồng riêng."""
        allData = self.load_data_ai_from_db()
        if not allData:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(allData) + (ky_bat_dau_kiem_tra - 1)
        
        self.update_output(f"Đã dịch: {custom_bridge_name}. Đang test...")

        results = BACKTEST_CUSTOM_CAU_V16(
            allData, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra,
            custom_bridge_name, mode
        )
        self.root.after(0, self.show_backtest_results, title, results)
            
    def run_tonghop(self, mode):
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng."""
        title = f"Tổng Hợp Top 3 (15 Cầu Cổ Điển)"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Bước 1/2: Đang chạy Backtest 15 Cầu N1 (nền)...")
        self._run_task_in_thread(self._task_run_tonghop, mode, title)

    def _task_run_tonghop(self, mode, title):
        """(MỚI) Bước 2: Logic Tổng Hợp chạy trong luồng riêng."""
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return
            
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)
        
        fullBacktestN1Range = BACKTEST_15_CAU_N1_V31_AI_V8(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.update_output("Bước 2/2: Backtest N1 hoàn tất. Đang tổng hợp Top 3...")
        
        lastDataRowForPrediction = toan_bo_A_I[-1]
        
        func_to_call = TONGHOP_TOP_CAU_RATE_V5 if mode == 'rate' else TONGHOP_TOP_CAU_N1_V5
        
        results = func_to_call(fullBacktestN1Range, lastDataRowForPrediction, topN=3)

        if results and results[0]:
            self.update_output(">>> TỔNG HỢP TOP 3 (15 CẦU) HOÀN TẤT:")
            self.update_output(str(results[0])) 
        else:
            self.update_output("Lỗi: Hàm tổng hợp không trả về kết quả.")

    def run_backtest_managed_n1(self):
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng."""
        title = "Backtest Cầu Đã Lưu (N1)"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang tải danh sách cầu và chạy backtest...")
        self._run_task_in_thread(self._task_run_backtest_managed_n1, title)

    def _task_run_backtest_managed_n1(self, title):
        """(MỚI) Bước 2: Logic Backtest N1 Cầu Đã Lưu chạy trong luồng riêng."""
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)

        results_data = BACKTEST_MANAGED_BRIDGES_N1(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.update_output(f"Backtest Cầu Đã Lưu N1 hoàn tất. Đang mở cửa sổ kết quả...")
        self.root.after(0, self.show_backtest_results, title, results_data)

    def run_backtest_managed_k2n(self):
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng."""
        title = "Backtest Cầu Đã Lưu (K2N)"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang tải danh sách cầu và chạy backtest K2N (với Chuỗi)...")
        self._run_task_in_thread(self._task_run_backtest_managed_k2n, title)

    def _task_run_backtest_managed_k2n(self, title):
        """(MỚI) Bước 2: Logic Backtest K2N Cầu Đã Lưu chạy trong luồng riêng."""
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)

        # (SỬA LỖI GĐ 1) Truyền 'history=True' cho K2N
        results_data = BACKTEST_MANAGED_BRIDGES_K2N(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra, history=True)
        
        self.update_output(f"Backtest Cầu Đã Lưu K2N hoàn tất. Đang mở cửa sổ kết quả...")
        self.root.after(0, self.show_backtest_results, title, results_data)
            
    def run_decision_dashboard(self):
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng."""
        title = "Bảng Tổng Hợp Quyết Định"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang chạy 7 hệ thống phân tích... (Bao gồm 3 backtest ngầm)") # (SỬA) 7 hệ thống
        self._run_task_in_thread(self._task_run_decision_dashboard, title)

    def _task_run_decision_dashboard(self, title):
        """(SỬA LỖI GĐ 1) Logic Bảng Tổng Hợp chạy trong luồng riêng."""
        all_data_ai = self.load_data_ai_from_db()
        
        if not all_data_ai or len(all_data_ai) < 2:
            self.update_output("LỖI: Cần ít nhất 2 kỳ dữ liệu để chạy Bảng Tổng Hợp.")
            return
        
        last_row = all_data_ai[-1]
        n_days_stats = 7
        n_days_gan = 15 
        next_ky = f"Kỳ {int(last_row[0]) + 1}" if last_row[0].isdigit() else f"Kỳ {last_row[0]} (Next)"

        # --- 1. Thống kê N ngày ---
        self.update_output("... (1/7) Đang thống kê Loto Về Nhiều...")
        stats_n_day = get_loto_stats_last_n_days(all_data_ai, n=n_days_stats)
        
        # --- 2. (SỬA LỖI GĐ 1) Chạy hàm K2N Cache TRƯỚC ---
        self.update_output("... (2/7) Đang chạy hàm Cập nhật K2N Cache (tối ưu)...")
        # Hàm này chạy backtest K2N (tối ưu) cho Cả 15 Cầu VÀ Cầu Đã Lưu,
        # sau đó cập nhật CSDL và trả về dict các cầu đang chờ N2.
        pending_k2n_data, cache_message = run_and_update_all_bridge_K2N_cache(all_data_ai, self.db_name)
        self.update_output(f"... (Cache K2N) {cache_message}")
        
        # --- 3. (SỬA LỖI GĐ 1) Thống kê "Vote" (ĐỌC TỪ CACHE) ---
        self.update_output("... (3/7) Đang thống kê Cặp Số Dự Đoán (đọc cache)...")
        consensus = get_prediction_consensus(last_row)
        
        # --- 4. (SỬA LỖI GĐ 1) Thống kê "Cầu Tỷ Lệ Cao" (ĐỌC TỪ CACHE) ---
        self.update_output("... (4/7) Đang lọc Cầu V17 Tỷ Lệ Cao (>=47%, đọc cache)...")
        high_win = get_high_win_rate_predictions(last_row, threshold=47.0)

        # --- 5. Chạy Backtest Bạc Nhớ ngầm ---
        self.update_output("... (5/7) Đang chạy Backtest 756 Cầu Bạc Nhớ ngầm...")
        top_memory_bridges = get_top_memory_bridge_predictions(all_data_ai, last_row, top_n=5)
        
        # --- 6. Thống kê Lô Gan ---
        self.update_output(f"... (6/7) Đang tìm Lô Gan (trên {n_days_gan} kỳ)...")
        gan_stats = get_loto_gan_stats(all_data_ai, n_days=n_days_gan)
        
        # --- 7. HỆ THỐNG CHẤM ĐIỂM ---
        self.update_output("... (7/7) Đang chấm điểm và tổng hợp quyết định...")
        top_scores = get_top_scored_pairs(
            stats_n_day,
            consensus, 
            high_win, 
            pending_k2n_data, # (SỬA GĐ 1) Biến này giờ đã là dict
            gan_stats,
            top_memory_bridges 
        )
        
        self.update_output("Phân tích hoàn tất. Đang hiển thị Bảng Tổng Hợp...")
        
        self.root.after(0, self._show_dashboard_window, 
            next_ky, stats_n_day, n_days_stats, 
            consensus, high_win, pending_k2n_data, 
            gan_stats, top_scores, top_memory_bridges
        )

    def _show_dashboard_window(self, next_ky, stats_n_day, n_days_stats, consensus, high_win, pending_k2n_data, gan_stats, top_scores, top_memory_bridges):
        """(SỬA) Chuyển sang gọi Class DashboardWindow và thêm top_memory_bridges"""
        try:
            if self.dashboard_window and self.dashboard_window.window.winfo_exists():
                self.dashboard_window.window.lift()
                self.dashboard_window.clear_data()
            else:
                self.dashboard_window = DashboardWindow(self) 
            
            self.dashboard_window.populate_data(
                next_ky, stats_n_day, n_days_stats, 
                consensus, high_win, pending_k2n_data, 
                gan_stats, top_scores, top_memory_bridges
            )
        except Exception as e:
            self.update_output(f"LỖI khi hiển thị Bảng Tổng Hợp: {e}")
            self.update_output(traceback.format_exc())

    # ===================================================================================
    # (SỬA GĐ 1) HÀM CẬP NHẬT TỶ LỆ CẦU (ĐÃ BỊ THAY THẾ)
    # ===================================================================================
    
    # (MỚI GĐ 1 / BƯỚC 6c) HÀM CẬP NHẬT K2N CACHE
    def run_update_all_bridge_K2N_cache(self):
        """(MỚI GĐ 1) Bước 1: Gọi hàm chạy đa luồng từ Cửa sổ Quản lý Cầu."""
        title = "Cập nhật Cache K2N Hàng Loạt"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang chạy Backtest K2N (tối ưu) cho 15 Cầu CĐ + Cầu Đã Lưu...")
        self._run_task_in_thread(self._task_run_update_all_bridge_K2N_cache, title)

    def _task_run_update_all_bridge_K2N_cache(self, title):
        """(MỚI GĐ 1) Bước 2: Logic Cập nhật K2N Cache chạy trong luồng riêng."""
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
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng cho Tự động Dò Cầu."""
        title = "Tự động Dò & Thêm Cầu V17"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("CẢNH BÁO: Tác vụ này RẤT NẶNG (23.005 cầu). Vui lòng chờ...")
        self.update_output(f"Các cầu có Tỷ lệ > {AUTO_ADD_MIN_RATE}% sẽ được tự động thêm/cập nhật...")
        self._run_task_in_thread(self._task_run_auto_find_bridges, title)

    def _task_run_auto_find_bridges(self, title):
        """(MỚI) Bước 2: Logic Tự động Dò Cầu chạy trong luồng riêng."""
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
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng cho Tự động Lọc Cầu."""
        title = "Tự động Lọc/Tắt Cầu Yếu"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang chạy backtest N1 cho các Cầu Đã Lưu...")
        self.update_output(f"Các cầu có Tỷ lệ < {AUTO_PRUNE_MIN_RATE}% sẽ bị TẮT (vô hiệu hóa)...")
        self._run_task_in_thread(self._task_run_auto_prune_bridges, title)

    def _task_run_auto_prune_bridges(self, title):
        """(MỚI) Bước 2: Logic Tự động Lọc Cầu chạy trong luồng riêng."""
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
    # (MỚI) HÀM CALLBACK CẦU BẠC NHỚ
    # ===================================================================================
    
    def run_backtest_memory(self):
        """(MỚI) Bước 1: Gọi hàm chạy đa luồng cho Cầu Bạc Nhớ."""
        title = "Backtest 756 Cầu Bạc Nhớ (N1)"
        self.update_output(f"\n--- Bắt đầu: {title} ---")
        self.update_output("Đang chạy backtest 756 thuật toán (Tổng/Hiệu của 27 vị trí lô)...")
        self._run_task_in_thread(self._task_run_backtest_memory, title)

    def _task_run_backtest_memory(self, title):
        """(MỚI) Bước 2: Logic Cầu Bạc Nhớ chạy trong luồng riêng."""
        toan_bo_A_I = self.load_data_ai_from_db()
        if not toan_bo_A_I:
            return
        
        ky_bat_dau_kiem_tra = 2
        ky_ket_thuc_kiem_tra = len(toan_bo_A_I) + (ky_bat_dau_kiem_tra - 1)
        
        results_data = BACKTEST_MEMORY_BRIDGES(toan_bo_A_I, ky_bat_dau_kiem_tra, ky_ket_thuc_kiem_tra)
        
        self.update_output(f"Backtest Cầu Bạc Nhớ hoàn tất. Đang mở cửa sổ kết quả...")
        self.root.after(0, self.show_backtest_results, title, results_data)

    # ===================================================================================
    # CÁC HÀM GỌI CỬA SỔ CON (Đã Tách)
    # ===================================================================================

    def show_lookup_window(self):
        """Mở cửa sổ Tra cứu từ ui/ui_lookup.py"""
        self.lookup_window = LookupWindow(self)

    def show_bridge_manager_window(self):
        """Mở cửa sổ Quản lý Cầu từ ui/ui_bridge_manager.py"""
        self.bridge_manager_window_instance = BridgeManagerWindow(self)

    def show_backtest_results(self, title, results_data, show_save_button=False):
        """Mở cửa sổ Hiển thị Kết quả từ ui/ui_results_viewer.py"""
        # (SỬA) Bật nút lưu cho V17 (23k cầu)
        if "V17" in title:
            show_save_button = True
        
        self.results_window = ResultsViewerWindow(self, title, results_data, show_save_button)

    # ===================================================================================
    # HÀM TRIGGER TỪ BẢNG TỔNG HỢP
    # ===================================================================================
    
    def trigger_bridge_backtest(self, bridge_name):
        """
        (MỚI) Được gọi khi người dùng double-click vào một cầu
        từ Bảng Tổng Hợp Tương Tác.
        """
        if not bridge_name:
            return
            
        if bridge_name.startswith("Cầu "):
            # Đây là 1 trong 15 Cầu Cổ Điển (ví dụ: "Cầu 5")
            self.update_output(f"--- Trigger: Mở Backtest K2N cho 15 Cầu Cổ Điển (focus vào {bridge_name})...")
            self.run_backtest('K2N')
            
        elif "+" in bridge_name or "Bong(" in bridge_name:
            # Đây là Cầu V17 (ví dụ: "GDB[0] + G1[4]" hoặc "Bong(G1[0]) + G7.2[1]")
            self.update_output(f"--- Trigger: Chạy Backtest K2N tùy chỉnh cho {bridge_name}...")
            self.custom_bridge_entry.delete(0, "end")
            self.custom_bridge_entry.insert(0, bridge_name)
            self.run_custom_backtest('K2N')
            self.notebook.select(self.tab1_frame)

        elif "Tổng(" in bridge_name or "Hiệu(" in bridge_name:
             # (MỚI) Đây là Cầu Bạc Nhớ
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
            
            # (SỬA) Chỉ cho phép lưu cầu V17 (chứa + hoặc Bong)
            if not ("+" in bridge_name or "Bong(" in bridge_name):
                messagebox.showerror("Lỗi Lưu Cầu", "Chức năng này chỉ hỗ trợ lưu Cầu V17 (ví dụ: GDB[0] + Bong(G1[4])).\nKhông thể lưu Cầu 15 Cổ Điển hoặc Cầu Bạc Nhớ.", parent=tree.master)
                return

            description = simpledialog.askstring("Lưu Cầu Mới", 
                                                 f"Nhập mô tả cho cầu:\n{bridge_name}",
                                                 initialvalue=bridge_name, 
                                                 parent=tree.master)
            
            if description is None: return

            # (SỬA) Dùng hàm UPSERT thay vì ADD
            # Hàm upsert đã có trong db_manager và service
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