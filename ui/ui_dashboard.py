import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import traceback

try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: ui_dashboard.py không thể import logic.config_manager...")
    SETTINGS = type('obj', (object,), {'GAN_DAYS': 15, 'HIGH_WIN_THRESHOLD': 47.0, 'K2N_RISK_START_THRESHOLD': 4})

class DashboardWindow:
    def __init__(self, app_instance):
        self.app = app_instance
        self.root = app_instance.root
        
        self.window = tk.Toplevel(self.root)
        self.window.title("Bảng Quyết Định Tối Ưu (V7.0 - 4 Bảng Cốt Lõi)") # (MỚI V7.0)
        self.window.geometry("1400x900") 
        self.window.transient(self.root)
        # Đã xóa self.window.grab_set() để cửa sổ là NON-MODAL

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1) 

        self.header_frame = ttk.Frame(self.window)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        self.title_label = ttk.Label(self.header_frame, text="Đang tải...", font=('Arial', 16, 'bold'))
        self.title_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.refresh_button = ttk.Button(self.header_frame, text="Làm Mới Dữ Liệu", command=self.refresh_data)
        self.refresh_button.pack(side=tk.RIGHT)
        
        # --- Tab 1: Tổng Hợp 4 Bảng Chính (TỐI ƯU HÓA) ---
        self.main_analysis_frame = ttk.Frame(self.window, padding=10)
        self.main_analysis_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Cấu hình lưới 2x2 cho 4 bảng cốt lõi
        self.main_analysis_frame.columnconfigure(0, weight=1) # Cột trái: Scoring/Hot
        self.main_analysis_frame.columnconfigure(1, weight=1) # Cột phải: AI/Gan
        self.main_analysis_frame.rowconfigure(0, weight=2) # Hàng trên: Scoring/AI (Quan trọng hơn)
        self.main_analysis_frame.rowconfigure(1, weight=1) # Hàng dưới: Hot/Gan
        self.main_analysis_frame.rowconfigure(2, weight=1) # Hàng dưới cùng: K2N Pending

        # ===================================================================
        # TẠO CÁC BẢNG (SỬ DỤNG 5 TRONG TỔNG SỐ 8 CŨ)
        # ===================================================================

        # 1. Bảng Chấm Điểm (Scoring) - VỊ TRÍ CHÍNH (Hàng 0, Cột 0)
        self._create_top_scores_ui(self.main_analysis_frame)
        self.top_scores_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 2. Dự đoán AI (AI Predictions) - VỊ TRÍ CHÍNH (Hàng 0, Cột 1)
        self._create_ai_predictions_ui(self.main_analysis_frame)
        self.ai_predictions_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 3. Loto Về Nhiều (Hot Loto / Tần suất) - VỊ TRÍ THỐNG KÊ (Hàng 1, Cột 0)
        self._create_hot_loto_ui(self.main_analysis_frame)
        self.hot_loto_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # 4. Lô Gan (Gan Loto) - VỊ TRÍ THỐNG KÊ (Hàng 1, Cột 1)
        self._create_gan_loto_ui(self.main_analysis_frame)
        self.gan_loto_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 5. Cầu K2N Đang Chờ (Pending K2N) - VỊ TRÍ BỔ SUNG (Hàng 2, Cột 0, 1 - Mở rộng)
        self._create_pending_k2n_ui(self.main_analysis_frame)
        self.pending_k2n_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # --- (Đã loại bỏ các bảng Consensus, High Win, Memory Bridges để tối ưu hóa) ---
        # Để lại hàm tạo UI (Private Methods) cho 5 bảng được sử dụng

    # ===================================================================================
    # CÁC HÀM TẠO UI (Sử dụng lại 5 hàm cũ)
    # ===================================================================================
    
    def _create_top_scores_ui(self, parent_frame):
        self.top_scores_frame = ttk.Labelframe(parent_frame, text="🏆 Bảng Chấm Điểm Tổng Lực (V6.2 + AI)")
        tree_frame = ttk.Frame(self.top_scores_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('score', 'pair', 'gan', 'reasons')
        self.scores_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=15)
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

    def _create_hot_loto_ui(self, parent_frame):
        self.hot_loto_frame = ttk.Labelframe(parent_frame, text=f"🔥 Loto Về Nhiều (7 ngày)")
        tree_frame = ttk.Frame(self.hot_loto_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('loto', 'hits', 'days')
        self.hot_loto_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8) # Giảm height
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
        self.gan_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8) # Giảm height
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
        self.k2n_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=8) # Giảm height
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

    def _create_ai_predictions_ui(self, parent_frame):
        self.ai_predictions_frame = ttk.Labelframe(parent_frame, text="🧠 Dự đoán AI (Loto Đơn)")
        tree_frame = ttk.Frame(self.ai_predictions_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('loto', 'probability')
        self.ai_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=15)
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

    # --- HÀM NẠP DỮ LIỆU ---

    def clear_data(self):
        self.title_label.config(text="Đang tải...")
        # (SỬA LỖI) Xóa tất cả các Treeview được sử dụng
        for tree in [self.scores_tree, self.hot_loto_tree, self.gan_tree, self.k2n_tree, self.ai_tree]:
            try:
                # Xóa toàn bộ dữ liệu trong Treeview
                for item in tree.get_children():
                    tree.delete(item)
            except Exception as e:
                # Báo cáo lỗi nếu có (dù không nên xảy ra)
                print(f"Lỗi khi xóa tree {tree.winfo_name()}: {e}")

    # Hàm này được giữ nguyên và sử dụng để cập nhật
    def populate_data(self, next_ky, stats, n_days_stats, 
                      consensus, high_win, pending_k2n, 
                      gan_stats, top_scores, top_memory_bridges,
                      ai_predictions): 
        
        try:
            # BƯỚC KHẮC PHỤC LỖI: Luôn xóa dữ liệu cũ trước khi nạp dữ liệu mới
            self.clear_data()
            
            # --- Cập nhật Tiêu đề ---
            today = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            self.title_label.config(text=f"Bảng Quyết Định Tối Ưu - {next_ky} (Cập nhật: {today})")

            # --- Nạp Bảng 1: Chấm Điểm (V5 + AI) ---
            self._populate_top_scores(top_scores)

            # --- Nạp Bảng 2: Loto Về Nhiều ---
            self.hot_loto_frame.config(text=f"🔥 Loto Về Nhiều ({n_days_stats} ngày)")
            self._populate_hot_loto(stats)

            # --- Nạp Bảng 3: Lô Gan ---
            gan_threshold = SETTINGS.GAN_DAYS
            self.gan_loto_frame.config(text=f"🧊 Lô Gan (Trên {gan_threshold} ngày)")
            self._populate_gan_loto(gan_stats)

            # --- Nạp Bảng 4: Cầu K2N ---
            self._populate_pending_k2n(pending_k2n)
            
            # --- Nạp Bảng 5: Dự đoán AI ---
            self._populate_ai_predictions(ai_predictions)
            
            # (V7.0) Bỏ Consensus, High Win, Memory (chỉ lấy data chính)

        except Exception as e:
            messagebox.showerror("Lỗi Nạp Dữ Liệu Dashboard", f"Lỗi chi tiết: {e}\n{traceback.format_exc()}", parent=self.window)
            
    # ===================================================================================
    # CÁC HÀM NẠP DỮ LIỆU CHI TIẾT (Giữ lại 5 hàm cũ, loại bỏ 3 hàm không dùng)
    # ===================================================================================

    def _populate_top_scores(self, top_scores):
        if not top_scores:
            self.scores_tree.insert('', tk.END, values=("N/A", "N/A", "", "Không có cặp nào"))
            return
        for i, item in enumerate(top_scores[:40]): # Hiển thị 40 dòng
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

    def _populate_pending_k2n(self, pending_k2n):
        if not pending_k2n:
            self.k2n_tree.insert('', tk.END, values=("(N/A)", "", "", "Không có cầu K2N nào chờ"))
            return
        try:
            sorted_k2n = sorted(pending_k2n.items(), key=lambda item: (int(str(item[1]['streak']).split(' ')[0]), -int(item[1].get('max_lose', 99))), reverse=True)
        except Exception:
             sorted_k2n = list(pending_k2n.items())
        risk_threshold = SETTINGS.K2N_RISK_START_THRESHOLD
        for bridge_name, data in sorted_k2n:
            stl, streak, max_lose = data['stl'], data['streak'], data.get('max_lose', 0)
            tags = ()
            if max_lose > risk_threshold: tags = ('risk',)
            elif max_lose < risk_threshold: tags = ('safe',)
            self.k2n_tree.insert('', tk.END, values=(stl, streak, f"{max_lose} lần", bridge_name), tags=tags)

    def _populate_ai_predictions(self, ai_predictions):
        if not ai_predictions:
            self.ai_tree.insert('', tk.END, values=("(N/A)", "Vui lòng Huấn luyện AI"))
            return
            
        for i, pred in enumerate(ai_predictions[:20]): # Chỉ hiển thị Top 20
            loto = pred['loto']
            prob = pred['probability']
            
            tags = ()
            if i == 0:
                tags = ('top1',)
            elif i < 5:
                tags = ('top5',)
                
            self.ai_tree.insert('', tk.END, values=(
                loto,
                f"{prob:.2f}%"
            ), tags=tags)

    # ===================================================================================
    # HÀM TƯƠNG TÁC (SỬA V6.5)
    # ===================================================================================
    
    def refresh_data(self):
        # Hàm này được gọi khi nhấn nút "Làm Mới" trên Dashboard
        self.app.update_output("\n--- (Làm Mới) Bắt đầu chạy lại Bảng Quyết Định Tối Ưu ---")
        self.app.run_decision_dashboard() 

    def on_tree_double_click(self, event):
        try:
            item_id = event.widget.focus()
            if not item_id: return
            item = event.widget.item(item_id)
            values = item['values']
            bridge_name = ""
            
            # (SỬA V7.0) Giữ lại K2N Pending (bridge_name là values[3])
            if event.widget == self.k2n_tree: bridge_name = values[3] 
            
            if bridge_name:
                self.app.trigger_bridge_backtest(bridge_name)
        except Exception as e:
            print(f"Lỗi double-click: {e}")