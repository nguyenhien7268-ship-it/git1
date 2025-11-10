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
        self.window.title("Bảng Tổng Hợp (V6.6 - Tích hợp AI + 2 Tab)") # (SỬA V6.6)
        self.window.geometry("1400x900") 
        self.window.transient(self.root)
        self.window.grab_set()

        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1) 

        self.header_frame = ttk.Frame(self.window)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        self.title_label = ttk.Label(self.header_frame, text="Đang tải...", font=('Arial', 16, 'bold'))
        self.title_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.refresh_button = ttk.Button(self.header_frame, text="Làm Mới Dữ Liệu", command=self.refresh_data)
        self.refresh_button.pack(side=tk.RIGHT)
        
        # (SỬA V6.5) Dùng lại Notebook (2 Tab)
        self.notebook = ttk.Notebook(self.window)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # --- Tab 1: 4 Bảng Ưu Tiên ---
        self.tab1_priority = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab1_priority, text='Tổng Quan (Ưu Tiên)')
        # Cấu hình lưới 2x2
        self.tab1_priority.columnconfigure(0, weight=1)
        self.tab1_priority.columnconfigure(1, weight=1)
        self.tab1_priority.rowconfigure(0, weight=1)
        self.tab1_priority.rowconfigure(1, weight=1)

        # --- Tab 2: 4 Bảng Chi Tiết Cầu ---
        self.tab2_details = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab2_details, text='Chi Tiết Cầu & AI') # (SỬA V6.6)
        # Cấu hình lưới 2x2
        self.tab2_details.columnconfigure(0, weight=1)
        self.tab2_details.columnconfigure(1, weight=1)
        self.tab2_details.rowconfigure(0, weight=1)
        self.tab2_details.rowconfigure(1, weight=1)
        
        # ===================================================================
        # (SỬA V6.6) TẠO 8 BẢNG VÀ PHÂN VÀO CÁC TAB
        # ===================================================================

        # --- 4 BẢNG ƯU TIÊN (TAB 1) ---
        
        # Ưu tiên 1: Chấm Điểm (Bao gồm AI)
        self._create_top_scores_ui(self.tab1_priority)
        self.top_scores_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Ưu tiên 2: Loto Về Nhiều
        self._create_hot_loto_ui(self.tab1_priority)
        self.hot_loto_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Ưu tiên 3: Lô Gan
        self._create_gan_loto_ui(self.tab1_priority)
        self.gan_loto_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Ưu tiên 4: Cầu K2N
        self._create_pending_k2n_ui(self.tab1_priority)
        self.pending_k2n_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # --- 4 BẢNG CHI TIẾT (TAB 2) ---
        
        # Chi tiết 1: Cầu Bạc Nhớ
        self._create_memory_bridges_ui(self.tab2_details)
        self.memory_bridges_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Chi tiết 2: Consensus (Vote)
        self._create_consensus_ui(self.tab2_details)
        self.consensus_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Chi tiết 3: Cầu Tỷ Lệ Cao
        self._create_high_win_ui(self.tab2_details)
        self.high_win_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # (MỚI V6.6) Chi tiết 4: Bảng AI (Loto đơn)
        self._create_ai_predictions_ui(self.tab2_details)
        self.ai_predictions_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

    # ===================================================================================
    # CÁC HÀM TẠO UI (SỬA V6.6 - Đủ 8 hàm)
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
        self.hot_loto_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=15)
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
        self.gan_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=15)
        self.gan_tree.heading('loto', text='Loto')
        self.gan_tree.heading('days', text='Số ngày Gan')
        self.gan_tree.column('loto', width=50, anchor=tk.CENTER)
        self.gan_tree.column('days', width=100, anchor=tk.E)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.gan_tree.yview)
        self.gan_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.gan_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_pending_k2n_ui(self, parent_frame):
        self.pending_k2n_frame = ttk.Labelframe(parent_frame, text="⏳ Cầu K2N Đang Chờ (Chờ N2)")
        tree_frame = ttk.Frame(self.pending_k2n_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('stl', 'streak', 'max_lose', 'name')
        self.k2n_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=15)
        self.k2n_tree.heading('stl', text='Cặp số')
        self.k2n_tree.heading('streak', text='Chuỗi')
        self.k2n_tree.heading('max_lose', text='Gãy Max')
        self.k2n_tree.heading('name', text='Tên cầu')
        self.k2n_tree.column('stl', width=60, anchor=tk.CENTER)
        self.k2n_tree.column('streak', width=60, anchor=tk.CENTER)
        self.k2n_tree.column('max_lose', width=60, anchor=tk.CENTER)
        self.k2n_tree.column('name', width=150)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.k2n_tree.yview)
        self.k2n_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.k2n_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.k2n_tree.tag_configure('risk', foreground='red')
        self.k2n_tree.tag_configure('safe', foreground='green')
        self.k2n_tree.bind("<Double-1>", self.on_tree_double_click)

    # (SỬA V6.6) Trả lại các hàm tạo UI cho Tab 2
    def _create_memory_bridges_ui(self, parent_frame):
        self.memory_bridges_frame = ttk.Labelframe(parent_frame, text="💡 Cầu Bạc Nhớ (Top 5 Backtest)")
        tree_frame = ttk.Frame(self.memory_bridges_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('stl', 'rate', 'name')
        self.memory_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=10)
        self.memory_tree.heading('stl', text='Cặp số')
        self.memory_tree.heading('rate', text='Tỷ lệ')
        self.memory_tree.heading('name', text='Thuật toán')
        self.memory_tree.column('stl', width=60, anchor=tk.CENTER)
        self.memory_tree.column('rate', width=60, anchor=tk.E)
        self.memory_tree.column('name', width=210)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.memory_tree.yview)
        self.memory_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.memory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.memory_tree.bind("<Double-1>", self.on_tree_double_click)

    def _create_consensus_ui(self, parent_frame):
        self.consensus_frame = ttk.Labelframe(parent_frame, text="🗳️ Cặp Số Nhiều Vote (Cầu N1)")
        tree_frame = ttk.Frame(self.consensus_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('pair', 'count', 'sources')
        self.consensus_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=10)
        self.consensus_tree.heading('pair', text='Cặp số')
        self.consensus_tree.heading('count', text='Số Vote')
        self.consensus_tree.heading('sources', text='Nguồn')
        self.consensus_tree.column('pair', width=60, anchor=tk.CENTER)
        self.consensus_tree.column('count', width=60, anchor=tk.E)
        self.consensus_tree.column('sources', width=150)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.consensus_tree.yview)
        self.consensus_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.consensus_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_high_win_ui(self, parent_frame):
        self.high_win_frame = ttk.Labelframe(parent_frame, text="🎯 Cầu Tỷ Lệ Cao (N1)")
        tree_frame = ttk.Frame(self.high_win_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ('stl', 'rate', 'name')
        self.high_win_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', height=10)
        self.high_win_tree.heading('stl', text='Cặp số')
        self.high_win_tree.heading('rate', text='Tỷ lệ')
        self.high_win_tree.heading('name', text='Tên cầu')
        self.high_win_tree.column('stl', width=60, anchor=tk.CENTER)
        self.high_win_tree.column('rate', width=60, anchor=tk.E)
        self.high_win_tree.column('name', width=150)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.high_win_tree.yview)
        self.high_win_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.high_win_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.high_win_tree.bind("<Double-1>", self.on_tree_double_click)

    # (MỚI V6.6) Trả lại hàm tạo Bảng AI
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

    def _create_hidden_ui_elements(self):
        """ (V6.5) Đã thay đổi - không cần nữa
        vì chúng ta tạo tất cả 8 bảng."""
        pass

    # ===================================================================================
    # HÀM NẠP DỮ LIỆU (Populate)
    # ===================================================================================

    def clear_data(self):
        self.title_label.config(text="Đang tải...")
        # (SỬA V6.6) Xóa 8 cây
        for tree in [self.scores_tree, self.hot_loto_tree, self.gan_tree, self.k2n_tree,
                     self.memory_tree, self.consensus_tree, self.high_win_tree, self.ai_tree]:
            try:
                # Kiểm tra xem tree đã được tạo chưa
                if hasattr(self, tree.winfo_name().replace("!treeview", "")):
                    for item in tree.get_children():
                        tree.delete(item)
            except Exception as e:
                print(f"Lỗi khi xóa tree: {e}")

    # (CẬP NHẬT V6.6) Trả lại `ai_predictions`
    def populate_data(self, next_ky, stats, n_days_stats, 
                      consensus, high_win, pending_k2n, 
                      gan_stats, top_scores, top_memory_bridges,
                      ai_predictions): 
        
        try:
            self.clear_data()
            
            # --- Cập nhật Tiêu đề ---
            today = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            self.title_label.config(text=f"Bảng Tổng Hợp - {next_ky} (Cập nhật: {today})")

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
            
            # --- (SỬA V6.6) Nạp 4 bảng Tab 2 ---
            
            # --- Nạp Bảng 5: Cầu Bạc Nhớ ---
            self._populate_memory_bridges(top_memory_bridges)

            # --- Nạp Bảng 6: Consensus (Vote) ---
            self._populate_consensus(consensus)
            
            # --- Nạp Bảng 7: Cầu Tỷ Lệ Cao ---
            high_win_thresh = SETTINGS.HIGH_WIN_THRESHOLD
            self.high_win_frame.config(text=f"🎯 Cầu Tỷ Lệ Cao (N1 >= {high_win_thresh}%)")
            self._populate_high_win(high_win)
            
            # --- (MỚI V6.6) Nạp Bảng 8: Dự đoán AI ---
            self._populate_ai_predictions(ai_predictions)
            
        except Exception as e:
            messagebox.showerror("Lỗi Nạp Dữ Liệu Dashboard", f"Lỗi chi tiết: {e}\n{traceback.format_exc()}", parent=self.window)
            
    # ===================================================================================
    # (SỬA V6.6) HÀM NẠP DỮ LIỆU CHI TIẾT (Đủ 8 hàm)
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

    # (SỬA V6.6) Trả lại các hàm nạp dữ liệu cho Tab 2
    def _populate_memory_bridges(self, top_memory_bridges):
        if not top_memory_bridges:
            self.memory_tree.insert('', tk.END, values=("(N/A)", "", "Không có cầu BN nào"))
            return
        for bridge in top_memory_bridges:
            self.memory_tree.insert('', tk.END, values=(",".join(bridge['stl']), bridge['rate'], bridge['name']))

    def _populate_consensus(self, consensus):
        if not consensus:
            self.consensus_tree.insert('', tk.END, values=("(N/V)", "", "Không có cầu N1 trùng"))
            return
        for pair, count, sources in consensus: 
            self.consensus_tree.insert('', tk.END, values=(pair, count, sources))

    def _populate_high_win(self, high_win):
        if not high_win:
            self.high_win_tree.insert('', tk.END, values=("(N/A)", "", "Không có cầu nào đạt"))
            return
        for bridge in high_win:
            self.high_win_tree.insert('', tk.END, values=(",".join(bridge['stl']), bridge['rate'], bridge['name']))

    # (MỚI V6.6) Trả lại hàm nạp Bảng AI
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
        self.app.update_output("\n--- (Làm Mới) Bắt đầu chạy lại Bảng Tổng Hợp ---")
        self.app.run_decision_dashboard() 

    def on_tree_double_click(self, event):
        try:
            item_id = event.widget.focus()
            if not item_id: return
            item = event.widget.item(item_id)
            values = item['values']
            bridge_name = ""
            
            # (SỬA V6.5) Kiểm tra cả 3 cây có thể click
            if event.widget == self.k2n_tree: bridge_name = values[3]
            elif event.widget == self.high_win_tree: bridge_name = values[2]
            elif event.widget == self.memory_tree: bridge_name = values[2]
            
            if bridge_name:
                self.app.trigger_bridge_backtest(bridge_name)
        except Exception as e:
            print(f"Lỗi double-click: {e}")