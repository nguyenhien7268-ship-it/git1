# Tên file: CODE5/git1/ui/ui_bridge_manager.py
#
# (PHIÊN BẢN V7.9 - FIXED KEY ERROR DATE_ADDED)
#
import tkinter as tk
from tkinter import messagebox, ttk

# Import các hàm logic cần thiết
try:
    from lottery_service import (
        add_managed_bridge,
        delete_managed_bridge,
        get_all_managed_bridges,
        update_managed_bridge,
    )
except ImportError:
    print("LỖI: ui_bridge_manager.py không thể import lottery_service.")
    # Fallback functions để tránh crash IDE
    def get_all_managed_bridges(db, only_enabled=False): return []
    def add_managed_bridge(n, d, w): return False, "Lỗi Import"
    def update_managed_bridge(i, d, s): return False, "Lỗi Import"
    def delete_managed_bridge(i): return False, "Lỗi Import"


class BridgeManagerWindow:
    """Quản lý cửa sổ Toplevel Quản lý Cầu."""

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.all_bridges_cache = []  # Cache danh sách cầu
        
        # Kiểm tra xem cửa sổ đã mở chưa
        if (
            hasattr(self.app, "bridge_manager_window")
            and self.app.bridge_manager_window
            and self.app.bridge_manager_window.winfo_exists()
        ):
            self.app.bridge_manager_window.lift()
            return

        # Khởi tạo cửa sổ mới
        self.window = tk.Toplevel(self.root)
        self.window.title("Quản Lý Cầu (Bridge Manager)")
        self.window.geometry("900x600")
        
        # Lưu tham chiếu vào App để controller gọi lại được
        self.app.bridge_manager_window = self.window
        self.app.bridge_manager_window_instance = self # Quan trọng cho controller gọi refresh

        # Layout chính
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)

        # 1. FORM NHẬP LIỆU (Trên cùng)
        self.create_input_form()

        # 2. DANH SÁCH CẦU (Giữa)
        self.create_bridge_list()

        # 3. THANH CÔNG CỤ (Dưới cùng)
        self.create_toolbar()

        # Load dữ liệu ban đầu
        self.refresh_bridge_list()

    def create_input_form(self):
        """Tạo form thêm/sửa cầu."""
        frame = ttk.LabelFrame(self.window, text="Thông tin Cầu", padding="10")
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        frame.columnconfigure(1, weight=1)

        # Hàng 1: Tên cầu & Trạng thái
        ttk.Label(frame, text="Tên Cầu (VD: Cầu 1, Bong(0,1)):").grid(row=0, column=0, sticky="w")
        self.name_entry = ttk.Entry(frame)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5)

        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Đang Bật (Sử dụng)", variable=self.enabled_var).grid(row=0, column=2, padx=5)

        # Hàng 2: Mô tả
        ttk.Label(frame, text="Mô tả:").grid(row=1, column=0, sticky="w")
        self.desc_entry = ttk.Entry(frame)
        self.desc_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

    def create_bridge_list(self):
        """Tạo bảng danh sách cầu."""
        frame = ttk.Frame(self.window)
        frame.grid(row=1, column=0, sticky="nsew", padx=10)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        columns = ("id", "name", "desc", "win_rate", "status", "created_at")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        
        # Định nghĩa cột
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=40, anchor="center")
        
        self.tree.heading("name", text="Tên Cầu")
        self.tree.column("name", width=150)
        
        self.tree.heading("desc", text="Mô Tả")
        self.tree.column("desc", width=250)
        
        self.tree.heading("win_rate", text="Tỷ lệ thắng (K2N)")
        self.tree.column("win_rate", width=100, anchor="center")
        
        self.tree.heading("status", text="Trạng Thái")
        self.tree.column("status", width=80, anchor="center")
        
        self.tree.heading("created_at", text="Ngày Tạo")
        self.tree.column("created_at", width=120, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind sự kiện chọn dòng
        self.tree.bind("<<TreeviewSelect>>", self.on_bridge_select)

    def create_toolbar(self):
        """Tạo thanh công cụ chứa các nút chức năng."""
        frame = ttk.Frame(self.window, padding="10")
        frame.grid(row=2, column=0, sticky="ew")
        
        # Style cho nút tối ưu
        style = ttk.Style()
        style.configure("Smart.TButton", foreground="blue", font=("Helvetica", 10, "bold"))

        # Nhóm 1: Thao tác CRUD
        ttk.Button(frame, text="Thêm Mới", command=self.add_bridge).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame, text="Cập Nhật", command=self.update_selected_bridge).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame, text="Xóa", command=self.delete_selected_bridge).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame, text="Làm Mới List", command=self.refresh_bridge_list).pack(side=tk.LEFT, padx=2)

        # Nhóm 2: Chức năng nâng cao (Nút mới)
        ttk.Separator(frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.btn_smart_opt = ttk.Button(
            frame, 
            text="⚡ Tối Ưu Cầu Thông Minh", 
            style="Smart.TButton",
            command=self.run_smart_optimization
        )
        self.btn_smart_opt.pack(side=tk.LEFT, padx=2)
        
        # Nhóm 3: Backtest nhanh (Bên phải)
        ttk.Button(frame, text="Test Cầu Này", command=self.run_quick_backtest).pack(side=tk.RIGHT, padx=2)

    # --- LOGIC HANDLERS ---

    def refresh_bridge_list(self):
        """Tải lại danh sách cầu từ DB."""
        # Xóa cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Tải mới
        self.all_bridges_cache = get_all_managed_bridges(self.app.db_name)
        
        # Hiển thị
        for b in self.all_bridges_cache:
            status_text = "Đang Bật" if b['is_enabled'] else "Đã Tắt"
            # Tô màu dòng nếu tắt
            tags = ("disabled",) if not b['is_enabled'] else ()
            
            # [FIXED] Sử dụng .get('date_added') thay vì ['created_at'] để khớp với DB
            created_date = b.get('date_added', 'N/A')
            
            self.tree.insert(
                "", tk.END, 
                values=(b['id'], b['name'], b['description'], b.get('win_rate_text', 'N/A'), status_text, created_date),
                tags=tags
            )
        
        self.tree.tag_configure("disabled", foreground="gray")

    def on_bridge_select(self, event):
        """Khi chọn 1 dòng, đổ dữ liệu lên form."""
        selected = self.tree.focus()
        if not selected: return
        
        values = self.tree.item(selected, "values")
        if not values: return
        
        # Điền form
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[1])
        
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, values[2])
        
        is_enabled = (values[4] == "Đang Bật")
        self.enabled_var.set(is_enabled)

    def add_bridge(self):
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        if not name:
            messagebox.showwarning("Lỗi", "Tên cầu không được để trống!", parent=self.window)
            return
            
        success, msg = add_managed_bridge(name, desc)
        if success:
            self.app.logger.log(f"Thêm cầu thành công: {name}")
            self.refresh_bridge_list()
            self.reset_form()
        else:
            messagebox.showerror("Lỗi", msg, parent=self.window)

    def update_selected_bridge(self):
        selected = self.tree.focus()
        if not selected: return
        
        bridge_id = self.tree.item(selected, "values")[0]
        desc = self.desc_entry.get().strip()
        status = 1 if self.enabled_var.get() else 0
        
        success, msg = update_managed_bridge(bridge_id, desc, status)
        if success:
            self.app.logger.log(f"Cập nhật cầu {bridge_id}: {msg}")
            self.refresh_bridge_list()
        else:
            messagebox.showerror("Lỗi", msg, parent=self.window)

    def delete_selected_bridge(self):
        selected = self.tree.focus()
        if not selected: return
        
        bridge_id = self.tree.item(selected, "values")[0]
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa cầu này?", parent=self.window):
            success, msg = delete_managed_bridge(bridge_id)
            if success:
                self.app.logger.log(f"Đã xóa cầu {bridge_id}")
                self.refresh_bridge_list()
                self.reset_form()

    def reset_form(self):
        self.name_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.enabled_var.set(True)

    def run_smart_optimization(self):
        """Gọi logic Tối ưu hóa từ Controller."""
        if messagebox.askyesno("Tối Ưu Cầu", "Hệ thống sẽ:\n1. Tắt các cầu hiệu quả thấp (Lọc)\n2. Bật lại các cầu tiềm năng\n3. Làm mới danh sách\n\nTiếp tục?"):
            self.app.task_manager.run_task(self.app.controller.task_run_smart_optimization, "Tối Ưu Cầu Thông Minh")

    def run_quick_backtest(self):
        """Chạy backtest cho cầu đang chọn."""
        selected = self.tree.focus()
        if not selected: return
        
        bridge_name = self.tree.item(selected, "values")[1]
        self.app.trigger_bridge_backtest(bridge_name)