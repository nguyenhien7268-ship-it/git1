#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Bridge Scanner Tab
Scan for new bridges and add them to management
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, 
    QLabel, QCheckBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QMessageBox, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon

try:
    from logic.db_manager import DB_NAME
    from lottery_service import add_managed_bridge
    from ui.pyqt_workers import BridgeScanWorker
    from ui.pyqt_progress_dialog import ProgressDialog
except ImportError as e:
    print(f"Import error in pyqt_bridge_scanner: {e}")
    DB_NAME = "data/xo_so_prizes_all_logic.db"
    def add_managed_bridge(*args, **kwargs): return False, "Module unavailable"

class BridgeScannerTab(QWidget):
    """Tab for scanning new bridges"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.scan_results = []
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # === Controls Section ===
        controls_group = QGroupBox("🔍 Điều Khiển Quét Cầu")
        controls_layout = QVBoxLayout()
        controls_group.setLayout(controls_layout)
        
        # Row 1: Lo Scanning
        lo_layout = QHBoxLayout()
        lo_layout.addWidget(QLabel("<b>Quét Cầu Lô:</b>"))
        
        btn_v17 = QPushButton("📊 Quét V17 Shadow")
        btn_v17.clicked.connect(lambda: self._start_scan("V17 Shadow"))
        lo_layout.addWidget(btn_v17)
        
        btn_mem = QPushButton("🧠 Quét Bạc Nhớ")
        btn_mem.clicked.connect(lambda: self._start_scan("Bạc Nhớ"))
        lo_layout.addWidget(btn_mem)
        
        btn_fixed = QPushButton("📌 Cầu Cố Định")
        btn_fixed.clicked.connect(lambda: self._start_scan("Cầu Cố Định"))
        lo_layout.addWidget(btn_fixed)
        
        btn_all_lo = QPushButton("⚡ QUÉT TẤT CẢ LÔ")
        btn_all_lo.setStyleSheet("color: white; background-color: #007AFF; font-weight: bold;")
        btn_all_lo.clicked.connect(lambda: self._start_scan("TẤT CẢ LÔ"))
        lo_layout.addWidget(btn_all_lo)
        
        lo_layout.addStretch()
        controls_layout.addLayout(lo_layout)
        
        # Row 2: De Scanning
        de_layout = QHBoxLayout()
        de_layout.addWidget(QLabel("<b>Quét Cầu Đề:</b>"))
        
        btn_de = QPushButton("🔮 Quét Cầu Đề")
        btn_de.clicked.connect(lambda: self._start_scan("Cầu Đề"))
        de_layout.addWidget(btn_de)
        
        # De Options
        self.chk_de_set = QCheckBox("📦 Bộ")
        self.chk_de_set.setChecked(True)
        de_layout.addWidget(self.chk_de_set)
        
        self.chk_de_pascal = QCheckBox("🔺 Pascal")
        self.chk_de_pascal.setChecked(True)
        de_layout.addWidget(self.chk_de_pascal)
        
        self.chk_de_mem = QCheckBox("🧠 Bạc Nhớ")
        self.chk_de_mem.setChecked(True)
        de_layout.addWidget(self.chk_de_mem)
        
        self.chk_de_touch = QCheckBox("👆 Chạm")
        self.chk_de_touch.setChecked(False) # Too many
        de_layout.addWidget(self.chk_de_touch)
        
        de_layout.addStretch()
        controls_layout.addLayout(de_layout)
        
        layout.addWidget(controls_group)
        
        # === Results Table ===
        table_group = QGroupBox("📋 Kết Quả Quét (Cầu Mới Phát Hiện)")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Loại", "Tên Cầu", "Mô Tả", "Tỷ Lệ K2N", "Chuỗi", "Đã Thêm"
        ])
        
        # Table Styling
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        
        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 80) # Type
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 150) # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Desc
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 100) # Rate
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed) # Streak
        header.resizeSection(4, 80)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed) # Status
        header.resizeSection(5, 100)
        
        table_layout.addWidget(self.table)
        
        # === Actions ===
        actions_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Thêm Cầu Đã Chọn")
        add_btn.clicked.connect(self._add_selected)
        actions_layout.addWidget(add_btn)
        
        add_all_btn = QPushButton("➕➕ Thêm TẤT CẢ")
        add_all_btn.clicked.connect(self._add_all)
        actions_layout.addWidget(add_all_btn)
        
        clear_btn = QPushButton("🗑️ Xóa Kết Quả")
        clear_btn.clicked.connect(self._clear_results)
        actions_layout.addWidget(clear_btn)
        
        actions_layout.addStretch()
        table_layout.addLayout(actions_layout)
        
        layout.addWidget(table_group)
        
    def _start_scan(self, scan_type):
        """Start scanning process"""
        # Collect options for De
        scan_options = {
            'DE_SET': self.chk_de_set.isChecked(),
            'DE_PASCAL': self.chk_de_pascal.isChecked(),
            'DE_MEMORY': self.chk_de_mem.isChecked(),
            'DE_DYNAMIC_K': self.chk_de_touch.isChecked()
        }
        
        # Create Worker
        self.worker = BridgeScanWorker(DB_NAME, scan_type, scan_options)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_scan_finished)
        self.worker.error.connect(self._on_error)
        
        # Progress Dialog
        self.progress_dialog = ProgressDialog(self, f"Đang quét: {scan_type}")
        self.progress_dialog.cancelled.connect(self.worker.terminate)
        
        self.worker.start()
        self.progress_dialog.exec()
        
    def _on_progress(self, msg):
        if self.progress_dialog:
            self.progress_dialog.set_status(msg)
            
    def _on_error(self, msg):
        if self.progress_dialog:
            self.progress_dialog.close()
        QMessageBox.critical(self, "Lỗi Quét", msg)
        
    def _on_scan_finished(self, results, scan_type):
        if self.progress_dialog:
            self.progress_dialog.close()
            
        if scan_type == "Cầu Cố Định":
            # Just a message, no table results
             # The 'results' var will be "Fixed Bridges Updated: X" string or empty list?
             # Ah, worker emits ([], message) for Fixed. Wait, scanning worker returns (list, type).
             # For Fixed, I returned ([], msg).
             # The signature is finished(list, str).
             # So results is [], scan_type is string message? No, scan_type is "Cầu Cố Định".
             # Wait, I emitted: self.finished.emit([], f"Fixed Bridges Updated: {count}")
             # So the second arg is the message, but my signature says `scan_type`. 
             # I need to handle this.
             pass
             
         # Special handling for Fixed bridges update message which comes as type string in my worker hack
        if scan_type.startswith("Fixed Bridges Updated"):
            QMessageBox.information(self, "Thành công", scan_type)
            return

        if not results:
            QMessageBox.information(self, "Kết Quả", "Không tìm thấy cầu mới nào.")
            return
            
        # Add to table
        self._append_results(results)
        QMessageBox.information(self, "Xong", f"Đã tìm thấy {len(results)} cầu mới.")
        
    def _append_results(self, results):
        start_row = self.table.rowCount()
        self.table.setRowCount(start_row + len(results))
        
        for i, item_data in enumerate(results):
            row = start_row + i
            
            # Save data in hidden widget item
            type_item = QTableWidgetItem(item_data.get('type', ''))
            type_item.setData(Qt.ItemDataRole.UserRole, item_data) # Store full data
            self.table.setItem(row, 0, type_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(str(item_data.get('name', ''))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item_data.get('desc', ''))))
            self.table.setItem(row, 3, QTableWidgetItem(str(item_data.get('rate', ''))))
            
            streak_item = QTableWidgetItem(str(item_data.get('streak', '')))
            streak_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, streak_item)
            
            status_item = QTableWidgetItem("❌ Chưa")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, status_item)
            
    def _add_selected(self):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn cầu để thêm.")
            return
            
        added_count = 0
        errors = []
        
        for row in selected_rows:
            # Check if already added
            status_item = self.table.item(row, 5)
            if status_item.text() == "✅ Rồi":
                continue
                
            # Get data
            item = self.table.item(row, 0)
            data = item.data(Qt.ItemDataRole.UserRole)
            
            name = data.get('name')
            desc = data.get('desc')
            rate = data.get('rate')
            
            # Map types
            bridge_type = data.get('bridge_type')
            display_type = data.get('type')
            
            db_type = "UNKNOWN"
            if display_type == "LÔ_V17": db_type = "LO_POS"
            elif display_type == "LÔ_BN": db_type = "LO_MEM"
            elif display_type == "ĐỀ": 
                # Use specific hidden type if available
                db_type = bridge_type if bridge_type else "DE_ALGO"
            
            # Add to DB
            success, msg = add_managed_bridge(
                bridge_name=name,
                description=desc,
                bridge_type=db_type,
                win_rate_text=rate,
                db_name=DB_NAME,
                pos1_idx=-2, # Scanner marker
                pos2_idx=-2,
                search_rate_text=rate,
                is_enabled=1
            )
            
            if success or "already exists" in msg.lower():
                status_item.setText("✅ Rồi")
                status_item.setForeground(QColor("green"))
                added_count += 1
            else:
                errors.append(f"{name}: {msg}")
                
        # Report
        if errors:
            QMessageBox.warning(self, "Kết quả", f"Thêm {added_count} cầu.\nLỗi {len(errors)}: " + errors[0])
        else:
            QMessageBox.information(self, "Thành công", f"Đã thêm {added_count} cầu vào quản lý.")
            
    def _add_all(self):
        self.table.selectAll()
        self._add_selected()
        
    def _clear_results(self):
        self.table.setRowCount(0)
