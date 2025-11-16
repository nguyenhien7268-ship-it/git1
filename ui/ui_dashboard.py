# Tên file: code1/ui/ui_dashboard.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - TÁI CẤU TRÚC THEO MVC)
#
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import traceback

# (MỚI GĐ 4) Import thư viện biểu đồ và pandas (Giữ lại, vì đây là Presentation Logic)
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Tinh chỉnh matplotlib cho giao diện tối (hoặc sáng)
plt.style.use('ggplot') 

# (ĐÃ XÓA) Bỏ import logic.config_manager. SETTINGS sẽ được truyền từ Controller.

class DashboardWindow(ttk.Frame): 
    def __init__(self, app_instance):
        super().__init__(app_instance.notebook, padding=10)
        
        self.app = app_instance
        self.root = app_instance.root
        self.controller = app_instance.controller # Thêm tham chiếu Controller
        
        # (MỚI GĐ 4) Biến giữ đối tượng biểu đồ
        self.fig = None
        self.ax = None
        self.canvas = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1) 

        self.header_frame = ttk.Frame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        self.title_label = ttk.Label(self.header_frame, text="Đang tải...", font=('Arial', 16, 'bold'))
        self.title_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.refresh_button = ttk.Button(self.header_frame, text="Làm Mới Dữ Liệu", command=self.refresh_data)
        self.refresh_button.pack(side=tk.RIGHT)
        
        self.main_analysis_frame = ttk.Frame(self, padding=10)
        self.main_analysis_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # (SỬA GĐ 4) Cấu hình lưới 2 Cột, 4 Hàng
        self.main_analysis_frame.columnconfigure(0, weight=1) # Cột trái
        self.main_analysis_frame.columnconfigure(1, weight=1) # Cột phải
        self.main_analysis_frame.rowconfigure(0, weight=2) # Hàng 0: Bảng Điểm / AI
        self.main_analysis_frame.rowconfigure(1, weight=2) # Hàng 1: (MỚI) Biểu đồ
        self.main_analysis_frame.rowconfigure(2, weight=1) # Hàng 2: Hot / Gan
        self.main_analysis_frame.rowconfigure(3, weight=1) # Hàng 3: K2N

        # ===================================================================
        # TẠO CÁC BẢNG (Sửa đổi vị trí)
        # ===================================================================

        # 1. Bảng Chấm Điểm (Hàng 0, Cột 0)
        self._create_top_scores_ui(self.main_analysis_frame)
        self.top_scores_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 2. Dự đoán AI (Hàng 0, Cột 1)
        self._create_ai_predictions_ui(self.main_analysis_frame)
        self.ai_predictions_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 3. (MỚI) Biểu đồ Bảng Chấm Điểm (Hàng 1, Cột 0, Mở rộng 2 cột)
        self._create_scores_chart_ui(self.main_analysis_frame)
        self.scores_chart_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # 4. Loto Về Nhiều (SỬA) (Hàng 2, Cột 0)
        self._create_hot_loto_ui(self.main_analysis_frame)
        self.hot_loto_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # 5. Lô Gan (SỬA) (Hàng 2, Cột 1)
        self._create_gan_loto_ui(self.main_analysis_frame)
        self.gan_loto_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)

        # 6. Cầu K2N Đang Chờ (SỬA) (Hàng 3, Cột 0, Mở rộng 2 cột)
        self._create_pending_k2n_ui(self.main_analysis_frame)
        self.pending_k2n_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
    # ===================================================================================
    # CÁC HÀM TẠO UI 
    # ===================================================================================
    
    def _create_top_scores_ui(self, parent_frame):
        self.top_scores_frame = ttk.Labelframe(parent_frame, text="🏆 Bảng Chấm Điểm Tổng Lực (V6.2 + AI)")
        tree_frame = ttk.Frame(self.top_scores_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('score', 'pair', 'gan', 'reasons')
        self.scores_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=10) 
        self.scores_tree.heading('score', text='Điểm')
        self.scores_tree.heading('pair', text='Cặp số')
        self.scores_tree.heading('gan', text='Gan')
        self.scores_tree.heading('reasons', text='Lý do (Tích hợp AI)')
        self.scores_tree.column('score', width=50, anchor=tk.E)
        self.scores_tree.column('pair', width=60, anchor=tk.CENTER)
        self.scores_tree.column('gan', width=50, anchor=tk.CENTER)
        self.scores_tree.column('reasons', width=300)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.scores_tree.yview)
        self.scores_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scores_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scores_tree.tag_configure('gan', foreground='red')
        self.scores_tree.tag_configure('top1', background='#D5E8D4', font=('Arial', 10, 'bold'))
        self.scores_tree.tag_configure('top3', background='#FFF2CC')

    def _create_ai_predictions_ui(self, parent_frame):
        self.ai_predictions_frame = ttk.Labelframe(parent_frame, text="🧠 Dự đoán AI (Loto Đơn)")
        tree_frame = ttk.Frame(self.ai_predictions_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('loto', 'probability')
        self.ai_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=10) 
        self.ai_tree.heading('loto', text='Loto')
        self.ai_tree.heading('probability', text='Xác suất (%)')
        self.ai_tree.column('loto', width=80, anchor=tk.CENTER)
        self.ai_tree.column('probability', width=120, anchor=tk.E)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.ai_tree.yview)
        self.ai_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ai_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.ai_tree.tag_configure('top1', background='#D5E8D4', font=('Arial', 10, 'bold'))
        self.ai_tree.tag_configure('top5', background='#FFF2CC')

    def _create_scores_chart_ui(self, parent_frame):
        self.scores_chart_frame = ttk.Labelframe(parent_frame, text="📊 Biểu đồ Phân bổ Điểm (Top 5)")
        
        self.fig = plt.Figure(figsize=(10, 2.5), dpi=100) 
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.scores_chart_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fig.tight_layout(pad=0.5)

    def _create_hot_loto_ui(self, parent_frame):
        self.hot_loto_frame = ttk.Labelframe(parent_frame, text=f"🔥 Loto Về Nhiều (7 ngày)")
        tree_frame = ttk.Frame(self.hot_loto_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('loto', 'hits', 'days')
        self.hot_loto_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8) 
        self.hot_loto_tree.heading('loto', text='Loto')
        self.hot_loto_tree.heading('hits', text='Số nháy')
        self.hot_loto_tree.heading('days', text='Số kỳ')
        self.hot_loto_tree.column('loto', width=50, anchor=tk.CENTER)
        self.hot_loto_tree.column('hits', width=60, anchor=tk.E)
        self.hot_loto_tree.column('days', width=50, anchor=tk.E)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.hot_loto_tree.yview)
        self.hot_loto_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hot_loto_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_gan_loto_ui(self, parent_frame):
        self.gan_loto_frame = ttk.Labelframe(parent_frame, text=f"🧊 Lô Gan (Trên 15 ngày)")
        tree_frame = ttk.Frame(self.gan_loto_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('loto', 'days')
        self.gan_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8) 
        self.gan_tree.heading('loto', text='Loto')
        self.gan_tree.heading('days', text='Số ngày Gan')
        self.gan_tree.column('loto', width=50, anchor=tk.CENTER)
        self.gan_tree.column('days', width=100, anchor=tk.E)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.gan_tree.yview)
        self.gan_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.gan_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_pending_k2n_ui(self, parent_frame):
        self.pending_k2n_frame = ttk.Labelframe(parent_frame, text="⏳ Cầu K2N Đang Chờ (Chờ N2) - [Bổ Sung]")
        tree_frame = ttk.Frame(self.pending_k2n_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('stl', 'streak', 'max_lose', 'name')
        self.k2n_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8) 
        self.k2n_tree.heading('stl', text='Cặp số')
        self.k2n_tree.heading('streak', text='Chuỗi')
        self.k2n_tree.heading('max_lose', text='Gãy Max')
        self.k2n_tree.heading('name', text='Tên cầu')
        self.k2n_tree.column('stl', width=60, anchor=tk.CENTER)
        self.k2n_tree.column('streak', width=60, anchor=tk.CENTER)
        self.k2n_tree.column('max_lose', width=60, anchor=tk.CENTER)
        self.k2n_tree.column('name', width=300)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.k2n_tree.yview)
        self.k2n_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.k2n_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.k2n_tree.tag_configure('risk', foreground='red')
        self.k2n_tree.tag_configure('safe', foreground='green')
        self.k2n_tree.bind("<Double-1>", self.on_tree_double_click)

    # --- HÀM NẠP DỮ LIỆU ---

    def clear_data(self):
        self.title_label.config(text="Đang tải...")
        for tree in [self.scores_tree, self.hot_loto_tree, self.gan_tree, self.k2n_tree, self.ai_tree]:
            try:
                for item in tree.get_children():
                    tree.delete(item)
            except Exception as e:
                # In lỗi an toàn
                print(f"Lỗi khi xóa tree {tree.winfo_name()}: {e}")
        
        # (MỚI GĐ 4) Xóa biểu đồ
        try:
            if self.ax:
                self.ax.clear()
                self.ax.set_title("Đang tải dữ liệu biểu đồ...")
                self.canvas.draw()
        except Exception as e:
            # In lỗi an toàn
            print(f"Lỗi xóa biểu đồ: {e}")

    def populate_data(self, next_ky, stats, n_days_stats, 
                      consensus, high_win, pending_k2n, 
                      gan_stats, top_scores, top_memory_bridges,
                      ai_predictions, gan_threshold=15, risk_threshold=4): # Cập nhật signature để nhận ngưỡng
        
        try:
            self.clear_data()
            
            today = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            self.title_label.config(text=f"Bảng Quyết Định Tối Ưu - {next_ky} (Cập nhật: {today})")

            # Nạp Bảng 1: Chấm Điểm
            self._populate_top_scores(top_scores)

            # (MỚI GĐ 4) Nạp Biểu đồ
            self._populate_top_scores_chart(top_scores)

            # Nạp Bảng 2: Loto Về Nhiều
            self.hot_loto_frame.config(text=f"🔥 Loto Về Nhiều ({n_days_stats} ngày)")
            self._populate_hot_loto(stats)

            # Nạp Bảng 3: Lô Gan
            # SỬA: Dùng tham số gan_threshold được truyền vào
            self.gan_loto_frame.config(text=f"🧊 Lô Gan (Trên {gan_threshold} ngày)") 
            self._populate_gan_loto(gan_stats)

            # Nạp Bảng 4: Cầu K2N
            # SỬA: Truyền tham số risk_threshold vào hàm nạp
            self._populate_pending_k2n(pending_k2n, risk_threshold) 
            
            # Nạp Bảng 5: Dự đoán AI
            self._populate_ai_predictions(ai_predictions)
            
        except Exception as e:
            messagebox.showerror("Lỗi Nạp Dữ Liệu Dashboard", f"Lỗi chi tiết: {e}\n{traceback.format_exc()}", parent=self)
            
    # ===================================================================================
    # CÁC HÀM NẠP DỮ LIỆU CHI TIẾT
    # ===================================================================================

    def _populate_top_scores(self, top_scores):
        if not top_scores:
            self.scores_tree.insert('', tk.END, values=("N/A", "N/A", "", "Không có cặp nào"))
            return
        for i, item in enumerate(top_scores[:40]): 
            tags = ()
            if item['is_gan']: tags += ('gan',)
            if i == 0: tags += ('top1',)
            elif i < 3: tags += ('top3',)
            self.scores_tree.insert('', tk.END, values=(
                item['score'],
                item['pair'],
                f"{item['gan_days']} ngày" if item['is_gan'] else "",
                item['reasons']
            ), tags=tags)

    def _populate_top_scores_chart(self, top_scores):
        try:
            self.ax.clear() 

            if not top_scores or len(top_scores) == 0:
                self.ax.set_title("Không có dữ liệu điểm để vẽ biểu đồ")
                self.canvas.draw()
                return

            # 1. Trích xuất dữ liệu (Top 5)
            top_5_data = top_scores[:5][::-1] 
            
            pairs = [item['pair'] for item in top_5_data]
            scores = [item['score'] for item in top_5_data]
            
            # 2. Tạo DataFrame (Pandas)
            df = pd.DataFrame({'Cặp số': pairs, 'Điểm': scores})
            
            # 3. Vẽ biểu đồ (vẽ ngang - 'barh' - để dễ đọc tên)
            df.plot(kind='barh', x='Cặp số', y='Điểm', ax=self.ax, 
                    legend=False, 
                    color=['#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8', '#1e3a8a']) 

            # 4. Tinh chỉnh biểu đồ
            self.ax.set_title("Top 5 Cặp số có Điểm cao nhất", fontsize=10)
            self.ax.set_ylabel("Cặp số", fontsize=8)
            self.ax.set_xlabel("Điểm Tổng Lực", fontsize=8)
            
            # Thêm giá trị (điểm) vào cuối mỗi cột
            for index, value in enumerate(scores):
                self.ax.text(value + 0.1, index, f"{value:.2f}", va='center', fontsize=8) 
            
            self.ax.tick_params(axis='both', which='major', labelsize=8)
            self.fig.tight_layout(pad=1.0) 

            # 5. Vẽ lên canvas
            self.canvas.draw()

        except Exception as e:
            print(f"Lỗi vẽ biểu đồ: {e}")
            if self.ax:
                self.ax.set_title(f"Lỗi vẽ biểu đồ: {e}")
                self.canvas.draw()

    def _populate_hot_loto(self, stats):
        if not stats:
            self.hot_loto_tree.insert('', tk.END, values=("(N/A)", "", ""))
            return
        for loto, hits, days in stats: 
            self.hot_loto_tree.insert('', tk.END, values=(loto, hits, days))

    def _populate_gan_loto(self, gan_stats):
        if not gan_stats:
            self.gan_tree.insert('', tk.END, values=("(N/A)", "Không có lô gan"))
            return
        for loto, days in gan_stats:
            self.gan_tree.insert('', tk.END, values=(loto, f"{days} ngày"))

    def _populate_pending_k2n(self, pending_k2n, risk_threshold):
        """
        (FIX LỖI KeyError) Sửa lại các key truy cập dữ liệu để khớp với CSDL
        (ví dụ: 'stl' -> 'next_prediction_stl')
        """
        if not pending_k2n:
            self.k2n_tree.insert('', tk.END, values=("(N/A)", "", "", "Không có cầu K2N nào chờ"))
            return
        
        try:
            # (FIX) Sửa key 'streak' -> 'current_streak' và 'max_lose' -> 'max_lose_streak_k2n'
            sorted_k2n = sorted(
                pending_k2n.items(), 
                key=lambda item: (
                    int(str(item[1].get('current_streak', 0)).split(' ')[0]), 
                    -int(item[1].get('max_lose_streak_k2n', 0))
                ), 
                reverse=True
            )
        except Exception as e:
             print(f"Lỗi sắp xếp K2N (UI): {e}") # Log lỗi
             sorted_k2n = list(pending_k2n.items())
             
        items_added = 0
        for bridge_name, data in sorted_k2n:
            try:
                # (FIX) Sửa key 'stl' -> 'next_prediction_stl', 'streak' -> 'current_streak', 'max_lose' -> 'max_lose_streak_k2n'
                stl = data.get('next_prediction_stl', 'LỖI')
                streak = data.get('current_streak', 0)
                max_lose = data.get('max_lose_streak_k2n', 0)

                # Chỉ hiển thị các cầu đang chờ (streak > 0)
                if streak > 0:
                    tags = ()
                    if max_lose > risk_threshold: tags = ('risk',)
                    elif max_lose < risk_threshold: tags = ('safe',)
                    
                    self.k2n_tree.insert('', tk.END, values=(stl, f"{streak} ngày", f"{max_lose} lần", bridge_name), tags=tags)
                    items_added += 1
            
            except Exception as e_inner:
                print(f"Lỗi nạp dòng K2N (UI) {bridge_name}: {e_inner}")
        
        # Nếu sau khi lọc không có cầu nào (streak > 0), hiển thị thông báo
        if items_added == 0:
             self.k2n_tree.insert('', tk.END, values=("(N/A)", "", "", "Không có cầu K2N nào chờ"))

    def _populate_ai_predictions(self, ai_predictions):
        if not ai_predictions:
            self.ai_tree.insert('', tk.END, values=("(N/A)", "Vui lòng Huấn luyện AI"))
            return
        for i, pred in enumerate(ai_predictions[:20]):
            loto = pred['loto']
            prob = pred['probability']
            tags = ()
            if i == 0: tags = ('top1',)
            elif i < 5: tags = ('top5',)
            self.ai_tree.insert('', tk.END, values=(loto, f"{prob:.2f}%"), tags=tags)

    # ===================================================================================
    # HÀM TƯƠNG TÁC (CHỈ ỦY QUYỀN)
    # ===================================================================================
    
    def refresh_data(self):
        """[VIEW ACTION] Ủy quyền cho app chính/Controller chạy lại Dashboard."""
        self.app.logger.log("\n--- (Làm Mới) Bắt đầu chạy lại Bảng Quyết Định Tối Ưu ---")
        self.app.run_decision_dashboard() 

    def on_tree_double_click(self, event):
        try:
            item_id = event.widget.focus()
            if not item_id: return
            item = event.widget.item(item_id)
            values = item['values']
            bridge_name = ""
            
            if event.widget == self.k2n_tree: bridge_name = values[3] 
            
            if bridge_name:
                # Ủy quyền cho app chính/Controller chạy backtest
                self.app.trigger_bridge_backtest(bridge_name)
        except Exception as e:
            print(f"Lỗi double-click: {e}")