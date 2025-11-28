# Tên file: git1/ui/ui_de_dashboard.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading

try:
    from logic.de_utils import BO_SO_DE, check_cham, check_tong, get_gdb_last_2
    from logic.de_analytics import (
        analyze_market_trends, 
        get_de_consensus, 
        calculate_number_scores, 
        get_top_strongest_sets
    )
    from logic.bridges.de_bridge_scanner import run_de_scanner
    from logic.bridges.bridge_manager_de import de_manager
except ImportError:
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
        ttk.Button(toolbar, text="🚀 1. Cập Nhật Phong Độ (V78)", command=self.on_update_cache_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 2. Phân Tích Thị Trường", command=self.on_analyze_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 3. Quét Cầu & Chốt Số (V77)", command=self.on_scan_click).pack(side=tk.LEFT, padx=2)
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
        
        tab_history = ttk.Frame(nb_left)
        nb_left.add(tab_history, text="Lịch Sử")
        self.tree_history = ttk.Treeview(tab_history, columns=("date", "gdb", "de"), show="headings", height=15)
        self.tree_history.heading("date", text="Ngày"); self.tree_history.column("date", width=80)
        self.tree_history.heading("gdb", text="GĐB"); self.tree_history.column("gdb", width=70)
        self.tree_history.heading("de", text="Đề"); self.tree_history.column("de", width=40, anchor="center")
        self.tree_history.pack(fill=tk.BOTH, expand=True)

        self._init_stat_tabs(nb_left)

        # --- COL 2: KẾT QUẢ QUÉT (CENTER) ---
        frame_mid = ttk.LabelFrame(paned, text="🌉 Kết Quả Quét", padding=5)
        paned.add(frame_mid, weight=2)
        
        cols = ("name", "predict", "streak", "form", "hp")
        self.tree_bridges = ttk.Treeview(frame_mid, columns=cols, show="headings", selectmode="extended")
        self.tree_bridges.heading("name", text="Vị Trí (Quy luật)")
        self.tree_bridges.column("name", width=140)
        self.tree_bridges.heading("predict", text="Báo Số")
        self.tree_bridges.column("predict", width=100, anchor="center")
        self.tree_bridges.heading("streak", text="Thông")
        self.tree_bridges.column("streak", width=60, anchor="center")
        self.tree_bridges.heading("form", text="Phong Độ")
        self.tree_bridges.column("form", width=80, anchor="center")
        self.tree_bridges.heading("hp", text="Máu")
        self.tree_bridges.column("hp", width=60, anchor="center")
        
        self.tree_bridges.pack(fill=tk.BOTH, expand=True)
        # Bind double-click event
        self.tree_bridges.bind("<Double-1>", self.on_bridge_double_click)
        # Test: Bind cả Button-1 để debug
        self.tree_bridges.bind("<Button-1>", lambda e: print(f"[DEBUG] Button-1 clicked on tree_bridges"))
        print("[DEBUG] Double-click event đã được bind vào tree_bridges")

        # --- COL 3: CHỐT SỐ (RIGHT) ---
        frame_right = ttk.Frame(paned)
        paned.add(frame_right, weight=2)
        
        # 1. Manual Tool
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
        
        # 2. Final Score
        grp_score = ttk.LabelFrame(frame_right, text="🏆 CHỐT SỐ FINAL (V77 Ultimate)", padding=5)
        grp_score.pack(fill=tk.BOTH, expand=True)
        
        f_ind = ttk.Frame(grp_score)
        f_ind.pack(fill=tk.X, pady=5)
        self.lbl_cham_thong = ttk.Label(f_ind, text="💎 Chạm Thông: ...", foreground="red", font=("Arial", 10, "bold"))
        self.lbl_cham_thong.pack(anchor="w")
        self.lbl_cham_rate = ttk.Label(f_ind, text="⭐ Chạm Tỉ Lệ: ...", foreground="blue", font=("Arial", 10, "bold"))
        self.lbl_cham_rate.pack(anchor="w")
        self.lbl_bo_dep = ttk.Label(f_ind, text="📦 Bộ Đẹp: ...", foreground="green", font=("Arial", 10, "bold"))
        self.lbl_bo_dep.pack(anchor="w")

        self.nb_result = ttk.Notebook(grp_score)
        self.nb_result.pack(fill=tk.BOTH, expand=True)
        
        self.tab_65 = ttk.Frame(self.nb_result); self.nb_result.add(self.tab_65, text="Dàn 65")
        self.txt_65 = tk.Text(self.tab_65, wrap=tk.WORD); self.txt_65.pack(fill=tk.BOTH, expand=True)
        
        self.tab_10 = ttk.Frame(self.nb_result); self.nb_result.add(self.tab_10, text="Top 10")
        self.txt_10 = tk.Text(self.tab_10, wrap=tk.WORD, font=("Arial", 11)); self.txt_10.pack(fill=tk.BOTH, expand=True)
        
        self.tab_4 = ttk.Frame(self.nb_result); self.nb_result.add(self.tab_4, text="Tứ Thủ")
        self.txt_4 = tk.Text(self.tab_4, wrap=tk.WORD, font=("Arial", 14, "bold"), fg="red"); self.txt_4.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(grp_score, text="📋 Copy", command=self.copy_current_tab).pack(fill=tk.X, pady=5)

    def _init_stat_tabs(self, nb):
        for label, suffix in [("Chạm", "cham"), ("Tổng", "tong"), ("Bộ", "bo")]:
            tab = ttk.Frame(nb)
            nb.add(tab, text=label)
            tree = ttk.Treeview(tab, columns=("val", "freq", "gan"), show="headings")
            tree.heading("val", text=label); tree.column("val", width=35, anchor="center")
            tree.heading("freq", text="Về"); tree.column("freq", width=35, anchor="center")
            tree.heading("gan", text="Gan"); tree.column("gan", width=35, anchor="center")
            tree.pack(fill=tk.BOTH, expand=True)
            tree.tag_configure("hot", background="#C3FDB8"); tree.tag_configure("cold", foreground="red")
            setattr(self, f"tree_{suffix}", tree)

    def get_data(self): return self.controller.all_data_ai if hasattr(self.controller, 'all_data_ai') else []
        
    def update_data(self, df): self.on_analyze_click()

    def on_analyze_click(self):
        if 'analyze_market_trends' not in globals(): return
        data = self.get_data()
        if not data: return
        for r in self.tree_history.get_children(): self.tree_history.delete(r)
        for r in reversed(data[-30:]):
            g = str(r[2]); d = get_gdb_last_2(r)
            self.tree_history.insert("", "end", values=(r[0], g, d if d else ""))
        stats = analyze_market_trends(data)
        self._populate_sorted_tree(self.tree_cham, stats.get('freq_cham', {}), stats.get('gan_cham', {}), range(10))
        self._populate_sorted_tree(self.tree_tong, stats.get('freq_tong', {}), stats.get('gan_tong', {}), range(10))
        self._populate_sorted_tree(self.tree_bo, stats.get('freq_bo', {}), stats.get('gan_bo', {}), BO_SO_DE.keys())
        self.lbl_status.config(text="Đã cập nhật.", foreground="green")

    def _populate_sorted_tree(self, tree, freq_dict, gan_dict, keys):
        for row in tree.get_children(): tree.delete(row)
        data_list = []
        for k in keys:
            f = freq_dict.get(k, 0); g = gan_dict.get(k, 0)
            data_list.append((k, f, g))
        data_list.sort(key=lambda x: x[2])
        for item in data_list:
            val, f, g = item
            tags = ()
            # SỬA LỖI SYNTAX Ở ĐÂY
            if g < 3: 
                tags = ("hot",)
            elif g > 10: 
                tags = ("cold",)
            tree.insert("", "end", values=(val, f, g), tags=tags)

    def on_update_cache_click(self):
        data = self.get_data()
        if not data: return
        self.lbl_status.config(text="Đang cập nhật Hồ sơ Phong độ...", foreground="blue")
        threading.Thread(target=self._run_cache_update, args=(data,)).start()

    def _run_cache_update(self, data):
        self.after(0, lambda: self._update_history_ui(data))
        if 'de_manager' in globals():
            count, active_bridges = de_manager.update_daily_stats(data)
            self.found_bridges = active_bridges
            self.scores = calculate_number_scores(active_bridges)
            self.strong_sets = get_top_strongest_sets(active_bridges)
            self.after(0, self._update_ui_final)

    def _update_history_ui(self, data):
        for r in self.tree_history.get_children(): self.tree_history.delete(r)
        for r in reversed(data[-30:]):
            g = str(r[2]); d = get_gdb_last_2(r)
            self.tree_history.insert("", "end", values=(r[0], g, d if d else ""))

    def on_scan_click(self):
        if 'run_de_scanner' not in globals(): messagebox.showerror("Lỗi", "Chưa tải Scanner."); return
        data = self.get_data()
        if not data: return
        self.lbl_status.config(text="Đang Vét Cạn...", foreground="orange")
        threading.Thread(target=self._run_scan, args=(data,)).start()
        
    def _run_scan(self, data):
        count, bridges = run_de_scanner(data)
        self.found_bridges = bridges
        self.scores = calculate_number_scores(bridges)
        self.strong_sets = get_top_strongest_sets(bridges)
        
        # Top 4 Chạm (Consensus)
        consensus = get_de_consensus(bridges)
        top_cham_list = consensus.get('consensus_cham', [])[:4]
        self.top_touches = [str(item[0]) for item in top_cham_list]
        self.after(0, self._update_scan_ui)
        
    def _update_scan_ui(self):
        for row in self.tree_bridges.get_children(): self.tree_bridges.delete(row)
        
        # Đảm bảo self.strong_sets được khởi tạo
        if not hasattr(self, 'strong_sets') or self.strong_sets is None:
            self.strong_sets = []
        
        best_thong_val = None
        best_rate_val = None
        max_streak_found = -1
        max_rate_found = -1.0  # Sử dụng float để so sánh win_rate
        
        # Helper: Chuyển tên Bộ thành chuỗi chạm (VD: Bộ 01 -> "0,1,5,6")
        def expand_bo_to_touch(bo_name):
            if bo_name in BO_SO_DE:
                digits = set()
                for n in BO_SO_DE[bo_name]: digits.add(n[0]); digits.add(n[1])
                return ",".join(sorted(list(digits)))
            return bo_name

        # DUYỆT CẦU ĐỂ HIỂN THỊ VÀ TÌM BEST
        for i, b in enumerate(self.found_bridges):
            try:
                p_val = b.get('predicted_value', '')
                b_type = str(b.get('type', '')).upper()
                
                lbl_type = "Cầu Thông"
                if 'BO' in b_type: lbl_type = "Cầu Bộ"
                elif 'TI_LE' in b_type: lbl_type = "Cầu Tỉ Lệ"
                
                p_text = f"Bộ {p_val}" if 'BO' in b_type else f"Chạm {p_val}"
                info = f"{b.get('streak', 0)} kỳ" if 'THONG' in b_type else f"{b.get('win_rate', 0):.0f}%"
                if 'BO' in b_type and 'THONG' in b_type: info += " (🔥)"
                
                # For old format compatibility
                wins_10 = b.get('wins_10', 0)
                hp = b.get('hp', 3)
                form_show = f"{wins_10}/10" if wins_10 > 0 else info
                hp_show = "❤️" * hp if hp <= 3 else str(hp)
                
                self.tree_bridges.insert("", "end", iid=i, values=(b.get('name', ''), p_text, b.get('streak', 0), form_show, hp_show))
                
                # --- LOGIC TÌM BEST (FIXED) ---
                # 1. Tìm Chạm Thông Tốt Nhất (Ưu tiên Streak cao nhất)
                # Đảm bảo streak là số hợp lệ
                streak = b.get('streak', 0)
                if not isinstance(streak, (int, float)):
                    try:
                        streak = float(streak) if streak else 0
                    except (ValueError, TypeError):
                        streak = 0
                
                if streak > max_streak_found:
                    max_streak_found = streak
                    if 'BO' in b_type:
                        best_thong_val = expand_bo_to_touch(p_val) # Bung Bộ ra chạm
                    else:
                        best_thong_val = str(p_val) if p_val else None
                
                # 2. Tìm Chạm Tỉ Lệ Tốt Nhất (Ưu tiên WinRate cao nhất)
                # Đảm bảo win_rate là số hợp lệ và >= 0
                win_rate = b.get('win_rate', 0)
                if not isinstance(win_rate, (int, float)):
                    try:
                        win_rate = float(win_rate) if win_rate else 0
                    except (ValueError, TypeError):
                        win_rate = 0
                
                if win_rate >= 0 and win_rate > max_rate_found:
                    max_rate_found = win_rate
                    if 'BO' in b_type:
                        best_rate_val = expand_bo_to_touch(p_val)
                    else:
                        best_rate_val = str(p_val) if p_val else None
            except Exception as e:
                # Bỏ qua lỗi và tiếp tục với cầu tiếp theo
                print(f"Lỗi xử lý cầu {i}: {e}")
                continue

        # Nếu không tìm thấy tỉ lệ (hiếm), fallback
        if not best_rate_val and best_thong_val:
            best_rate_val = best_thong_val
        
        # Đảm bảo giá trị không None trước khi hiển thị
        cham_thong_display = best_thong_val if best_thong_val else '...'
        cham_rate_display = best_rate_val if best_rate_val else '...'
        
        self.lbl_cham_thong.config(text=f"💎 Chạm Thông: {cham_thong_display}")
        self.lbl_cham_rate.config(text=f"⭐ Chạm Tỉ Lệ: {cham_rate_display}")
        
        # Đảm bảo self.strong_sets tồn tại và là list
        if not hasattr(self, 'strong_sets') or not isinstance(self.strong_sets, list):
            self.strong_sets = []
        
        top3_sets = self.strong_sets[:3] if self.strong_sets else []
        bo_dep_display = ', '.join(top3_sets) if top3_sets else '...'
        self.lbl_bo_dep.config(text=f"📦 Bộ Đẹp: {bo_dep_display}")

        # Update Dàn
        if self.scores:
            top_65_list = [x[0] for x in self.scores[:65]]
            priority_nums = []
            backup_nums = []
            
            for num in top_65_list:
                found_bo = None
                for bn, bl in BO_SO_DE.items():
                    if num in bl: found_bo = bn; break
                if found_bo and found_bo in top3_sets: priority_nums.append(num)
                else: backup_nums.append(num)
            
            final_sorted = priority_nums + backup_nums
            dan_10 = sorted(final_sorted[:10])
            dan_4 = sorted(final_sorted[:4])
            
            self.txt_65.delete("1.0", tk.END); self.txt_65.insert("1.0", ",".join(sorted(top_65_list)))
            self.txt_10.delete("1.0", tk.END); self.txt_10.insert("1.0", ",".join(dan_10))
            self.txt_4.delete("1.0", tk.END); self.txt_4.insert("1.0", ",".join(dan_4))
            
        self.lbl_status.config(text=f"Xong. Tìm thấy {len(self.found_bridges)} cầu.", foreground="green")

    def _update_ui_final(self):
        for r in self.tree_bridges.get_children(): self.tree_bridges.delete(r)
        best_rank, best_form = None, None
        
        for b in self.found_bridges:
            p_val = b['predicted_value']
            p_show = f"Bộ {p_val}" if "Bộ" in b.get('name','') else f"Chạm {p_val}"
            
            wins_10 = b.get('wins_10', 0)
            form_show = f"{wins_10}/10" + (" 🔥" if wins_10 >= 8 else "")
            hp = b.get('hp', 3)
            hp_show = "❤️❤️❤️"[:hp] if hp <= 3 else str(hp)
            
            self.tree_bridges.insert("", "end", values=(b['name'], p_show, b['streak'], form_show, hp_show))
            
            if not best_rank: best_rank = p_val
            if (not best_form or wins_10 > 8) and wins_10 >= 5: 
                if not best_form: best_form = p_val

        self.lbl_cham_thong.config(text=f"💎 Top Rank: {best_rank or '...'}")
        self.lbl_cham_rate.config(text=f"⭐ Top Form: {best_form or '...'}")
        
        # Đảm bảo self.strong_sets tồn tại và là list
        if not hasattr(self, 'strong_sets') or not isinstance(self.strong_sets, list):
            self.strong_sets = []
        
        top3_sets_final = self.strong_sets[:3] if self.strong_sets else []
        bo_dep_final = ', '.join(top3_sets_final) if top3_sets_final else '...'
        self.lbl_bo_dep.config(text=f"📦 Bộ Đẹp: {bo_dep_final}")
        
        # Update text widgets
        if self.scores:
            top_65 = [x[0] for x in self.scores[:65]]
            self.txt_65.delete("1.0", tk.END); self.txt_65.insert("1.0", ",".join(sorted(top_65)))
            
            priority_nums = []
            backup_nums = []
            top3_sets = self.strong_sets[:3]
            for num in top_65:
                found_bo = None
                for bn, bl in BO_SO_DE.items():
                    if num in bl: found_bo = bn; break
                if found_bo and found_bo in top3_sets: priority_nums.append(num)
                else: backup_nums.append(num)
            
            final_sorted = priority_nums + backup_nums
            dan_10 = sorted(final_sorted[:10])
            dan_4 = sorted(final_sorted[:4])
            self.txt_10.delete("1.0", tk.END); self.txt_10.insert("1.0", ",".join(dan_10))
            self.txt_4.delete("1.0", tk.END); self.txt_4.insert("1.0", ",".join(dan_4))
        
        self.lbl_status.config(text=f"V78: Đang nuôi {len(self.found_bridges)} cầu.", foreground="green")

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
        self.txt_manual.delete("1.0", tk.END); self.txt_manual.insert("1.0", ",".join(result))

    def on_bridge_select(self, event): pass
    
    def on_bridge_double_click(self, event):
        """Xử lý double-click trên cầu để mở backtest popup."""
        print(f"[DEBUG] on_bridge_double_click được gọi! Event: {event}")
        try:
            # Kiểm tra controller có tồn tại không
            if not hasattr(self, 'controller') or self.controller is None:
                print("[ERROR] Controller chưa được khởi tạo.")
                messagebox.showwarning("Lỗi", "Controller chưa được khởi tạo. Vui lòng đợi một chút và thử lại.")
                return
            
            print(f"[DEBUG] Controller OK: {type(self.controller)}")
            
            # Lấy item được chọn từ event (giống như ui_dashboard.py)
            widget = event.widget
            print(f"[DEBUG] Widget: {widget}, Tree bridges: {self.tree_bridges}")
            
            # Sử dụng focus() để lấy item được chọn (giống ui_dashboard.py)
            item_id = widget.focus()
            print(f"[DEBUG] Item ID từ focus: {item_id}")
            
            if not item_id:
                print("[DEBUG] Không có item được chọn.")
                return
            
            # Lấy giá trị từ item
            item = widget.item(item_id)
            values = item.get("values", [])
            print(f"[DEBUG] Values: {values}")
            
            if not values or len(values) == 0:
                print("[DEBUG] Values rỗng.")
                return
            
            # Lấy tên cầu từ cột đầu tiên (name)
            bridge_name = values[0] if values else ""
            print(f"[DEBUG] Bridge name: '{bridge_name}'")
            
            if bridge_name:
                # Gọi Controller với cờ báo hiệu là cầu Đề
                if hasattr(self.controller, 'trigger_bridge_backtest'):
                    print(f"[DEBUG] Gọi trigger_bridge_backtest với bridge_name='{bridge_name}', is_de=True")
                    self.controller.trigger_bridge_backtest(bridge_name, is_de=True)
                    print("[DEBUG] trigger_bridge_backtest đã được gọi.")
                else:
                    print(f"[ERROR] Controller không có method trigger_bridge_backtest.")
                    messagebox.showerror("Lỗi", "Controller không có method trigger_bridge_backtest.")
            else:
                print("[DEBUG] Bridge name rỗng.")
        except Exception as e:
            print(f"[ERROR] Lỗi khi double-click cầu: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Lỗi", f"Lỗi khi double-click: {e}")

    def copy_current_tab(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.nb_result.nametowidget(self.nb_result.select()).winfo_children()[0].get("1.0", tk.END).strip())
            messagebox.showinfo("Copy", "Đã copy!")
        except: pass