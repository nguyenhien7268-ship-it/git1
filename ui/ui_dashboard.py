# File: ui/ui_dashboard.py
import tkinter as tk
from tkinter import ttk

class DashboardWindow:
    """
    (MỚI) Quản lý cửa sổ Bảng Tổng Hợp Quyết Định (Tương tác).
    Thay thế cho cửa sổ tk.Text tĩnh.
    """
    
    def __init__(self, app):
        self.app = app # Tham chiếu đến app chính (ui_main_window)
        self.root = app.root
        
        self.window = tk.Toplevel(self.root)
        self.window.title("Bảng Tổng Hợp Quyết Định (Tương tác)")
        self.window.geometry("800x600")

        frame = ttk.Frame(self.window, padding="5")
        frame.pack(expand=True, fill=tk.BOTH)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        # --- Tạo Treeview ---
        cols = ('#0', 'col_detail', 'col_source') # 3 cột: Tên, Chi tiết, Nguồn (ẩn)
        self.tree = ttk.Treeview(frame, columns=('col_detail', 'col_source'), show="tree headings")
        
        # Cột #0 (Cột chính, dạng cây)
        self.tree.heading('#0', text='Hạng mục')
        self.tree.column('#0', width=300, minwidth=200, stretch=tk.YES)
        
        # Cột 1 (Chi tiết)
        self.tree.heading('col_detail', text='Chi tiết')
        self.tree.column('col_detail', width=400, minwidth=250, stretch=tk.YES)
        
        # Cột 2 (Nguồn - Dùng để lưu dữ liệu ẩn cho double-click)
        self.tree.heading('col_source', text='Nguồn (Ẩn)')
        self.tree.column('col_source', width=0, minwidth=0, stretch=tk.NO) # Ẩn cột này
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # --- Scrollbar ---
        yscroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        yscroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=yscroll.set)

        # --- Style ---
        self.tree.tag_configure('section_header', font=('TkDefaultFont', 10, 'bold'), background='#E0E0E0')
        self.tree.tag_configure('clickable', foreground='blue') # (MỚI) Tag cho các dòng có thể nhấn
        # (SỬA) Thêm tag cho cảnh báo Lô Gan
        self.tree.tag_configure('gan_warning', foreground='#E65C00', font=('TkDefaultFont', 9, 'italic'))

        
        # (MỚI) Gán sự kiện Double-Click
        self.tree.bind("<Double-1>", self.on_double_click)

    def clear_data(self):
        """(MỚI) Xóa toàn bộ dữ liệu cũ trong Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def populate_data(self, next_ky, stats, n_days, consensus, high_win, pending_k2n, gan_stats, top_scores): # (SỬA) Thêm top_scores
        """
        (CẬP NHẬT) Bơm dữ liệu thô (đã phân tích) vào Treeview.
        Thêm gan_stats và top_scores.
        """
        self.clear_data() # Xóa dữ liệu cũ trước
        self.window.title(f"Bảng Tổng Hợp Quyết Định - Dự đoán cho {next_ky}")
        
        # --- (SỬA) MỤC 0: BẢNG ĐIỂM QUYẾT ĐỊNH ---
        iid_0 = "top_scores"
        self.tree.insert("", "end", iid=iid_0, text=f"🏆 0. BẢNG ĐIỂM QUYẾT ĐỊNH (TOP 10)", tags=('section_header',))
        if top_scores:
            for item in top_scores[:10]: # Lấy Top 10
                pair = item['pair']
                score = item['score']
                reasons = item['reasons']
                is_gan = item['is_gan']
                gan_days = item['gan_days']
                
                details = f"Điểm: {score} | {reasons}"
                tags_to_apply = ()
                
                if is_gan:
                    details += f" | 🚧 CẢNH BÁO: LÔ GAN {gan_days} KỲ"
                    tags_to_apply = ('gan_warning',) # Thêm tag
                
                self.tree.insert(iid_0, "end", text=f"  - Cặp {pair}", 
                                 values=(details, "top_score"),
                                 tags=tags_to_apply) # Áp dụng tag
        else:
            self.tree.insert(iid_0, "end", text="  (Không có cặp nào đạt điểm)")
        self.tree.item(iid_0, open=True) # Mặc định mở
        
        # --- Mục 1: Loto Về Nhiều ---
        iid_1 = "stats_n_day"
        self.tree.insert("", "end", iid=iid_1, text=f"1. LOTO VỀ NHIỀU ({n_days} KỲ GẦN NHẤT)", tags=('section_header',))
        if stats:
            for loto, count_nhay, count_ky in stats[:10]:
                self.tree.insert(iid_1, "end", text=f"  - Loto {loto}", 
                                 values=(f"{count_nhay} lần (xuất hiện {count_ky}/{n_days} kỳ)", "stats"))
        else:
            self.tree.insert(iid_1, "end", text="  (Không có dữ liệu)")
        self.tree.item(iid_1, open=True) # Mặc định mở

        # --- Mục 2: Cặp Số Dự Đoán ---
        iid_2 = "consensus"
        self.tree.insert("", "end", iid=iid_2, text="2. CẶP SỐ ĐƯỢC DỰ ĐOÁN NHIỀU NHẤT", tags=('section_header',))
        if consensus:
            for pair, count, sources in consensus[:10]:
                self.tree.insert(iid_2, "end", text=f"  - Cặp {pair}", 
                                 values=(f"{count} phiếu (từ: {sources})", "consensus"))
        else:
            self.tree.insert(iid_2, "end", text="  (Không có dự đoán nào)")
        self.tree.item(iid_2, open=True)

        # --- Mục 3: Cầu Tỷ Lệ Cao ---
        iid_3 = "high_win"
        self.tree.insert("", "end", iid=iid_3, text="3. DÀN LÔ TỪ CẦU TỶ LỆ CAO (>=47%)", tags=('section_header',))
        if high_win:
            for bridge in high_win:
                bridge_name = bridge['name']
                self.tree.insert(iid_3, "end", text=f"  - Cặp {','.join(bridge['stl'])}", 
                                 values=(f"(Cầu '{bridge_name}' - {bridge['rate']})", bridge_name), # Lưu bridge_name vào cột ẩn
                                 tags=('clickable',)) # Đánh dấu là có thể nhấn
        else:
            self.tree.insert(iid_3, "end", text="  (Không tìm thấy cầu nào >=47% đang Bật)")
        self.tree.item(iid_3, open=True)

        # --- Mục 4: Cầu K2N Đang Chờ ---
        iid_4 = "pending_k2n"
        self.tree.insert("", "end", iid=iid_4, text="4. CÁC CẦU K2N ĐANG CHỜ NGÀY 2", tags=('section_header',))
        if pending_k2n:
            for item in pending_k2n:
                bridge_name = item['name']
                self.tree.insert(iid_4, "end", text=f"  - Cặp {item['stl']}", 
                                 values=(f"(Cầu '{bridge_name}' - Tỷ lệ: {item['rate']}, Chuỗi: {item['streak']})", bridge_name), # Lưu bridge_name vào cột ẩn
                                 tags=('clickable',)) # Đánh dấu là có thể nhấn
        else:
            self.tree.insert(iid_4, "end", text="  (Không có cầu K2N nào đang chờ N2)")
        self.tree.item(iid_4, open=True)
        
        # --- (MỚI) Mục 5: Thống Kê Lô Gan ---
        iid_5 = "gan_stats"
        n_days_gan = 15 # (Nên đồng bộ với main_window, nhưng tạm thời để 15)
        self.tree.insert("", "end", iid=iid_5, text=f"5. THỐNG KÊ LÔ GAN (Lớn hơn {n_days_gan} kỳ)", tags=('section_header',))
        if gan_stats:
            for loto, days in gan_stats:
                self.tree.insert(iid_5, "end", text=f"  - Loto {loto}", 
                                 values=(f"Gan {days} kỳ", "gan"))
        else:
            self.tree.insert(iid_5, "end", text=f"  (Không có loto nào gan trên {n_days_gan} kỳ)")
        self.tree.item(iid_5, open=False) # Mặc định đóng
        
        # --- Hướng dẫn ---
        iid_guide = "guide"
        self.tree.insert("", "end", iid=iid_guide, text="Ghi chú: Nhấn đúp (Double-Click) vào các dòng màu xanh để xem chi tiết backtest.", 
                         tags=('section_header',))

    def on_double_click(self, event):
        """
        (MỚI) Xử lý sự kiện nhấn đúp chuột.
        """
        try:
            selected_iid = self.tree.focus() # Lấy ID của dòng đang chọn
            if not selected_iid:
                return

            item = self.tree.item(selected_iid)
            tags = item.get('tags', [])
            
            # Chỉ xử lý nếu dòng đó có tag 'clickable'
            if 'clickable' in tags:
                values = item.get('values', [])
                if not values or len(values) < 2:
                    return
                    
                bridge_name = values[1] # Lấy bridge_name từ cột ẩn (col_source)
                
                if bridge_name:
                    self.app.update_output(f"--- Bảng Tổng Hợp: Yêu cầu xem chi tiết {bridge_name} ---")
                    # Gọi hàm trigger trên app chính
                    self.app.trigger_bridge_backtest(bridge_name)
                    
        except Exception as e:
            self.app.update_output(f"Lỗi on_double_click: {e}")