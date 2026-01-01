#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Dashboard Tab - Display Analysis Results
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont


class DashboardTab(QWidget):
    """Dashboard tab for displaying analysis results"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.current_results = None
        
        # Setup UI
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_layout = QHBoxLayout()
        self.period_label = QLabel("Kỳ tiếp theo: Chưa có dữ liệu")
        self.period_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.period_label)
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Rank", "Cặp", "Điểm", "AI %", "Vote", "Tin Cậy", "Form", "Ghi Chú"
        ])
        
        # Table settings
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        
        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 60)  # Rank
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 80)  # Cặp
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        
        # Footer stats
        self.stats_label = QLabel("Sẵn sàng hiển thị kết quả phân tích")
        self.stats_label.setStyleSheet("color: #86868B; font-size: 9pt;")
        layout.addWidget(self.stats_label)
    
    def update_results(self, results):
        """Update dashboard with analysis results"""
        self.current_results = results
        
        # Update period
        next_ky = results.get('next_ky', 'Unknown')
        self.period_label.setText(f"Kỳ tiếp theo: {next_ky}")
        
        # Get top scores
        top_scores = results.get('top_scores', [])
        
        # Clear and populate table
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)  # Disable while populating
        
        for i, item in enumerate(top_scores[:50], 1):  # Show top 50
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Rank
            rank_item = QTableWidgetItem(str(i))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rank_item.setFlags(rank_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Color coding for top ranks
            if i == 1:
                rank_item.setBackground(QColor("#34C759"))  # Green
                rank_item.setForeground(QColor("white"))
            elif i <= 3:
                rank_item.setBackground(QColor("#FF9500"))  # Orange
                rank_item.setForeground(QColor("white"))
            elif i <= 10:
                rank_item.setBackground(QColor("#5AC8FA"))  # Light blue
            
            self.table.setItem(row, 0, rank_item)
            
            # Pair
            pair_item = QTableWidgetItem(item.get('pair', '??-??'))
            pair_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            pair_item.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
            pair_item.setFlags(pair_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, pair_item)
            
            # Score
            score = item.get('score', 0)
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            score_item.setData(Qt.ItemDataRole.UserRole, score)  # For sorting
            score_item.setFlags(score_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, score_item)
            
            # AI Probability
            ai_prob = item.get('ai_prob', 0)
            ai_item = QTableWidgetItem(f"{ai_prob:.1f}%")
            ai_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ai_item.setData(Qt.ItemDataRole.UserRole, ai_prob)
            ai_item.setFlags(ai_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, ai_item)
            
            # Vote Count
            vote = item.get('vote_count', 0)
            vote_item = QTableWidgetItem(str(vote))
            vote_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            vote_item.setData(Qt.ItemDataRole.UserRole, vote)
            vote_item.setFlags(vote_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, vote_item)
            
            # Confidence
            confidence = item.get('confidence', 0)
            conf_item = QTableWidgetItem(str(confidence))
            conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            conf_item.setData(Qt.ItemDataRole.UserRole, confidence)
            conf_item.setFlags(conf_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, conf_item)
            
            # Form Score
            form = item.get('form_bonus', 0)
            form_item = QTableWidgetItem(f"{form:.1f}")
            form_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            form_item.setData(Qt.ItemDataRole.UserRole, form)
            form_item.setFlags(form_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 6, form_item)
            
            # Notes
            notes = []
            if item.get('is_gan', False):
                notes.append("GAN")
            if item.get('is_consensus', False):
                notes.append("VOTE")
            if item.get('high_win', False):
                notes.append("HIGH_WIN")
            
            note_item = QTableWidgetItem(", ".join(notes) if notes else "-")
            note_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            note_item.setFlags(note_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 7, note_item)
        
        self.table.setSortingEnabled(True)  # Re-enable sorting
        
        # Update stats
        total = len(top_scores)
        self.stats_label.setText(f"Hiển thị {min(50, total)}/{total} cặp có điểm cao nhất")
    
    def _refresh(self):
        """Refresh display with current results"""
        if self.current_results:
            self.update_results(self.current_results)
    
    def clear(self):
        """Clear dashboard"""
        self.table.setRowCount(0)
        self.period_label.setText("Kỳ tiếp theo: Chưa có dữ liệu")
        self.stats_label.setText("Sẵn sàng hiển thị kết quả phân tích")
