# Tên file: git3/ui/ui_bridge_manager.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA F401, W503)
#
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

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

    # Hàm giả
    def get_all_managed_bridges():
        return []

    def add_managed_bridge(n, d, w):
        return False, "Lỗi"

    def update_managed_bridge(i, d, s):
        return False, "Lỗi"

    def delete_managed_bridge(i):
        return False, "Lỗi"


class BridgeManagerWindow:
    """Quản lý cửa sổ Toplevel Quản lý Cầu."""

    def __init__(self, app):
        self.app = app
        self.root = app.root
        self.all_bridges_cache = []  # Cache

        if (
            hasattr(self.app, "bridge_manager_window")
            and self.app.bridge_manager_window
            and self.app.bridge_manager_window.winfo_exists()
        ):
            self.app.bridge_manager_window.lift()
            return

        # (SỬA LỖI V5) Thay thế self.app.update_output bằng self.app.logger.log
        self.app.logger.log("Đang mở cửa sổ Quản lý Cầu...")

        self.window = tk.Toplevel(self.root)
        self.window.title("Quản lý Cầu Đã Lưu")
        self.app.bridge_manager_window = self.window
        self.window.geometry("800x600")

        self.window.transient(self.root)
        self.window.grab_set()

        # Frame chính
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Cấu hình grid
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # 1. Danh sách (Bên trái)
        list_frame = ttk.Labelframe(main_frame, text="Danh Sách Cầu", padding=10)
        list_frame.grid(row=0, column=0, sticky="nswe", padx=(0, 5))

        # 2. Chi tiết (Bên phải)
        details_frame = ttk.Labelframe(
            main_frame, text="Chi Tiết / Thêm Mới", padding=10
        )
        details_frame.grid(row=0, column=1, sticky="nswe")
        details_frame.columnconfigure(1, weight=1)

        # --- Cây Treeview ---
        self.tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Name", "Rate", "Streak", "Prediction"),
            show="headings",
        )
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Tên Cầu")
        self.tree.heading("Rate", text="Tỷ Lệ K2N")
        self.tree.heading("Streak", text="Chuỗi")
        self.tree.heading("Prediction", text="Dự Đoán")

        self.tree.column("ID", width=40, stretch=False)
        self.tree.column("Name", width=200, stretch=True)
        self.tree.column("Rate", width=80, stretch=False)
        self.tree.column("Streak", width=60, stretch=False)
        self.tree.column("Prediction", width=70, stretch=False)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Nút Xóa
        delete_button = ttk.Button(
            list_frame, text="Xóa Cầu Đã Chọn", command=self.delete_selected_bridge
        )
        delete_button.pack(fill=tk.X, pady=(5, 0))

        # --- Form Chi Tiết ---
        ttk.Label(details_frame, text="Tên Cầu:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.name_entry = ttk.Entry(details_frame, width=40)
        self.name_entry.grid(row=0, column=1, sticky="we", pady=5)

        ttk.Label(details_frame, text="Mô Tả:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.desc_entry = ttk.Entry(details_frame, width=40)
        self.desc_entry.grid(row=1, column=1, sticky="we", pady=5)

        ttk.Label(details_frame, text="Trạng Thái:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.enabled_var = tk.BooleanVar(value=True)
        self.enabled_check = ttk.Checkbutton(
            details_frame, text="Bật (Enabled)", variable=self.enabled_var
        )
        self.enabled_check.grid(row=2, column=1, sticky="w", pady=5)

        # Nút bấm (Thêm/Cập nhật/Reset)
        button_frame = ttk.Frame(details_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky="e")

        self.reset_button = ttk.Button(
            button_frame, text="Reset Form", command=self.reset_form
        )
        self.reset_button.pack(side=tk.LEFT, padx=5)

        self.add_button = ttk.Button(
            button_frame, text="Thêm Cầu Mới", command=self.add_new_bridge
        )
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.update_button = ttk.Button(
            button_frame, text="Cập Nhật Cầu", command=self.update_selected_bridge
        )
        self.update_button.pack(side=tk.LEFT, padx=5)

        # Binding
        self.tree.bind("<<TreeviewSelect>>", self.on_bridge_select)

        self.refresh_bridge_list()
        self.reset_form()  # Đặt form ở chế độ Thêm Mới

    def refresh_bridge_list(self):
        """Tải lại danh sách cầu từ DB và hiển thị lên Treeview."""
        self.tree.delete(*self.tree.get_children())
        self.all_bridges_cache = get_all_managed_bridges()  # Lấy dict

        if not self.all_bridges_cache:
            return

        for bridge in self.all_bridges_cache:
            try:
                # (SỬA GĐ 4) Hiển thị max_lose_streak_k2n
                streak_val = bridge.get("current_streak", 0)
                max_lose_val = bridge.get("max_lose_streak_k2n", 0)
                streak_str = f"{streak_val} (L={max_lose_val})"

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        bridge["id"],
                        bridge["name"],
                        bridge.get("win_rate_text", "N/A"),
                        streak_str,
                        bridge.get("next_prediction_stl", "N/A"),
                    ),
                    tags=("enabled" if bridge["is_enabled"] else "disabled",),
                )
            except Exception as e:
                print(f"Lỗi khi chèn cầu vào treeview: {e}")

        self.tree.tag_configure("disabled", foreground="gray")
        self.tree.tag_configure("enabled", foreground="black")

    def get_selected_bridge_info(self):
        """Lấy ID và dict data của cầu đang chọn."""
        selected_item = self.tree.focus()
        if not selected_item:
            return None, None

        item = self.tree.item(selected_item)
        bridge_id = item["values"][0]

        # Tìm trong cache
        bridge_data = next(
            (b for b in self.all_bridges_cache if b["id"] == bridge_id), None
        )
        return bridge_id, bridge_data

    def delete_selected_bridge(self):
        """Xóa cầu đang chọn (sau khi xác nhận)."""
        bridge_id, bridge_data = self.get_selected_bridge_info()
        if not bridge_data:
            messagebox.showwarning(
                "Chưa chọn cầu", "Vui lòng chọn một cầu để xóa.", parent=self.window
            )
            return

        if not messagebox.askyesno(
            "Xác nhận Xóa",
            f"Bạn có chắc muốn xóa cầu:\n{bridge_data['name']}\n\nThao tác này không thể hoàn tác.",
            parent=self.window,
        ):
            return

        success, message = delete_managed_bridge(bridge_id)
        if success:
            # (SỬA LỖI V5) Thay thế self.app.update_output bằng self.app.logger.log
            self.app.logger.log(f"Đã XÓA cầu ID {bridge_id}.")
            self.refresh_bridge_list()
        else:
            # (SỬA LỖI V5) Thay thế self.app.update_output bằng self.app.logger.log
            self.app.logger.log(f"LỖI: {message}")
            messagebox.showerror("Lỗi", message, parent=self.window)

    def on_bridge_select(self, event):
        """(SỬA GĐ 4) Khi chọn cầu trong Treeview."""
        selected_item = self.tree.focus()
        if not selected_item:
            return
        item = self.tree.item(selected_item)
        values = item["values"]

        bridge_id, bridge_data = self.get_selected_bridge_info()
        if not bridge_data:
            return

        self.name_entry.config(state=tk.NORMAL)
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[1])  # Tên Cầu
        self.name_entry.config(state=tk.DISABLED)  # KHÔNG CHO SỬA TÊN

        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, bridge_data.get("description", ""))

        self.enabled_var.set(bool(bridge_data.get("is_enabled", True)))

        self.add_button.config(state=tk.DISABLED)
        self.update_button.config(state=tk.NORMAL)

    def reset_form(self):
        """Reset form về trạng thái Thêm Mới."""
        self.tree.selection_remove(self.tree.selection())  # Bỏ chọn

        self.name_entry.config(state=tk.NORMAL)
        self.name_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.enabled_var.set(True)

        self.add_button.config(state=tk.NORMAL)
        self.update_button.config(state=tk.DISABLED)

    def add_new_bridge(self):
        """Thêm cầu mới (chỉ hỗ trợ cầu bạc nhớ/tùy chỉnh)."""
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()

        if not name:
            messagebox.showwarning(
                "Thiếu Tên", "Tên cầu không được để trống.", parent=self.window
            )
            return

        # Hàm add_managed_bridge chỉ cần tên và mô tả
        success, message = add_managed_bridge(name, desc)

        if success:
            # (SỬA LỖI V5) Thay thế self.app.update_output bằng self.app.logger.log
            self.app.logger.log(message)
            self.refresh_bridge_list()
            self.reset_form()
        else:
            # (SỬA LỖI V5) Thay thế self.app.update_output bằng self.app.logger.log
            self.app.logger.log(f"Lỗi khi thêm cầu: {message}")
            messagebox.showerror("Lỗi Thêm Cầu", message, parent=self.window)

    def update_selected_bridge(self):
        """Cập nhật mô tả và trạng thái Bật/Tắt của cầu."""
        bridge_id, bridge_data = self.get_selected_bridge_info()
        if not bridge_data:
            messagebox.showwarning(
                "Chưa chọn cầu",
                "Vui lòng chọn một cầu để cập nhật.",
                parent=self.window,
            )
            return

        new_desc = self.desc_entry.get().strip()
        new_enabled = self.enabled_var.get()

        success, message = update_managed_bridge(bridge_id, new_desc, new_enabled)

        if success:
            self.refresh_bridge_list()
            self.reset_form()
        else:
            messagebox.showerror("Lỗi Cập Nhật", message, parent=self.window)
