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
    from lottery_service import DB_NAME, add_managed_bridge, upsert_managed_bridge
except ImportError as e:
    print(f"LỖI IMPORT tại ui_bridge_scanner: {e}")
    def TIM_CAU_TOT_NHAT_V16(*args, **kwargs): return []
    def TIM_CAU_BAC_NHO_TOT_NHAT(*args, **kwargs): return []
    def update_fixed_lo_bridges(*args, **kwargs): return 0
    def find_and_auto_manage_bridges_de(*args, **kwargs): return []
    def load_data_ai_from_db(*args, **kwargs): return [], 0
    def add_managed_bridge(*args, **kwargs): return False, "Lỗi Import"
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
                # FIX: Capture scan_type in lambda default parameter
                self.after(0, lambda st=scan_type: self.scan_status_label.config(
                    text=f"✅ Quét {st} hoàn tất!", 
                    foreground="green"
                ))
            except Exception as e:
                # FIX: Capture variables in lambda default parameters
                error_msg = str(e)
                self.after(0, lambda st=scan_type, err=error_msg: self.scan_status_label.config(
                    text=f"❌ Lỗi quét {st}: {err}", 
                    foreground="red"
                ))
                self.after(0, lambda st=scan_type, err=error_msg: messagebox.showerror(
                    "Lỗi Quét", f"Không thể quét {st}:\n{err}"
                ))
        
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
        """
        Thực hiện quét Đề với xử lý robust cho nhiều dạng kết quả.
        
        V8.3: Enhanced with normalization for diverse scanner return formats:
        - Handles (list, int), (int, list), list, or single objects
        - Normalizes bridge attributes from dict/object
        - Handles win_rate as fraction/percentage/list
        - Captures all variables in lambda closures properly
        """
        all_data, _ = load_data_ai_from_db(self.db_name)
        if not all_data:
            raise Exception("Không có dữ liệu xổ số")
        
        # Import DE scanner directly to get full results
        try:
            from logic.bridges.de_bridge_scanner import run_de_scanner
            scanner_result = run_de_scanner(all_data)
            
            # ROBUST NORMALIZATION: Handle various return formats
            count = 0
            found_bridges = []
            
            if scanner_result is None:
                count = 0
                found_bridges = []
            elif isinstance(scanner_result, tuple) and len(scanner_result) == 2:
                # Could be (list, int) or (int, list)
                if isinstance(scanner_result[0], (list, tuple)) and isinstance(scanner_result[1], int):
                    found_bridges, count = scanner_result[0], scanner_result[1]
                elif isinstance(scanner_result[0], int) and isinstance(scanner_result[1], (list, tuple)):
                    count, found_bridges = scanner_result[0], scanner_result[1]
                else:
                    # Fallback: treat first as bridges
                    found_bridges = scanner_result[0] if isinstance(scanner_result[0], (list, tuple)) else [scanner_result[0]]
                    count = len(found_bridges)
            elif isinstance(scanner_result, (list, tuple)):
                found_bridges = scanner_result
                count = len(found_bridges)
            else:
                # Single object
                found_bridges = [scanner_result]
                count = 1
            
            # Process and display results
            if found_bridges and count > 0:
                for bridge in found_bridges:
                    # NORMALIZE BRIDGE: Handle dict or object with attributes
                    bridge_dict = bridge if isinstance(bridge, dict) else {}
                    
                    # Try various attribute names for name
                    if isinstance(bridge, dict):
                        name = bridge.get('name') or bridge.get('normalized_name') or bridge.get('description', 'N/A')
                    else:
                        name = getattr(bridge, 'name', None) or getattr(bridge, 'normalized_name', None) or getattr(bridge, 'description', 'N/A')
                    
                    # Description
                    if isinstance(bridge, dict):
                        desc = bridge.get('description', bridge.get('name', 'N/A'))
                    else:
                        desc = getattr(bridge, 'description', getattr(bridge, 'name', 'N/A'))
                    
                    # Win rate - handle fraction (0-1), percentage, or list
                    if isinstance(bridge, dict):
                        win_rate = bridge.get('win_rate', 0)
                    else:
                        win_rate = getattr(bridge, 'win_rate', 0)
                    
                    if isinstance(win_rate, (list, tuple)):
                        # Join list of rates
                        rate_str = ', '.join([f"{r:.1f}%" if isinstance(r, (int, float)) else str(r) for r in win_rate])
                    elif isinstance(win_rate, (int, float)):
                        # Convert fraction to percentage if needed
                        if 0 < win_rate <= 1:
                            rate_str = f"{win_rate * 100:.1f}%"
                        else:
                            rate_str = f"{win_rate:.1f}%"
                    else:
                        rate_str = str(win_rate)
                    
                    # Streak - handle int, list, or string
                    if isinstance(bridge, dict):
                        streak = bridge.get('streak', 0)
                    else:
                        streak = getattr(bridge, 'streak', 0)
                    
                    if isinstance(streak, (list, tuple)):
                        streak_str = ', '.join([str(s) for s in streak])
                    else:
                        streak_str = str(streak)
                    
                    # Bridge type
                    if isinstance(bridge, dict):
                        bridge_type = bridge.get('type', 'UNKNOWN')
                    else:
                        bridge_type = getattr(bridge, 'type', 'UNKNOWN')
                    
                    # Add type indicator to name for clarity
                    type_display = ""
                    if 'DE_MEMORY' in bridge_type or bridge_type == 'DE_MEMORY':
                        type_display = " [BẠC NHỚ]"
                    elif 'DE_SET' in bridge_type:
                        type_display = " [BỘ]"
                    elif 'DE_PASCAL' in bridge_type:
                        type_display = " [PASCAL]"
                    elif 'DE_KILLER' in bridge_type:
                        type_display = " [LOẠI TRỪ]"
                    elif 'DE_DYNAMIC' in bridge_type:
                        type_display = " [ĐỘNG]"
                    
                    name_with_type = str(name) + type_display
                    
                    # FIX: Add to results table with ALL variables captured in default params
                    self.after(0, lambda n=name_with_type, d=desc, r=rate_str, s=streak_str, bt=bridge_type: 
                        self._add_de_result_to_table(n, d, r, s, bt))
                
                # FIX: Capture count in default parameter
                self.after(0, lambda c=count: messagebox.showinfo(
                    "Quét Cầu Đề", 
                    f"Đã tìm thấy {c} cầu Đề. Xem kết quả bên dưới."
                ))
            else:
                # FIX: No closure issue here (no variables), but keep consistent style
                self.after(0, lambda: messagebox.showinfo(
                    "Quét Cầu Đề", 
                    "Không tìm thấy cầu Đề mới."
                ))
        except Exception as e:
            # FIX: Capture error message in default parameter
            error_msg = str(e)
            self.after(0, lambda err=error_msg: messagebox.showerror(
                "Lỗi Quét Đề",
                f"Không thể quét cầu Đề:\n{err}"
            ))
    
    def _do_scan_all_lo(self):
        """Quét tất cả loại cầu Lô."""
        self._do_scan_v17()
        self._do_scan_memory()
        self._do_scan_fixed()
    
    def _process_scan_results(self, results, bridge_type):
        """Xử lý và hiển thị kết quả quét."""
        if not results or len(results) <= 1:  # Chỉ có header
            # FIX: Capture bridge_type in default parameter
            self.after(0, lambda bt=bridge_type: messagebox.showinfo(
                "Kết Quả Quét", 
                f"Không tìm thấy cầu mới loại {bt}."
            ))
            return
        
        # Skip header row
        for row in results[1:]:
            if len(row) >= 4:  # STT, Tên, Mô tả, Tỷ lệ, Chuỗi
                # FIX: Already captured correctly with r=row, bt=bridge_type
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
    
    def _add_de_result_to_table(self, name, desc, rate, streak, bridge_type="ĐỀ"):
        """Thêm kết quả cầu Đề vào bảng với thông tin type chính xác."""
        # Store actual bridge type in hidden data
        item_id = self.results_tree.insert(
            "", tk.END,
            values=("ĐỀ", name, desc, rate, str(streak), "❌ Chưa"),
            tags=("new", bridge_type)  # Store bridge_type as tag for retrieval
        )
        self.results_tree.tag_configure("new", background="#e3f2fd")
    
    # ==================== NORMALIZATION HELPERS ====================
    
    def _normalize_selection_rows(self, selected_items):
        """
        Normalize bridge data from tree selection for DB insertion.
        
        This helper extracts and normalizes bridge attributes from tree view rows,
        handling various data formats and ensuring required fields are present.
        
        Args:
            selected_items: List of tree item IDs
            
        Yields:
            Dict with normalized bridge attributes:
                - name: str (required, stripped)
                - description: str
                - display_type: str (e.g., "LÔ_V17", "ĐỀ")
                - db_type: str (mapped type for DB, e.g., "LO_POS", "DE_SET")
                - win_rate_text: str
                - is_already_added: bool
                - tree_item: item ID for UI update
                
        Example:
            >>> for normalized in self._normalize_selection_rows(selected):
            ...     if not normalized["is_already_added"]:
            ...         add_managed_bridge(**normalized)
        """
        for item in selected_items:
            values = self.results_tree.item(item, "values")
            
            # Check if already added
            if len(values) > 5 and values[5] == "✅ Rồi":
                yield {
                    "is_already_added": True,
                    "name": values[1] if len(values) > 1 else None,
                    "tree_item": item
                }
                continue
            
            # Extract bridge info from tree columns
            # Columns: (type, name, description, scan_rate, streak, added)
            display_type = values[0] if len(values) > 0 else "UNKNOWN"
            name = values[1] if len(values) > 1 else None
            desc = values[2] if len(values) > 2 else ""
            rate = values[3] if len(values) > 3 else "N/A"
            
            # Validate and normalize name
            if not name or name == "N/A" or not str(name).strip():
                yield {
                    "is_already_added": False,
                    "name": None,
                    "error": "Invalid or missing name",
                    "tree_item": item,
                    "description": desc[:30] if desc else "N/A"
                }
                continue
            
            normalized_name = str(name).strip()
            
            # Get actual bridge type from tags (for DE bridges with specific subtypes)
            tags = self.results_tree.item(item, "tags")
            actual_bridge_type = None
            for tag in tags:
                if tag.startswith('DE_') or tag in ['DE_MEMORY', 'DE_SET', 'DE_PASCAL', 
                                                      'DE_KILLER', 'DE_DYNAMIC_K', 'DE_POS_SUM']:
                    actual_bridge_type = tag
                    break
            
            # Validate and normalize display type
            if not display_type or display_type not in ["LÔ_V17", "LÔ_BN", "LÔ_STL_FIXED", "ĐỀ"]:
                yield {
                    "is_already_added": False,
                    "name": normalized_name,
                    "error": f"Unknown type: {display_type}",
                    "tree_item": item,
                    "description": desc
                }
                continue
            
            # Map display type to DB type
            if display_type == "LÔ_V17":
                db_type = "LO_POS"
            elif display_type == "LÔ_BN":
                db_type = "LO_MEM"
            elif display_type == "LÔ_STL_FIXED":
                db_type = "LO_STL_FIXED"
            elif display_type == "ĐỀ":
                # Use actual bridge type if available, otherwise default
                db_type = actual_bridge_type if actual_bridge_type else "DE_ALGO"
            else:
                db_type = "UNKNOWN"
            
            # Yield normalized data
            yield {
                "is_already_added": False,
                "name": normalized_name,
                "description": desc,
                "display_type": display_type,
                "db_type": db_type,
                "win_rate_text": rate,
                "error": None,
                "tree_item": item,
                "tags": tags
            }
    
    # ==================== ACTION FUNCTIONS ====================
    
    def _add_selected_to_management(self):
        """
        Thêm các cầu đã chọn vào hệ thống quản lý.
        V11.4: Refactored to use normalization helper and service layer adapter.
        
        Improvements:
        - Uses _normalize_selection_rows() for consistent data extraction
        - Calls add_managed_bridge() service adapter instead of direct DB call
        - Enhanced error handling and logging
        - Maintains backward compatibility with existing UI behavior
        """
        import os
        import json
        from datetime import datetime
        import logging
        
        logger = logging.getLogger(__name__)
        
        selected = self.results_tree.selection()
        if not selected:
            messagebox.showwarning("Chưa Chọn", "Vui lòng chọn ít nhất một cầu để thêm.")
            return
        
        # Prepare log file
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        log_file = os.path.join(logs_dir, "batch_add.log")
        
        added_count = 0
        skipped_count = 0
        error_list = []
        log_entries = []
        
        # Use normalization helper to extract and validate bridge data
        for normalized in self._normalize_selection_rows(selected):
            # Handle already added bridges
            if normalized.get("is_already_added"):
                skipped_count += 1
                continue
            
            # Handle validation errors from normalization
            if normalized.get("error"):
                error_msg = f"- Cầu '{normalized.get('name') or normalized.get('description', 'N/A')[:30]}': {normalized['error']}"
                error_list.append(error_msg)
                log_entries.append({
                    "timestamp": datetime.now().isoformat(),
                    "bridge_name": normalized.get("name") or normalized.get("description", "N/A")[:30],
                    "action": "add",
                    "status": "failed",
                    "reason": normalized["error"]
                })
                continue
            
            # Extract normalized values
            name = normalized["name"]
            desc = normalized.get("description", "")
            db_type = normalized["db_type"]
            rate = normalized.get("win_rate_text", "N/A")
            item = normalized["tree_item"]
            
            try:
                # Call service layer adapter (V11.4 - NEW)
                success, msg = add_managed_bridge(
                    bridge_name=name,
                    description=desc,
                    bridge_type=db_type,
                    win_rate_text=rate,
                    db_name=self.db_name,
                    pos1_idx=-2,  # Special marker for scanner-added bridges
                    pos2_idx=-2,
                    search_rate_text=rate,
                    is_enabled=1
                )
                
                logger.info(f"add_managed_bridge returned: success={success}, msg={msg}")
                
                if success:
                    # Update table to mark as added
                    # Need to get current values again
                    current_values = self.results_tree.item(item, "values")
                    self.results_tree.item(item, values=(
                        current_values[0], current_values[1], current_values[2], 
                        current_values[3], current_values[4], "✅ Rồi"
                    ))
                    self.results_tree.item(item, tags=("added",))
                    added_count += 1
                    log_entries.append({
                        "timestamp": datetime.now().isoformat(),
                        "bridge_name": name,
                        "bridge_type": db_type,
                        "action": "add",
                        "status": "success",
                        "message": msg
                    })
                else:
                    # Bridge already exists or other error
                    if "đã tồn tại" in msg.lower() or "already exists" in msg.lower():
                        # Mark as added anyway
                        current_values = self.results_tree.item(item, "values")
                        self.results_tree.item(item, values=(
                            current_values[0], current_values[1], current_values[2], 
                            current_values[3], current_values[4], "✅ Rồi"
                        ))
                        self.results_tree.item(item, tags=("added",))
                        skipped_count += 1
                        log_entries.append({
                            "timestamp": datetime.now().isoformat(),
                            "bridge_name": name,
                            "bridge_type": db_type,
                            "action": "add",
                            "status": "skipped",
                            "reason": "Already exists"
                        })
                    else:
                        error_list.append(f"- Cầu '{name}': {msg}")
                        log_entries.append({
                            "timestamp": datetime.now().isoformat(),
                            "bridge_name": name,
                            "bridge_type": db_type,
                            "action": "add",
                            "status": "failed",
                            "error": msg
                        })
            except Exception as e:
                error_msg = f"- Cầu '{name}': Lỗi thêm - {str(e)}"
                error_list.append(error_msg)
                logger.exception(f"Exception adding bridge {name}: {e}")
                log_entries.append({
                    "timestamp": datetime.now().isoformat(),
                    "bridge_name": name,
                    "action": "add",
                    "status": "failed",
                    "exception": str(e)
                })
        
        # Write logs to file
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                for entry in log_entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
        
        self.results_tree.tag_configure("added", background="#c8e6c9")
        
        # Build result message
        result_msg = []
        if added_count > 0:
            result_msg.append(f"✅ Đã thêm {added_count} cầu mới")
        if skipped_count > 0:
            result_msg.append(f"⏭️ Bỏ qua {skipped_count} cầu đã tồn tại")
        if error_list:
            result_msg.append(f"\n❌ Có {len(error_list)} lỗi:\n" + "\n".join(error_list[:5]))
            if len(error_list) > 5:
                result_msg.append(f"... và {len(error_list) - 5} lỗi khác")
        
        if result_msg:
            if error_list and added_count == 0:
                messagebox.showerror("Lỗi Thêm Cầu", "\n".join(result_msg))
            else:
                messagebox.showinfo("Kết Quả Thêm Cầu", "\n".join(result_msg))
        else:
            messagebox.showinfo("Thông Báo", "Không có cầu nào được thêm.")
        
        # Notify management tab to refresh if it exists
        if added_count > 0 and hasattr(self.app, 'bridge_management_tab'):
            self.app.bridge_management_tab.refresh_bridge_list()
    
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
