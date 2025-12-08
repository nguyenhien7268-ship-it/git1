# Tên file: ui/ui_bridge_management.py
# (PHIÊN BẢN V1.0 - TAB QUẢN LÝ CẦU - MANAGEMENT ONLY)
#
# Mục đích: Tab chuyên dụng cho QUẢN LÝ CẦU đã có.
#           KHÔNG có chức năng quét/dò tìm cầu mới.

import tkinter as tk
from tkinter import messagebox, ttk
import threading

# Import management functions ONLY
try:
    from logic.data_repository import get_managed_bridges_with_prediction
    from logic.bridges.bridge_manager_core import (
        prune_bad_bridges,
        auto_manage_bridges,
    )
    from lottery_service import (
        add_managed_bridge,
        delete_managed_bridge,
        update_managed_bridge,
        DB_NAME,
    )
except ImportError as e:
    print(f"LỖI IMPORT tại ui_bridge_management: {e}")
    def get_managed_bridges_with_prediction(*args, **kwargs): return []
    def prune_bad_bridges(*args, **kwargs): return "Lỗi Import"
    def auto_manage_bridges(*args, **kwargs): return "Lỗi Import"
    def add_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def update_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    def delete_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    DB_NAME = "data/xo_so_prizes_all_logic.db"


class BridgeManagementTab(ttk.Frame):
    """
    Tab chuyên dụng cho QUẢN LÝ CẦU.
    
    Chức năng:
    - Hiển thị danh sách cầu đang quản lý
    - Bật/tắt cầu
    - Chỉnh sửa thông tin cầu
    - Xóa cầu
    - Ghim/Bỏ ghim cầu
    - Tối ưu thông minh (prune bad bridges)
    - Auto-manage bridges
    
    KHÔNG có:
    - Quét cầu mới
    - Dò tìm cầu
    - Các chức năng scanning
    """
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db_name = DB_NAME
        self.all_bridges_cache = []
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        self._create_edit_form()
        self._create_bridge_table()
        self._create_toolbar()
        
        # Auto-refresh on init
        self.after(100, self.refresh_bridge_list)
    
    def _create_edit_form(self):
        """Tạo form chỉnh sửa cầu."""
        frame = ttk.LabelFrame(self, text="✏️ Chỉnh Sửa Cầu", padding="10")
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        
        ttk.Label(frame, text="Tên Cầu:").grid(row=0, column=0, sticky="w", padx=5)
        self.name_entry = ttk.Entry(frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        self.enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame, 
            text="🟢 Đang Bật (Sử dụng)", 
            variable=self.enabled_var
        ).grid(row=0, column=2, padx=10)
        
        ttk.Label(frame, text="Mô tả:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.desc_entry = ttk.Entry(frame)
        self.desc_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
    
    def _create_bridge_table(self):
        """Tạo bảng hiển thị danh sách cầu đang quản lý."""
        frame = ttk.LabelFrame(self, text="📋 Danh Sách Cầu Đang Quản Lý", padding="10")
        frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        
        # Add filter controls
        filter_frame = ttk.Frame(frame)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        ttk.Label(filter_frame, text="Lọc theo loại:", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=(0, 10))
        
        self.filter_var = tk.StringVar(value="ALL")
        filter_options = [
            ("Tất cả", "ALL"),
            ("Chỉ Cầu Lô", "LO"),
            ("Chỉ Cầu Đề", "DE"),
        ]
        
        for text, value in filter_options:
            ttk.Radiobutton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                command=self.refresh_bridge_list
            ).pack(side=tk.LEFT, padx=5)
        
        columns = ("id", "type", "name", "desc", "win_rate_k1n", "win_rate_scan", "status", "pinned", "created_at")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=40, anchor="center")
        
        self.tree.heading("type", text="Loại")
        self.tree.column("type", width=60, anchor="center")
        
        self.tree.heading("name", text="Tên Cầu")
        self.tree.column("name", width=140, anchor=tk.W)
        
        self.tree.heading("desc", text="Mô Tả")
        self.tree.column("desc", width=200, anchor=tk.W)
        
        self.tree.heading("win_rate_k1n", text="K1N (Thực Tế)")
        self.tree.column("win_rate_k1n", width=110, anchor="center")
        
        self.tree.heading("win_rate_scan", text="K2N (Lúc Dò)")
        self.tree.column("win_rate_scan", width=110, anchor="center")
        
        self.tree.heading("status", text="Trạng Thái")
        self.tree.column("status", width=90, anchor="center")
        
        self.tree.heading("pinned", text="📌 Ghim")
        self.tree.column("pinned", width=70, anchor="center")
        
        self.tree.heading("created_at", text="Ngày Tạo")
        self.tree.column("created_at", width=110, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_bridge_select)
        
        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="📌 Ghim/Bỏ Ghim", command=self._toggle_pin)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔍 Xem Backtest 30 Ngày", command=self._run_backtest)
        self.tree.bind("<Button-3>", self._show_context_menu)
    
    def _create_toolbar(self):
        """Tạo toolbar với các nút quản lý."""
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Left side: CRUD operations
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            left_frame, 
            text="➕ Thêm Mới", 
            command=self._add_bridge
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_frame, 
            text="💾 Cập Nhật", 
            command=self._update_bridge
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_frame, 
            text="🗑️ Xóa", 
            command=self._delete_bridge
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_frame, 
            text="📌 Ghim/Bỏ Ghim", 
            command=self._toggle_pin
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(left_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(
            left_frame, 
            text="🔄 Làm Mới", 
            command=self.refresh_bridge_list
        ).pack(side=tk.LEFT, padx=2)
        
        # Right side: Smart operations
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT)
        
        style = ttk.Style()
        style.configure("Smart.TButton", foreground="blue", font=("Helvetica", 10, "bold"))
        
        ttk.Button(
            right_frame, 
            text="⚡ Tối Ưu Thông Minh", 
            style="Smart.TButton",
            command=self._smart_optimize
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            right_frame, 
            text="🔍 Test Cầu", 
            command=self._run_backtest
        ).pack(side=tk.LEFT, padx=5)
    
    # ==================== DISPLAY FUNCTIONS ====================
    
    def refresh_bridge_list(self):
        """Tải lại danh sách cầu đang quản lý."""
        try:
            # Clear old items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Get current data
            current_data = getattr(self.app, 'all_data_ai', [])
            if not current_data and hasattr(self.app, 'controller'):
                current_data = getattr(self.app.controller, 'all_data_ai', [])
            
            # Fallback to loading from DB
            if not current_data:
                try:
                    from logic.data_repository import load_data_ai_from_db
                    rows, _ = load_data_ai_from_db(self.db_name)
                    if rows:
                        current_data = rows
                except:
                    pass
            
            # Get managed bridges with prediction
            self.all_bridges_cache = get_managed_bridges_with_prediction(
                self.db_name,
                current_data=current_data,
                only_enabled=False
            )
            
            # Get filter selection
            filter_type = getattr(self, 'filter_var', None)
            filter_value = filter_type.get() if filter_type else "ALL"
            
            # Display in table with filter
            for b in self.all_bridges_cache:
                # Get bridge type
                bridge_type = b.get('type', 'UNKNOWN')
                
                # Apply filter
                if filter_value == "LO":
                    # Show only LO bridges
                    if not bridge_type.startswith(('LO_', 'LO')):
                        continue
                elif filter_value == "DE":
                    # Show only DE bridges (including DE_MEMORY)
                    valid_de_types = ['DE_DYNAMIC_K', 'DE_POS_SUM', 'DE_SET', 'DE_PASCAL', 'DE_KILLER', 'DE_MEMORY', 'CAU_DE']
                    is_de = any(bridge_type.startswith(t) or bridge_type == t for t in valid_de_types)
                    if not is_de:
                        continue
                # If "ALL", show everything
                
                # Determine display type
                if bridge_type.startswith('LO_'):
                    display_type = "🔵 Lô"
                elif bridge_type.startswith('DE_') or bridge_type.startswith('CAU_DE') or bridge_type == 'DE_MEMORY':
                    display_type = "🔴 Đề"
                else:
                    display_type = bridge_type[:8]  # Truncate if too long
                status_text = "🟢 Đang Bật" if b['is_enabled'] else "🔴 Đã Tắt"
                is_pinned = b.get('is_pinned', 0)
                pinned_text = "📌 Có" if is_pinned else "❌ Không"
                
                tags = []
                if not b['is_enabled']:
                    tags.append("disabled")
                if is_pinned:
                    tags.append("pinned")
                
                created_date = b.get('created_at') or b.get('date_added', 'N/A')
                
                # K1N rate
                k1n_rate = str(b.get('win_rate_text', ''))
                if not k1n_rate or 'N/A' in k1n_rate:
                    pred = str(b.get('next_prediction_stl', ''))
                    if not pred or 'N/A' in pred:
                        k1n_rate = "Chờ dữ liệu..." if not current_data else "Không xác định"
                    else:
                        k1n_rate = f"Dự: {pred}"
                
                # K2N scan rate
                search_rate = b.get("search_rate_text", "")
                search_period = b.get("search_period", 0)
                if search_rate and search_rate != "0.00%":
                    k2n_display = f"{search_rate}"
                    if search_period > 0:
                        k2n_display += f" ({search_period}kỳ)"
                else:
                    k2n_display = "-"
                
                self.tree.insert(
                    "", tk.END,
                    values=(
                        b['id'], display_type, b['name'], b['description'],
                        k1n_rate,
                        k2n_display,
                        status_text, pinned_text, created_date
                    ),
                    tags=tuple(tags) if tags else ()
                )
            
            self.tree.tag_configure("disabled", foreground="gray")
            self.tree.tag_configure("pinned", background="#fff9c4")
            
        except Exception as e:
            print(f"Lỗi refresh_bridge_list: {e}")
            messagebox.showerror("Lỗi", f"Không thể tải danh sách cầu:\n{e}")
    
    def _on_bridge_select(self, event):
        """Xử lý khi chọn một cầu trong bảng."""
        selected = self.tree.focus()
        if not selected:
            return
        
        values = self.tree.item(selected, "values")
        if not values:
            return
        
        # Fill form (updated for new column structure: id, type, name, desc, ...)
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[2])  # name is now at index 2
        
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, values[3])  # desc is now at index 3
        
        # Status is now at index 6
        is_enabled = ("🟢" in values[6])
        self.enabled_var.set(is_enabled)
    
    def _show_context_menu(self, event):
        """Hiển thị context menu."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    # ==================== CRUD OPERATIONS ====================
    
    def _add_bridge(self):
        """Thêm cầu mới."""
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Thiếu Thông Tin", "Vui lòng nhập tên cầu.")
            return
        
        is_enabled = 1 if self.enabled_var.get() else 0
        
        success, msg = add_managed_bridge(name, desc, "N/A")
        
        if success:
            messagebox.showinfo("Thành Công", f"Đã thêm cầu: {name}")
            self.refresh_bridge_list()
            self.name_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Lỗi", f"Không thể thêm cầu:\n{msg}")
    
    def _update_bridge(self):
        """Cập nhật thông tin cầu đã chọn."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn một cầu để cập nhật.")
            return
        
        values = self.tree.item(selected, "values")
        bridge_id = values[0]
        
        new_desc = self.desc_entry.get().strip()
        is_enabled = 1 if self.enabled_var.get() else 0
        
        success, msg = update_managed_bridge(bridge_id, new_desc, is_enabled, self.db_name)
        
        if success:
            messagebox.showinfo("Thành Công", "Đã cập nhật cầu.")
            self.refresh_bridge_list()
        else:
            messagebox.showerror("Lỗi", f"Không thể cập nhật:\n{msg}")
    
    def _delete_bridge(self):
        """Xóa cầu đã chọn."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn một cầu để xóa.")
            return
        
        values = self.tree.item(selected, "values")
        bridge_id = values[0]
        bridge_name = values[2]  # name is now at index 2 (id, type, name, ...)
        
        if not messagebox.askyesno("Xác Nhận", f"Xóa cầu '{bridge_name}'?"):
            return
        
        success, msg = delete_managed_bridge(bridge_id)
        
        if success:
            messagebox.showinfo("Thành Công", f"Đã xóa cầu: {bridge_name}")
            self.refresh_bridge_list()
            self.name_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Lỗi", f"Không thể xóa:\n{msg}")
    
    def _toggle_pin(self):
        """Ghim/Bỏ ghim cầu."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn một cầu.")
            return
        
        values = self.tree.item(selected, "values")
        bridge_id = values[0]
        
        # Find bridge in cache
        bridge = next((b for b in self.all_bridges_cache if b['id'] == bridge_id), None)
        if not bridge:
            return
        
        new_pinned = 0 if bridge.get('is_pinned', 0) else 1
        
        # Update in DB
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_name)
            conn.execute("UPDATE ManagedBridges SET is_pinned=? WHERE id=?", (new_pinned, bridge_id))
            conn.commit()
            conn.close()
            
            self.refresh_bridge_list()
            messagebox.showinfo("Thành Công", "Đã cập nhật trạng thái ghim.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể cập nhật:\n{e}")
    
    # ==================== MANAGEMENT OPERATIONS ====================
    
    def _smart_optimize(self):
        """Tối ưu thông minh - Prune bad bridges."""
        if not messagebox.askyesno(
            "Xác Nhận", 
            "Tối ưu thông minh sẽ TẮT các cầu yếu (K1N & K2N < 40%).\n\nTiếp tục?"
        ):
            return
        
        def worker():
            try:
                # Get data
                current_data = getattr(self.app, 'all_data_ai', [])
                if not current_data and hasattr(self.app, 'controller'):
                    current_data = getattr(self.app.controller, 'all_data_ai', [])
                
                if not current_data:
                    from logic.data_repository import load_data_ai_from_db
                    rows, _ = load_data_ai_from_db(self.db_name)
                    if rows:
                        current_data = rows
                
                # Run optimization
                result = prune_bad_bridges(current_data, self.db_name)
                
                self.after(0, lambda: messagebox.showinfo("Kết Quả Tối Ưu", result))
                self.after(0, self.refresh_bridge_list)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể tối ưu:\n{e}"))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _run_backtest(self):
        """Chạy backtest cho cầu đã chọn."""
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn một cầu để test.")
            return
        
        values = self.tree.item(selected, "values")
        bridge_name = values[2]  # name is now at index 2 (id, type, name, ...)
        
        messagebox.showinfo(
            "Backtest", 
            f"Chức năng backtest cho cầu '{bridge_name}' sẽ được triển khai sau.\n\n"
            "Hiện tại bạn có thể sử dụng chức năng Backtest trong tab Tối Ưu Hóa."
        )
