import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# (ĐÃ XÓA) Bỏ import logic.config_manager, logic.backtester, v.v.
# VIEW không được chứa logic nghiệp vụ

class OptimizerTab(ttk.Frame):
    """
    Giao diện Tab Tối ưu Hóa Chiến lược (VIEW). 
    Lớp này chỉ chứa giao diện và ủy quyền lệnh cho Controller.
    """
    
    def __init__(self, notebook, app_instance):
        super().__init__(notebook, padding="10")
        self.app = app_instance
        self.controller = app_instance.controller # Lấy tham chiếu Controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Dành không gian cho Treeview
        
        # --- Khởi tạo các biến kiểm soát ---
        self.strategy_var = tk.StringVar(value="Tối ưu Top 1 (N1)")
        self.days_var = tk.StringVar(value="30")
        
        # Danh sách các tham số có thể tối ưu
        self.tunable_params = {
            "AI_SCORE_WEIGHT": {"desc": "Trọng số AI", "min": 0.5, "max": 5.0, "step": 0.5, "type": float},
            "K2N_RISK_START_THRESHOLD": {"desc": "Ngưỡng rủi ro K2N", "min": 3, "max": 7, "step": 1, "type": int},
            "K2N_RISK_PENALTY_PER_FRAME": {"desc": "Điểm phạt K2N", "min": 0.1, "max": 1.0, "step": 0.1, "type": float},
            "HIGH_WIN_THRESHOLD": {"desc": "Ngưỡng Cầu Tỷ lệ Cao (%)", "min": 45.0, "max": 60.0, "step": 2.5, "type": float},
        }
        
        self.param_vars = {} # Chứa các StringVar/IntVar cho từng tham số
        self._setup_ui()
        
    def _setup_ui(self):
        
        # --- Khung Điều Khiển ---
        control_frame = ttk.Labelframe(self, text="Điều Khiển Tối ưu", padding="10")
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Hàng 0: Chiến lược
        ttk.Label(control_frame, text="Chiến lược:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        strategies = ["Tối ưu Top 1 (N1)", "Tối ưu Top 3 (N1)"]
        strategy_menu = ttk.Combobox(control_frame, textvariable=self.strategy_var, values=strategies, state="readonly", width=30)
        strategy_menu.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        # Hàng 1: Số ngày
        ttk.Label(control_frame, text="Số ngày Backtest:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        days_entry = ttk.Entry(control_frame, textvariable=self.days_var, width=10)
        days_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # Hàng 2: Nút chạy/Log
        self.run_button = ttk.Button(control_frame, text="🚀 Bắt Đầu Tối Ưu", command=self.run_optimization)
        self.run_button.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        
        
        # --- Khung Tham Số Tối Ưu ---
        param_frame = ttk.Labelframe(self, text="Phạm Vi Tham Số Kiểm Thử", padding="10")
        param_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        for i, (key, data) in enumerate(self.tunable_params.items()):
            row = i
            
            # Cột 0: Tên tham số
            ttk.Label(param_frame, text=f"{data['desc']} ({key}):").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            
            # Cột 1: Checkbox (Bật/Tắt tối ưu)
            var_type = tk.IntVar if data['type'] == int else tk.DoubleVar
            self.param_vars[key] = {
                'enabled': tk.IntVar(value=0),
                'from': var_type(value=data['min']),
                'to': var_type(value=data['max']),
                'step': var_type(value=data['step'])
            }
            check = ttk.Checkbutton(param_frame, variable=self.param_vars[key]['enabled'])
            check.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            
            # Cột 2-4: From, To, Step
            ttk.Label(param_frame, text="Từ:").grid(row=row, column=2, sticky="e", padx=2, pady=2)
            ttk.Entry(param_frame, textvariable=self.param_vars[key]['from'], width=10).grid(row=row, column=3, sticky="w", padx=2, pady=2)
            
            ttk.Label(param_frame, text="Đến:").grid(row=row, column=4, sticky="e", padx=2, pady=2)
            ttk.Entry(param_frame, textvariable=self.param_vars[key]['to'], width=10).grid(row=row, column=5, sticky="w", padx=2, pady=2)
            
            ttk.Label(param_frame, text="Bước:").grid(row=row, column=6, sticky="e", padx=2, pady=2)
            ttk.Entry(param_frame, textvariable=self.param_vars[key]['step'], width=10).grid(row=row, column=7, sticky="w", padx=2, pady=2)
            
        # --- Khung Kết Quả và Log ---
        results_frame = ttk.Labelframe(self, text="Kết Quả Tối Ưu", padding="10")
        results_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # 1. Treeview Kết quả
        tree_frame = ttk.Frame(results_frame)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        cols = ('rate', 'hits', 'params')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=8)
        self.tree.heading('rate', text='Tỷ lệ Win')
        self.tree.column('rate', width=100, anchor='center')
        self.tree.heading('hits', text='Hits')
        self.tree.column('hits', width=80, anchor='center')
        self.tree.heading('params', text='Tham số Tối ưu')
        self.tree.column('params', width=300, anchor='w')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.config(yscrollcommand=tree_scroll_y.set)
        
        self.tree.tag_configure('best', background='#D6F5D6', foreground='green')
        self.tree.bind("<<TreeviewSelect>>", self.on_result_select)

        # 2. Log Text Area
        self.log_text = tk.Text(results_frame, height=5, state=tk.DISABLED, font=('Courier New', 9))
        self.log_text.grid(row=1, column=0, sticky="ew", padx=0, pady=5)
        
        # 3. Nút Áp dụng & Entry cấu hình
        apply_frame = ttk.Frame(results_frame)
        apply_frame.grid(row=2, column=0, sticky="ew")
        apply_frame.columnconfigure(1, weight=1)
        
        self.apply_button = ttk.Button(apply_frame, text="✅ ÁP DỤNG Cấu Hình", 
                                        command=self.apply_optimized_settings, 
                                        state=tk.DISABLED)
        self.apply_button.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.config_entry = ttk.Entry(apply_frame, state=tk.DISABLED)
        self.config_entry.grid(row=0, column=1, sticky="ew")

    def log(self, message):
        """[VIEW CALLBACK] Ghi log vào Text Area (an toàn trên luồng chính)."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def clear_results_tree(self):
        """[VIEW CALLBACK] Xóa nội dung Treeview."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state=tk.DISABLED)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.config_entry.config(state=tk.NORMAL)
        self.config_entry.delete(0, tk.END)
        self.config_entry.config(state=tk.DISABLED)
        self.apply_button.config(state=tk.DISABLED)

    # --- CÁC HÀM XỬ LÝ SỰ KIỆN (CHỈ ỦY QUYỀN) ---
    
    def on_result_select(self, event):
        """[VIEW ACTION] Chọn kết quả trong Treeview để hiển thị cấu hình JSON."""
        selected_item = self.tree.focus()
        if not selected_item: 
            self.config_entry.config(state=tk.DISABLED)
            return

        tags = self.tree.item(selected_item, 'tags')
        if tags and len(tags) > 0:
            config_json_str = tags[0] # Giá trị config JSON luôn là tag đầu tiên
            
            self.config_entry.config(state=tk.NORMAL)
            self.config_entry.delete(0, tk.END)
            self.config_entry.insert(0, config_json_str)
            self.config_entry.config(state=tk.DISABLED)

    def run_optimization(self):
        """[VIEW ACTION] Bắt đầu quá trình tối ưu hóa. Chỉ kiểm tra input cơ bản và ủy quyền."""
        try:
            days_to_test = int(self.days_var.get())
            if days_to_test <= 0:
                 messagebox.showwarning("Lỗi Input", "Số ngày Backtest phải lớn hơn 0.", parent=self)
                 return
        except ValueError:
            messagebox.showwarning("Lỗi Input", "Số ngày Backtest không hợp lệ.", parent=self)
            return

        param_ranges = {}
        enabled_count = 0
        
        # 1. Thu thập các tham số đã Bật
        for key, vars in self.param_vars.items():
            if vars['enabled'].get() == 1:
                enabled_count += 1
                try:
                    val_from = vars['from'].get()
                    val_to = vars['to'].get()
                    val_step = vars['step'].get()
                    
                    if val_step == 0:
                        messagebox.showwarning("Lỗi Tham số", f"Bước nhảy của {self.tunable_params[key]['desc']} không được bằng 0.", parent=self)
                        return
                    if val_from > val_to:
                        messagebox.showwarning("Lỗi Tham số", f"Giá trị 'Từ' phải nhỏ hơn hoặc bằng 'Đến' cho {self.tunable_params[key]['desc']}.", parent=self)
                        return
                        
                    param_ranges[key] = (val_from, val_to, val_step)
                    
                except ValueError:
                    messagebox.showwarning("Lỗi Input", f"Các giá trị Từ/Đến/Bước cho {self.tunable_params[key]['desc']} phải là số.", parent=self)
                    return
        
        if enabled_count == 0:
            messagebox.showwarning("Thiếu Input", "Vui lòng chọn ít nhất một tham số để tối ưu.", parent=self)
            return
            
        # 2. Ủy quyền cho Controller
        self.run_button.config(state=tk.DISABLED)
        self.clear_results_tree()
        self.log(f"--- Bắt đầu Tối ưu Chiến lược: {self.strategy_var.get()} trên {days_to_test} ngày ---")
        
        self.app.task_manager.run_task(
            self.controller.task_run_strategy_optimization, 
            self.strategy_var.get(), 
            days_to_test, 
            param_ranges, 
            self # Truyền đối tượng View hiện tại (self) làm callback
        )
        
    def apply_optimized_settings(self):
        """[VIEW ACTION] Áp dụng cấu hình đã chọn. Chỉ lấy giá trị và ủy quyền."""
        config_dict_str = self.config_entry.get().strip()
        if not config_dict_str:
            messagebox.showwarning("Lỗi", "Vui lòng chọn một kết quả tối ưu để áp dụng.", parent=self)
            return
            
        # Ủy quyền cho View chính/Controller để xử lý xác nhận và lưu logic
        self.app.apply_optimized_settings(config_dict_str, self)