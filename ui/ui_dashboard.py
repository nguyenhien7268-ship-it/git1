import tkinter as tk
from tkinter import ttk, messagebox
import re # Cần import re để định nghĩa font
import traceback # (MỚI) Thêm traceback để in lỗi chi tiết

class DashboardWindow:
    
    def __init__(self, app_instance):
        self.app = app_instance
        self.window = tk.Toplevel(self.app.root)
        self.window.title("Bảng Tổng Hợp Quyết Định")
        self.window.geometry("1200x700") 
        
        # Tạo các font chữ
        self.default_font = ("TkDefaultFont", 10)
        self.default_font_bold = ("TkDefaultFont", 10, "bold")
        self.header_font = ("TkDefaultFont", 12, "bold")
        self.pair_font = ("TkDefaultFont", 11, "bold")
        
        # --- (SỬA GĐ 5) Cấu trúc GUI 3 Cột ---
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.rowconfigure(1, weight=1) # Hàng 1 (danh sách) sẽ co giãn
        
        main_frame.columnconfigure(0, weight=2) # Cột 0 (Kết quả)
        main_frame.columnconfigure(1, weight=1) # Cột 1 (Bối cảnh)
        main_frame.columnconfigure(2, weight=1) # Cột 2 (Dữ liệu gốc)

        # --- Hàng 0: Tiêu đề và Nút Refresh ---
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=5)
        
        self.title_label = ttk.Label(title_frame, text="Bảng Tổng Hợp: [CHƯA CẬP NHẬT]", font=self.header_font)
        self.title_label.pack(side=tk.LEFT, anchor="w")
        
        self.refresh_button = ttk.Button(title_frame, 
                                         text="Làm Mới Dữ Liệu", 
                                         command=self.app.run_decision_dashboard)
        self.refresh_button.pack(side=tk.RIGHT, anchor="e")

        # --- Cột 0: Bảng Chấm Điểm (Kết quả) ---
        frame_scores = ttk.Labelframe(main_frame, text="Bảng Chấm Điểm Tổng Lực (Kết Quả)")
        frame_scores.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self.tree_scores = self._create_treeview(
            frame_scores, 
            columns=("Hạng", "Cặp Số", "Điểm", "Lý Do Chấm Điểm"),
            widths=(40, 70, 50, 250)
        )
        self.tree_scores.tag_configure('top1', background='#FFFFE0', font=self.default_font_bold)
        self.tree_scores.tag_configure('top3', background='#FFFFE0')
        self.tree_scores.tag_configure('gan', foreground='red')
        self.tree_scores.tag_configure('gan_hot', background='#FFECEC', foreground='red')
        
        # --- Cột 1: Bối cảnh (Hot/Gan) ---
        context_frame = ttk.Frame(main_frame)
        context_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 5))
        context_frame.rowconfigure(0, weight=1)
        context_frame.rowconfigure(1, weight=1)
        context_frame.columnconfigure(0, weight=1)

        # Cột 1a: Loto Về Nhiều
        frame_hot = ttk.Labelframe(context_frame, text="Loto Về Nhiều (7 Ngày)")
        frame_hot.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        self.tree_hot = self._create_treeview(
            frame_hot, 
            columns=("Loto", "Nháy", "Số Kỳ"),
            widths=(60, 50, 50)
        )
        self.tree_hot.tag_configure('top3', background='#FFFFE0') # Vàng nhạt

        # Cột 1b: Lô Gan
        frame_gan = ttk.Labelframe(context_frame, text="Lô Gan (Trên 15 Ngày)")
        frame_gan.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        self.tree_gan = self._create_treeview(
            frame_gan, 
            columns=("Loto", "Số Ngày Gan"),
            widths=(60, 80)
        )
        self.tree_gan.tag_configure('gan', foreground='red')

        # --- Cột 2: Dữ liệu gốc (Vote/Cầu) ---
        data_frame = ttk.Frame(main_frame)
        data_frame.grid(row=1, column=2, sticky="nsew", padx=(5, 0))
        data_frame.rowconfigure(0, weight=1)
        data_frame.rowconfigure(1, weight=1)
        data_frame.columnconfigure(0, weight=1)

        # Cột 2a: Cặp Số "Vote" Cao
        frame_consensus = ttk.Labelframe(data_frame, text="Cặp Số Được Vote Nhiều Nhất")
        frame_consensus.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        self.tree_consensus = self._create_treeview(
            frame_consensus, 
            columns=("Cặp Số", "Số Vote", "Nguồn Cầu"),
            widths=(80, 60, 150)
        )
        self.tree_consensus.tag_configure('top3', background='#FFFFE0') # Vàng nhạt

        # Cột 2b: Cầu Tỷ Lệ Cao & K2N
        frame_bridges = ttk.Labelframe(data_frame, text="Dự Đoán Từ Các Cầu Tốt Nhất")
        frame_bridges.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        self.tree_high_win = self._create_treeview(
            frame_bridges, 
            columns=("Tên Cầu (Double-click để xem)", "STL", "Tỷ Lệ/Chuỗi"),
            widths=(200, 70, 100) # (SỬA LỖI) Tăng độ rộng cột 3
        )
        self.tree_high_win.tag_configure('header', font=self.default_font_bold, background='#F0F0F0')
        self.tree_high_win.tag_configure('italic', font=(self.default_font[0], self.default_font[1], 'italic'))
        self.tree_high_win.tag_configure('high_win', background='#FFFFE0') # Vàng nhạt
        self.tree_high_win.tag_configure('k2n', background='#E0FFF0') # Xanh lá nhạt
        self.tree_high_win.tag_configure('separator', font=self.default_font_bold, background='#E0E0E0')
        self.tree_high_win.tag_configure('memory_bridge', background='#E0F0FF') # Xanh nhạt
        
        self.tree_high_win.bind("<Double-1>", self.on_bridge_double_click)
        
        
    def _create_treeview(self, parent, columns, widths):
        """Hàm nội bộ tạo Treeview chuẩn."""
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=5)
        tree.grid(row=0, column=0, sticky="nsew")
        
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor=tk.W)
            
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        return tree

    def clear_data(self):
        """Xóa toàn bộ dữ liệu cũ trên Treeviews."""
        all_trees = [self.tree_hot, self.tree_consensus, self.tree_gan, self.tree_high_win, self.tree_scores]
        for tree in all_trees:
            for item in tree.get_children():
                tree.delete(item)

    def populate_data(self, next_ky, stats_n_day, n_days_stats, consensus, high_win, pending_k2n_data, gan_stats, top_scores, top_memory_bridges):
        """
        (SỬA LỖI GĐ 4) Bơm dữ liệu vào các bảng (đã sửa logic K2N).
        """
        self.clear_data()
        self.title_label.config(text=f"Bảng Tổng Hợp Quyết Định (Dự đoán cho {next_ky})")
        
        try:
            # --- 1. Loto Về Nhiều ---
            self.tree_hot.heading("Loto", text=f"Loto ({n_days_stats} Ngày)")
            if not stats_n_day:
                self.tree_hot.insert("", tk.END, values=("(Không có dữ liệu)", "", ""))
            
            for i, (loto, nhay, ky) in enumerate(stats_n_day[:15]): # Hiển thị Top 15
                tags = ()
                if i < 3:
                    tags = ('top3',)
                self.tree_hot.insert("", tk.END, values=(loto, nhay, ky), tags=tags)

            # --- 2. Cặp Số Vote Cao ---
            if not consensus:
                self.tree_consensus.insert("", tk.END, values=("(Không có dữ liệu)", "", ""))
                
            for i, (pair, count, sources) in enumerate(consensus[:15]): # Hiển thị Top 15
                tags = ()
                if i < 3:
                    tags = ('top3',)
                self.tree_consensus.insert("", tk.END, values=(pair, count, sources), tags=tags)

            # --- 3. Lô Gan ---
            self.tree_gan.heading("Loto", text=f"Lô Gan (>{n_days_stats} Ngày)")
            if not gan_stats:
                self.tree_gan.insert("", tk.END, values=("(Không có lô gan)", ""), tags=('italic',))
            
            for loto, days in gan_stats:
                self.tree_gan.insert("", tk.END, values=(loto, f"{days} ngày"), tags=('gan',))

            # --- 4. Cầu Tỷ Lệ Cao (V17 Đã lưu) ---
            self.tree_high_win.insert("", tk.END, values=("--- CẦU TỶ LỆ CAO (V17 ĐÃ LƯU) ---", "---", "---"), tags=('header',))
            if not high_win:
                self.tree_high_win.insert("", tk.END, values=("(Không có cầu V17 nào > 47%)", "", ""), tags=('italic',))
            
            for bridge in high_win:
                stl_str = f"{bridge['stl'][0]},{bridge['stl'][1]}"
                self.tree_high_win.insert(
                    "", tk.END, 
                    values=(bridge['name'], stl_str, bridge['rate']), 
                    tags=('high_win',) 
                )
            
            # --- (MỚI) 4B. Cầu Bạc Nhớ (Top 5) ---
            if top_memory_bridges:
                self.tree_high_win.insert(
                    "", tk.END, 
                    values=("--- CẦU BẠC NHỚ (TOP 5) ---", "---", "---"), 
                    tags=('separator',) # Dùng tag để tô đậm
                )
                
                for bridge in top_memory_bridges:
                    stl_str = f"{bridge['stl'][0]},{bridge['stl'][1]}"
                    self.tree_high_win.insert(
                        "", tk.END, 
                        values=(bridge['name'], stl_str, bridge['rate']), 
                        tags=('memory_bridge',) # Thêm 1 tag riêng
                    )

            # --- 5. Cầu K2N Đang Chờ ---
            self.tree_high_win.insert("", tk.END, values=("--- CẦU ĐANG CHỜ K2N ---", "---", "---"), tags=('header',))
            if not pending_k2n_data:
                self.tree_high_win.insert("", tk.END, values=("(Không có cầu nào chờ K2N)", "", ""), tags=('italic',))
            
            # (SỬA LỖI) Cập nhật logic để hiển thị chuỗi thắng VÀ chuỗi thua max
            for bridge_name, data in pending_k2n_data.items():
                # Lấy dữ liệu an toàn
                stl = data.get('stl', 'Lỗi')
                streak_str = data.get('streak', '0 khung')
                max_lose = data.get('max_lose', 0)
                
                # Tạo chuỗi hiển thị mới
                streak_info = f"{streak_str} (Thua max: {max_lose})"
                
                self.tree_high_win.insert(
                    "", tk.END, 
                    values=(bridge_name, stl, streak_info), 
                    tags=('k2n',)
                )

            # --- 6. Bảng Chấm Điểm ---
            if not top_scores:
                self.tree_scores.insert("", tk.END, values=("", "(Không có cặp nào đạt điểm)", "", ""), tags=('italic',))

            for i, item in enumerate(top_scores[:15]): # Hiển thị Top 15
                tags = ()
                if i == 0:
                    tags = ('top1',)
                elif i < 3:
                    tags = ('top3',)
                
                if item['is_gan']:
                    if 'Loto Hot' in item['reasons']:
                         tags = ('gan_hot',) # Vừa gan vừa hot
                    else:
                         tags = ('gan',) # Chỉ gan
                
                self.tree_scores.insert(
                    "", tk.END, 
                    values=(f"#{i+1}", item['pair'], item['score'], item['reasons']), 
                    tags=tags
                )
                
        except Exception as e:
            messagebox.showerror("Lỗi Populate Data", f"Lỗi khi hiển thị dữ liệu Bảng Tổng Hợp:\n{e}", parent=self.window)
            print(traceback.format_exc())

    def on_bridge_double_click(self, event):
        """Xử lý sự kiện double-click trên cây cầu."""
        try:
            item_id = self.tree_high_win.focus()
            if not item_id: return
            
            item_values = self.tree_high_win.item(item_id, 'values')
            if not item_values: return
            
            bridge_name = item_values[0]
            
            # Bỏ qua các dòng tiêu đề hoặc dòng trống
            if bridge_name.startswith("---") or bridge_name.startswith("("):
                return
                
            # Gửi tên cầu về app chính để xử lý
            self.app.trigger_bridge_backtest(bridge_name)
            
        except Exception as e:
            messagebox.showerror("Lỗi Double-Click", f"Lỗi xử lý click: {e}", parent=self.window)