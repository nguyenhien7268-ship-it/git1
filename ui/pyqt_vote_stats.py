#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Vote Statistics Window
Displays pair predictions consensus
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

try:
    from lottery_service import get_prediction_consensus
except ImportError:
    print("Warning: lottery_service not found, using dummy data")
    def get_prediction_consensus():
        return []

class VoteStatisticsDialog(QDialog):
    """Vote statistics dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Thống Kê Vote - Cặp Số Dự Đoán")
        self.resize(800, 600)
        self.parent = parent
        
        # Setup UI
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_layout = QVBoxLayout()
        title = QLabel("📊 Thống Kê Vote Theo Cặp Số")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        desc = QLabel(
            "Hiển thị cặp số được dự đoán bởi bao nhiêu cầu.\n"
            "Vote càng cao = càng nhiều cầu đồng thuận dự đoán cặp số đó."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #666;")
        header_layout.addWidget(desc)
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Cặp Số", "Số Vote", "Các Cầu Dự Đoán"])
        
        # Table styling
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 100)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 100)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Làm Mới")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Đóng")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Status bar
        self.status = QLabel("Sẵn sàng")
        self.status.setStyleSheet("color: blue;")
        layout.addWidget(self.status)
        
        # Initial load
        self.load_data()
        
    def load_data(self):
        """Load and display data"""
        self.status.setText("Đang tải dữ liệu...")
        self.table.setRowCount(0)
        
        try:
            consensus_list = get_prediction_consensus()
            
            if not consensus_list:
                self.status.setText("Không có dữ liệu dự đoán.")
                QMessageBox.information(
                    self,
                    "Thông báo",
                    "Không tìm thấy dự đoán từ các cầu đã bật.\n"
                    "Hãy đảm bảo:\n"
                    "1. Đã BẬT các cầu trong 'Quản Lý Cầu'\n"
                    "2. Đã chạy 'Cập Nhật Cache K2N'"
                )
                return
                
            self.table.setRowCount(len(consensus_list))
            
            for i, (pair_key, vote_count, bridges_str) in enumerate(consensus_list):
                # Pair
                item_pair = QTableWidgetItem(str(pair_key))
                item_pair.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, 0, item_pair)
                
                # Vote
                item_vote = QTableWidgetItem(f"x{vote_count}")
                item_vote.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_vote.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.table.setItem(i, 1, item_vote)
                
                # Bridges
                item_bridges = QTableWidgetItem(str(bridges_str))
                self.table.setItem(i, 2, item_bridges)
                
                # Color coding
                bg_color = None
                if vote_count >= 10:
                    bg_color = QColor("#90EE90") # Light green
                elif vote_count >= 5:
                    bg_color = QColor("#FFE4B5") # Moccasin
                
                if bg_color:
                    for col in range(3):
                        item = self.table.item(i, col)
                        item.setBackground(bg_color)
                        
            # Update status
            max_vote = max([v[1] for v in consensus_list]) if consensus_list else 0
            self.status.setText(f"✅ Tìm thấy {len(consensus_list)} cặp số. Vote cao nhất: x{max_vote}")
            
        except Exception as e:
            self.status.setText(f"Lỗi: {str(e)}")
            QMessageBox.critical(self, "Lỗi", f"Không thể tải thống kê:\n{str(e)}")
