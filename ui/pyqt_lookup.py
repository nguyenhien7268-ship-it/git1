#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Lookup Tab
View past results detail
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget, 
    QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox, 
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

try:
    from lottery_service import (
        calculate_loto_stats, delete_ky_from_db,
        get_all_kys_from_db, get_results_by_ky, getAllLoto_V30
    )
except ImportError:
    print("Lookup Import Error")
    def get_all_kys_from_db(): return []
    def get_results_by_ky(k): return None
    def getAllLoto_V30(r): return []
    def calculate_loto_stats(l): return {}, {}
    def delete_ky_from_db(k): return False, "Error"

class LookupTab(QWidget):
    """Lookup tab for viewing past results"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.all_ky_data = []
        
        self._setup_ui()
        self.refresh_list()
        
    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === Left Panel: List ===
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Tìm kiếm:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Kỳ hoặc Ngày...")
        self.search_input.textChanged.connect(self._filter_list)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Làm Mới")
        refresh_btn.clicked.connect(self.refresh_list)
        btn_layout.addWidget(refresh_btn)
        
        del_btn = QPushButton("🗑️ Xóa Kỳ")
        del_btn.clicked.connect(self._delete_ky)
        btn_layout.addWidget(del_btn)
        left_layout.addLayout(btn_layout)
        
        # List
        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.list_widget)
        
        splitter.addWidget(left_widget)
        
        # === Right Panel: Detail ===
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        right_layout.addWidget(QLabel("<b>Chi tiết kết quả:</b>"))
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.detail_text)
        
        splitter.addWidget(right_widget)
        
        # Splitter sizes (30% - 70%)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        
        layout.addWidget(splitter)
        
    def refresh_list(self):
        try:
            self.all_ky_data = get_all_kys_from_db()
            self._filter_list()
        except Exception as e:
            print(f"Error refreshing lookup: {e}")
            
    def _filter_list(self):
        self.list_widget.clear()
        search = self.search_input.text().lower().strip()
        
        if not self.all_ky_data:
            self.list_widget.addItem("Không có dữ liệu")
            return
            
        for ky in self.all_ky_data:
            # ky[0] = id/sub, ky[1] = date
            display = f"{ky[0]}   ({ky[1]})"
            
            if search in display.lower():
                self.list_widget.addItem(display)
                
    def _on_selection_changed(self, current, previous):
        if not current: return
        
        text = current.text()
        if "Không có dữ liệu" in text: return
        
        ma_so_ky = text.split()[0]
        self._show_details(ma_so_ky)
        
    def _show_details(self, ma_so_ky):
        try:
            row = get_results_by_ky(ma_so_ky)
            if not row:
                self.detail_text.setText(f"Không tìm thấy dữ liệu cho kỳ {ma_so_ky}")
                return
                
            loto_list = getAllLoto_V30(row)
            dau_stats, duoi_stats = calculate_loto_stats(loto_list)
            
            # Format output
            lines = []
            lines.append(f"KẾT QUẢ KỲ: {ma_so_ky}")
            lines.append("=" * 46 + "\n")
            
            giai_ten = ["Đặc Biệt", "Nhất", "Nhì", "Ba", "Bốn", "Năm", "Sáu", "Bảy"]
            LABEL_WIDTH, NUMBER_WIDTH = 10, 33
            
            for i in range(len(giai_ten)):
                giai_name = giai_ten[i].ljust(LABEL_WIDTH)
                data_str = str(row[i + 3] or "")
                numbers = [n.strip() for n in data_str.split(",") if n.strip()]
                
                if not numbers:
                    lines.append(f"{giai_name} : {str('').center(NUMBER_WIDTH)}")
                elif len(numbers) <= 3:
                     val = " - ".join(numbers)
                     lines.append(f"{giai_name} : {val.center(NUMBER_WIDTH)}")
                elif len(numbers) == 4:
                     l1 = " - ".join(numbers[:2])
                     l2 = " - ".join(numbers[2:])
                     lines.append(f"{giai_name} : {l1.center(NUMBER_WIDTH)}")
                     lines.append(f"{''.ljust(LABEL_WIDTH)} : {l2.center(NUMBER_WIDTH)}")
                elif len(numbers) == 6:
                     l1 = " - ".join(numbers[:3])
                     l2 = " - ".join(numbers[3:])
                     lines.append(f"{giai_name} : {l1.center(NUMBER_WIDTH)}")
                     lines.append(f"{''.ljust(LABEL_WIDTH)} : {l2.center(NUMBER_WIDTH)}")
                else:
                     lines.append(f"{giai_name} : {' - '.join(numbers)}")
                     
            lines.append("\n" + "=" * 46)
            lines.append("THỐNG KÊ LOTO (Đầu - Đuôi)")
            lines.append("-" * 46)
            
            lines.append(f"{'Đầu':<3} | {'Loto':<12} | {'Đuôi':<4} | {'Loto':<12}")
            lines.append("-" * 3 + "-+-" + "-" * 12 + "-+-" + "-" * 4 + "-+-" + "-" * 12)
            
            for i in range(10):
                d_val = ",".join(dau_stats[i])
                du_val = ",".join(duoi_stats[i])
                lines.append(f"{str(i):<3} | {d_val:<12} | {str(i):<4} | {du_val:<12}")
                
            self.detail_text.setText("\n".join(lines))
            
        except Exception as e:
            self.detail_text.setText(f"Lỗi hiển thị: {e}")
            
    def _delete_ky(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        ma_so_ky = item.text().split()[0]
        
        if QMessageBox.question(self, "Xác nhận", f"Xóa kỳ {ma_so_ky}?") == QMessageBox.StandardButton.Yes:
            success, msg = delete_ky_from_db(ma_so_ky)
            if success:
                QMessageBox.information(self, "OK", "Đã xóa!")
                self.refresh_list()
            else:
                QMessageBox.critical(self, "Lỗi", msg)
