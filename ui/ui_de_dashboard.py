# Tên file: code6/ui/ui_de_dashboard.py
# (PHIÊN BẢN V3.9.20 - FIX: HIỂN THỊ ĐỦ 15 BỘ SỐ KỂ CẢ KHI KHÔNG VỀ)

import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
from datetime import datetime, timedelta

# --- 1. IMPORT UTILS ---
try:
    from logic.de_utils import get_gdb_last_2, BO_SO_DE
except ImportError as e:
    print(f"[UI ERROR] Utils Import Failed: {e}")
    def get_gdb_last_2(r): return "00"
    BO_SO_DE = {}

# --- 2. IMPORT ANALYTICS ---
try:
    from logic.de_analytics import (
        analyze_market_trends,
        calculate_number_scores,
        run_intersection_matrix_analysis,
        calculate_top_touch_combinations
    )
    HAS_ANALYTICS = True
except ImportError as e:
    print(f"[UI ERROR] Analytics Import Failed: {e}")
    HAS_ANALYTICS = False
    def analyze_market_trends(*a, **k): return {}
    def calculate_number_scores(*a, **k): return []
    def run_intersection_matrix_analysis(*a): return {"ranked": [], "message": str(e)}
    def calculate_top_touch_combinations(*a, **k): return []

# --- 3. IMPORT SCANNER ---
try:
    from logic.bridges.de_bridge_scanner import run_de_scanner
    HAS_SCANNER = True
except ImportError as e:
    print(f"[UI ERROR] Scanner Import Failed: {e}")
    HAS_SCANNER = False
    def run_de_scanner(d): return 0, []

class UiDeDashboard(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # Define fonts
        self.font_vip = font.Font(family="Helvetica", size=14, weight="bold")
        self.font_label = font.Font(family="Helvetica", size=10, weight="bold")
        self.font_header = font.Font(family="Arial", size=11, weight="bold")
        self.font_normal = font.Font(family="Consolas", size=10)
        self._init_ui()

    def _init_ui(self):
        # TOOLBAR
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(fill=tk.X)
        
        btn_scan = ttk.Button(toolbar, text="🚀 QUÉT & PHÂN TÍCH (V3.9.20)", command=self.on_scan_click)
        btn_scan.pack(side=tk.LEFT, padx=5)
        
        self.lbl_status = ttk.Label(toolbar, text="Sẵn sàng", foreground="blue")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # MAIN LAYOUT
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- COL 1: STATS ---
        f_stats = ttk.LabelFrame(paned, text="📊 Thống Kê (30 ngày)")
        paned.add(f_stats, weight=1)
        
        self.nb_stats = ttk.Notebook(f_stats)
        self.nb_stats.pack(fill=tk.BOTH, expand=True)
        
        self.tree_hist = self._create_tab_tree(self.nb_stats, "Lịch Sử", ["Ngày", "Đề"])
        self.tree_cham = self._create_tab_tree(self.nb_stats, "Chạm", ["Chạm", "Về", "Gan"])
        self.tree_bo = self._create_tab_tree(self.nb_stats, "Bộ", ["Bộ", "Về", "Gan"])
        
        # --- COL 2: BRIDGES ---
        f_scan = ttk.LabelFrame(paned, text="🎯 Cầu Động")
        paned.add(f_scan, weight=2)
        self.tree_br = self._create_tree(f_scan, ["Tên", "Loại", "Thông", "Số"], height=15)

        # --- COL 3: MATRIX & FORECAST ---
        f_res = ttk.LabelFrame(paned, text="🔮 Ma Trận & Chốt Số")
        paned.add(f_res, weight=2)
        
        nb_res = ttk.Notebook(f_res)
        nb_res.pack(fill=tk.BOTH, expand=True)
        
        # TAB 1: CHỐT SỐ VIP
        t_fc = ttk.Frame(nb_res)
        nb_res.add(t_fc, text="CHỐT SỐ VIP")
        
        # [UI] Canvas & Scrollbar setup
        self.canvas = tk.Canvas(t_fc, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(t_fc, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        # Bind events
        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # [HEADER]
        fr_header = ttk.Frame(self.scroll_frame, padding=5)
        fr_header.pack(fill="x", pady=5)
        self.lbl_ky_pred = ttk.Label(fr_header, text="KỲ: ---", font=self.font_header, foreground="#E65100")
        self.lbl_ky_pred.pack(side="left", padx=(0, 10))
        self.lbl_date_pred = ttk.Label(fr_header, text="NGÀY: ---", font=self.font_header, foreground="#2E7D32")
        self.lbl_date_pred.pack(side="left")

        # === KHU VỰC 1: KẾT QUẢ TRỌNG TÂM ===
        fr_vip = ttk.LabelFrame(self.scroll_frame, text="🔥🔥 KẾT QUẢ TRỌNG TÂM", padding=5)
        fr_vip.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(fr_vip, text="TỨ THỦ ĐỀ:", font=self.font_label, foreground="#D32F2F").pack(anchor="center")
        self.txt_4 = tk.Text(fr_vip, height=1, width=20, font=self.font_vip, bd=0, bg="#f0f0f0", fg="#D32F2F")
        self.txt_4.tag_configure("center", justify='center')
        self.txt_4.pack(fill="x", pady=(0, 5))
        
        ttk.Label(fr_vip, text="TOP 10 MA TRẬN:", font=self.font_label, foreground="#1976D2").pack(anchor="center")
        self.txt_10 = tk.Text(fr_vip, height=1, width=30, font=("Helvetica", 11, "bold"), bd=0, bg="#f0f0f0", fg="#1976D2")
        self.txt_10.tag_configure("center", justify='center')
        self.txt_10.pack(fill="x", pady=(0, 5))

        # === KHU VỰC 2: CẦU & BỘ ===
        fr_cau = ttk.LabelFrame(self.scroll_frame, text="⚡ BỘ SỐ & CẦU CHẠM", padding=5)
        fr_cau.pack(fill="x", padx=5, pady=5)
        
        self.txt_bo_top = self._create_info_row(fr_cau, "Bộ Số Tiềm Năng:", height=2)
        
        self.txt_4c_thong = self._create_info_row(fr_cau, "4 Chạm (Thông):")
        self.txt_4c_tile = self._create_info_row(fr_cau, "4 Chạm (Tỉ Lệ):")

        # === KHU VỰC 3: DÀN SỐ ===
        fr_dan = ttk.LabelFrame(self.scroll_frame, text="📋 DÀN SỐ & LỌC", padding=5)
        fr_dan.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(fr_dan, text="Dàn 65 (Tăng dần):", font=("Arial", 9, "bold")).pack(anchor="w")
        self.txt_65 = tk.Text(fr_dan, height=6, width=30, font=("Consolas", 9), wrap="word", bd=1, relief="solid")
        self.txt_65.pack(fill="x", pady=2)

        # TAB 2: CHI TIẾT SỐ
        t_mx = ttk.Frame(nb_res)
        nb_res.add(t_mx, text="ĐIỂM SỐ")
        self.tree_mx = self._create_tree(t_mx, ["Hạng", "Số", "Điểm", "Note"])
        self.tree_mx.tag_configure("S", background="#FFCDD2") 
        self.tree_mx.tag_configure("A", background="#C8E6C9")

        # TAB 3: ĐÁNH GIÁ BỘ/CHẠM
        t_eval = ttk.Frame(nb_res)
        nb_res.add(t_eval, text="ĐÁNH GIÁ BỘ/CHẠM")
        
        self.tree_eval = self._create_tree(t_eval, ["Loại", "Giá Trị", "Về (30N)", "Gan", "Điểm ĐG"])
        self.tree_eval.column("Loại", width=60)
        self.tree_eval.column("Giá Trị", width=80)
        self.tree_eval.column("Điểm ĐG", width=70)
        self.tree_eval.tag_configure("HOT", background="#FFF9C4", foreground="red") 

    def update_data(self, *args):
        try:
            if self.winfo_exists():
                self.on_scan_click()
        except Exception as e:
            print(f"[UiDeDashboard] Update Data Error: {e}")

    # --- UI HELPERS ---
    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _create_info_row(self, parent, label_text, height=1):
        container = ttk.Frame(parent)
        container.pack(fill="x", pady=2)
        ttk.Label(container, text=label_text, font=("Arial", 9, "bold"), width=15, anchor="w").pack(side="left")
        txt = tk.Text(container, height=height, font=("Consolas", 9), wrap="word", bd=1, relief="solid")
        txt.pack(side="left", fill="x", expand=True)
        return txt

    def _create_tree(self, parent, cols, height=None):
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=height if height else 8)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=50, anchor="center")
        sb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        return tree

    def _create_tab_tree(self, notebook, title, cols):
        f = ttk.Frame(notebook)
        notebook.add(f, text=title)
        return self._create_tree(f, cols)

    def _update_txt(self, widget, text, tag=None):
        widget.config(state='normal')
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        if tag: widget.tag_add(tag, "1.0", "end")
        widget.config(state='disabled')

    def on_scan_click(self):
        data = getattr(self.controller, 'all_data_ai', [])
        if not data: data = getattr(self.controller, 'df', None)
        if not data or len(data) == 0:
            print("[UiDeDashboard] No data available for scan.")
            return 
        self.lbl_status.config(text="Đang phân tích...", foreground="orange")
        threading.Thread(target=self._run_logic, args=(data,), daemon=True).start()

    def _run_logic(self, data):
        list_data = data
        if hasattr(data, "values"): list_data = data.values.tolist()
        
        bridges = []
        if HAS_SCANNER:
            try: _, bridges = run_de_scanner(list_data)
            except: pass
        
        matrix_res = {"ranked": [], "message": "N/A"}
        if HAS_ANALYTICS:
            try: matrix_res = run_intersection_matrix_analysis(data)
            except Exception as e: matrix_res["message"] = str(e)
                
        stats, scores, touch_combinations = {}, [], []
        if HAS_ANALYTICS:
            try:
                stats = analyze_market_trends(list_data, n_days=30)
                scores = calculate_number_scores(bridges, stats)
                touch_combinations = calculate_top_touch_combinations(list_data, num_touches=4, days=30)
            except: pass

        self.after(0, lambda: self._update_ui(list_data, bridges, matrix_res, scores, stats, touch_combinations))

    def _update_ui(self, data, bridges, matrix_res, scores, stats, touch_combinations):
        self.lbl_status.config(text="Hoàn tất.", foreground="green")
        
        # 1. Update Header
        next_ky_str, next_date_str = "---", "---"
        try:
            if data and len(data) > 0:
                last_row = data[-1]
                try: next_ky_str = f"#{int(last_row[0]) + 1}"
                except: pass
                # Date
                for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                    try:
                        dt = datetime.strptime(str(last_row[1]), fmt)
                        next_date_str = (dt + timedelta(days=1)).strftime("%d/%m/%Y")
                        break
                    except ValueError: continue
        except: pass
        self.lbl_ky_pred.config(text=f"KỲ: {next_ky_str}")
        self.lbl_date_pred.config(text=f"NGÀY: {next_date_str}")
        
        # 2. Update Stats (Left Tabs)
        for i in self.tree_hist.get_children(): self.tree_hist.delete(i)
        for r in reversed(data[-30:]):
            val = get_gdb_last_2(r) if isinstance(r, (list, tuple)) else str(r)
            self.tree_hist.insert("", "end", values=(r[0], val))
            
        freq_cham = stats.get('freq_cham', {})
        gan_cham = stats.get('gan_cham', {})
        freq_bo = stats.get('freq_bo', {})
        gan_bo = stats.get('gan_bo', {})

        self._fill_stat_tree(self.tree_cham, freq_cham, gan_cham)
        
        # [FIX V3.9.20] Hiển thị đủ 15 Bộ kể cả khi không về
        self._fill_stat_tree_full_bo(self.tree_bo, freq_bo, gan_bo)

        # 3. Update Bridges
        for i in self.tree_br.get_children(): self.tree_br.delete(i)
        if bridges:
            bridges.sort(key=lambda x: x.get('streak',0), reverse=True)
            for b in bridges[:50]:
                self.tree_br.insert("", "end", values=(b.get('name'), b.get('type'), b.get('streak'), b.get('predicted_value')))
        
        # 4. Update Matrix (Scores Tab)
        for i in self.tree_mx.get_children(): self.tree_mx.delete(i)
        ranked = matrix_res.get('ranked', [])
        if ranked:
            for item in ranked[:30]:
                self.tree_mx.insert("", "end", values=(item['rank'], item['so'], item['diem'], item['note']), tags=(item['rank'],))
            top10 = [x['so'] for x in ranked[:10]]
            self._update_txt(self.txt_10, ", ".join(top10), "center")
            self._update_txt(self.txt_4,  " - ".join(top10[:4]), "center")
        else:
            self._update_txt(self.txt_10, f"Lỗi: {matrix_res.get('message')}")
            
        # 5. Update Dan 65
        if scores:
            top65 = [x[0] for x in scores[:65]]
            top65.sort()
            self._update_txt(self.txt_65, ",".join(top65))
        else: self._update_txt(self.txt_65, "")

        # 6. Touch Combos
        if touch_combinations:
            top_streak = sorted(touch_combinations, key=lambda x: x['streak'], reverse=True)[:3]
            str_streak = " | ".join([f"C{','.join(map(str, x['touches']))}({x['streak']}N)" for x in top_streak])
            
            top_rate = sorted(touch_combinations, key=lambda x: x['rate_percent'], reverse=True)[:3]
            str_rate = " | ".join([f"C{','.join(map(str, x['touches']))}({x['rate_percent']:.0f}%)" for x in top_rate])
            
            self._update_txt(self.txt_4c_thong, str_streak)
            self._update_txt(self.txt_4c_tile, str_rate)
        else:
            self._update_txt(self.txt_4c_thong, "---")
            self._update_txt(self.txt_4c_tile, "---")
            
        # 7. UPDATE EVALUATION & TOP SETS
        self._update_evaluation_and_top_sets(freq_bo, gan_bo, freq_cham, gan_cham)

    def _update_evaluation_and_top_sets(self, freq_bo, gan_bo, freq_cham, gan_cham):
        for i in self.tree_eval.get_children(): self.tree_eval.delete(i)
        
        # [FIX] CẬP NHẬT LOGIC HIỂN THỊ BỘ (Quét hết BO_SO_DE.keys())
        bo_scores = []
        if BO_SO_DE:
            # Lấy danh sách tất cả các bộ từ utils (đảm bảo đủ 15 bộ)
            all_bo_names = list(BO_SO_DE.keys())
            for bo in all_bo_names:
                f = freq_bo.get(bo, 0)
                g = gan_bo.get(bo, 30) # Default Gan 30 ngày nếu không thấy
                # Điểm: Tần suất * 1.5 - Gan * 0.5
                score = (f * 1.5) - (float(g) * 0.5)
                bo_scores.append({"type": "BỘ", "val": bo, "f": f, "g": g, "s": score})
        else:
            # Fallback nếu BO_SO_DE rỗng (hiếm)
            for bo, freq in freq_bo.items():
                bo_scores.append({"type": "BỘ", "val": bo, "f": freq, "g": 0, "s": 0})

        cham_scores = []
        for ch, freq in freq_cham.items():
            gan = gan_cham.get(ch, 0)
            score = (freq * 2.0) - (float(gan) * 0.5)
            cham_scores.append({"type": "CHẠM", "val": str(ch), "f": freq, "g": gan, "s": score})
            
        all_items = bo_scores + cham_scores
        all_items.sort(key=lambda x: x['s'], reverse=True)
        
        for item in all_items:
            tags = ()
            if item['s'] >= 5.0: tags = ("HOT",) 
            self.tree_eval.insert("", "end", values=(item['type'], item['val'], item['f'], item['g'], f"{item['s']:.1f}"), tags=tags)
            
        top_bo = sorted(bo_scores, key=lambda x: x['s'], reverse=True)[:5]
        str_top_bo = " | ".join([f"Bộ {b['val']} ({b['s']:.1f}đ)" for b in top_bo])
        self._update_txt(self.txt_bo_top, str_top_bo)

    def _fill_stat_tree(self, tree, freq, gan):
        for i in tree.get_children(): tree.delete(i)
        if not freq: return
        all_keys = sorted(freq.keys())
        items = []
        for k in all_keys:
            items.append((k, freq.get(k, 0), gan.get(k, 0)))
        items.sort(key=lambda x: x[2], reverse=True)
        for k, f, g in items:
            tree.insert("", "end", values=(k, f, g))

    # [NEW Helper] Hàm điền bảng thống kê Bộ riêng (Full 15 bộ)
    def _fill_stat_tree_full_bo(self, tree, freq, gan):
        for i in tree.get_children(): tree.delete(i)
        # Nếu có BO_SO_DE thì lấy key từ đó, nếu không thì lấy từ freq
        keys_to_scan = list(BO_SO_DE.keys()) if BO_SO_DE else sorted(freq.keys())
        
        items = []
        for k in keys_to_scan:
            f = freq.get(k, 0)
            g = gan.get(k, 30)
            items.append((k, f, g))
            
        # Sort theo Gan giảm dần để dễ nhìn các bộ lâu chưa về
        items.sort(key=lambda x: x[2], reverse=True)
        
        for k, f, g in items:
            tree.insert("", "end", values=(k, f, g))