# Tên file: ui/popups/ui_backtest_popup.py
# Popup hiển thị kết quả backtest 30 ngày (Dùng chung cho Lô và Đề)

import tkinter as tk
from tkinter import ttk


class BacktestPopup(tk.Toplevel):
    """
    Popup hiển thị kết quả backtest 30 ngày.
    Dùng chung cho cả Lô và Đề.
    """
    
    def __init__(self, parent, bridge_name, backtest_data):
        """
        Args:
            parent: Parent window
            bridge_name: Tên cầu
            backtest_data: List các dict với format:
                [{'date': 'DD/MM/YYYY', 'pred': 'xx-yy', 'result': 'zz', 'is_win': True/False, 'status': 'Ăn/Gãy'}]
        """
        super().__init__(parent)
        
        self.bridge_name = bridge_name
        self.backtest_data = backtest_data or []
        
        self.title(f"Backtest 30 Ngày - {bridge_name}")
        self.geometry("700x500")
        self.transient(parent)
        self.grab_set()
        
        # Tính thống kê
        total_days = len(self.backtest_data)
        win_count = sum(1 for item in self.backtest_data if item.get('is_win', False))
        win_rate = (win_count / total_days * 100) if total_days > 0 else 0
        
        # Header với thống kê
        header_frame = ttk.Frame(self, padding=10)
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            header_frame,
            text=f"Cầu: {bridge_name}",
            font=("Arial", 12, "bold")
        )
        title_label.pack(anchor=tk.W)
        
        stats_label = ttk.Label(
            header_frame,
            text=f"Thắng {win_count}/{total_days} ngày ({win_rate:.1f}%)",
            font=("Arial", 10)
        )
        stats_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Treeview
        tree_frame = ttk.Frame(self, padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("date", "pred", "result", "status")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=15
        )
        
        # Cấu hình cột
        self.tree.heading("date", text="Ngày")
        self.tree.heading("pred", text="Dự Đoán")
        self.tree.heading("result", text="Kết Quả")
        self.tree.heading("status", text="Trạng Thái")
        
        self.tree.column("date", width=120, anchor=tk.CENTER)
        self.tree.column("pred", width=100, anchor=tk.CENTER)
        self.tree.column("result", width=300, anchor=tk.W)
        self.tree.column("status", width=100, anchor=tk.CENTER)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tags cho màu sắc
        self.tree.tag_configure("win", background="#D5E8D4")  # Xanh nhạt
        self.tree.tag_configure("lose", background="#F8CECC")  # Đỏ nhạt
        
        # Nạp dữ liệu
        self._populate_data()
        
        # Nút đóng
        button_frame = ttk.Frame(self, padding=10)
        button_frame.pack(fill=tk.X)
        
        close_button = ttk.Button(button_frame, text="Đóng", command=self.destroy)
        close_button.pack(side=tk.RIGHT)
        
        # Focus vào window
        self.focus_set()
    
    def _populate_data(self):
        """Nạp dữ liệu vào treeview"""
        for item in self.backtest_data:
            date = item.get('date', '')
            pred = item.get('pred', '')
            result = item.get('result', '')
            status = item.get('status', '')
            is_win = item.get('is_win', False)
            
            # Chọn tag dựa trên kết quả
            tag = "win" if is_win else "lose"
            
            self.tree.insert(
                "",
                tk.END,
                values=(date, pred, result, status),
                tags=(tag,)
            )

