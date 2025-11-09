# File: ui/ui_mini_dashboard.py - ĐÃ NÂNG CẤP VÀ SỬA LỖI HIỂN THỊ DỮ LIỆU RỖNG
import tkinter as tk
from tkinter import ttk

class MiniDashboardWindow:
    """
    Cửa sổ độc lập (luôn hiển thị) chỉ chứa Bảng Điểm Quyết Định và Lô Gan.
    """
    
    def __init__(self, app):
        self.app = app 
        self.root = app.root
        
        self.window = tk.Toplevel(self.root)
        self.window.title("🎯 Dự Đoán Nhanh (Mini Dashboard)")
        self.window.geometry("500x350")
        self.window.attributes('-topmost', True) # Luôn hiển thị trên cùng

        main_frame = ttk.Frame(self.window, padding="5")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(0, weight=1)
        
        # Khai báo các hàng trong main_frame
        main_frame.rowconfigure(0, weight=0) # Title 1
        main_frame.rowconfigure(1, weight=3) # Treeview Scores
        main_frame.rowconfigure(2, weight=0) # Title 2
        main_frame.rowconfigure(3, weight=2) # Treeview Gan
        main_frame.rowconfigure(4, weight=0) # Control Frame

        # Khai báo control_frame (HÀNG 4)
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, sticky=tk.E, padx=5, pady=5)
        control_frame.columnconfigure(0, weight=1)
        
        # --- Treeview 1: Bảng Điểm Quyết Định (Top Scores) ---
        ttk.Label(main_frame, text="1. Bảng Điểm Quyết Định (TOP 10)", font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        
        score_frame = ttk.Frame(main_frame)
        score_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=2)
        score_frame.columnconfigure(0, weight=1)
        score_frame.rowconfigure(0, weight=1)

        self.tree_scores = ttk.Treeview(score_frame, columns=('score_col', 'detail_col'), show="headings", height=8)
        self.tree_scores.heading('#0', text='Cặp số')
        self.tree_scores.heading('score_col', text='Điểm')
        self.tree_scores.heading('detail_col', text='Chi tiết (Vote, K2N, Tỷ lệ)')
        
        self.tree_scores.column('#0', width=80, minwidth=70, stretch=tk.NO)
        self.tree_scores.column('score_col', width=40, minwidth=30, stretch=tk.NO, anchor='center')
        self.tree_scores.column('detail_col', width=300, minwidth=150, stretch=tk.YES)
        
        self.tree_scores.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # --- Treeview 2: Lô Gan (Gan Lô Warning) ---
        ttk.Label(main_frame, text="2. Cảnh Báo Lô Gan > 15 Kỳ", font=('TkDefaultFont', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, padx=2, pady=5)
        
        gan_frame = ttk.Frame(main_frame)
        gan_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=2)
        gan_frame.columnconfigure(0, weight=1)
        gan_frame.rowconfigure(0, weight=1)
        
        self.tree_gan = ttk.Treeview(gan_frame, columns=('days_col'), show="headings", height=5)
        self.tree_gan.heading('#0', text='Lô Gan')
        self.tree_gan.heading('days_col', text='Số Kỳ Gan')
        
        self.tree_gan.column('#0', width=100, minwidth=80, stretch=tk.NO)
        self.tree_gan.column('days_col', width=100, minwidth=80, stretch=tk.YES, anchor='center')
        
        self.tree_gan.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # --- Nút mở Dashboard chi tiết ---
        self.open_dashboard_button = ttk.Button(control_frame, 
                                            text="Mở Bảng Tổng Hợp Chi Tiết", 
                                            command=self.app.run_decision_dashboard)
        self.open_dashboard_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # --- Styles for data ---
        self.tree_scores.tag_configure('gan_warning', foreground='#E65C00', font=('TkDefaultFont', 9, 'italic'))
        self.tree_scores.bind("<Double-1>", self.on_double_click)


    def clear_data(self):
        """Xóa toàn bộ dữ liệu trong cả 2 Treeview."""
        for item in self.tree_scores.get_children():
            self.tree_scores.delete(item)
        for item in self.tree_gan.get_children():
            self.tree_gan.delete(item)

    def populate_data(self, top_scores, gan_stats):
        """Điền dữ liệu vào 2 Treeview tối giản."""
        self.clear_data()

        # 1. Điền Bảng Điểm Quyết Định
        if top_scores:
            for item in top_scores[:10]: # Top 10
                pair = item['pair']
                score = item['score']
                reasons_str = item['reasons'] 
                is_gan = item['is_gan']
                gan_days = item['gan_days']
                
                # Bổ sung: Hiển thị tóm tắt lý do
                vote_count = reasons_str.count("Dự Đoán") # Số Vote
                is_hot = "Loto Hot" in reasons_str
                is_rate = "Cầu" in reasons_str # T.Lệ
                is_k2n = "K2N" in reasons_str
                
                details = f"Điểm: {score} | Vote: {vote_count}"
                if is_hot:
                    details += " | 🔥 Hot"
                if is_rate:
                    details += " | T.Lệ"
                if is_k2n:
                    details += " | K2N"
                
                tags_to_apply = ()
                if is_gan:
                    details += f" | 🚧 Gan {gan_days} kỳ"
                    tags_to_apply = ('gan_warning',) 
                
                self.tree_scores.insert("", "end", text=pair, 
                                values=(score, details),
                                tags=tags_to_apply) 
        else:
            # <<< HIỂN THỊ KHI RỖNG >>>
            self.tree_scores.insert("", "end", text="(Chưa có cặp nào đạt điểm)", 
                                    values=("-", "Không có tín hiệu mạnh."))
            
        # 2. Điền Bảng Lô Gan
        if gan_stats:
            for loto, days in gan_stats:
                self.tree_gan.insert("", "end", text=loto, 
                                     values=(f"{days} kỳ"))
        else:
             # <<< HIỂN THỊ KHI RỖNG >>>
            self.tree_gan.insert("", "end", text="(Không có Lô Gan > 15 kỳ)", 
                                     values=("-"))

    def set_ui_ready(self):
        """Được gọi từ luồng chính sau khi phân tích xong (để mở khóa UI)."""
        pass 

    def on_double_click(self, event):
        """Double-click vào một cặp số sẽ mở Dashboard chi tiết."""
        self.app.run_decision_dashboard()