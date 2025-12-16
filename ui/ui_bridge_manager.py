# Tên file: code6/ui/ui_bridge_manager.py
# (PHIÊN BẢN V3.9.21 - FIX: TÍNH TOÁN DỰ ĐOÁN REAL-TIME ĐỂ KHẮC PHỤC LỖI N/A)

import tkinter as tk
from tkinter import messagebox, ttk
import threading

# Import Config
from logic.config_manager import SETTINGS

# Import Logic
try:
    # [FIX IMPORT] Thêm get_managed_bridges_with_prediction để tính toán nóng
    from logic.data_repository import get_managed_bridges_with_prediction
    from lottery_service import (
        add_managed_bridge,
        delete_managed_bridge,
        # get_all_managed_bridges, # Không dùng hàm thô này nữa
        # update_managed_bridge removed - now imported locally where needed
    )
except ImportError as e:
    print(f"LỖI IMPORT NGHIÊM TRỌNG tại ui_bridge_manager: {e}")
    def get_managed_bridges_with_prediction(db, current_data=None, only_enabled=False): return []
    def add_managed_bridge(n, d, w): return False, "Lỗi Import"
    def delete_managed_bridge(i): return False, "Lỗi Import"


class BridgeManagerWindow:
    """Quản lý cửa sổ Toplevel Quản lý Cầu."""

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.all_bridges_cache = []

        if (
            hasattr(self.app, "bridge_manager_window")
            and self.app.bridge_manager_window
            and self.app.bridge_manager_window.winfo_exists()
        ):
            self.app.bridge_manager_window.lift()
            return

        self.window = tk.Toplevel(self.root)
        self.window.title("Quản Lý Cầu (Bridge Manager) - K1N & Scan Check")
        self.window.geometry("1150x650")

        self.app.bridge_manager_window = self.window
        self.app.bridge_manager_window_instance = self

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)

        self.create_input_form()
        self.create_bridge_list()
        self.create_toolbar()

        self.refresh_bridge_list()

    def create_input_form(self):
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
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=40, anchor="center")

        self.tree.heading("name", text="Tên Cầu")
        self.tree.column("name", width=140, anchor=tk.W)

        self.tree.heading("desc", text="Mô Tả")
        self.tree.column("desc", width=180, anchor=tk.W)

        self.tree.heading("win_rate_k1n", text="K1N (Thực Tế)")
        self.tree.column("win_rate_k1n", width=100, anchor="center")

        self.tree.heading("win_rate_scan", text="K2N (Lúc Dò)")
        self.tree.column("win_rate_scan", width=100, anchor="center")

        self.tree.heading("status", text="Trạng Thái")
        self.tree.column("status", width=80, anchor="center")

        self.tree.heading("pinned", text="📌 Ghim")
        self.tree.column("pinned", width=60, anchor="center")

        self.tree.heading("created_at", text="Ngày Tạo")
        self.tree.column("created_at", width=100, anchor="center")

    def create_bridge_list(self):
        frame = ttk.Frame(self.window)
        frame.grid(row=1, column=0, sticky="nsew", padx=10)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        columns = ("id", "name", "desc", "win_rate_k1n", "win_rate_scan", "status", "pinned", "created_at")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
        self._setup_treeview_columns()

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", self.on_bridge_select)

        # Add controls frame for bulk operations
        controls_frame = ttk.Frame(frame)
        controls_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.delete_selected_btn = ttk.Button(controls_frame, text="Delete selected", command=self._on_delete_selected)
        self.delete_selected_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.delete_selected_btn.state(['disabled'])

        self.context_menu = tk.Menu(self.window, tearoff=0)
        self.context_menu.add_command(label="📌 Ghim/Bỏ Ghim", command=self.toggle_pin_selected_bridge)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔍 Xem Backtest 30 Ngày", command=self.run_quick_backtest)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def create_toolbar(self):
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
        """
        Tải lại danh sách cầu.
        [FIX V3.9.22] Cải thiện logic kiểm tra N/A và lấy dữ liệu nguồn.
        """
        try:
            if not hasattr(self, 'window') or not self.window.winfo_exists(): return

            # Xóa cũ
            for item in self.tree.get_children(): self.tree.delete(item)

            # 1. Lấy dữ liệu xổ số: Thử nhiều nguồn khác nhau để chắc chắn có dữ liệu
            current_data = getattr(self.app, 'all_data_ai', [])
            if not current_data and hasattr(self.app, 'controller'):
                current_data = getattr(self.app.controller, 'all_data_ai', [])

            # [FALLBACK] Nếu vẫn không có, thử load trực tiếp từ DB (Chậm hơn chút nhưng chắc chắn có)
            if not current_data:
                try:
                    from logic.data_repository import load_data_ai_from_db
                    rows, _ = load_data_ai_from_db(self.app.db_name)
                    if rows: current_data = rows
                except: pass

            # 2. Gọi hàm tính toán
            self.all_bridges_cache = get_managed_bridges_with_prediction(
                self.app.db_name,
                current_data=current_data,
                only_enabled=False
            )

            for b in self.all_bridges_cache:
                status_text = "Đang Bật" if b['is_enabled'] else "Đã Tắt"
                is_pinned = b.get('is_pinned', 0)
                pinned_text = "📌 Có" if is_pinned else "❌ Không"

                tags = []
                if not b['is_enabled']: tags.append("disabled")
                if is_pinned: tags.append("pinned")

                created_date = b.get('created_at') or b.get('date_added', 'N/A')

                # --- [FIX LOGIC HIỂN THỊ] ---
                k1n_rate = str(b.get('win_rate_text', ''))

                # Điều kiện lỏng hơn: Chấp nhận 'N/A', 'N/A ', None, rỗng
                if not k1n_rate or 'N/A' in k1n_rate:
                    pred = str(b.get('next_prediction_stl', ''))

                    if not pred or 'N/A' in pred:
                        # Nếu không có cả dự đoán -> Có thể do chưa có dữ liệu xổ số
                        k1n_rate = "Chờ dữ liệu..." if not current_data else "Không xác định"
                    else:
                        k1n_rate = f"Dự: {pred}"

                # --- SCAN RATE ---
                search_rate = b.get("search_rate_text", "")
                search_period = b.get("search_period", 0)
                if search_rate and search_rate != "0.00%":
                    k2n_display = f"{search_rate}"
                    if search_period > 0: k2n_display += f" ({search_period}kỳ)"
                else:
                    k2n_display = "-"

                self.tree.insert(
                    "", tk.END,
                    values=(
                        b['id'], b['name'], b['description'],
                        k1n_rate,
                        k2n_display,
                        status_text, pinned_text, created_date
                    ),
                    tags=tuple(tags) if tags else ()
                )

            self.tree.tag_configure("disabled", foreground="gray")
            self.tree.tag_configure("pinned", background="#fff9c4")

        except Exception as e:
            print(f"Lỗi refresh_bridge_list (Ignored): {e}")

    def on_bridge_select(self, event):
        selected_items = self.tree.selection()

        # Enable/disable bulk delete button based on selection
        if hasattr(self, 'delete_selected_btn'):
            if selected_items:
                self.delete_selected_btn.state(['!disabled'])
            else:
                self.delete_selected_btn.state(['disabled'])

        # For single selection, populate the form fields
        selected = self.tree.focus()
        if not selected: return
        values = self.tree.item(selected, "values")
        if not values: return

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[1])
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, values[2])

        # Status là cột index 5
        is_enabled = (values[5] == "Đang Bật")
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
        """
        Phase 1: Update selected bridge(s) with activation and recalculation.
        """
        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn ít nhất một cầu để cập nhật.", parent=self.window)
            return

        # Get bridge names from selected items
        bridge_names = []
        for item in selected_items:
            values = self.tree.item(item, "values")
            if values and len(values) > 1:
                bridge_names.append(values[1])  # Column 1 is bridge name

        if not bridge_names:
            messagebox.showerror("Lỗi", "Không thể lấy tên cầu từ các mục đã chọn.", parent=self.window)
            return

        # For single selection, update description and status first
        if len(selected_items) == 1:
            bridge_id = self.tree.item(selected_items[0], "values")[0]
            desc = self.desc_entry.get().strip()
            status = 1 if self.enabled_var.get() else 0

            # Update description and basic status
            try:
                from logic.db_manager import update_managed_bridge
                success, msg = update_managed_bridge(bridge_id, desc, status)
                if not success:
                    messagebox.showerror("Lỗi", msg, parent=self.window)
                    return
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể cập nhật thông tin cơ bản: {e}", parent=self.window)
                return

        # Use controller to activate and recalculate bridges in background
        if hasattr(self.app, 'controller') and self.app.controller:
            self.app.controller.execute_batch_bridge_activation(bridge_names)

            # Show feedback to user
            if len(bridge_names) == 1:
                messagebox.showinfo(
                    "Đang xử lý",
                    f"Đang kích hoạt và tính toán lại cầu '{bridge_names[0]}' trong nền.\n"
                    "Vui lòng đợi kết quả trong log.",
                    parent=self.window
                )
            else:
                messagebox.showinfo(
                    "Đang xử lý",
                    f"Đang kích hoạt và tính toán lại {len(bridge_names)} cầu trong nền.\n"
                    "Vui lòng đợi kết quả trong log.",
                    parent=self.window
                )
        else:
            messagebox.showerror("Lỗi", "Controller không khả dụng.", parent=self.window)

    def delete_selected_bridge(self):
        """
        [FIX V3] Cập nhật để hỗ trợ xóa nhiều dòng bằng cách lặp qua self.tree.selection().
        Đồng thời, đảm bảo lấy đúng bridge_id (index 0) và hiển thị thông báo kết quả chi tiết.
        """
        # 1. Lấy tất cả ID của các dòng đang chọn
        selected_items = self.tree.selection()

        if not selected_items:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn ít nhất một cầu để xóa.", parent=self.window)
            return

        num_selected = len(selected_items)

        # Tạo thông báo xác nhận dựa trên số lượng dòng được chọn
        try:
            # Bridge name nằm ở cột thứ 2 (index 1)
            first_bridge_name = self.tree.item(selected_items[0], "values")[1]
        except IndexError:
            first_bridge_name = "đã chọn"

        if num_selected == 1:
            confirm_msg = f"Bạn có chắc muốn xóa cầu '{first_bridge_name}'?"
        else:
            confirm_msg = f"Bạn có chắc muốn xóa {num_selected} cầu đã chọn?"

        if not messagebox.askyesno("Xác nhận Xóa", confirm_msg, parent=self.window):
            return

        deleted_count = 0
        failed_names = []

        # 2. LẶP QUA TẤT CẢ CÁC DÒNG ĐƯỢC CHỌN VÀ THỰC HIỆN XÓA
        for selected_item_id in selected_items:
            try:
                # Bridge ID nằm ở cột đầu tiên (index 0)
                values = self.tree.item(selected_item_id, "values")
                bridge_id = values[0]
                bridge_name = values[1]

                # Gọi hàm xóa từ service
                success, msg = delete_managed_bridge(bridge_id)

                if success:
                    deleted_count += 1
                else:
                    failed_names.append((bridge_name, msg))

            except Exception as e:
                # Ghi lại lỗi nếu không đọc được dữ liệu dòng
                failed_names.append((f"Lỗi đọc dữ liệu dòng {selected_item_id}", str(e)))

        # 3. Cập nhật giao diện và thông báo kết quả
        if deleted_count > 0:
            self.refresh_bridge_list()
            self.reset_form()

        if deleted_count == num_selected:
            messagebox.showinfo("Thành công", f"Đã xóa thành công {deleted_count} cầu.", parent=self.window)
        elif deleted_count > 0:
            error_details = "\n".join([f"- {name}: {msg}" for name, msg in failed_names])
            messagebox.showwarning("Hoàn thành có lỗi",
                                  f"Đã xóa thành công {deleted_count}/{num_selected} cầu. "
                                  f"Có {len(failed_names)} cầu không thể xóa:\n{error_details}",
                                  parent=self.window)
        elif num_selected > 0:
             error_details = "\n".join([f"- {name}: {msg}" for name, msg in failed_names])
             messagebox.showerror("Lỗi Xóa", f"Không thể xóa bất kỳ cầu nào ({num_selected} cầu). Chi tiết:\n{error_details}", parent=self.window)

    def _on_delete_selected(self):
        """Handle bulk delete of selected bridges"""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        # Collect names - name is in column index 1
        names = []
        for iid in selected_items:
            row = self.tree.item(iid)
            values = row.get('values') or []
            if values:
                bridge_name = values[1]  # name column
            else:
                bridge_name = iid
            names.append(bridge_name)

        confirm = messagebox.askyesno(
            "Confirm bulk delete",
            f"Bạn sắp xóa {len(names)} cầu. Hành động không thể hoàn tác. Tiếp tục?",
            parent=self.window
        )
        if not confirm:
            return

        try:
            from lottery_service import delete_managed_bridges_batch
        except Exception:
            from logic.data_repository import delete_managed_bridges_batch

        result = delete_managed_bridges_batch(names, transactional=False)

        # Remove successfully deleted rows from tree
        deleted_set = set(result.get("deleted", []))
        for iid in list(selected_items):
            row = self.tree.item(iid)
            vals = row.get('values') or []
            name = vals[1] if len(vals) > 1 else iid
            if name in deleted_set:
                try:
                    self.tree.delete(iid)
                except Exception:
                    pass

        # Show summary to user
        deleted_count = len(result.get("deleted", []))
        missing_count = len(result.get("missing", []))
        failed = result.get("failed", [])
        summary = f"Deleted: {deleted_count}. Missing: {missing_count}."
        if failed:
            summary += f" Failed: {len(failed)} (see logs)."
        messagebox.showinfo("Bulk delete result", summary, parent=self.window)

        # Audit append to file
        try:
            import json
            import time
            import os
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            entry = {
                "ts": int(time.time()),
                "user": getattr(self.app, 'current_user', 'unknown'),
                "names_count": len(names),
                "deleted": result.get("deleted", []),
                "missing": result.get("missing", []),
                "failed": result.get("failed", [])
            }
            with open(os.path.join(log_dir, "bulk_delete_audit.log"), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Failed to write audit log: {e}")

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
        is_de = bridge_name.startswith("DE_") or "Đề" in bridge_name
        if hasattr(self.app, 'controller') and self.app.controller:
            self.app.controller.trigger_bridge_backtest(bridge_name, is_de=is_de)
        else:
            messagebox.showerror("Lỗi", "Controller không khả dụng.", parent=self.window)

    def toggle_pin_selected_bridge(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Chưa chọn cầu", "Vui lòng chọn một cầu.", parent=self.window)
            return
        bridge_name = self.tree.item(selected, "values")[1]
        current_pinned = self.tree.item(selected, "values")[6]
        action_text = "bỏ ghim" if current_pinned == "📌 Có" else "ghim"
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn {action_text} cầu '{bridge_name}'?", parent=self.window):
            if hasattr(self.app, 'controller') and self.app.controller:
                def run_toggle_pin():
                    try:
                        self.app.controller.task_run_toggle_pin(bridge_name)
                        self.window.after(500, self.refresh_bridge_list)
                    except Exception as e:
                        self.window.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể {action_text}: {e}", parent=self.window))
                thread = threading.Thread(target=run_toggle_pin, daemon=True)
                thread.start()
            else:
                messagebox.showerror("Lỗi", "Controller không khả dụng.", parent=self.window)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
            try: self.context_menu.tk_popup(event.x_root, event.y_root)
            finally: self.context_menu.grab_release()