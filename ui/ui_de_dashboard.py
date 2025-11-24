import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from logic.bridges.de_bridge_scanner import DeBridgeScanner
from logic.utils import setup_logger

BO_SO_DE = {
    "01": ["01", "06", "10", "15", "51", "60", "56", "65"],
    "02": ["02", "07", "20", "70", "25", "52", "57", "75"],
    "03": ["03", "08", "30", "80", "35", "53", "58", "85"],
    "04": ["04", "09", "40", "90", "45", "54", "59", "95"],
    "12": ["12", "21", "17", "71", "26", "62", "67", "76"],
    "13": ["13", "31", "18", "81", "36", "63", "68", "86"],
    "14": ["14", "41", "19", "91", "46", "64", "69", "96"],
    "23": ["23", "32", "28", "82", "37", "73", "78", "87"],
    "24": ["24", "42", "29", "92", "47", "74", "79", "97"],
    "34": ["34", "43", "39", "93", "48", "84", "89", "98"],
    "00": ["00", "05", "50", "55"],
    "11": ["11", "16", "61", "66"],
    "22": ["22", "27", "72", "77"],
    "33": ["33", "38", "83", "88"],
    "44": ["44", "49", "94", "99"]
}

class UiDeDashboard(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.scanner = DeBridgeScanner()
        self.df = None
        self.active_bridges = []
        self.init_ui()
    def init_ui(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # --- FRAME 1: THỐNG KÊ (LEFT) ---
        frame_stats = ttk.LabelFrame(paned, text="📊 Thống Kê Thị Trường (30 Kỳ)")
        paned.add(frame_stats, weight=1)
        # Bảng Thống kê Chạm
        self.tree_stats = ttk.Treeview(frame_stats, columns=("cham", "freq", "gan"), show="headings", height=12)
        self.tree_stats.heading("cham", text="Chạm")
        self.tree_stats.heading("freq", text="Xuất Hiện")
        self.tree_stats.heading("gan", text="Gan (Ngày)")
        self.tree_stats.column("cham", width=50, anchor="center")
        self.tree_stats.column("freq", width=70, anchor="center")
        self.tree_stats.column("gan", width=70, anchor="center")
        self.tree_stats.pack(fill=tk.X, padx=5, pady=5)
        # Bảng Thống kê Bộ Số
        self.tree_boso = ttk.Treeview(frame_stats, columns=("bo", "count", "content"), show="headings", height=8)
        self.tree_boso.heading("bo", text="Bộ")
        self.tree_boso.heading("count", text="Tần Suất")
        self.tree_boso.heading("content", text="Chi Tiết")
        self.tree_boso.column("bo", width=45, anchor="center")
        self.tree_boso.column("count", width=65, anchor="center")
        self.tree_boso.column("content", width=165, anchor="w")
        self.tree_boso.pack(fill=tk.X, padx=2, pady=(0,5))
        # --- FRAME 2: SOI CẦU (CENTER) ---
        frame_bridges = ttk.LabelFrame(paned, text="🔍 Cầu Đề Đang Chạy")
        paned.add(frame_bridges, weight=2)
        btn_scan = ttk.Button(frame_bridges, text="Quét Cầu Mới Ngay", command=self.on_scan_click)
        btn_scan.pack(pady=5)
        self.tree_bridges = ttk.Treeview(frame_bridges, columns=("id", "val", "streak"), show="headings")
        self.tree_bridges.heading("id", text="#")
        self.tree_bridges.heading("val", text="Báo Chạm")
        self.tree_bridges.heading("streak", text="Độ Thông")
        self.tree_bridges.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # --- FRAME 3: DỰ ĐOÁN (RIGHT) ---
        frame_predict = ttk.LabelFrame(paned, text="🎯 Chốt Số Dự Đoán")
        paned.add(frame_predict, weight=2)
        tk.Label(frame_predict, text="Top 4 Chạm:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5)
        self.lbl_top_chams = tk.Label(frame_predict, text="---", fg="blue", font=("Arial", 12, "bold"))
        self.lbl_top_chams.pack(fill=tk.X, padx=5)
        tk.Label(frame_predict, text="Dàn 65 Số (Full Chạm):", font=("Arial", 10, "bold")).pack(anchor="w", padx=5, pady=(10,0))
        self.txt_dan_65 = tk.Text(frame_predict, height=8, width=30)
        self.txt_dan_65.pack(fill=tk.X, padx=5)
        tk.Label(frame_predict, text="Top 10 (Kết):", font=("Arial", 10, "bold")).pack(anchor="w", padx=5, pady=(10,0))
        self.lbl_top_10 = tk.Label(frame_predict, text="---", fg="red", font=("Arial", 11, "bold"))
        self.lbl_top_10.pack(fill=tk.X, padx=5)
    def update_data(self, df: pd.DataFrame):
        self.df = df
        self.calculate_market_stats()
    def calculate_market_stats(self):
        if self.df is None or len(self.df) < 30:
            return
        recent = self.df.tail(30)
        # Tính tần suất và gan
        freq = {i: 0 for i in range(10)}
        # Bộ số Đề
        boso_count = {bo: 0 for bo in BO_SO_DE}
        # Duyệt từng kỳ
        for idx, row in recent.iterrows():
            gdb = str(row.get('GDB', ''))
            if len(gdb) >= 2:
                c1 = int(gdb[-2])
                c2 = int(gdb[-1])
                freq[c1] += 1
                if c1 != c2:
                    freq[c2] += 1
                # Xét bộ số
                gdb2 = gdb[-2:]
                for bo, lst in BO_SO_DE.items():
                    if gdb2 in lst:
                        boso_count[bo] += 1
                        break
        # Tính Gan (quét toàn bộ lịch sử nếu cần chính xác, ở đây quét 50 kỳ)
        scan_gan = self.df.tail(50)
        gan_counts = {i: 50 for i in range(10)}
        for i in range(10):
            for r_idx in range(len(scan_gan) - 1, -1, -1):
                row = scan_gan.iloc[r_idx]
                gdb = str(row.get('GDB', ''))
                if len(gdb) >= 2 and (str(i) in gdb[-2:]):
                    gan_counts[i] = (len(scan_gan) - 1) - r_idx
                    break
        # Cập nhật bảng Chạm
        for item in self.tree_stats.get_children():
            self.tree_stats.delete(item)
        sorted_stats = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        for num, count in sorted_stats:
            gan = gan_counts.get(num, ">50")
            self.tree_stats.insert("", "end", values=(num, count, gan))
        # Cập nhật bảng Bộ Số
        for item in self.tree_boso.get_children():
            self.tree_boso.delete(item)
        sorted_bo = sorted(boso_count.items(), key=lambda x: x[1], reverse=True)
        for bo, count in sorted_bo:
            self.tree_boso.insert("", "end", values=(bo, count, ",".join(BO_SO_DE[bo])))
    def on_scan_click(self):
        if self.df is None: return
        # 1. Chạy Scanner
        bridges = self.scanner.scan_best_bridges(self.df)
        self.active_bridges = bridges
        # 2. Hiển thị Cầu
        for item in self.tree_bridges.get_children():
            self.tree_bridges.delete(item)
        for i, b in enumerate(bridges):
            self.tree_bridges.insert("", "end", values=(i+1, f"Chạm {b.predicted_value}", f"{int(b.score)} ngày"))
        # 3. Tổng hợp Dự đoán (Top 4 Chạm)
        if not bridges: return
        # Lấy top 4 chạm xuất hiện nhiều nhất trong top bridges
        counts = {}
        for b in bridges:
            v = b.predicted_value
            counts[v] = counts.get(v, 0) + b.score # Cộng điểm streak làm trọng số
        top_chams = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:4]
        cham_vals = [x[0] for x in top_chams]
        self.lbl_top_chams.config(text=f"{cham_vals}")
        # 4. Tạo Dàn 65 (Hợp của 4 chạm)
        dan_set = set()
        for c in cham_vals:
            for i in range(100):
                if i // 10 == c or i % 10 == c:
                    dan_set.add(f"{i:02d}")
        sorted_dan = sorted(list(dan_set))
        self.txt_dan_65.delete("1.0", tk.END)
        self.txt_dan_65.insert("1.0", ",".join(sorted_dan))
        # 5. Top 10 (Giao của 2 chạm mạnh nhất)
        if len(cham_vals) >= 2:
            c1, c2 = cham_vals[0], cham_vals[1]
            # Các số vừa dính chạm 1 VÀ chạm 2
            top_10 = []
            for i in range(100):
                s = f"{i:02d}"
                has_c1 = (i // 10 == c1 or i % 10 == c1)
                has_c2 = (i // 10 == c2 or i % 10 == c2)
                if has_c1 and has_c2:
                    top_10.append(s)
            self.lbl_top_10.config(text=",".join(top_10))
