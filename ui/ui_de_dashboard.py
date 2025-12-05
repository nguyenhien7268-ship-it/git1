# Tên file: code6/ui/ui_de_dashboard.py
# (PHIÊN BẢN V3.7 - ULTIMATE: ANALYTICS + FINAL FORECAST)

import tkinter as tk
from tkinter import ttk, messagebox
import threading

# --- IMPORTS ---
try:
    from logic.de_utils import BO_SO_DE, check_cham, get_gdb_last_2, get_set_name_of_number
    from logic.de_analytics import (
        analyze_market_trends,
        calculate_number_scores,
        get_top_strongest_sets,
        calculate_top_touch_combinations,
        run_intersection_matrix_analysis,
    )
    from logic.bridges.de_bridge_scanner import run_de_scanner
    print(f"[DEBUG UI_DE_DASHBOARD] Imports thành công. BO_SO_DE size: {len(BO_SO_DE)}")
except ImportError as e:
    print(f"[ERROR UI_DE_DASHBOARD] Import failed: {e}")
    # Fallback definitions
    BO_SO_DE = {}
    def get_set_name_of_number(n): return "00"
    def run_de_scanner(*args): return 0, []
    def analyze_market_trends(*args, **kwargs): return {}
    def calculate_number_scores(*args, **kwargs): return []
    def get_top_strongest_sets(*args, **kwargs): return []
    def calculate_top_touch_combinations(*args, **kwargs): return []
    def run_intersection_matrix_analysis(*args, **kwargs): return {"ranked": []}
    def get_gdb_last_2(r): return r[2][-2:] if len(r)>2 else ""

class UiDeDashboard(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.found_bridges = []
        self._init_ui()

    def _init_ui(self):
        # 1. TOOLBAR
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(fill=tk.X)
        btn_scan = ttk.Button(toolbar, text="🚀 QUÉT & CHỐT SỐ (V3.8)", command=self.on_scan_click)
        btn_scan.pack(side=tk.LEFT, padx=5)
        self.lbl_status = ttk.Label(toolbar, text="Sẵn sàng", foreground="blue")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # 2. MAIN LAYOUT (3 CỘT)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- CỘT 1: THỐNG KÊ (20%) ---
        frame_stats = ttk.LabelFrame(paned, text="📊 Thị Trường", padding=2)
        paned.add(frame_stats, weight=1)
        
        nb_stats = ttk.Notebook(frame_stats)
        nb_stats.pack(fill=tk.BOTH, expand=True)
        
        # Tab Lịch Sử
        tab_history = ttk.Frame(nb_stats)
        nb_stats.add(tab_history, text="Lịch Sử")
        self.tree_history = ttk.Treeview(tab_history, columns=("date", "de"), show="headings")
        self.tree_history.heading("date", text="Ngày"); self.tree_history.column("date", width=80)
        self.tree_history.heading("de", text="Đề"); self.tree_history.column("de", width=40, anchor="center")
        self.tree_history.pack(fill=tk.BOTH, expand=True)
        
        # Tab Chạm/Bộ
        self.tree_cham_stat = self._create_stat_tab(nb_stats, "Chạm")
        self.tree_bo_stat = self._create_stat_tab(nb_stats, "Bộ")

        # --- CỘT 2: SCANNER (45%) ---
        frame_scan = ttk.Frame(paned, width=450)
        paned.add(frame_scan, weight=3)
        
        paned_vertical = ttk.PanedWindow(frame_scan, orient=tk.VERTICAL)
        paned_vertical.pack(fill=tk.BOTH, expand=True)

        # A. Cầu Chốt
        frame_pos = ttk.LabelFrame(paned_vertical, text="🎯 Cầu Chốt (Pascal, Memory...)", padding=2)
        paned_vertical.add(frame_pos, weight=3)
        cols_br = ("name", "type", "streak", "pred", "win")
        self.tree_bridges = ttk.Treeview(frame_pos, columns=cols_br, show="headings")
        self.tree_bridges.heading("name", text="Tên Cầu"); self.tree_bridges.column("name", width=140)
        self.tree_bridges.heading("type", text="Loại"); self.tree_bridges.column("type", width=70)
        self.tree_bridges.heading("streak", text="Thông"); self.tree_bridges.column("streak", width=50, anchor="center")
        self.tree_bridges.heading("pred", text="Dự Đoán"); self.tree_bridges.column("pred", width=100)
        self.tree_bridges.heading("win", text="Win10"); self.tree_bridges.column("win", width=50, anchor="center")
        
        sb_pos = ttk.Scrollbar(frame_pos, orient=tk.VERTICAL, command=self.tree_bridges.yview)
        self.tree_bridges.configure(yscrollcommand=sb_pos.set)
        sb_pos.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_bridges.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.tree_bridges.tag_configure("pascal", foreground="#00008B", font=("Arial", 9, "bold"))
        self.tree_bridges.tag_configure("memory", foreground="#800080", font=("Arial", 9, "bold"))
        self.tree_bridges.bind("<Double-1>", self.on_bridge_double_click)

        # B. Cầu Loại
        frame_kill = ttk.LabelFrame(paned_vertical, text="💀 Cầu Loại (Killer)", padding=2)
        paned_vertical.add(frame_kill, weight=1)
        cols_kill = ("name", "streak", "pred")
        self.tree_killer = ttk.Treeview(frame_kill, columns=cols_kill, show="headings")
        self.tree_killer.heading("name", text="Tên Cầu"); self.tree_killer.column("name", width=140)
        self.tree_killer.heading("streak", text="Gãy"); self.tree_killer.column("streak", width=50, anchor="center")
        self.tree_killer.heading("pred", text="Loại"); self.tree_killer.column("pred", width=120)
        self.tree_killer.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tree_killer.tag_configure("killer", foreground="red", font=("Arial", 9, "bold"))

        # --- CỘT 3: ANALYTICS & CHỐT SỐ (35%) ---
        frame_right = ttk.LabelFrame(paned, text="🔮 Phân Tích & Chốt Số", padding=2)
        paned.add(frame_right, weight=2)
        
        nb_right = ttk.Notebook(frame_right)
        nb_right.pack(fill=tk.BOTH, expand=True)
        
        # TAB 1: PHÂN TÍCH (Analysis)
        tab_analysis = ttk.Frame(nb_right)
        nb_right.add(tab_analysis, text="Phân Tích")
        
        # Top Chạm & Bộ (Grid)
        f_top = ttk.Frame(tab_analysis)
        f_top.pack(fill=tk.BOTH, expand=True)
        f_top.columnconfigure(0, weight=1); f_top.columnconfigure(1, weight=1)
        
        # Bảng Top Chạm
        ttk.Label(f_top, text="Top Chạm:").grid(row=0, column=0, sticky="w")
        self.tree_touch = ttk.Treeview(f_top, columns=("val", "score"), show="headings", height=5)
        self.tree_touch.heading("val", text="Chạm"); self.tree_touch.column("val", width=40, anchor="center")
        self.tree_touch.heading("score", text="Điểm"); self.tree_touch.column("score", width=40, anchor="center")
        self.tree_touch.grid(row=1, column=0, sticky="nsew", padx=2)
        
        # Bảng Top Bộ
        ttk.Label(f_top, text="Top Bộ:").grid(row=0, column=1, sticky="w")
        self.tree_set = ttk.Treeview(f_top, columns=("val", "score"), show="headings", height=5)
        self.tree_set.heading("val", text="Bộ"); self.tree_set.column("val", width=40, anchor="center")
        self.tree_set.heading("score", text="Điểm"); self.tree_set.column("score", width=40, anchor="center")
        self.tree_set.grid(row=1, column=1, sticky="nsew", padx=2)

        # Bảng Tổ Hợp Chạm Thông (NEW)
        ttk.Label(tab_analysis, text="Tổ Hợp Chạm Thông (Hot):").pack(anchor="w", pady=(5,0))
        self.tree_combos = ttk.Treeview(tab_analysis, columns=("combo", "info"), show="headings", height=5)
        self.tree_combos.heading("combo", text="Tổ Hợp"); self.tree_combos.column("combo", width=80)
        self.tree_combos.heading("info", text="Thông/Tỉ Lệ"); self.tree_combos.column("info", width=120)
        self.tree_combos.pack(fill=tk.BOTH, expand=True, padx=2)

        # TAB 2: CHỐT SỐ (Forecast)
        tab_forecast = ttk.Frame(nb_right)
        nb_right.add(tab_forecast, text="Chốt Số")
        
        # Dàn 65
        ttk.Label(tab_forecast, text="Dàn 65 Số (Lọc AI):", font=("Arial", 9, "bold")).pack(anchor="w")
        self.txt_65 = tk.Text(tab_forecast, height=4, width=30, wrap=tk.WORD, font=("Arial", 9))
        self.txt_65.pack(fill=tk.X, padx=2, pady=2)
        
        # Top 10
        ttk.Label(tab_forecast, text="Top 10 (Tinh Hoa):", font=("Arial", 9, "bold")).pack(anchor="w")
        self.txt_10 = tk.Text(tab_forecast, height=2, width=30, wrap=tk.WORD, font=("Arial", 10))
        self.txt_10.pack(fill=tk.X, padx=2, pady=2)
        
        # Tứ Thủ
        ttk.Label(tab_forecast, text="Tứ Thủ Đề (Vip):", font=("Arial", 9, "bold"), foreground="red").pack(anchor="w")
        self.txt_4 = tk.Text(tab_forecast, height=1, width=30, wrap=tk.WORD, font=("Arial", 12, "bold"))
        self.txt_4.pack(fill=tk.X, padx=2, pady=2)

        # [NEW] Danh sách Killer (Số bị loại)
        ttk.Label(tab_forecast, text="⛔ Số Bị Loại (Killer):", font=("Arial", 8, "italic"), foreground="gray").pack(anchor="w", pady=(5,0))
        self.txt_killed = tk.Text(tab_forecast, height=2, width=30, wrap=tk.WORD, font=("Arial", 8), foreground="gray")
        self.txt_killed.pack(fill=tk.X, padx=2, pady=0)
        
        # Nút Copy
        btn_copy = ttk.Button(tab_forecast, text="📋 Copy Tứ Thủ & Top 10", command=self.copy_forecast)
        btn_copy.pack(fill=tk.X, pady=5, padx=2)

    def _create_stat_tab(self, notebook, title):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=title)
        cols = ("val", "freq", "gan")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        tree.heading("val", text=title); tree.column("val", width=35, anchor="center")
        tree.heading("freq", text="Về"); tree.column("freq", width=35, anchor="center")
        tree.heading("gan", text="Gan"); tree.column("gan", width=35, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)
        tree.tag_configure("hot", background="#90EE90")
        tree.tag_configure("cold", foreground="red")
        return tree

    def on_scan_click(self):
        if not hasattr(self.controller, 'all_data_ai') or not self.controller.all_data_ai:
            messagebox.showwarning("Lỗi", "Chưa có dữ liệu. Vui lòng nạp dữ liệu trước.")
            return
        
        self.lbl_status.config(text="⏳ Đang chạy Full Analysis (Scanner + Stats + Forecast)...", foreground="orange")
        threading.Thread(target=self._run_full_analysis, args=(self.controller.all_data_ai,), daemon=True).start()

    def _run_full_analysis(self, data):
        try:
            # 1. Quét cầu (Gồm cả Positive và Killer)
            count, bridges = run_de_scanner(data)
            
            # 2. Thống kê thị trường (60 ngày)
            market_stats = analyze_market_trends(data, n_days=60)
            
            # 3. Tính điểm số học (V3.8 ULTIMATE) [UPDATED]
            # Truyền market_stats vào để tính Bonus
            scores = calculate_number_scores(bridges, market_stats=market_stats)
            
            # 4. Tìm bộ số mạnh nhất (Vẫn giữ tham khảo)
            last_row = data[-1] if data else None
            strong_sets = get_top_strongest_sets(bridges, market_stats, last_row)
            
            # 5. Phân tích tổ hợp chạm
            touch_combos = calculate_top_touch_combinations(data, num_touches=4, days=10, market_stats=market_stats)

            # 6. Ma trận giao thoa (Chạm Thông + Chạm Tỉ Lệ + Bộ Số)
            matrix_result = run_intersection_matrix_analysis(data)
            
            # Update UI
            self.after(0, lambda: self._update_ui_full(
                data, bridges, market_stats, scores, strong_sets, touch_combos, matrix_result
            ))
            
        except Exception as e:
            print(f"[ERROR] Full analysis error: {e}")
            import traceback
            traceback.print_exc()
            self.after(0, lambda: self.lbl_status.config(text="❌ Lỗi phân tích!", foreground="red"))

    def _update_ui_full(self, data, bridges, market_stats, scores, strong_sets, touch_combos, matrix_result):
        self.found_bridges = bridges
        self.lbl_status.config(text=f"✅ Hoàn tất. Tìm thấy {len(bridges)} cầu.", foreground="green")
        
        # --- A. CỘT 1: LỊCH SỬ & THỐNG KÊ ---
        for i in self.tree_history.get_children(): self.tree_history.delete(i)
        for row in reversed(data[-20:]):
            date = row[0]; de = get_gdb_last_2(row)
            self.tree_history.insert("", "end", values=(date, de))
            
        self._fill_stat_tree(self.tree_cham_stat, market_stats.get('freq_cham',{}), market_stats.get('gan_cham',{}), range(10))
        self._fill_stat_tree(self.tree_bo_stat, market_stats.get('freq_bo',{}), market_stats.get('gan_bo',{}), BO_SO_DE.keys())

        # --- B. CỘT 2: CẦU (LIST) ---
        for t in [self.tree_bridges, self.tree_killer]:
            for i in t.get_children(): t.delete(i)
            
        pos_bridges, kill_bridges = [], []
        for b in bridges:
            (kill_bridges if b.get('type') == 'DE_KILLER' else pos_bridges).append(b)

        for b in pos_bridges:
            tag = "pascal" if b['type'] == 'DE_PASCAL' else ("memory" if b['type'] == 'DE_MEMORY' else "")
            self.tree_bridges.insert("", "end", values=(
                b['name'], b['type'], b['streak'], b['predicted_value'], f"{b.get('win_rate',0):.0f}%"
            ), tags=(tag,))

        for k in kill_bridges:
            self.tree_killer.insert("", "end", values=(k['name'], k['streak'], k['predicted_value']), tags=("killer",))

        # --- C. CỘT 3: PHÂN TÍCH & CHỐT SỐ ---
        
        # 1. Top Chạm & Bộ (Tính lại điểm hiển thị)
        self._update_analytics_tab(pos_bridges, kill_bridges, market_stats, touch_combos)
        
        # 2. Chốt Số (Forecast)
        self._update_forecast_tab(scores, strong_sets, matrix_result)

    def _update_analytics_tab(self, pos_bridges, kill_bridges, market_stats, touch_combos):
        # Clear
        for t in [self.tree_touch, self.tree_set, self.tree_combos]:
            for i in t.get_children(): t.delete(i)
            
        # Logic tính điểm nhanh cho Top Chạm/Bộ
        touch_scores, set_scores = {}, {}
        for b in pos_bridges:
            pred = str(b.get('predicted_value', ''))
            score = float(b.get('ranking_score', 1.0))
            # (Giản lược: Tự động cộng điểm chạm/bộ từ predicted_value)
            if "CHẠM" in pred and "LOẠI" not in pred:
                try: touch_scores[int(pred.split(" ")[1])] = touch_scores.get(int(pred.split(" ")[1]), 0) + score
                except: pass
            else:
                nums = pred.replace(',', ' ').split()
                if nums:
                    unit = score/len(nums)
                    for n in nums:
                        if len(n)==2 and n.isdigit():
                            d1, d2 = int(n[0]), int(n[1])
                            touch_scores[d1] = touch_scores.get(d1,0)+unit
                            touch_scores[d2] = touch_scores.get(d2,0)+unit
                            sn = get_set_name_of_number(n)
                            if sn: set_scores[sn] = set_scores.get(sn,0)+unit

        # Trừ điểm Killer
        for k in kill_bridges:
            if "LOẠI CHẠM" in str(k.get('predicted_value','')):
                try: 
                    d = int(k['predicted_value'].split(" ")[-1])
                    if d in touch_scores: touch_scores[d] -= (k['streak'] * 1)
                except: pass

        # Fill Top Chạm
        for t, s in sorted(touch_scores.items(), key=lambda x:x[1], reverse=True)[:5]:
            gan = market_stats.get('gan_cham', {}).get(t, 0)
            self.tree_touch.insert("", "end", values=(f"C{t} (Gan {gan})", f"{s:.1f}"))
            
        # Fill Top Bộ
        for s, sc in sorted(set_scores.items(), key=lambda x:x[1], reverse=True)[:5]:
            gan = market_stats.get('gan_bo', {}).get(s, 0)
            self.tree_set.insert("", "end", values=(f"B{s} (Gan {gan})", f"{sc:.1f}"))
            
        # Fill Tổ Hợp Chạm Thông (Combos)
        if touch_combos:
            # Sort theo rate_percent
            for c in sorted(touch_combos, key=lambda x: x['rate_percent'], reverse=True)[:5]:
                touches = "".join(map(str, c['touches']))
                info = f"{c['streak']} kỳ | {c['rate_percent']:.0f}%"
                self.tree_combos.insert("", "end", values=(touches, info))

    def _update_forecast_tab(self, scores, strong_sets, matrix_result=None):
        self.txt_65.delete("1.0", tk.END)
        self.txt_10.delete("1.0", tk.END)
        self.txt_4.delete("1.0", tk.END)
        self.txt_killed.delete("1.0", tk.END) # Clear Killer box
        
        # Ưu tiên chốt theo Ma Trận Giao Thoa
        ranked = matrix_result.get("ranked") if matrix_result else []
        if ranked:
            dan_full = [x["so"] for x in ranked]
            note = f"CT {matrix_result.get('cham_thong', [])} | TL {matrix_result.get('cham_ti_le', [])} | B{matrix_result.get('bo_so_chon', [])}"
            
            # Dàn 65
            self.txt_65.insert("1.0", f"{note}\n" + ",".join(dan_full[:65]))
            
            # Top 10 & Tứ thủ
            dan_10 = sorted(dan_full[:10])
            dan_4 = sorted(dan_full[:4])
            self.txt_10.insert("1.0", ",".join(dan_10))
            self.txt_4.insert("1.0", ",".join(dan_4))
            
            # Killer giữ nguyên từ scores (nếu có)
            killed_nums = [x[0] for x in scores if x[1] < -2.0] if scores else []
            if killed_nums:
                self.txt_killed.insert("1.0", ",".join(sorted(killed_nums)))
            else:
                self.txt_killed.insert("1.0", "(Không có số bị loại)")
            return
        
        # Fallback: giữ logic V3.8 nếu chưa có ma trận
        if not scores: 
            self.txt_killed.insert("1.0", "(Không có dữ liệu)")
            return
        
        top_65_list = [x[0] for x in scores[:65]]
        self.txt_65.insert("1.0", ",".join(sorted(top_65_list)))
        
        candidates = scores[:15] 
        candidate_nums = [x[0] for x in candidates]
        top_sets = strong_sets[:3] if strong_sets else []
        prioritized = []
        others = []
        for num in candidate_nums:
            my_set = get_set_name_of_number(num)
            if my_set and my_set in top_sets:
                prioritized.append(num)
            else:
                others.append(num)
        final_top = prioritized + others
        dan_10 = sorted(final_top[:10])
        dan_4 = sorted(final_top[:4])
        self.txt_10.insert("1.0", ",".join(dan_10))
        self.txt_4.insert("1.0", ",".join(dan_4))
        
        killed_nums = [x[0] for x in scores if x[1] < -2.0]
        if killed_nums:
            killed_display = ",".join(sorted(killed_nums))
            self.txt_killed.insert("1.0", killed_display)
        else:
             self.txt_killed.insert("1.0", "(Không có số bị loại)")

    def _fill_stat_tree(self, tree, freq_dict, gan_dict, keys):
        for i in tree.get_children(): tree.delete(i)
        items = [(k, freq_dict.get(k,0), gan_dict.get(k,0)) for k in keys]
        items.sort(key=lambda x: x[2], reverse=True) # Sort gan
        for k, f, g in items:
            tag = "cold" if g > 15 else ("hot" if g < 3 else "")
            tree.insert("", "end", values=(k, f, g), tags=(tag,))

    def on_bridge_double_click(self, event):
        item = self.tree_bridges.selection()
        if not item: return
        val = self.tree_bridges.item(item[0], "values")
        name = val[0].split(" ")[-1] if " " in val[0] else val[0]
        if hasattr(self.controller, 'trigger_bridge_backtest'):
            self.controller.trigger_bridge_backtest(name, is_de=True)

    def copy_forecast(self):
        try:
            t10 = self.txt_10.get("1.0", tk.END).strip()
            t4 = self.txt_4.get("1.0", tk.END).strip()
            content = f"TOP 10: {t10}\nTỨ THỦ: {t4}"
            self.clipboard_clear()
            self.clipboard_append(content)
            messagebox.showinfo("Copy", "Đã copy Top 10 & Tứ Thủ!")
        except: pass

    