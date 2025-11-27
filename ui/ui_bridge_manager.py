# Tên file: git1/ui/ui_bridge_manager.py
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
except ImportError as e:
    print(f"LỖI IMPORT NGHIÊM TRỌNG tại ui_bridge_manager: {e}")
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
        
        if (
            hasattr(self.app, "bridge_manager_window")
            and self.app.bridge_manager_window
            and self.app.bridge_manager_window.winfo_exists()
        ):
            self.app.bridge_manager_window.lift()
            return

        self.window = tk.Toplevel(self.root)
        self.window.title("Quản Lý Cầu (Bridge Manager)")
        self.window.geometry("900x600")
        
        self.app.bridge_manager_window = self.window
        self.app.bridge_manager_window_instance = self

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)

        self.create_input_form()
        self.create_bridge_list()
        self.create_toolbar()

        self.refresh_bridge_list()

    def create_input_form(self):
        """Tạo form thêm/sửa cầu."""
        frame = ttk.LabelFrame(self.window, text="Thông tin Cầu", padding="10")
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Tên Cầu (VD: Cầu 1, Bong(0,1)):").grid(row=0, column=0, sticky="w")
        self.name_entry = ttk.Entry(frame)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5)

        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Đang Bật (Sử dụng)", variable=self.enabled_var).grid(row=0, column=2, padx=5)

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

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self.on_bridge_select)

    def create_toolbar(self):
        """Tạo thanh công cụ chứa các nút chức năng."""
        frame = ttk.Frame(self.window, padding="10")
        frame.grid(row=2, column=0, sticky="ew")
        
        style = ttk.Style()
        style.configure("Smart.TButton", foreground="blue", font=("Helvetica", 10, "bold"))

        ttk.Button(frame, text="Thêm Mới", command=self.add_bridge).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame, text="Cập Nhật", command=self.update_selected_bridge).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame, text="Xóa", command=self.delete_selected_bridge).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame, text="Làm Mới List", command=self.refresh_bridge_list).pack(side=tk.LEFT, padx=2)

        ttk.Separator(frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.btn_smart_opt = ttk.Button(
            frame, 
            text="⚡ Tối Ưu Cầu Thông Minh", 
            style="Smart.TButton",
            command=self.run_smart_optimization
        )
        self.btn_smart_opt.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(frame, text="Test Cầu Này", command=self.run_quick_backtest).pack(side=tk.RIGHT, padx=2)

    # --- LOGIC HANDLERS ---

    def refresh_bridge_list(self):
        """Tải lại danh sách cầu từ DB (ĐÃ FIX LỖI RACE CONDITION)."""
        try:
            # [FIX QUAN TRỌNG]: Kiểm tra self.window chứ không phải self
            if not hasattr(self, 'window') or not self.window.winfo_exists():
                return
            
            # Kiểm tra treeview còn tồn tại không
            try:
                self.tree.get_children()
            except tk.TclError:
                return

            for item in self.tree.get_children():
                self.tree.delete(item)
                
            self.all_bridges_cache = get_all_managed_bridges(self.app.db_name)
            
            for b in self.all_bridges_cache:
                status_text = "Đang Bật" if b['is_enabled'] else "Đã Tắt"
                tags = ("disabled",) if not b['is_enabled'] else ()
                
                # Dùng .get() an toàn cho các key có thể thiếu
                created_date = b.get('created_at') or b.get('date_added', 'N/A')
                win_rate = b.get('win_rate_text', 'N/A')
                
                self.tree.insert(
                    "", tk.END, 
                    values=(b['id'], b['name'], b['description'], win_rate, status_text, created_date),
                    tags=tags
                )
            
            self.tree.tag_configure("disabled", foreground="gray")
            
        except Exception as e:
            print(f"Lỗi refresh_bridge_list (Ignored): {e}")

    def on_bridge_select(self, event):
        selected = self.tree.focus()
        if not selected: return
        
        values = self.tree.item(selected, "values")
        if not values: return
        
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
        if messagebox.askyesno("Tối Ưu Cầu", "Hệ thống sẽ:\n1. Tắt các cầu hiệu quả thấp (Lọc)\n2. Bật lại các cầu tiềm năng\n3. Làm mới danh sách\n\nTiếp tục?"):
            self.app.task_manager.run_task(self.app.controller.task_run_smart_optimization, "Tối Ưu Cầu Thông Minh")

    def run_quick_backtest(self):
        selected = self.tree.focus()
        if not selected: return
        
        bridge_name = self.tree.item(selected, "values")[1]
        self.app.trigger_bridge_backtest(bridge_name)