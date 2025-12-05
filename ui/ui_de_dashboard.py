# Tên file: code6/ui/ui_de_dashboard.py
# (PHIÊN BẢN V3.9.5 - FULL UI RESTORE: TABS CHAM/BO + SAFE IMPORT)

import tkinter as tk
from tkinter import ttk, messagebox
import threading

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
        run_intersection_matrix_analysis
    )
    HAS_ANALYTICS = True
except ImportError as e:
    print(f"[UI ERROR] Analytics Import Failed: {e}")
    HAS_ANALYTICS = False
    def analyze_market_trends(*a, **k): return {}
    def calculate_number_scores(*a, **k): return []
    def run_intersection_matrix_analysis(*a): return {"ranked": [], "message": str(e)}

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
        self._init_ui()

    def _init_ui(self):
        # TOOLBAR
        toolbar = ttk.Frame(self, padding=5)
        toolbar.pack(fill=tk.X)
        
        btn_scan = ttk.Button(toolbar, text="🚀 QUÉT & PHÂN TÍCH (V3.9.5)", command=self.on_scan_click)
        btn_scan.pack(side=tk.LEFT, padx=5)
        
        self.lbl_status = ttk.Label(toolbar, text="Sẵn sàng", foreground="blue")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # MAIN LAYOUT
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- COL 1: STATS (ĐÃ KHÔI PHỤC TABS) ---
        f_stats = ttk.LabelFrame(paned, text="📊 Thống Kê")
        paned.add(f_stats, weight=1)
        
        # Tạo Notebook chứa 3 tab: Lịch Sử, Chạm, Bộ
        self.nb_stats = ttk.Notebook(f_stats)
        self.nb_stats.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Lịch Sử
        self.tree_hist = self._create_tab_tree(self.nb_stats, "Lịch Sử", ["Ngày", "Đề"])
        
        # Tab 2: Chạm
        self.tree_cham = self._create_tab_tree(self.nb_stats, "Chạm", ["Chạm", "Về", "Gan"])
        
        # Tab 3: Bộ
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
        
        # Tab Chốt Số
        t_fc = ttk.Frame(nb_res)
        nb_res.add(t_fc, text="CHỐT SỐ")
        self._add_txt_block(t_fc, "Dàn 65 (Scoring):", "txt_65")
        self._add_txt_block(t_fc, "Top 10 (Ma Trận):", "txt_10")
        self._add_txt_block(t_fc, "Tứ Thủ VIP:", "txt_4")
        
        # Tab Matrix Detail
        t_mx = ttk.Frame(nb_res)
        nb_res.add(t_mx, text="CHI TIẾT")
        self.tree_mx = self._create_tree(t_mx, ["Hạng", "Số", "Điểm", "Note"])
        self.tree_mx.tag_configure("S", background="#FFCDD2")
        self.tree_mx.tag_configure("A", background="#BBDEFB")

    def _create_tree(self, parent, cols, height=None):
        """Tạo Treeview cơ bản"""
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
        """Helper tạo Tab chứa Treeview"""
        f = ttk.Frame(notebook)
        notebook.add(f, text=title)
        return self._create_tree(f, cols)

    def _add_txt_block(self, parent, label, attr):
        ttk.Label(parent, text=label, font=("bold")).pack(anchor="w")
        txt = tk.Text(parent, height=3, width=30)
        txt.pack(fill="x", padx=2, pady=2)
        setattr(self, attr, txt)

    def on_scan_click(self):
        data = getattr(self.controller, 'all_data_ai', [])
        if not data: data = getattr(self.controller, 'df', None)
        
        if not data or len(data) == 0:
            messagebox.showerror("Lỗi", "Không có dữ liệu đầu vào!")
            return
            
        self.lbl_status.config(text="Đang phân tích...", foreground="orange")
        threading.Thread(target=self._run_logic, args=(data,), daemon=True).start()

    def _run_logic(self, data):
        # 1. Chuẩn bị dữ liệu List (cho Scanner/Stats)
        list_data = data
        if hasattr(data, "values"): list_data = data.values.tolist()
        
        # 2. Run Scanner (Isolated)
        bridges = []
        if HAS_SCANNER:
            try:
                _, bridges = run_de_scanner(list_data)
            except Exception as e:
                print(f"Scanner Error: {e}")
        
        # 3. Run Matrix (Isolated)
        matrix_res = {"ranked": [], "message": "N/A"}
        if HAS_ANALYTICS:
            try:
                matrix_res = run_intersection_matrix_analysis(data)
            except Exception as e:
                print(f"Matrix Error: {e}")
                matrix_res["message"] = str(e)
                
        # 4. Run Stats & Scoring
        stats = {}
        scores = []
        if HAS_ANALYTICS:
            try:
                stats = analyze_market_trends(list_data, n_days=60)
                scores = calculate_number_scores(bridges, stats)
            except Exception as e:
                print(f"Stats Error: {e}")

        self.after(0, lambda: self._update_ui(list_data, bridges, matrix_res, scores, stats))

    def _update_ui(self, data, bridges, matrix_res, scores, stats):
        self.lbl_status.config(text="Hoàn tất.", foreground="green")
        
        # 1. Update Stats (History, Cham, Bo)
        # History
        for i in self.tree_hist.get_children(): self.tree_hist.delete(i)
        for r in reversed(data[-15:]):
            val = get_gdb_last_2(r) if isinstance(r, (list, tuple)) else str(r)
            self.tree_hist.insert("", "end", values=(r[0], val))
            
        # Cham Stats
        self._fill_stat_tree(self.tree_cham, stats.get('freq_cham', {}), stats.get('gan_cham', {}))
        
        # Bo Stats
        self._fill_stat_tree(self.tree_bo, stats.get('freq_bo', {}), stats.get('gan_bo', {}))

        # 2. Update Bridges
        for i in self.tree_br.get_children(): self.tree_br.delete(i)
        if bridges:
            bridges.sort(key=lambda x: x.get('streak',0), reverse=True)
            for b in bridges[:50]:
                self.tree_br.insert("", "end", values=(b.get('name'), b.get('type'), b.get('streak'), b.get('predicted_value')))
        
        # 3. Update Matrix & Forecast
        for i in self.tree_mx.get_children(): self.tree_mx.delete(i)
        ranked = matrix_res.get('ranked', [])
        
        if ranked:
            for item in ranked[:30]:
                self.tree_mx.insert("", "end", values=(item['rank'], item['so'], item['diem'], item['note']), tags=(item['rank'],))
            
            top10 = [x['so'] for x in ranked[:10]]
            self.txt_10.delete("1.0", tk.END); self.txt_10.insert("1.0", ",".join(top10))
            self.txt_4.delete("1.0", tk.END); self.txt_4.insert("1.0", ",".join(top10[:4]))
        else:
            self.txt_10.insert("1.0", f"Lỗi: {matrix_res.get('message')}")
            
        # 4. Update Scoring (Dàn 65)
        self.txt_65.delete("1.0", tk.END)
        if scores:
            top65 = [x[0] for x in scores[:65]]
            self.txt_65.insert("1.0", ",".join(top65))

    def _fill_stat_tree(self, tree, freq, gan):
        """Helper điền dữ liệu vào bảng thống kê"""
        for i in tree.get_children(): tree.delete(i)
        if not freq: return
        
        # Lấy tất cả key (0-9 cho chạm, hoặc tên bộ)
        all_keys = sorted(freq.keys())
        # Tạo list items
        items = []
        for k in all_keys:
            f = freq.get(k, 0)
            g = gan.get(k, 0)
            items.append((k, f, g))
            
        # Sort theo Gan giảm dần (ưu tiên hiển thị gan cao lên đầu)
        items.sort(key=lambda x: x[2], reverse=True)
        
        for k, f, g in items:
            tree.insert("", "end", values=(k, f, g))