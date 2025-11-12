# Tên file: code1/ui/ui_lookup.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - TÁI CẤU TRÚC THEO MVC)
#
import tkinter as tk
from tkinter import ttk

# (ĐÃ XÓA) Bỏ import logic.lottery_service. VIEW không được truy cập Model trực tiếp.

class LookupWindow(ttk.Frame): 
    """Quản lý tab Tra Cứu Kết Quả (VIEW)."""
    
    def __init__(self, app):
        super().__init__(app.notebook, padding=10)
        
        self.app = app
        self.root = app.root
        self.controller = app.controller # Lấy tham chiếu Controller
        self.all_ky_data_list = [] # Dữ liệu Listbox (View Cache)
        
        # (SỬA) Gắn PanedWindow vào self (Frame chính)
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill=tk.BOTH, padx=0, pady=0) 

        # --- Khung trái (Listbox + Search) ---
        list_frame = ttk.Frame(paned_window, width=250)
        list_frame.pack(expand=True, fill=tk.BOTH)
        
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5), padx=2)
        
        search_label = ttk.Label(search_frame, text="Tìm kiếm (Kỳ/Ngày):")
        search_label.pack(anchor="w")
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        refresh_button = ttk.Button(search_frame, text="Làm Mới", 
                                    command=self.refresh_lookup_list)
        refresh_button.pack(side=tk.LEFT, padx=(5,0))
        
        list_label = ttk.Label(list_frame, text="Danh sách các kỳ (mới nhất ở trên):")
        list_label.pack(pady=(0, 5), anchor="w", padx=2)
        
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.list_box = tk.Listbox(list_frame, yscrollcommand=list_scrollbar.set, exportselection=False)
        list_scrollbar.config(command=self.list_box.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.list_box.pack(expand=True, fill=tk.BOTH)
        
        paned_window.add(list_frame, weight=1)

        # --- Khung phải (Chi tiết) ---
        detail_frame = ttk.Frame(paned_window, width=550)
        detail_frame.pack(expand=True, fill=tk.BOTH)
        detail_label = ttk.Label(detail_frame, text="Chi tiết kết quả:")
        detail_label.pack(pady=(0, 5))
        
        self.detail_text = tk.Text(detail_frame, wrap=tk.WORD, state=tk.DISABLED, font=('Courier New', 10))
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.config(yscrollcommand=detail_scrollbar.set)
        detail_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text.pack(expand=True, fill=tk.BOTH)
        
        paned_window.add(detail_frame, weight=3)

        # --- Logic Lọc/Tìm kiếm ---
        self.search_entry.bind("<KeyRelease>", self.on_lookup_search_change)

        # --- Nạp dữ liệu ---
        try:
            self.refresh_lookup_list() # Lời gọi đầu tiên
            self.list_box.bind("<<ListboxSelect>>", self.on_ky_selected)
        except Exception as e:
            self.app.logger.log(f"Lỗi khi mở cửa sổ tra cứu: {e}")
            self.list_box.insert(tk.END, f"Lỗi: {e}")

    # ===================================================================
    # VIEW ACTIONS (ỦY QUYỀN CHO CONTROLLER)
    # ===================================================================

    def refresh_lookup_list(self):
        """[VIEW ACTION] Ủy quyền cho Controller tải danh sách Kỳ."""
        try:
            self.controller.task_load_ky_list(self)
            self.app.logger.log("Đang tải danh sách Kỳ trong Tra Cứu...")
        except Exception as e:
             self.app.logger.log(f"Lỗi khi ủy quyền refresh_lookup_list: {e}")

    def on_lookup_search_change(self, event):
        self.filter_lookup_list()

    def filter_lookup_list(self):
        """Chỉ lọc và hiển thị dựa trên Listbox Cache (View Logic)."""
        search_term = self.search_entry.get().strip().lower()
        self.list_box.delete(0, tk.END)
        self.update_detail_text("...")
        
        if not self.all_ky_data_list: return
        
        for ky in self.all_ky_data_list:
            display_text = f"{ky[0]}   ({ky[1]} {ky[2]})"
            if search_term in display_text.lower():
                self.list_box.insert(tk.END, display_text)

    def on_ky_selected(self, event):
        """[VIEW ACTION] Lấy Kỳ đã chọn và ủy quyền cho Controller tải chi tiết."""
        if not self.detail_text: return
        try:
            widget = event.widget
            selected_indices = widget.curselection()
            if not selected_indices: return

            selected_line = widget.get(selected_indices[0])
            ma_so_ky = selected_line.split()[0]
            
            # 1. Hiển thị trạng thái tải
            self.update_detail_text(f"Đang tải chi tiết kỳ {ma_so_ky}...")

            # 2. Ủy quyền cho Controller. Controller sẽ trả về chuỗi đã định dạng.
            self.controller.task_load_ky_details(ma_so_ky, self)
            
        except Exception as e:
            self.app.logger.log(f"Lỗi on_ky_selected: {e}") 
            self.update_detail_text(f"Lỗi: {e}")

    # ===================================================================
    # VIEW CALLBACKS (CONTROLLER GỌI ĐỂ CẬP NHẬT UI)
    # ===================================================================

    def populate_ky_list(self, ky_data_list):
        """[VIEW CALLBACK] Controller gọi để điền dữ liệu Listbox."""
        self.all_ky_data_list = ky_data_list
        
        # Chỉ gọi filter, không tự động gọi ListboxSelect
        self.filter_lookup_list()
        
        if self.list_box.size() > 0:
            # Tự động chọn dòng đầu tiên
            self.list_box.select_set(0)
            self.list_box.event_generate("<<ListboxSelect>>")
            
        self.app.logger.log(f"Đã tải {len(ky_data_list)} kỳ.")

    def populate_ky_details(self, output_text):
        """[VIEW CALLBACK] Controller gọi để điền chi tiết Kỳ."""
        self.update_detail_text(output_text)
            
    def update_detail_text(self, message):
        """Hàm hỗ trợ cập nhật Text ở cửa sổ tra cứu"""
        if not self.detail_text: return
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, message)
        self.detail_text.config(state=tk.DISABLED)