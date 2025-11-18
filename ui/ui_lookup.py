# Tên file: git3/ui/ui_lookup.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - SỬA E741, E226)
#
import tkinter as tk
from tkinter import ttk

# Import các hàm logic cần thiết
try:
    from lottery_service import (
        calculate_loto_stats,
        get_all_kys_from_db,
        get_results_by_ky,
        getAllLoto_V30,
    )
except ImportError:
    print("LỖI: ui_lookup.py không thể import lottery_service.")

    def get_all_kys_from_db():
        return []

    def get_results_by_ky(k):
        return None

    def getAllLoto_V30(r):
        return []

    # Sửa E741: đổi l thành loto_list
    def calculate_loto_stats(loto_list):
        return {}, {}


class LookupWindow(ttk.Frame):  # (SỬA) Kế thừa từ ttk.Frame
    """Quản lý tab Tra Cứu Kết Quả."""

    def __init__(self, app):
        # (SỬA) Khởi tạo Frame
        super().__init__(app.notebook, padding=10)

        self.app = app
        self.root = app.root
        self.all_ky_data_list = []  # Dữ liệu cache

        # (SỬA) Gắn PanedWindow vào self (Frame chính)
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill=tk.BOTH, padx=0, pady=0)  # Xóa padx/pady

        # --- Khung trái (Listbox + Search) ---
        list_frame = ttk.Frame(paned_window, width=250)
        list_frame.pack(expand=True, fill=tk.BOTH)

        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5), padx=2)

        search_label = ttk.Label(search_frame, text="Tìm kiếm (Kỳ/Ngày):")
        search_label.pack(anchor="w")
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        refresh_button = ttk.Button(
            search_frame, text="Làm Mới", command=self.refresh_lookup_list
        )
        refresh_button.pack(side=tk.LEFT, padx=(5, 0))

        list_label = ttk.Label(list_frame, text="Danh sách các kỳ (mới nhất ở trên):")
        list_label.pack(pady=(0, 5), anchor="w", padx=2)

        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.list_box = tk.Listbox(
            list_frame, yscrollcommand=list_scrollbar.set, exportselection=False
        )
        list_scrollbar.config(command=self.list_box.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.list_box.pack(expand=True, fill=tk.BOTH)

        paned_window.add(list_frame, weight=1)

        # --- Khung phải (Chi tiết) ---
        detail_frame = ttk.Frame(paned_window, width=550)
        detail_frame.pack(expand=True, fill=tk.BOTH)
        detail_label = ttk.Label(detail_frame, text="Chi tiết kết quả:")
        detail_label.pack(pady=(0, 5))

        self.detail_text = tk.Text(
            detail_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Courier New", 10)
        )
        detail_scrollbar = ttk.Scrollbar(
            detail_frame, orient=tk.VERTICAL, command=self.detail_text.yview
        )
        self.detail_text.config(yscrollcommand=detail_scrollbar.set)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text.pack(expand=True, fill=tk.BOTH)

        paned_window.add(detail_frame, weight=3)

        # --- Logic Lọc/Tìm kiếm ---
        self.search_entry.bind("<KeyRelease>", self.on_lookup_search_change)

        # --- Nạp dữ liệu ---
        try:
            self.refresh_lookup_list()
            self.list_box.bind("<<ListboxSelect>>", self.on_ky_selected)
            if self.list_box.size() > 0:
                self.list_box.select_set(0)
                self.list_box.event_generate("<<ListboxSelect>>")
        except Exception as e:
            # (SỬA) Gọi qua logger
            self.app.logger.log(f"Lỗi khi mở cửa sổ tra cứu: {e}")
            self.list_box.insert(tk.END, f"Lỗi: {e}")

    def refresh_lookup_list(self):
        """Tải lại toàn bộ dữ liệu cho Listbox Tra Cứu."""
        try:
            self.all_ky_data_list = get_all_kys_from_db()
            if not self.all_ky_data_list:
                self.list_box.delete(0, tk.END)
                self.list_box.insert(tk.END, "Lỗi: Không tìm thấy dữ liệu.")
                return

            self.filter_lookup_list()

            if self.list_box.size() > 0:
                self.list_box.select_set(0)
                self.list_box.event_generate("<<ListboxSelect>>")

            # (SỬA) Gọi qua logger
            self.app.logger.log("Đã làm mới danh sách Kỳ trong Tra Cứu.")
        except Exception as e:
            self.app.logger.log(f"Lỗi refresh_lookup_list: {e}")

    def on_lookup_search_change(self, event):
        self.filter_lookup_list()

    def filter_lookup_list(self):
        """Chỉ lọc và hiển thị, không tải lại DB."""
        search_term = self.search_entry.get().strip().lower()
        self.list_box.delete(0, tk.END)
        self.update_detail_text("...")

        if not self.all_ky_data_list:
            return

        for ky in self.all_ky_data_list:
            # CSDL V6 (db_manager) chỉ trả về 2 cột: ky[0] (Kỳ) và ky[1] (Ngày)
            display_text = f"{ky[0]}   ({ky[1]})"

            if search_term in display_text.lower():
                self.list_box.insert(tk.END, display_text)

    def on_ky_selected(self, event):
        """Hiển thị chi tiết kỳ (Đã căn chỉnh)."""
        if not self.detail_text:
            return
        try:
            widget = event.widget
            selected_indices = widget.curselection()
            if not selected_indices:
                return

            selected_line = widget.get(selected_indices[0])
            ma_so_ky = selected_line.split()[0]

            row = get_results_by_ky(ma_so_ky)
            if not row:
                self.update_detail_text(
                    f"Không tìm thấy dữ liệu chi tiết cho kỳ: {ma_so_ky}"
                )
                return

            # logic get_results_by_ky (V6) trả về 38 cột (results_A_I)
            # Cột 0=id, 1=ky, 2=date, 3-10=giải, 11-37=lô
            if len(row) < 38:
                self.update_detail_text(
                    f"Lỗi: Dữ liệu kỳ {ma_so_ky} không đủ 38 cột (chỉ có {len(row)})."
                )
                return

            loto_list = getAllLoto_V30(row)
            dau_stats, duoi_stats = calculate_loto_stats(loto_list)

            output = f"KẾT QUẢ KỲ: {ma_so_ky}\n"
            output += "=" * 46 + "\n\n"
            giai_ten = ["Đặc Biệt", "Nhất", "Nhì", "Ba", "Bốn", "Năm", "Sáu", "Bảy"]
            LABEL_WIDTH, NUMBER_WIDTH = 10, 33

            for i in range(len(giai_ten)):
                giai_name = giai_ten[i].ljust(LABEL_WIDTH)
                # Dữ liệu giải bắt đầu từ index 3 (gdb)
                giai_data_str = str(row[i + 3] or "")
                numbers = [n.strip() for n in giai_data_str.split(",") if n.strip()]
                num_count = len(numbers)

                if num_count == 0:
                    output += f"{giai_name} : {''.center(NUMBER_WIDTH)}\n"
                elif num_count <= 3:
                    line_str = " - ".join(numbers)
                    output += f"{giai_name} : {line_str.center(NUMBER_WIDTH)}\n"
                elif num_count == 4:
                    line1_str, line2_str = " - ".join(numbers[:2]), " - ".join(
                        numbers[2:]
                    )
                    output += f"{giai_name} : {line1_str.center(NUMBER_WIDTH)}\n"
                    output += (
                        f"{''.ljust(LABEL_WIDTH)} : {line2_str.center(NUMBER_WIDTH)}\n"
                    )
                elif num_count == 6:
                    line1_str, line2_str = " - ".join(numbers[:3]), " - ".join(
                        numbers[3:]
                    )
                    output += f"{giai_name} : {line1_str.center(NUMBER_WIDTH)}\n"
                    output += (
                        f"{''.ljust(LABEL_WIDTH)} : {line2_str.center(NUMBER_WIDTH)}\n"
                    )
                else:
                    output += f"{giai_name} : {" - ".join(numbers)}\n"

            output += "\n" + "=" * 46 + "\n"
            output += "THỐNG KÊ LOTO (Đầu - Đuôi)\n"
            output += "-" * 46 + "\n"
            COL_DAU_W, COL_LOTO_W, COL_DUOI_W = 3, 12, 4
            output += f"{'Đầu'.ljust(COL_DAU_W)} | {'Loto'.ljust(COL_LOTO_W)} | {'Đuôi'.ljust(COL_DUOI_W)} | {'Loto'.ljust(COL_LOTO_W)}\n"
            output += f"{'-' * COL_DAU_W} | {'-' * COL_LOTO_W} | {'-' * COL_DUOI_W} | {'-' * COL_LOTO_W}\n"

            for i in range(10):
                dau_val_str = ",".join(dau_stats[i])
                duoi_val_str = ",".join(duoi_stats[i])
                # Sửa E226: Thêm khoảng trắng
                output += f"{str(i).ljust(COL_DAU_W)} | {dau_val_str.ljust(COL_LOTO_W)} | {str(i).ljust(COL_DUOI_W)} | {duoi_val_str.ljust(COL_LOTO_W)}\n"

            self.update_detail_text(output)
        except Exception as e:
            self.app.logger.log(f"Lỗi on_ky_selected: {e}")
            self.update_detail_text(f"Lỗi: {e}")

    def update_detail_text(self, message):
        """Hàm hỗ trợ cập nhật Text ở cửa sổ tra cứu"""
        if not self.detail_text:
            return
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, message)
        self.detail_text.config(state=tk.DISABLED)
