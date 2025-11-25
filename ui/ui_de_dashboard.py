# Tên file: ui/ui_de_dashboard.py
# (PHIÊN BẢN ĐÃ FIX LỖI ATTRIBUTE ERROR: UPDATE_DATA)
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Import an toàn
try:
    from logic.de_utils import BO_SO_DE, check_cham, check_tong, get_gdb_last_2
    from logic.de_analytics import (
        analyze_market_trends, 
        get_de_consensus, 
        calculate_number_scores, 
        get_top_strongest_sets
    )
    from logic.bridges.de_bridge_scanner import run_de_scanner
except ImportError:
    # Sẽ xử lý kiểm tra trong hàm dùng logic
    pass

class UiDeDashboard(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.found_bridges = []
        self.scores = []
        self.strong_sets = []
        self.top_touches = []
        self.init_ui()
        
    def init_ui(self):
        # TOOLBAR
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="🔄 1. Phân Tích Thị Trường", command=self.on_analyze_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 2. Quét Cầu & Chấm Điểm", command=self.on_scan_click).pack(side=tk.LEFT, padx=2)
        self.lbl_status = ttk.Label(toolbar, text="Sẵn sàng", foreground="blue")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # MAIN LAYOUT
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- COL 1: THỐNG KÊ (LEFT) ---
        frame_left = ttk.LabelFrame(paned, text="📊 Dữ Liệu", padding=5)
        paned.add(frame_left, weight=1)
        nb_left = ttk.Notebook(frame_left)
        nb_left.pack(fill=tk.BOTH, expand=True)
        
        # Tab History
        tab_history = ttk.Frame(nb_left)
        nb_left.add(tab_history, text="Lịch Sử")
        self.tree_history = ttk.Treeview(tab_history, columns=("date", "gdb", "de"), show="headings", height=15)
        self.tree_history.heading("date", text="Ngày")
        self.tree_history.heading("gdb", text="GĐB")
        self.tree_history.heading("de", text="Đề")
        self.tree_history.column("date", width=80)
        self.tree_history.column("gdb", width=70)
        self.tree_history.column("de", width=40, anchor="center")
        self.tree_history.pack(fill=tk.BOTH, expand=True)

        # Tab Chạm/Tổng/Bộ
        self._init_stat_tabs(nb_left)

        # --- COL 2: CẦU CHẠY (CENTER) ---
        frame_mid = ttk.LabelFrame(paned, text="🌉 Cầu Đang Thông", padding=5)
        paned.add(frame_mid, weight=2)
        self.tree_bridges = ttk.Treeview(frame_mid, columns=("name", "predict", "streak"), show="headings", selectmode="extended")
        self.tree_bridges.heading("name", text="Tên Cầu")
        self.tree_bridges.heading("predict", text="Báo")
        self.tree_bridges.heading("streak", text="Thông")
        self.tree_bridges.column("name", width=120)
        self.tree_bridges.column("predict", width=60, anchor="center")
        self.tree_bridges.column("streak", width=40, anchor="center")
        self.tree_bridges.pack(fill=tk.BOTH, expand=True)
        self.tree_bridges.bind("<<TreeviewSelect>>", self.on_bridge_select)

        # --- COL 3: CÔNG CỤ & DỰ ĐOÁN (RIGHT) ---
        frame_right = ttk.Frame(paned)
        paned.add(frame_right, weight=2)
        
        # 1. CÔNG CỤ TẠO DÀN THỦ CÔNG
        grp_manual = ttk.LabelFrame(frame_right, text="🛠️ Tạo Dàn Thủ Công", padding=5)
        grp_manual.pack(fill=tk.X, pady=(0, 5))
        f_input = ttk.Frame(grp_manual)
        f_input.pack(fill=tk.X)
        ttk.Label(f_input, text="Nhập Chạm:").pack(side=tk.LEFT)
        self.ent_cham = ttk.Entry(f_input, width=15)
        self.ent_cham.pack(side=tk.LEFT, padx=5)
        self.ent_cham.insert(0, "05")
        ttk.Button(f_input, text="⚡ Tạo Dàn", command=self.manual_gen_cham).pack(side=tk.LEFT, padx=5)
        self.txt_manual = tk.Text(grp_manual, height=3, width=30)
        self.txt_manual.pack(fill=tk.X, pady=5)
        
        # 2. KẾT QUẢ PHÂN TÍCH SCORING
        grp_score = ttk.LabelFrame(frame_right, text="🎯 Dự Đoán Theo Điểm & Bộ Số", padding=5)
        grp_score.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_top_touches = ttk.Label(grp_score, text="🔥 Top 4 Chạm: ...", foreground="blue", font=("Arial", 10, "bold"))
        self.lbl_top_touches.pack(anchor="w", padx=5, pady=(0, 5))
        
        self.lbl_top_sets = ttk.Label(grp_score, text="Top Bộ Mạnh: ...", foreground="red")
        self.lbl_top_sets.pack(anchor="w", padx=5)

        self.nb_result = ttk.Notebook(grp_score)
        self.nb_result.pack(fill=tk.BOTH, expand=True)
        
        self.tab_65 = ttk.Frame(self.nb_result)
        self.nb_result.add(self.tab_65, text="Dàn 65")
        self.txt_65 = tk.Text(self.tab_65, wrap=tk.WORD)
        self.txt_65.pack(fill=tk.BOTH, expand=True)
        
        self.tab_10 = ttk.Frame(self.nb_result)
        self.nb_result.add(self.tab_10, text="Top 10 (Lọc Bộ)")
        self.txt_10 = tk.Text(self.tab_10, wrap=tk.WORD, font=("Arial", 11))
        self.txt_10.pack(fill=tk.BOTH, expand=True)
        
        self.tab_4 = ttk.Frame(self.nb_result)
        self.nb_result.add(self.tab_4, text="Top 4 (Tứ Thủ)")
        self.txt_4 = tk.Text(self.tab_4, wrap=tk.WORD, font=("Arial", 14, "bold"), fg="red")
        self.txt_4.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(grp_score, text="📋 Copy Dàn Đang Xem", command=self.copy_current_tab).pack(fill=tk.X, pady=5)

    def _init_stat_tabs(self, nb):
        # Tạo các tab thống kê thủ công
        tabs_map = [("Chạm", "cham"), ("Tổng", "tong"), ("Bộ", "bo")]
        
        for label, suffix in tabs_map:
            tab = ttk.Frame(nb)
            nb.add(tab, text=label)
            
            cols = ("val", "freq", "gan")
            tree = ttk.Treeview(tab, columns=cols, show="headings")
            tree.heading("val", text=label)
            tree.heading("freq", text="Về")
            tree.heading("gan", text="Gan")
            
            tree.column("val", width=40, anchor="center")
            tree.column("freq", width=40, anchor="center")
            tree.column("gan", width=40, anchor="center")
            
            tree.pack(fill=tk.BOTH, expand=True)
            tree.tag_configure("hot", background="#C3FDB8")
            tree.tag_configure("cold", foreground="red")
            
            # Gán vào biến self.tree_cham, self.tree_tong...
            setattr(self, f"tree_{suffix}", tree)
            
        # Map lại biến để dùng cho logic update
        self.tree_cham = self.tree_cham
        self.tree_tong = self.tree_tong
        self.tree_bo = self.tree_bo

    # --- LOGIC ---
    def get_data(self):
        if hasattr(self.controller, 'all_data_ai'): return self.controller.all_data_ai
        return []
        
    def update_data(self, df):
        """
        [FIX] Hàm này được Controller gọi khi có dữ liệu mới.
        Chúng ta sẽ làm mới lại giao diện (History) ngay lập tức.
        """
        # Tự động chạy phân tích để hiển thị dữ liệu mới lên Grid
        self.on_analyze_click()

    def on_analyze_click(self):
        # Kiểm tra dependencies
        if 'analyze_market_trends' not in globals() or 'get_gdb_last_2' not in globals():
            # Nếu import lỗi thì không chạy để tránh crash
            self.lbl_status.config(text="Lỗi: Thiếu thư viện logic.", foreground="red")
            return

        data = self.get_data()
        if not data: return
        
        # 1. Update History
        for row in self.tree_history.get_children(): self.tree_history.delete(row)
        recent = data[-30:]
        for row in reversed(recent):
            gdb = str(row[2])
            de = get_gdb_last_2(row)
            self.tree_history.insert("", "end", values=(row[0], gdb, de if de else ""))
            
        # 2. Update Stats
        stats = analyze_market_trends(data)
        self._populate_sorted_tree(self.tree_cham, stats.get('freq_cham', {}), stats.get('gan_cham', {}), range(10))
        self._populate_sorted_tree(self.tree_tong, stats.get('freq_tong', {}), stats.get('gan_tong', {}), range(10))
        self._populate_sorted_tree(self.tree_bo, stats.get('freq_bo', {}), stats.get('gan_bo', {}), BO_SO_DE.keys())
        self.lbl_status.config(text="Đã cập nhật & Sắp xếp theo Gan.", foreground="green")

    def _populate_sorted_tree(self, tree, freq_dict, gan_dict, keys):
        for row in tree.get_children(): tree.delete(row)
        data_list = []
        for k in keys:
            f = freq_dict.get(k, 0)
            g = gan_dict.get(k, 0)
            data_list.append((k, f, g))
        data_list.sort(key=lambda x: x[2]) # Sort by Gan (Index 2)
        for item in data_list:
            val, f, g = item
            tags = ()
            if g < 3: tags = ("hot",)
            elif g > 10: tags = ("cold",)
            tree.insert("", "end", values=(val, f, g), tags=tags)

    def on_scan_click(self):
        if 'run_de_scanner' not in globals():
            messagebox.showerror("Lỗi", "Chưa tải được logic Scanner.")
            return

        data = self.get_data()
        if not data: return
        self.lbl_status.config(text="Đang quét & Chấm điểm...", foreground="orange")
        threading.Thread(target=self._run_scan, args=(data,)).start()
        
    def _run_scan(self, data):
        count, bridges = run_de_scanner(data)
        self.found_bridges = bridges
        
        # 1. Tính điểm
        self.scores = calculate_number_scores(bridges)
        
        # 2. Tìm Top Bộ Mạnh
        self.strong_sets = get_top_strongest_sets(bridges)
        
        # 3. Lấy Top 4 Chạm từ consensus
        consensus = get_de_consensus(bridges)
        consensus_cham = consensus.get('consensus_cham', [])
        self.top_touches = [str(item[0]) for item in consensus_cham[:4]]
        
        self.after(0, self._update_scan_ui)
        
    def _update_scan_ui(self):
        # Update Bridges UI
        for row in self.tree_bridges.get_children(): self.tree_bridges.delete(row)
        for i, b in enumerate(self.found_bridges):
            p_val = b['predicted_value']
            b_type = b['type']
            p_text = f"Bộ {p_val}" if 'BO' in b_type else (f"Chạm {p_val}" if 'CHAM' in b_type else f"Tổng {p_val}")
            self.tree_bridges.insert("", "end", iid=i, values=(b['name'], p_text, b['streak']))
        
        # Update Top 4 Chạm Label
        if self.top_touches:
            self.lbl_top_touches.config(text=f"🔥 Top 4 Chạm: {', '.join(self.top_touches)}")
        else:
            self.lbl_top_touches.config(text="🔥 Top 4 Chạm: Chưa có dữ liệu")
            
        # Update Strong Sets Label
        if self.strong_sets:
            self.lbl_top_sets.config(text=f"Ưu Tiên Bộ: {', '.join(self.strong_sets[:5])}")
        else:
            self.lbl_top_sets.config(text="Không có cầu bộ mạnh")

        # --- LOGIC LỌC SỐ NÂNG CAO ---
        if self.scores:
            # 1. Lấy Dàn 65 (Top điểm cao nhất)
            top_65_list = [x[0] for x in self.scores[:65]]
            
            # 2. Lọc Top 10 & Top 4 từ Dàn 65
            priority_nums = []
            backup_nums = []
            
            def get_bo_of_num(n_str):
                if 'BO_SO_DE' not in globals(): return None
                for b_name, b_nums in BO_SO_DE.items():
                    if n_str in b_nums: return b_name
                return None

            # Duyệt qua top 65 để phân loại
            for num in top_65_list:
                bo = get_bo_of_num(num)
                # Nếu số này thuộc trong Top 5 bộ mạnh nhất
                if bo and bo in self.strong_sets[:5]:
                    priority_nums.append(num)
                else:
                    backup_nums.append(num)
            
            # Ghép lại: Ưu tiên trước, Backup sau
            final_sorted = priority_nums + backup_nums
            
            # Cắt dàn
            dan_10 = sorted(final_sorted[:10])
            dan_4 = sorted(final_sorted[:4])
            
            # Hiển thị
            self.txt_65.delete("1.0", tk.END); self.txt_65.insert("1.0", ",".join(sorted(top_65_list)))
            self.txt_10.delete("1.0", tk.END); self.txt_10.insert("1.0", ",".join(dan_10))
            self.txt_4.delete("1.0", tk.END); self.txt_4.insert("1.0", ",".join(dan_4))
            
        self.lbl_status.config(text=f"Xong. Tìm thấy {len(self.found_bridges)} cầu.", foreground="green")

    def manual_gen_cham(self):
        if 'check_cham' not in globals(): return
        inp = self.ent_cham.get().strip()
        if not inp: return
        final_set = set()
        digits = [int(c) for c in inp if c.isdigit()]
        for d in digits:
            for i in range(100):
                s = f"{i:02d}"
                if check_cham(s, [d]): final_set.add(s)
        result = sorted(list(final_set))
        self.txt_manual.delete("1.0", tk.END)
        self.txt_manual.insert("1.0", ",".join(result))

    def on_bridge_select(self, event):
        pass

    def copy_current_tab(self):
        current_tab = self.nb_result.select()
        text_widget = self.nb_result.nametowidget(current_tab).winfo_children()[0]
        content = text_widget.get("1.0", tk.END).strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("Copy", "Đã copy dàn số!")
        else:
            messagebox.showwarning("Trống", "Không có dữ liệu.")