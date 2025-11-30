# Tên file: git1/ui/ui_bridge_manager.py
import tkinter as tk
from tkinter import messagebox, ttk

# Import các hàm logic cần thiết
from logic.config_manager import SETTINGS
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

    def _setup_treeview_columns(self):
        """
        Thiết lập tên cột và kích thước cho Treeview Cầu Đã Lưu.
        Sử dụng MANAGER_RATE_MODE để đặt tiêu đề động.
        """
        # ⚡ LOGIC SỬA LỖI UI: Đọc chế độ Backtest hiện tại từ cấu hình
        try:
            rate_mode = SETTINGS.MANAGER_RATE_MODE
            rate_header = f"Tỷ lệ thắng ({rate_mode.upper()})"
        except Exception:
            rate_header = "Tỷ lệ thắng (K1N)" # Fallback an toàn
        
        # Thiết lập các cột với tiêu đề động
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=40, anchor="center")
        
        self.tree.heading("name", text="Tên Cầu")
        self.tree.column("name", width=150, anchor=tk.W)
        
        self.tree.heading("desc", text="Mô Tả")
        self.tree.column("desc", width=200, anchor=tk.W)
        
        self.tree.heading("win_rate", text=rate_header)
        self.tree.column("win_rate", width=120, anchor="center")
        
        self.tree.heading("status", text="Trạng Thái")
        self.tree.column("status", width=80, anchor="center")
        
        self.tree.heading("pinned", text="📌 Ghim")
        self.tree.column("pinned", width=60, anchor="center")
        
        self.tree.heading("created_at", text="Ngày Tạo")
        self.tree.column("created_at", width=120, anchor="center")

    def create_bridge_list(self):
        """Tạo bảng danh sách cầu."""
        frame = ttk.Frame(self.window)
        frame.grid(row=1, column=0, sticky="nsew", padx=10)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        columns = ("id", "name", "desc", "win_rate", "status", "pinned", "created_at")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        
        # Thiết lập cột với tiêu đề động dựa trên MANAGER_RATE_MODE
        self._setup_treeview_columns()

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self.on_bridge_select)
        
        # Context menu (right-click) để ghim/bỏ ghim
        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="📌 Ghim/Bỏ Ghim", command=self.toggle_pin_selected_bridge)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔍 Xem Backtest 30 Ngày", command=self.run_quick_backtest)
        self.tree.bind("<Button-3>", self.show_context_menu)  # Right-click

    def create_toolbar(self):
        """Tạo thanh công cụ chứa các nút chức năng."""
        frame = ttk.Frame(self.window, padding="10")
        frame.grid(row=2, column=0, sticky="ew")
        
        style = ttk.Style()
        style.configure("Smart.TButton", foreground="blue", font=("Helvetica", 10, "bold"))

        ttk.Button(frame, text="Thêm Mới", command=self.add_bridge).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame, text="Cập Nhật", command=self.update_selected_bridge).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame, text="Xóa", command=self.delete_selected_bridge).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame, text="📌 Ghim/Bỏ Ghim", command=self.toggle_pin_selected_bridge).pack(side=tk.LEFT, padx=2)
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
                is_pinned = b.get('is_pinned', 0)
                pinned_text = "📌 Có" if is_pinned else "❌ Không"
                
                # Tạo tags để tô màu
                tags = []
                if not b['is_enabled']:
                    tags.append("disabled")
                if is_pinned:
                    tags.append("pinned")
                
                # Dùng .get() an toàn cho các key có thể thiếu
                created_date = b.get('created_at') or b.get('date_added', 'N/A')
                
                # LÔGIC HIỂN THỊ MỚI: Hiển thị Tỷ lệ Chuẩn VÀ Tỷ lệ Tối ưu
                win_rate_text_display = b.get('win_rate_text', 'N/A')
                
                # ⚡ HIỂN THỊ TỶ LỆ TỐI ƯU (search_rate_text) nếu khác và không phải là 0.00%
                search_rate = b.get("search_rate_text", "0.00%")
                search_period = b.get("search_period", 0)
                
                # Kiểm tra nếu Tỷ lệ Tối ưu khác Tỷ lệ Chuẩn và không phải là 0.00%
                if search_rate != win_rate_text_display and search_rate != "0.00%":
                    win_rate_text_display = f"{win_rate_text_display} (Tối ưu: {search_rate} / {search_period} kỳ)"
                
                self.tree.insert(
                    "", tk.END, 
                    values=(b['id'], b['name'], b['description'], win_rate_text_display, status_text, pinned_text, created_date),
                    tags=tuple(tags) if tags else ()
                )
            
            self.tree.tag_configure("disabled", foreground="gray")
            self.tree.tag_configure("pinned", background="#fff9c4")  # Màu vàng nhạt cho cầu đã ghim
            
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
        if not selected: 
            messagebox.showwarning("Chưa chọn cầu", "Vui lòng chọn một cầu từ danh sách.", parent=self.window)
            return
        
        bridge_name = self.tree.item(selected, "values")[1]
        # Xác định loại cầu (Đề hay Lô) dựa trên tên
        is_de = bridge_name.startswith("DE_") or "Đề" in bridge_name
        if hasattr(self.app, 'controller') and self.app.controller:
            self.app.controller.trigger_bridge_backtest(bridge_name, is_de=is_de)
        else:
            messagebox.showerror("Lỗi", "Controller không khả dụng.", parent=self.window)
    
    def toggle_pin_selected_bridge(self):
        """Ghim hoặc bỏ ghim cầu được chọn."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Chưa chọn cầu", "Vui lòng chọn một cầu từ danh sách để ghim/bỏ ghim.", parent=self.window)
            return
        
        bridge_name = self.tree.item(selected, "values")[1]
        
        # Kiểm tra trạng thái hiện tại
        current_pinned = self.tree.item(selected, "values")[5]
        action_text = "bỏ ghim" if current_pinned == "📌 Có" else "ghim"
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn {action_text} cầu '{bridge_name}'?", parent=self.window):
            # Gọi controller để thực hiện toggle pin
            if hasattr(self.app, 'controller') and self.app.controller:
                # Chạy trong background thread
                import threading
                def run_toggle_pin():
                    try:
                        self.app.controller.task_run_toggle_pin(bridge_name)
                        # Refresh danh sách sau khi hoàn tất
                        self.window.after(500, self.refresh_bridge_list)
                    except Exception as e:
                        self.window.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể {action_text} cầu: {e}", parent=self.window))
                
                thread = threading.Thread(target=run_toggle_pin, daemon=True)
                thread.start()
            else:
                messagebox.showerror("Lỗi", "Controller không khả dụng.", parent=self.window)
    
    def show_context_menu(self, event):
        """Hiển thị context menu khi right-click vào cầu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()