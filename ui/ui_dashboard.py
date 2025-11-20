# Tên file: git3/ui/ui_dashboard.py
#
# (NỘI DUNG THAY THẾ TOÀN BỘ - LAYOUT 24 CỘT: PHONG ĐỘ TĂNG 50%)
#
import datetime
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("LỖI: ui_dashboard.py không thể import logic.config_manager...")
    SETTINGS = type(
        "obj",
        (object,),
        {"GAN_DAYS": 15, "HIGH_WIN_THRESHOLD": 47.0, "K2N_RISK_START_THRESHOLD": 4},
    )

# Import DB Logic để lấy dữ liệu cầu
try:
    from logic.db_manager import DB_NAME
    from logic.data_repository import get_all_managed_bridges
except ImportError:
    print("LỖI: ui_dashboard.py không thể import DB logic...")
    DB_NAME = "data/xo_so_prizes_all_logic.db"

    def get_all_managed_bridges(db, only_enabled=True):
        return []


class DashboardWindow(ttk.Frame):
    def __init__(self, app_instance):
        super().__init__(app_instance.notebook, padding=10)

        self.app = app_instance
        self.root = app_instance.root

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.header_frame = ttk.Frame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        self.title_label = ttk.Label(
            self.header_frame, text="Đang tải...", font=("Arial", 16, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=(0, 20))

        self.refresh_button = ttk.Button(
            self.header_frame, text="Làm Mới Dữ Liệu", command=self.refresh_data
        )
        self.refresh_button.pack(side=tk.RIGHT)

        self.main_analysis_frame = ttk.Frame(self, padding=10)
        self.main_analysis_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # ===================================================================
        # CẤU HÌNH LAYOUT MỚI (LƯỚI 24 CỘT)
        # ===================================================================
        # Sử dụng 24 cột để chia tỷ lệ chính xác hơn.
        # Hàng 0: 2/3 (16 cột) - 1/3 (8 cột)
        # Hàng 1: AI (5 cột) - Phong độ (9 cột ~37.5%) - Hot (5 cột) - Gan (5 cột)
        # -------------------------------------------------------------------
        
        for i in range(24):
            self.main_analysis_frame.columnconfigure(i, weight=1)

        # Hàng 0: Các bảng chính (Cao hơn)
        self.main_analysis_frame.rowconfigure(0, weight=3)
        # Hàng 1: Các bảng tham khảo (Thấp hơn chút)
        self.main_analysis_frame.rowconfigure(1, weight=2)

        # ===================================================================
        # TẠO CÁC BẢNG
        # ===================================================================

        # --- HÀNG 0: KHU VỰC QUYẾT ĐỊNH (Chiếm 50% chiều cao) ---

        # 1. Bảng Chấm Điểm (Chiếm 16/24 cột = 2/3)
        self._create_top_scores_ui(self.main_analysis_frame)
        self.top_scores_frame.grid(row=0, column=0, columnspan=16, sticky="nsew", padx=5, pady=5)

        # 2. Cầu K2N Đang Chờ (Chiếm 8/24 cột = 1/3)
        self._create_pending_k2n_ui(self.main_analysis_frame)
        self.pending_k2n_frame.grid(row=0, column=16, columnspan=8, sticky="nsew", padx=5, pady=5)

        # --- HÀNG 1: KHU VỰC THAM KHẢO (Chiếm 50% chiều cao) ---

        # 3. Dự đoán AI (5/24 cột)
        self._create_ai_predictions_ui(self.main_analysis_frame)
        self.ai_predictions_frame.grid(row=1, column=0, columnspan=5, sticky="nsew", padx=5, pady=5)

        # 4. Cầu Thông 10 Kỳ (9/24 cột - Rộng nhất hàng dưới)
        self._create_recent_form_ui(self.main_analysis_frame)
        self.recent_form_frame.grid(row=1, column=5, columnspan=9, sticky="nsew", padx=5, pady=5)

        # 5. Loto Về Nhiều (5/24 cột)
        self._create_hot_loto_ui(self.main_analysis_frame)
        self.hot_loto_frame.grid(row=1, column=14, columnspan=5, sticky="nsew", padx=5, pady=5)

        # 6. Lô Gan (5/24 cột)
        self._create_gan_loto_ui(self.main_analysis_frame)
        self.gan_loto_frame.grid(row=1, column=19, columnspan=5, sticky="nsew", padx=5, pady=5)

    # ===================================================================================
    # CÁC HÀM TẠO UI
    # ===================================================================================

    def _create_top_scores_ui(self, parent_frame):
        self.top_scores_frame = ttk.Labelframe(
            parent_frame, text="🏆 Bảng Chấm Điểm Tổng Lực (V6.2 + AI)"
        )
        tree_frame = ttk.Frame(self.top_scores_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ("score", "pair", "gan", "reasons")
        self.scores_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", height=10
        )
        self.scores_tree.heading("score", text="Điểm")
        self.scores_tree.heading("pair", text="Cặp số")
        self.scores_tree.heading("gan", text="Gan")
        self.scores_tree.heading("reasons", text="Lý do (Tích hợp AI)")
        
        self.scores_tree.column("score", width=50, anchor=tk.E)
        self.scores_tree.column("pair", width=60, anchor=tk.CENTER)
        self.scores_tree.column("gan", width=50, anchor=tk.CENTER)
        self.scores_tree.column("reasons", width=400) 
        
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.scores_tree.yview
        )
        self.scores_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scores_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scores_tree.tag_configure("gan", foreground="red")
        self.scores_tree.tag_configure(
            "top1", background="#D5E8D4", font=("Arial", 10, "bold")
        )
        self.scores_tree.tag_configure("top3", background="#FFF2CC")

    def _create_ai_predictions_ui(self, parent_frame):
        self.ai_predictions_frame = ttk.Labelframe(
            parent_frame, text="🧠 AI (Đơn)"
        )
        tree_frame = ttk.Frame(self.ai_predictions_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        cols = ("loto", "probability")
        self.ai_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", height=8
        )
        self.ai_tree.heading("loto", text="Số")
        self.ai_tree.heading("probability", text="%")
        self.ai_tree.column("loto", width=40, anchor=tk.CENTER)
        self.ai_tree.column("probability", width=50, anchor=tk.E)
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.ai_tree.yview
        )
        self.ai_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ai_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.ai_tree.tag_configure(
            "top1", background="#D5E8D4", font=("Arial", 9, "bold")
        )

    def _create_recent_form_ui(self, parent_frame):
        self.recent_form_frame = ttk.Labelframe(
            parent_frame, text="🔥 Thông 10 Kỳ (>= 5/10)"
        )
        tree_frame = ttk.Frame(self.recent_form_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        cols = ("name", "wins", "prediction")
        self.recent_form_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", height=8
        )

        self.recent_form_tree.heading("name", text="Tên Cầu")
        self.recent_form_tree.heading("wins", text="Thắng")
        self.recent_form_tree.heading("prediction", text="Dự Đoán")

        # Tăng độ rộng cột tên cầu vì bảng đã rộng hơn
        self.recent_form_tree.column("name", width=150, anchor=tk.W)
        self.recent_form_tree.column("wins", width=60, anchor=tk.CENTER)
        self.recent_form_tree.column("prediction", width=60, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.recent_form_tree.yview
        )
        self.recent_form_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recent_form_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.recent_form_tree.tag_configure(
            "excellent", background="#D5E8D4", font=("Arial", 9, "bold")
        )
        self.recent_form_tree.tag_configure("good", background="#FFF2CC")
        
        self.recent_form_tree.bind("<Double-1>", self.on_tree_double_click)

    def _create_hot_loto_ui(self, parent_frame):
        self.hot_loto_frame = ttk.Labelframe(
            parent_frame, text="🔥 Hot (7 ngày)"
        )
        tree_frame = ttk.Frame(self.hot_loto_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        cols = ("loto", "hits")
        self.hot_loto_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", height=8
        )
        self.hot_loto_tree.heading("loto", text="Số")
        self.hot_loto_tree.heading("hits", text="Nháy")
        self.hot_loto_tree.column("loto", width=40, anchor=tk.CENTER)
        self.hot_loto_tree.column("hits", width=40, anchor=tk.CENTER)
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.hot_loto_tree.yview
        )
        self.hot_loto_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hot_loto_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_gan_loto_ui(self, parent_frame):
        self.gan_loto_frame = ttk.Labelframe(
            parent_frame, text="🧊 Lô Gan (>15)"
        )
        tree_frame = ttk.Frame(self.gan_loto_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        cols = ("loto", "days")
        self.gan_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", height=8
        )
        self.gan_tree.heading("loto", text="Số")
        self.gan_tree.heading("days", text="Ngày")
        self.gan_tree.column("loto", width=40, anchor=tk.CENTER)
        self.gan_tree.column("days", width=50, anchor=tk.CENTER)
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.gan_tree.yview
        )
        self.gan_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.gan_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_pending_k2n_ui(self, parent_frame):
        self.pending_k2n_frame = ttk.Labelframe(
            parent_frame, text="⏳ Cầu K2N Đang Chờ (Chờ N2)"
        )
        tree_frame = ttk.Frame(self.pending_k2n_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        cols = ("stl", "streak", "max_lose", "name")
        self.k2n_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", height=10
        )
        self.k2n_tree.heading("stl", text="Cặp số")
        self.k2n_tree.heading("streak", text="Chuỗi")
        self.k2n_tree.heading("max_lose", text="Gãy Max")
        self.k2n_tree.heading("name", text="Tên cầu")
        self.k2n_tree.column("stl", width=50, anchor=tk.CENTER)
        self.k2n_tree.column("streak", width=50, anchor=tk.CENTER)
        self.k2n_tree.column("max_lose", width=50, anchor=tk.CENTER)
        self.k2n_tree.column("name", width=200)
        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.k2n_tree.yview
        )
        self.k2n_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.k2n_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.k2n_tree.tag_configure("risk", foreground="red")
        self.k2n_tree.tag_configure("safe", foreground="green")
        self.k2n_tree.bind("<Double-1>", self.on_tree_double_click)

    # --- HÀM NẠP DỮ LIỆU ---

    def clear_data(self):
        self.title_label.config(text="Đang tải...")
        for tree in [
            self.scores_tree,
            self.hot_loto_tree,
            self.gan_tree,
            self.k2n_tree,
            self.ai_tree,
            self.recent_form_tree,
        ]:
            try:
                for item in tree.get_children():
                    tree.delete(item)
            except Exception as e:
                print(f"Lỗi khi xóa tree {tree.winfo_name()}: {e}")

    def populate_data(
        self,
        next_ky,
        stats,
        n_days_stats,
        consensus,
        high_win,
        pending_k2n,
        gan_stats,
        top_scores,
        top_memory_bridges,
        ai_predictions,
    ):

        try:
            self.clear_data()

            today = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            self.title_label.config(
                text=f"Bảng Quyết Định Tối Ưu - {next_ky} (Cập nhật: {today})"
            )

            # Nạp Bảng 1: Chấm Điểm
            self._populate_top_scores(top_scores)

            # Nạp Bảng 2: Cầu K2N Đang Chờ
            self._populate_pending_k2n(pending_k2n)

            # Nạp Bảng 3: Dự đoán AI
            self._populate_ai_predictions(ai_predictions)

            # Nạp Bảng 4: Phong Độ 10 Kỳ
            try:
                all_bridges = get_all_managed_bridges(DB_NAME, only_enabled=True)
                good_bridges = []
                for b in all_bridges:
                    recent_wins = b.get("recent_win_count_10", 0)
                    if isinstance(recent_wins, str):
                        try:
                            recent_wins = int(recent_wins)
                        except ValueError:
                            recent_wins = 0
                    if recent_wins >= 5:
                        good_bridges.append(b)

                good_bridges.sort(key=lambda x: x.get("recent_win_count_10", 0), reverse=True)
                self._populate_recent_form(good_bridges)

            except Exception as e:
                print(f"Lỗi khi lấy/lọc cầu phong độ: {e}")

            # Nạp Bảng 5: Loto Về Nhiều
            self.hot_loto_frame.config(text=f"🔥 Hot ({n_days_stats} ngày)")
            self._populate_hot_loto(stats)

            # Nạp Bảng 6: Lô Gan
            gan_threshold = SETTINGS.GAN_DAYS
            self.gan_loto_frame.config(text=f"🧊 Lô Gan (>{gan_threshold})")
            self._populate_gan_loto(gan_stats)

        except Exception as e:
            messagebox.showerror(
                "Lỗi Nạp Dữ Liệu Dashboard",
                f"Lỗi chi tiết: {e}\n{traceback.format_exc()}",
                parent=self,
            )

    # ===================================================================================
    # CÁC HÀM NẠP DỮ LIỆU CHI TIẾT
    # ===================================================================================

    def _populate_top_scores(self, top_scores):
        if not top_scores:
            self.scores_tree.insert(
                "", tk.END, values=("N/A", "N/A", "", "Không có cặp nào")
            )
            return
        for i, item in enumerate(top_scores[:40]):
            tags = ()
            if item["is_gan"]:
                tags += ("gan",)
            if i == 0:
                tags += ("top1",)
            elif i < 3:
                tags += ("top3",)
            self.scores_tree.insert(
                "",
                tk.END,
                values=(
                    item["score"],
                    item["pair"],
                    f"{item['gan_days']} ngày" if item["is_gan"] else "",
                    item["reasons"],
                ),
                tags=tags,
            )

    def _populate_pending_k2n(self, pending_k2n):
        if not pending_k2n:
            self.k2n_tree.insert(
                "", tk.END, values=("(N/A)", "", "", "Không có cầu K2N nào chờ")
            )
            return
        try:
            sorted_k2n = sorted(
                pending_k2n.items(),
                key=lambda item: (
                    int(str(item[1]["streak"]).split(" ")[0]),
                    -int(item[1].get("max_lose", 99)),
                ),
                reverse=True,
            )
        except Exception:
            sorted_k2n = list(pending_k2n.items())
        risk_threshold = SETTINGS.K2N_RISK_START_THRESHOLD
        for bridge_name, data in sorted_k2n:
            stl, streak, max_lose = data["stl"], data["streak"], data.get("max_lose", 0)
            tags = ()
            if max_lose > risk_threshold:
                tags = ("risk",)
            elif max_lose < risk_threshold:
                tags = ("safe",)
            self.k2n_tree.insert(
                "",
                tk.END,
                values=(stl, streak, f"{max_lose} lần", bridge_name),
                tags=tags,
            )

    def _populate_ai_predictions(self, ai_predictions):
        if not ai_predictions:
            self.ai_tree.insert("", tk.END, values=("(N/A)", "Vui lòng Huấn luyện AI"))
            return
        for i, pred in enumerate(ai_predictions[:20]):
            loto = pred["loto"]
            prob = pred["probability"]
            tags = ()
            if i == 0:
                tags = ("top1",)
            elif i < 5:
                tags = ("top5",)
            self.ai_tree.insert("", tk.END, values=(loto, f"{prob:.2f}%"), tags=tags)

    def _populate_recent_form(self, bridges):
        if not bridges:
            self.recent_form_tree.insert(
                "", tk.END, values=("Không có cầu nào >= 5/10", "", "")
            )
            return

        for b in bridges:
            wins = b.get("recent_win_count_10", 0)
            pred = b.get("next_prediction_stl", "N/A")
            
            tags = ()
            if wins >= 8:
                tags = ("excellent",)
            elif wins >= 6:
                tags = ("good",)
                
            self.recent_form_tree.insert(
                "",
                tk.END,
                values=(
                    b["name"],
                    f"{wins}/10",
                    pred
                ),
                tags=tags
            )

    def _populate_hot_loto(self, stats):
        if not stats:
            self.hot_loto_tree.insert("", tk.END, values=("(N/A)", ""))
            return
        for loto, hits, days in stats:
            self.hot_loto_tree.insert("", tk.END, values=(loto, hits))

    def _populate_gan_loto(self, gan_stats):
        if not gan_stats:
            self.gan_tree.insert("", tk.END, values=("(N/A)", "Không có lô gan"))
            return
        for loto, days in gan_stats:
            self.gan_tree.insert("", tk.END, values=(loto, f"{days} ngày"))

    # ===================================================================================
    # HÀM TƯƠNG TÁC
    # ===================================================================================

    def refresh_data(self):
        self.app.logger.log(
            "\n--- (Làm Mới) Bắt đầu chạy lại Bảng Quyết Định Tối Ưu ---"
        )
        self.app.run_decision_dashboard()

    def on_tree_double_click(self, event):
        try:
            item_id = event.widget.focus()
            if not item_id:
                return
            item = event.widget.item(item_id)
            values = item["values"]
            bridge_name = ""

            if event.widget == self.k2n_tree:
                bridge_name = values[3]
            elif event.widget == self.recent_form_tree:
                bridge_name = values[0]

            if bridge_name:
                self.app.trigger_bridge_backtest(bridge_name)
        except Exception as e:
            print(f"Lỗi double-click: {e}")