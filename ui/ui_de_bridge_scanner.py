# Tên file: ui/ui_de_bridge_scanner.py
# (PHIÊN BẢN V11.0 - NEW: GIAO DIỆN QUÉT VÀ DUYỆT CẦU ĐỀ)

"""
UI riêng biệt cho việc quét và duyệt cầu Đề.

Workflow:
1. User click "Quét Cầu Mới" -> Quét từ dữ liệu lịch sử
2. Hiển thị TẤT CẢ kết quả đã qua filter chất lượng
3. User chọn cầu muốn thêm vào quản lý (checkbox)
4. Click "Thêm vào Quản Lý" -> Lưu vào DB
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import List, Dict, Any


class DeBridgeScannerWindow:
    """Cửa sổ quét và duyệt cầu Đề."""
    
    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.scanned_bridges = []  # Kết quả scan tạm thời
        
        # Check if window already exists
        if (hasattr(self.app, "de_scanner_window") 
            and self.app.de_scanner_window 
            and self.app.de_scanner_window.winfo_exists()):
            self.app.de_scanner_window.lift()
            return
        
        self.window = tk.Toplevel(self.root)
        self.window.title("Quét Cầu Đề Mới - V11.0")
        self.window.geometry("1200x700")
        
        self.app.de_scanner_window = self.window
        
        self._create_ui()
    
    def _create_ui(self):
        """Tạo giao diện."""
        
        # === TOOLBAR ===
        toolbar = ttk.Frame(self.window, padding=5)
        toolbar.pack(fill=tk.X)
        
        ttk.Button(
            toolbar, 
            text="🔍 Quét Cầu Mới", 
            command=self._start_scan
        ).pack(side=tk.LEFT, padx=5)
        
        self.lbl_status = ttk.Label(
            toolbar, 
            text="Chưa quét", 
            foreground="gray"
        )
        self.lbl_status.pack(side=tk.LEFT, padx=10)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=10
        )
        
        ttk.Button(
            toolbar, 
            text="✅ Thêm Đã Chọn vào Quản Lý",
            command=self._approve_selected,
            style="Success.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="☑️ Chọn Tất Cả",
            command=self._select_all
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            toolbar, 
            text="⬜ Bỏ Chọn Tất Cả",
            command=self._deselect_all
        ).pack(side=tk.LEFT, padx=2)
        
        # === INFO PANEL ===
        info_frame = ttk.LabelFrame(self.window, text="Thông Tin", padding=5)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_total = ttk.Label(info_frame, text="Tổng cầu tìm thấy: 0")
        self.lbl_total.pack(side=tk.LEFT, padx=10)
        
        self.lbl_selected = ttk.Label(info_frame, text="Đã chọn: 0")
        self.lbl_selected.pack(side=tk.LEFT, padx=10)
        
        # === FILTER PANEL ===
        filter_frame = ttk.LabelFrame(self.window, text="Lọc Kết Quả", padding=5)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Loại cầu:").pack(side=tk.LEFT, padx=5)
        
        self.filter_type = tk.StringVar(value="ALL")
        types = [
            ("Tất cả", "ALL"),
            ("DE_DYN (Dynamic)", "DE_DYNAMIC_K"),
            ("DE_SET (Bộ)", "DE_SET"),
            ("DE_MEMORY (Bạc Nhớ)", "DE_MEMORY"),
            ("DE_PASCAL", "DE_PASCAL"),
            ("DE_POS_SUM", "DE_POS_SUM")
        ]
        
        for label, value in types:
            ttk.Radiobutton(
                filter_frame, 
                text=label, 
                variable=self.filter_type,
                value=value,
                command=self._apply_filter
            ).pack(side=tk.LEFT, padx=5)
        
        # === RESULTS TABLE ===
        table_frame = ttk.Frame(self.window)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview with checkbox column
        columns = ("select", "name", "type", "streak", "win_rate", "predicted", "description")
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings",
            selectmode="extended"
        )
        
        # Column headers
        self.tree.heading("select", text="☑️")
        self.tree.heading("name", text="Tên Cầu")
        self.tree.heading("type", text="Loại")
        self.tree.heading("streak", text="Thông (30N)")
        self.tree.heading("win_rate", text="Tỷ Lệ")
        self.tree.heading("predicted", text="Dự Đoán")
        self.tree.heading("description", text="Mô Tả")
        
        # Column widths
        self.tree.column("select", width=40, anchor="center")
        self.tree.column("name", width=200, anchor=tk.W)
        self.tree.column("type", width=120, anchor="center")
        self.tree.column("streak", width=80, anchor="center")
        self.tree.column("win_rate", width=80, anchor="center")
        self.tree.column("predicted", width=150, anchor="center")
        self.tree.column("description", width=400, anchor=tk.W)
        
        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Bind click event for checkbox toggle
        self.tree.bind("<Button-1>", self._on_tree_click)
        
        # Tag styles
        self.tree.tag_configure("selected", background="#E3F2FD")
        self.tree.tag_configure("DE_SET", foreground="#1976D2", font=("Arial", 9, "bold"))
        self.tree.tag_configure("DE_MEMORY", foreground="#7B1FA2")
        self.tree.tag_configure("high_rate", background="#C8E6C9")
        
        # Style for success button
        style = ttk.Style()
        style.configure("Success.TButton", foreground="green", font=("Arial", 10, "bold"))
    
    def _start_scan(self):
        """Bắt đầu quét cầu."""
        # Get data
        data = getattr(self.app, 'all_data_ai', [])
        if not data:
            if hasattr(self.app, 'controller'):
                data = getattr(self.app.controller, 'all_data_ai', [])
        
        if not data or len(data) < 30:
            messagebox.showwarning(
                "Thiếu Dữ Liệu",
                "Cần ít nhất 30 kỳ dữ liệu để quét cầu.\nVui lòng nạp dữ liệu trước.",
                parent=self.window
            )
            return
        
        self.lbl_status.config(text="Đang quét...", foreground="orange")
        self.window.update()
        
        # Run scan in thread
        thread = threading.Thread(target=self._run_scan_thread, args=(data,), daemon=True)
        thread.start()
    
    def _run_scan_thread(self, data):
        """Chạy scanner trong thread riêng."""
        try:
            # Import scanner
            from logic.bridges.de_bridge_scanner import run_de_scanner
            
            # Run scan WITHOUT auto_save
            count, bridges = run_de_scanner(data, auto_save=False)
            
            # Update UI in main thread
            self.window.after(0, lambda: self._display_results(bridges))
            
        except Exception as e:
            error_msg = f"Lỗi khi quét: {e}"
            print(error_msg)
            self.window.after(0, lambda: self._show_error(error_msg))
    
    def _display_results(self, bridges: List[Dict[str, Any]]):
        """Hiển thị kết quả quét."""
        self.scanned_bridges = bridges
        
        # Clear old data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Display all bridges
        for bridge in bridges:
            name = bridge.get('name', '')
            b_type = bridge.get('type', '')
            streak = bridge.get('streak', 0)
            win_rate = bridge.get('win_rate', 0)
            predicted = bridge.get('predicted_value', '')
            desc = bridge.get('display_desc', '')
            
            # Determine tags
            tags = [b_type]
            if win_rate >= 95:
                tags.append("high_rate")
            
            self.tree.insert(
                "", 
                tk.END,
                values=("⬜", name, b_type, streak, f"{win_rate:.1f}%", predicted, desc),
                tags=tuple(tags)
            )
        
        # Update status
        self.lbl_status.config(
            text=f"Hoàn tất! Tìm thấy {len(bridges)} cầu.", 
            foreground="green"
        )
        self.lbl_total.config(text=f"Tổng cầu tìm thấy: {len(bridges)}")
        self.lbl_selected.config(text="Đã chọn: 0")
    
    def _show_error(self, error_msg: str):
        """Hiển thị lỗi."""
        self.lbl_status.config(text="Lỗi!", foreground="red")
        messagebox.showerror("Lỗi Quét", error_msg, parent=self.window)
    
    def _on_tree_click(self, event):
        """Xử lý click vào tree (toggle checkbox)."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self.tree.identify_column(event.x)
        if column != "#1":  # Not checkbox column
            return
        
        item = self.tree.identify_row(event.y)
        if not item:
            return
        
        # Toggle checkbox
        values = list(self.tree.item(item, "values"))
        if values[0] == "⬜":
            values[0] = "☑️"
            tags = list(self.tree.item(item, "tags"))
            tags.append("selected")
            self.tree.item(item, values=values, tags=tuple(tags))
        else:
            values[0] = "⬜"
            tags = [t for t in self.tree.item(item, "tags") if t != "selected"]
            self.tree.item(item, values=values, tags=tuple(tags))
        
        # Update selected count
        selected_count = sum(1 for item in self.tree.get_children() 
                            if self.tree.item(item, "values")[0] == "☑️")
        self.lbl_selected.config(text=f"Đã chọn: {selected_count}")
    
    def _select_all(self):
        """Chọn tất cả."""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            values[0] = "☑️"
            tags = list(self.tree.item(item, "tags"))
            if "selected" not in tags:
                tags.append("selected")
            self.tree.item(item, values=values, tags=tuple(tags))
        
        selected_count = len(self.tree.get_children())
        self.lbl_selected.config(text=f"Đã chọn: {selected_count}")
    
    def _deselect_all(self):
        """Bỏ chọn tất cả."""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            values[0] = "⬜"
            tags = [t for t in self.tree.item(item, "tags") if t != "selected"]
            self.tree.item(item, values=values, tags=tuple(tags))
        
        self.lbl_selected.config(text="Đã chọn: 0")
    
    def _apply_filter(self):
        """Áp dụng filter theo loại cầu."""
        filter_value = self.filter_type.get()
        
        # Clear and refill
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filtered_bridges = self.scanned_bridges
        if filter_value != "ALL":
            filtered_bridges = [b for b in self.scanned_bridges 
                               if b.get('type') == filter_value]
        
        for bridge in filtered_bridges:
            name = bridge.get('name', '')
            b_type = bridge.get('type', '')
            streak = bridge.get('streak', 0)
            win_rate = bridge.get('win_rate', 0)
            predicted = bridge.get('predicted_value', '')
            desc = bridge.get('display_desc', '')
            
            tags = [b_type]
            if win_rate >= 95:
                tags.append("high_rate")
            
            self.tree.insert(
                "", 
                tk.END,
                values=("⬜", name, b_type, streak, f"{win_rate:.1f}%", predicted, desc),
                tags=tuple(tags)
            )
        
        self.lbl_total.config(text=f"Tổng cầu tìm thấy: {len(filtered_bridges)}")
        self.lbl_selected.config(text="Đã chọn: 0")
    
    def _approve_selected(self):
        """Duyệt và thêm các cầu đã chọn vào DB."""
        # Get selected bridges
        selected_bridges = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0] == "☑️":
                bridge_name = values[1]
                # Find bridge in scanned_bridges
                for bridge in self.scanned_bridges:
                    if bridge.get('name') == bridge_name:
                        selected_bridges.append(bridge)
                        break
        
        if not selected_bridges:
            messagebox.showinfo(
                "Chưa Chọn",
                "Vui lòng chọn ít nhất 1 cầu để thêm vào quản lý.",
                parent=self.window
            )
            return
        
        # Confirm
        if not messagebox.askyesno(
            "Xác Nhận",
            f"Bạn có chắc muốn thêm {len(selected_bridges)} cầu vào quản lý?\n\n"
            "Các cầu này sẽ được lưu vào database và có thể quản lý/phân tích sau này.",
            parent=self.window
        ):
            return
        
        # Approve in thread
        self.lbl_status.config(text="Đang thêm vào DB...", foreground="orange")
        thread = threading.Thread(
            target=self._approve_thread, 
            args=(selected_bridges,), 
            daemon=True
        )
        thread.start()
    
    def _approve_thread(self, bridges: List[Dict[str, Any]]):
        """Thread xử lý approval."""
        try:
            from logic.bridges.bridge_approval_service import approve_bridges
            
            success_count, failed_count, msg = approve_bridges(bridges)
            
            # Update UI
            self.window.after(0, lambda: self._show_approval_result(success_count, failed_count, msg))
            
        except Exception as e:
            error_msg = f"Lỗi khi thêm cầu: {e}"
            self.window.after(0, lambda: self._show_error(error_msg))
    
    def _show_approval_result(self, success: int, failed: int, msg: str):
        """Hiển thị kết quả approval."""
        self.lbl_status.config(text="Đã thêm xong!", foreground="green")
        
        if failed == 0:
            messagebox.showinfo("Thành Công", msg, parent=self.window)
            # Refresh bridge manager if open
            if hasattr(self.app, 'bridge_manager_window_instance'):
                try:
                    self.app.bridge_manager_window_instance.refresh_bridge_list()
                except:
                    pass
        else:
            messagebox.showwarning("Hoàn Thành (Có Lỗi)", msg, parent=self.window)
