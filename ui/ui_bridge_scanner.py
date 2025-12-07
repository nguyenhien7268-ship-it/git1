# Tên file: ui/ui_bridge_scanner.py
# (PHIÊN BẢN V1.0 - TAB DÒ TÌM CẦU MỚI - SCANNING ONLY)
#
# Mục đích: Tab chuyên dụng cho việc dò tìm/phát hiện cầu mới.
#           KHÔNG có chức năng quản lý (enable/disable/delete/edit).

import tkinter as tk
from tkinter import messagebox, ttk
import threading

# Import scanning functions ONLY
try:
    from logic.bridges.lo_bridge_scanner import (
        TIM_CAU_TOT_NHAT_V16,
        TIM_CAU_BAC_NHO_TOT_NHAT,
        update_fixed_lo_bridges,
    )
    from logic.bridges.bridge_manager_de import find_and_auto_manage_bridges_de
    from logic.data_repository import load_data_ai_from_db
    from lottery_service import DB_NAME, upsert_managed_bridge
except ImportError as e:
    print(f"LỖI IMPORT tại ui_bridge_scanner: {e}")
    def TIM_CAU_TOT_NHAT_V16(*args, **kwargs): return []
    def TIM_CAU_BAC_NHO_TOT_NHAT(*args, **kwargs): return []
    def update_fixed_lo_bridges(*args, **kwargs): return 0
    def find_and_auto_manage_bridges_de(*args, **kwargs): return []
    def load_data_ai_from_db(*args, **kwargs): return [], 0
    def upsert_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
    DB_NAME = "data/xo_so_prizes_all_logic.db"


class BridgeScannerTab(ttk.Frame):
    """
    Tab chuyên dụng cho DÒ TÌM CẦU MỚI.
    
    Chức năng:
    - Quét cầu Lô (V17 Shadow, Bạc Nhớ, Cố Định)
    - Quét cầu Đề
    - Hiển thị kết quả scan
    - Thêm cầu mới vào hệ thống quản lý
    
    KHÔNG có:
    - Bật/tắt cầu
    - Xóa cầu
    - Chỉnh sửa cầu
    - Prune/Auto-manage
    """
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.db_name = DB_NAME
        self.scan_results = []  # Lưu kết quả scan tạm thời (chưa quản lý)
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        self._create_scan_controls()
        self._create_results_table()
        self._create_action_buttons()
        
    def _create_scan_controls(self):
        """Tạo khu vực điều khiển quét cầu."""
        frame = ttk.LabelFrame(self, text="🔍 Điều Khiển Quét Cầu", padding="10")
        frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        frame.columnconfigure(1, weight=1)
        
        # Dòng 1: Quét Lô
        ttk.Label(frame, text="Quét Cầu Lô:", font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=5
        )
        
        btn_frame_lo = ttk.Frame(frame)
        btn_frame_lo.grid(row=0, column=1, sticky="ew", pady=5)
        
        ttk.Button(
            btn_frame_lo, 
            text="📊 Quét V17 Shadow", 
            command=self._scan_v17
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame_lo, 
            text="🧠 Quét Bạc Nhớ", 
            command=self._scan_memory
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame_lo, 
            text="📌 Cập Nhật Cầu Cố Định", 
            command=self._scan_fixed
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame_lo, 
            text="⚡ QUÉT TẤT CẢ LÔ", 
            command=self._scan_all_lo,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)
        
        # Dòng 2: Quét Đề
        ttk.Label(frame, text="Quét Cầu Đề:", font=("Helvetica", 10, "bold")).grid(
            row=1, column=0, sticky="w", pady=5
        )
        
        btn_frame_de = ttk.Frame(frame)
        btn_frame_de.grid(row=1, column=1, sticky="ew", pady=5)
        
        ttk.Button(
            btn_frame_de, 
            text="🔮 Quét Cầu Đề", 
            command=self._scan_de
        ).pack(side=tk.LEFT, padx=5)
        
        # Dòng 3: Thông tin
        self.scan_status_label = ttk.Label(
            frame, 
            text="📌 Sẵn sàng quét. Chọn loại quét và bấm nút để bắt đầu.", 
            foreground="blue"
        )
        self.scan_status_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
    
    def _create_results_table(self):
        """Tạo bảng hiển thị kết quả quét."""
        frame = ttk.LabelFrame(self, text="📋 Kết Quả Quét (Cầu Mới Phát Hiện)", padding="10")
        frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Columns: Loại, Tên Cầu, Vị Trí/Mô tả, Tỷ Lệ K2N, Chuỗi, Đã Thêm
        columns = ("type", "name", "description", "scan_rate", "streak", "added")
        self.results_tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
        
        self.results_tree.heading("type", text="Loại")
        self.results_tree.column("type", width=80, anchor="center")
        
        self.results_tree.heading("name", text="Tên Cầu")
        self.results_tree.column("name", width=150, anchor=tk.W)
        
        self.results_tree.heading("description", text="Mô Tả")
        self.results_tree.column("description", width=250, anchor=tk.W)
        
        self.results_tree.heading("scan_rate", text="Tỷ Lệ K2N")
        self.results_tree.column("scan_rate", width=100, anchor="center")
        
        self.results_tree.heading("streak", text="Chuỗi")
        self.results_tree.column("streak", width=80, anchor="center")
        
        self.results_tree.heading("added", text="Đã Thêm")
        self.results_tree.column("added", width=80, anchor="center")
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
    
    def _create_action_buttons(self):
        """Tạo các nút thao tác với kết quả quét."""
        frame = ttk.Frame(self, padding="10")
        frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        ttk.Label(frame, text="Thao tác với kết quả:", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            frame, 
            text="➕ Thêm Cầu Đã Chọn vào Quản Lý", 
            command=self._add_selected_to_management
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            frame, 
            text="➕➕ Thêm TẤT CẢ vào Quản Lý", 
            command=self._add_all_to_management
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            frame, 
            text="🗑️ Xóa Kết Quả Quét", 
            command=self._clear_results
        ).pack(side=tk.LEFT, padx=5)
    
    # ==================== SCANNING FUNCTIONS ====================
    
    def _scan_v17(self):
        """Quét cầu V17 Shadow."""
        self._run_scan_in_thread("V17 Shadow", self._do_scan_v17)
    
    def _scan_memory(self):
        """Quét cầu Bạc Nhớ."""
        self._run_scan_in_thread("Bạc Nhớ", self._do_scan_memory)
    
    def _scan_fixed(self):
        """Cập nhật cầu cố định."""
        self._run_scan_in_thread("Cầu Cố Định", self._do_scan_fixed)
    
    def _scan_de(self):
        """Quét cầu Đề."""
        self._run_scan_in_thread("Cầu Đề", self._do_scan_de)
    
    def _scan_all_lo(self):
        """Quét tất cả loại cầu Lô."""
        self._run_scan_in_thread("TẤT CẢ LÔ", self._do_scan_all_lo)
    
    def _run_scan_in_thread(self, scan_type, scan_func):
        """Chạy scan trong thread riêng để không block UI."""
        self.scan_status_label.config(text=f"⏳ Đang quét {scan_type}...", foreground="orange")
        self.update_idletasks()
        
        def worker():
            try:
                scan_func()
                self.after(0, lambda: self.scan_status_label.config(
                    text=f"✅ Quét {scan_type} hoàn tất!", 
                    foreground="green"
                ))
            except Exception as e:
                self.after(0, lambda: self.scan_status_label.config(
                    text=f"❌ Lỗi quét {scan_type}: {str(e)}", 
                    foreground="red"
                ))
                self.after(0, lambda: messagebox.showerror("Lỗi Quét", f"Không thể quét {scan_type}:\n{e}"))
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _do_scan_v17(self):
        """Thực hiện quét V17."""
        all_data, _ = load_data_ai_from_db(self.db_name)
        if not all_data:
            raise Exception("Không có dữ liệu xổ số")
        
        results = TIM_CAU_TOT_NHAT_V16(all_data, 2, len(all_data) + 1, self.db_name)
        self._process_scan_results(results, "LÔ_V17")
    
    def _do_scan_memory(self):
        """Thực hiện quét Bạc Nhớ."""
        all_data, _ = load_data_ai_from_db(self.db_name)
        if not all_data:
            raise Exception("Không có dữ liệu xổ số")
        
        results = TIM_CAU_BAC_NHO_TOT_NHAT(all_data, 2, len(all_data) + 1, self.db_name)
        self._process_scan_results(results, "LÔ_BN")
    
    def _do_scan_fixed(self):
        """Thực hiện cập nhật cầu cố định."""
        all_data, _ = load_data_ai_from_db(self.db_name)
        if not all_data:
            raise Exception("Không có dữ liệu xổ số")
        
        count = update_fixed_lo_bridges(all_data, self.db_name)
        self.after(0, lambda: messagebox.showinfo(
            "Cập Nhật Cầu Cố Định", 
            f"Đã cập nhật {count} cầu cố định.\nCác cầu này đã được thêm vào hệ thống quản lý."
        ))
    
    def _do_scan_de(self):
        """Thực hiện quét Đề."""
        all_data, _ = load_data_ai_from_db(self.db_name)
        if not all_data:
            raise Exception("Không có dữ liệu xổ số")
        
        results = find_and_auto_manage_bridges_de(all_data, self.db_name)
        # DE scanner returns different format, need to adapt
        self.after(0, lambda: messagebox.showinfo(
            "Quét Cầu Đề", 
            f"Đã quét cầu Đề.\nKết quả: {results if results else 'Xem trong hệ thống quản lý'}"
        ))
    
    def _do_scan_all_lo(self):
        """Quét tất cả loại cầu Lô."""
        self._do_scan_v17()
        self._do_scan_memory()
        self._do_scan_fixed()
    
    def _process_scan_results(self, results, bridge_type):
        """Xử lý và hiển thị kết quả quét."""
        if not results or len(results) <= 1:  # Chỉ có header
            self.after(0, lambda: messagebox.showinfo(
                "Kết Quả Quét", 
                f"Không tìm thấy cầu mới loại {bridge_type}."
            ))
            return
        
        # Skip header row
        for row in results[1:]:
            if len(row) >= 4:  # STT, Tên, Mô tả, Tỷ lệ, Chuỗi
                self.after(0, lambda r=row, bt=bridge_type: self._add_result_to_table(r, bt))
    
    def _add_result_to_table(self, row, bridge_type):
        """Thêm một kết quả vào bảng."""
        # row format: [STT, Name, Description, Rate, Streak]
        name = str(row[1]) if len(row) > 1 else "N/A"
        desc = str(row[2]) if len(row) > 2 else "N/A"
        rate = str(row[3]) if len(row) > 3 else "N/A"
        streak = str(row[4]) if len(row) > 4 else "0"
        
        self.results_tree.insert(
            "", tk.END,
            values=(bridge_type, name, desc, rate, streak, "❌ Chưa"),
            tags=("new",)
        )
        self.results_tree.tag_configure("new", background="#e3f2fd")
    
    # ==================== ACTION FUNCTIONS ====================
    
    def _add_selected_to_management(self):
        """Thêm các cầu đã chọn vào hệ thống quản lý."""
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn ít nhất một cầu để thêm.")
            return
        
        added_count = 0
        for item in selected:
            values = self.results_tree.item(item, "values")
            if values[5] == "✅ Rồi":  # Đã thêm rồi
                continue
            
            # Add to management system
            name = values[1]
            desc = values[2]
            rate = values[3]
            
            success, msg = upsert_managed_bridge(
                name=name,
                description=desc,
                win_rate_text=rate,
                db_name=self.db_name,
                pos1_idx=-2,  # Special marker for scanner-added bridges
                pos2_idx=-2,
                bridge_data={"search_rate_text": rate, "is_enabled": 1, "type": values[0]}
            )
            
            if success:
                # Update table to mark as added
                self.results_tree.item(item, values=(
                    values[0], values[1], values[2], values[3], values[4], "✅ Rồi"
                ))
                self.results_tree.item(item, tags=("added",))
                added_count += 1
        
        self.results_tree.tag_configure("added", background="#c8e6c9")
        
        if added_count > 0:
            messagebox.showinfo("Thêm Thành Công", f"Đã thêm {added_count} cầu vào hệ thống quản lý.")
            # Notify management tab to refresh if it exists
            if hasattr(self.app, 'bridge_management_tab'):
                self.app.bridge_management_tab.refresh_bridge_list()
        else:
            messagebox.showinfo("Thông Báo", "Không có cầu mới nào được thêm (có thể đã tồn tại).")
    
    def _add_all_to_management(self):
        """Thêm tất cả kết quả quét vào hệ thống quản lý."""
        all_items = self.results_tree.get_children()
        if not all_items:
            messagebox.showwarning("Không Có Kết Quả", "Không có kết quả quét nào để thêm.")
            return
        
        # Select all and add
        self.results_tree.selection_set(all_items)
        self._add_selected_to_management()
    
    def _clear_results(self):
        """Xóa tất cả kết quả quét."""
        if not self.results_tree.get_children():
            return
        
        if messagebox.askyesno("Xác Nhận", "Xóa tất cả kết quả quét?"):
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            self.scan_status_label.config(text="📌 Đã xóa kết quả. Sẵn sàng quét mới.", foreground="blue")
