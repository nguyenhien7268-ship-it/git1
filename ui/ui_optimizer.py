import tkinter as tk
from tkinter import ttk, messagebox
import traceback

# (MỚI GĐ 10) Import SETTINGS để lấy giá trị mặc định
try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: ui_optimizer.py không thể import logic.config_manager.")
    SETTINGS = None

class OptimizerTab(ttk.Frame):
    """
    (MỚI GĐ 10) Giao diện Tab "Tối ưu Hóa Chiến lược".
    Kế thừa từ ttk.Frame và sẽ được nhúng vào Notebook chính.
    """
    
    def __init__(self, parent_notebook, app_instance):
        super().__init__(parent_notebook, padding="10")
        self.app = app_instance
        self.root = app_instance.root
        
        # Biến lưu trữ các widget
        self.param_vars = {} # { "GAN_DAYS": (check_var, from_var, to_var, step_var) }
        
        # --- Cấu trúc GUI ---
        self.columnconfigure(0, weight=1) # Cột cài đặt
        self.columnconfigure(1, weight=2) # Cột kết quả
        self.rowconfigure(0, weight=1)    # Cả 2 cột co giãn

        # --- CỘT 1: KHUNG CÀI ĐẶT ---
        settings_frame = ttk.Frame(self)
        settings_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        settings_frame.columnconfigure(0, weight=1)
        
        # Khung Chiến lược & Ngày
        strategy_frame = ttk.Labelframe(settings_frame, text="1. Cài đặt Chiến lược", padding="10")
        strategy_frame.grid(row=0, column=0, sticky="ew")
        strategy_frame.columnconfigure(1, weight=1)
        
        ttk.Label(strategy_frame, text="Chiến lược Tối ưu:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.strategy_var = tk.StringVar(value="Tối ưu Top 1 (N1)")
        strategy_dropdown = ttk.Combobox(strategy_frame, 
                                         textvariable=self.strategy_var, 
                                         values=["Tối ưu Top 1 (N1)", "Tối ưu Top 3 (N1)"],
                                         state="readonly")
        strategy_dropdown.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(strategy_frame, text="Số ngày kiểm thử:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.days_to_test_var = tk.StringVar(value="30")
        days_entry = ttk.Entry(strategy_frame, textvariable=self.days_to_test_var, width=10)
        days_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Khung Tham số
        params_frame = ttk.Labelframe(settings_frame, text="2. Chọn Tham số để Tối ưu Hóa", padding="10")
        params_frame.grid(row=1, column=0, sticky="ew", pady=10)
        params_frame.columnconfigure(1, weight=1)
        
        # Header
        header_frame = ttk.Frame(params_frame)
        header_frame.grid(row=0, column=0, columnspan=5, sticky="ew")
        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(2, weight=1)
        header_frame.columnconfigure(3, weight=1)
        header_frame.columnconfigure(4, weight=1)
        ttk.Label(header_frame, text="Tham số", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=1)
        ttk.Label(header_frame, text="Từ", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=2)
        ttk.Label(header_frame, text="Đến", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=3)
        ttk.Label(header_frame, text="Bước nhảy", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=4)
        
        # Lấy cài đặt mặc định
        current_settings = SETTINGS.get_all_settings() if SETTINGS else {}

        # Danh sách tham số (ĐÃ CẬP NHẬT THÊM THAM SỐ AI)
        self.param_definitions = [
            ("GAN_DAYS", "Số ngày Lô Gan", current_settings.get("GAN_DAYS", 15), 1),
            ("HIGH_WIN_THRESHOLD", "Ngưỡng Cầu Tỷ Lệ Cao (%)", current_settings.get("HIGH_WIN_THRESHOLD", 47.0), 1.0),
            ("K2N_RISK_START_THRESHOLD", "Ngưỡng phạt K2N (khung)", current_settings.get("K2N_RISK_START_THRESHOLD", 4), 1),
            ("K2N_RISK_PENALTY_PER_FRAME", "Điểm phạt K2N / khung", current_settings.get("K2N_RISK_PENALTY_PER_FRAME", 0.5), 0.1),
            # --- START NEW AI PARAMETERS ---
            ("AI_MAX_DEPTH", "AI: Độ Sâu Cây Max", current_settings.get("AI_MAX_DEPTH", 6), 1),
            ("AI_N_ESTIMATORS", "AI: Số lượng Cây (Est.)", current_settings.get("AI_N_ESTIMATORS", 200), 50),
            ("AI_LEARNING_RATE", "AI: Tốc độ học (LR)", current_settings.get("AI_LEARNING_RATE", 0.05), 0.01),
            ("AI_SCORE_WEIGHT", "AI: Trọng số Điểm", current_settings.get("AI_SCORE_WEIGHT", 0.2), 0.1)
            # --- END NEW AI PARAMETERS ---
        ]
        
        current_row = 1
        for key, name, default_val, default_step in self.param_definitions:
            check_var = tk.BooleanVar(value=False)
            from_var = tk.StringVar(value=str(default_val))
            to_var = tk.StringVar(value=str(default_val))
            step_var = tk.StringVar(value=str(default_step))
            
            check = ttk.Checkbutton(params_frame, variable=check_var)
            check.grid(row=current_row, column=0, sticky="w", padx=5)
            
            ttk.Label(params_frame, text=name).grid(row=current_row, column=1, sticky="w", padx=5)
            
            from_entry = ttk.Entry(params_frame, textvariable=from_var, width=8)
            from_entry.grid(row=current_row, column=2, sticky="ew", padx=5, pady=2)
            
            to_entry = ttk.Entry(params_frame, textvariable=to_var, width=8)
            to_entry.grid(row=current_row, column=3, sticky="ew", padx=5, pady=2)
            
            step_entry = ttk.Entry(params_frame, textvariable=step_var, width=8)
            step_entry.grid(row=current_row, column=4, sticky="ew", padx=5, pady=2)
            
            self.param_vars[key] = (check_var, from_var, to_var, step_var)
            current_row += 1
            
        # Nút Chạy
        self.run_button = ttk.Button(settings_frame, text="Bắt đầu Tối ưu Hóa Chiến lược", command=self.run_optimization)
        self.run_button.grid(row=2, column=0, sticky="ew", pady=(15, 5))
        
        # Nút Áp dụng Cấu hình Tốt nhất
        self.apply_button = ttk.Button(settings_frame, text="Áp dụng Cấu hình Tốt nhất", 
                                       command=self.apply_best_settings, state=tk.DISABLED)
        self.apply_button.grid(row=3, column=0, sticky="ew", pady=(5, 5))


        # --- CỘT 2: KHUNG KẾT QUẢ ---
        results_frame = ttk.Frame(self)
        results_frame.grid(row=0, column=1, sticky="nsew")
        results_frame.rowconfigure(0, weight=1) # Bảng kết quả
        results_frame.rowconfigure(1, weight=1) # Log chi tiết
        results_frame.columnconfigure(0, weight=1)
        
        # Bảng Kết quả Xếp hạng
        tree_frame = ttk.Labelframe(results_frame, text="3. Kết quả Tối ưu (Xếp hạng theo Tỷ lệ thắng)", padding="10")
        tree_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        
        self.tree = self._create_treeview(tree_frame)
        self.tree.tag_configure('best', background='#FFFFE0', font=('TkDefaultFont', 9, 'bold'))
        self.tree.bind("<Double-1>", self.on_result_double_click)

        # Log Chi tiết
        log_frame = ttk.Labelframe(results_frame, text="Log Chi tiết", padding="10")
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=10, width=80, 
                                font=('Courier New', 9), 
                                yscrollcommand=log_scrollbar.set)
        self.log_text.pack(expand=True, fill=tk.BOTH)
        log_scrollbar.config(command=self.log_text.yview)
        self.log_text.config(state=tk.DISABLED)

    def _create_treeview(self, parent):
        """Tạo Treeview cho bảng kết quả."""
        tree_scroll_y = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        cols = ('rate', 'hits', 'params')
        tree = ttk.Treeview(parent, columns=cols, show="headings", yscrollcommand=tree_scroll_y.set)
        tree_scroll_y.config(command=tree.yview)
        
        tree.heading('rate', text='Tỷ lệ Thắng')
        tree.column('rate', width=80, anchor=tk.W)
        tree.heading('hits', text='Trúng/Trượt')
        tree.column('hits', width=80, anchor=tk.W)
        tree.heading('params', text='Cấu hình Tham số')
        tree.column('params', width=300, anchor=tk.W)
        
        tree.pack(expand=True, fill=tk.BOTH)
        return tree

    def log(self, message):
        """Ghi log an toàn vào Text box."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks() # Cập nhật UI ngay
        
    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def clear_results_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def run_optimization(self):
        """Lấy tất cả cài đặt và gọi hàm logic trong app chính."""
        try:
            # 1. Lấy cài đặt chiến lược
            strategy = self.strategy_var.get()
            days_to_test = int(self.days_to_test_var.get())
            
            if days_to_test <= 0:
                # (SỬA LỖI) parent=self
                messagebox.showerror("Lỗi", "Số ngày kiểm thử phải lớn hơn 0.", parent=self)
                return

            # 2. Lấy các tham số cần kiểm thử
            param_ranges = {}
            for key, (check_var, from_var, to_var, step_var) in self.param_vars.items():
                if check_var.get(): # Nếu được chọn
                    val_from = float(from_var.get())
                    val_to = float(to_var.get())
                    val_step = float(step_var.get())
                    
                    if val_step <= 0 or val_from > val_to:
                        # (SỬA LỖI) parent=self
                        messagebox.showerror("Lỗi Giá trị", f"Khoảng giá trị cho '{key}' không hợp lệ.", parent=self)
                        return
                    
                    # Chuyển đổi tham số số nguyên sang int (ví dụ: MAX_DEPTH, N_ESTIMATORS)
                    if key in ["GAN_DAYS", "K2N_RISK_START_THRESHOLD", "AI_MAX_DEPTH", "AI_N_ESTIMATORS"]:
                        # Kiểm tra nếu giá trị là số nguyên
                        if val_from != int(val_from) or val_to != int(val_to) or val_step != int(val_step):
                             messagebox.showerror("Lỗi Giá trị", f"'{key}' phải là số nguyên.", parent=self)
                             return
                        val_from = int(val_from)
                        val_to = int(val_to)
                        val_step = int(val_step)
                        
                    param_ranges[key] = (val_from, val_to, val_step)
            
            if not param_ranges:
                # (SỬA LỖI) parent=self
                messagebox.showwarning("Chưa chọn", "Vui lòng chọn ít nhất một tham số để tối ưu hóa.", parent=self)
                return

            # 3. Xóa log cũ và chuẩn bị
            self.clear_log()
            self.clear_results_tree()
            self.apply_button.config(state=tk.DISABLED)
            self.log(f"--- BẮT ĐẦU TỐI ƯU HÓA CHIẾN LƯỢC ---")
            self.log(f"Chiến lược: {strategy}")
            self.log(f"Số ngày kiểm thử: {days_to_test} ngày (tính từ ngày gần nhất)")
            self.log(f"Các tham số kiểm thử:")
            for key, (f, t, s) in param_ranges.items():
                self.log(f" - {key}: Từ {f} đến {t} (bước {s})")
            self.log("CẢNH BÁO: Tác vụ này rất nặng và sẽ mất nhiều thời gian...")
            
            # 4. Tắt nút
            self.run_button.config(state=tk.DISABLED)
            
            # 5. Gọi hàm logic trong app chính (sẽ được tạo ở Bước 4)
            self.app.run_strategy_optimization(strategy, days_to_test, param_ranges, self)
            
        except ValueError:
            # (SỬA LỖI) parent=self
            messagebox.showerror("Lỗi Giá trị", "Giá trị 'Số ngày', 'Từ', 'Đến', 'Bước nhảy' phải là số.", parent=self)
        except Exception as e:
            # (SỬA LỖI) parent=self
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}", parent=self)
            self.log(traceback.format_exc())

    def on_result_double_click(self, event):
        """(MỚI GĐ 10) Khi double-click, hỏi người dùng có muốn áp dụng cấu hình này không."""
        try:
            item_id = self.tree.focus()
            if not item_id: return
            
            # Lấy dict cấu hình đã lưu
            config_dict = self.tree.item(item_id, 'tags')[0]
            if not config_dict or not isinstance(config_dict, str):
                return

            # (Hàm này sẽ được tạo ở Bước 4)
            self.app.apply_optimized_settings(config_dict_str=config_dict, optimizer_window=self)
            
        except Exception as e:
            self.log(f"Lỗi khi chọn kết quả: {e}")
            self.log(traceback.format_exc())

    def apply_best_settings(self):
        """Áp dụng cấu hình tốt nhất (dòng đầu tiên)."""
        try:
            children = self.tree.get_children()
            if not children:
                self.log("Lỗi: Không có kết quả nào để áp dụng.")
                return
                
            item_id = children[0] # Lấy dòng đầu tiên
            config_dict_str = self.tree.item(item_id, 'tags')[0]
            if not config_dict_str or not isinstance(config_dict_str, str):
                 self.log("Lỗi: Không tìm thấy dữ liệu cấu hình trong kết quả tốt nhất.")
                 return

            # (Hàm này sẽ được tạo ở Bước 4)
            self.app.apply_optimized_settings(config_dict_str=config_dict_str, optimizer_window=self)
            
        except Exception as e:
            self.log(f"Lỗi khi áp dụng kết quả tốt nhất: {e}")
            self.log(traceback.format_exc())