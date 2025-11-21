# ui/ui_vote_statistics.py
# Bảng thống kê Vote - Hiển thị cặp số được dự đoán bởi bao nhiêu cầu

import tkinter as tk
from tkinter import ttk, messagebox

try:
    from lottery_service import get_prediction_consensus
except ImportError:
    print("LỖI: ui_vote_statistics.py không thể import lottery_service.")

    def get_prediction_consensus():
        return []


class VoteStatisticsWindow:
    """Cửa sổ hiển thị thống kê vote cho các cặp số dự đoán."""

    def __init__(self, app):
        self.app = app
        self.root = app.root

        # Ngăn mở nhiều cửa sổ
        if (
            hasattr(self.app, "vote_stats_window")
            and self.app.vote_stats_window
            and self.app.vote_stats_window.winfo_exists()
        ):
            self.app.vote_stats_window.lift()
            return

        self.app.logger.log("Đang mở cửa sổ Thống Kê Vote...")

        self.window = tk.Toplevel(self.root)
        self.window.title("📊 Thống Kê Vote - Cặp Số Dự Đoán")
        self.app.vote_stats_window = self.window
        self.window.geometry("700x500")

        self.window.transient(self.root)
        self.window.grab_set()

        # Main frame
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title và description
        title_label = ttk.Label(
            main_frame,
            text="📊 Thống Kê Vote Theo Cặp Số",
            font=("TkDefaultFont", 12, "bold"),
        )
        title_label.pack(pady=(0, 5))

        desc_label = ttk.Label(
            main_frame,
            text="Hiển thị cặp số được dự đoán bởi bao nhiêu cầu.\n"
            "Vote càng cao = càng nhiều cầu đồng thuận dự đoán cặp số đó.",
            font=("TkDefaultFont", 9),
            foreground="gray",
        )
        desc_label.pack(pady=(0, 10))

        # Treeview frame với scrollbar
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_h = ttk.Scrollbar(tree_frame, orient="horizontal")
        tree_scroll_h.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Pair", "VoteCount", "Bridges"),
            show="headings",
            yscrollcommand=tree_scroll.set,
            xscrollcommand=tree_scroll_h.set,
        )

        tree_scroll.config(command=self.tree.yview)
        tree_scroll_h.config(command=self.tree.xview)

        # Column headers
        self.tree.heading("Pair", text="Cặp Số")
        self.tree.heading("VoteCount", text="Số Vote")
        self.tree.heading("Bridges", text="Các Cầu Dự Đoán")

        # Column widths
        self.tree.column("Pair", width=100, stretch=False, anchor="center")
        self.tree.column("VoteCount", width=80, stretch=False, anchor="center")
        self.tree.column("Bridges", width=450, stretch=True, anchor="w")

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        refresh_button = ttk.Button(
            button_frame, text="🔄 Làm Mới", command=self.load_vote_statistics
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(
            button_frame, text="Đóng", command=self.window.destroy
        )
        close_button.pack(side=tk.RIGHT, padx=5)

        # Status label
        self.status_label = ttk.Label(
            main_frame, text="", font=("TkDefaultFont", 9), foreground="blue"
        )
        self.status_label.pack(pady=(5, 0))

        # Load data
        self.load_vote_statistics()

    def load_vote_statistics(self):
        """Tải và hiển thị thống kê vote."""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.status_label["text"] = "Đang tải..."
        self.window.update()

        try:
            # Get consensus data
            consensus_list = get_prediction_consensus()

            if not consensus_list:
                self.status_label["text"] = "Không có dữ liệu dự đoán."
                self.status_label["foreground"] = "red"
                messagebox.showinfo(
                    "Không có dữ liệu",
                    "Không tìm thấy dự đoán từ các cầu đã bật.\n\n"
                    "Hãy đảm bảo:\n"
                    "1. Đã BẬT các cầu trong 'Quản Lý Cầu'\n"
                    "2. Đã chạy 'Cập Nhật Cache K2N'",
                    parent=self.window,
                )
                return

            # Populate tree
            for pair_key, vote_count, bridges_str in consensus_list:
                # Add color coding based on vote count
                tag = ""
                if vote_count >= 10:
                    tag = "high_vote"
                elif vote_count >= 5:
                    tag = "medium_vote"
                else:
                    tag = "low_vote"

                self.tree.insert(
                    "",
                    "end",
                    values=(pair_key, f"x{vote_count}", bridges_str),
                    tags=(tag,),
                )

            # Configure tags for color coding
            self.tree.tag_configure("high_vote", background="#90EE90")  # Light green
            self.tree.tag_configure("medium_vote", background="#FFE4B5")  # Moccasin
            self.tree.tag_configure("low_vote", background="white")

            # Update status
            total_pairs = len(consensus_list)
            max_vote = max([v[1] for v in consensus_list]) if consensus_list else 0
            self.status_label["text"] = (
                f"✅ Tìm thấy {total_pairs} cặp số. Vote cao nhất: x{max_vote}"
            )
            self.status_label["foreground"] = "green"

            self.app.logger.log(
                f"Đã tải thống kê vote: {total_pairs} cặp số, vote cao nhất: x{max_vote}"
            )

        except Exception as e:
            self.status_label["text"] = f"Lỗi: {e}"
            self.status_label["foreground"] = "red"
            self.app.logger.log(f"Lỗi khi tải thống kê vote: {e}")
            messagebox.showerror(
                "Lỗi", f"Không thể tải thống kê vote:\n{e}", parent=self.window
            )
