#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Bridge Management Tab
Manage existing bridges (Edit/Delete/Optimize)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, 
    QLabel, QLineEdit, QCheckBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QAbstractItemView, QMessageBox, QRadioButton, QButtonGroup,
    QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QAction, QCursor

try:
    from logic.db_manager import DB_NAME
    from logic.data_repository import get_managed_bridges_with_prediction, load_data_ai_from_db
    from lottery_service import (
        add_managed_bridge, delete_managed_bridge, 
        update_managed_bridge, upsert_managed_bridge
    )
    from logic.bridges.bridge_manager_core import prune_bad_bridges
except ImportError as e:
    print(f"Import error in pyqt_bridge_management: {e}")
    DB_NAME = "data/xo_so_prizes_all_logic.db"
    def get_managed_bridges_with_prediction(*args, **kwargs): return []

class BridgeManagementTab(QWidget):
    """Tab for managing bridges"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.db_name = DB_NAME
        self.all_bridges_cache = []
        
        self._setup_ui()
        self.refresh_data()
        
    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # === Edit Form ===
        form_group = QGroupBox("✏️ Chỉnh Sửa Cầu")
        form_layout = QVBoxLayout()
        form_group.setLayout(form_layout)
        
        # Row 1
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Tên Cầu:"))
        self.name_input = QLineEdit()
        r1.addWidget(self.name_input, 1)
        
        self.enabled_chk = QCheckBox("🟢 Đang Bật (Sử dụng)")
        self.enabled_chk.setChecked(True)
        r1.addWidget(self.enabled_chk)
        form_layout.addLayout(r1)
        
        # Row 2
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Mô tả:"))
        self.desc_input = QLineEdit()
        r2.addWidget(self.desc_input, 1)
        form_layout.addLayout(r2)
        
        layout.addWidget(form_group)
        
        # === List Section ===
        list_group = QGroupBox("📋 Danh Sách Cầu Đang Quản Lý")
        list_layout = QVBoxLayout()
        list_group.setLayout(list_layout)
        
        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("<b>Lọc theo loại:</b>"))
        
        self.filter_group = QButtonGroup()
        self.radio_all = QRadioButton("Tất cả")
        self.radio_all.setChecked(True)
        self.radio_lo = QRadioButton("Chỉ Cầu Lô")
        self.radio_de = QRadioButton("Chỉ Cầu Đề")
        
        self.filter_group.addButton(self.radio_all)
        self.filter_group.addButton(self.radio_lo)
        self.filter_group.addButton(self.radio_de)
        
        # Events
        self.filter_group.buttonClicked.connect(self.refresh_data)
        
        filter_layout.addWidget(self.radio_all)
        filter_layout.addWidget(self.radio_lo)
        filter_layout.addWidget(self.radio_de)
        filter_layout.addStretch()
        list_layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Loại", "Tên Cầu", "Mô Tả", 
            "K1N (Thực Tế)", "K2N (Lúc Dò)", 
            "Trạng Thái", "📌 Ghim", "Ngày Tạo"
        ])
        
        # Table styling
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Column sizing
        header = self.table.horizontalHeader()
        header.resizeSection(0, 40) # ID
        header.resizeSection(1, 60) # Type
        header.resizeSection(2, 120) # Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) # Desc
        header.resizeSection(4, 100) # K1N
        header.resizeSection(5, 100) # K2N
        header.resizeSection(6, 80) # Status
        header.resizeSection(7, 60) # Pinned
        header.resizeSection(8, 100) # Date
        
        list_layout.addWidget(self.table)
        
        layout.addWidget(list_group)
        
        # === Toolbar ===
        toolbar = QHBoxLayout()
        
        btn_add = QPushButton("➕ Thêm Mới")
        btn_add.clicked.connect(self._add_bridge)
        toolbar.addWidget(btn_add)
        
        btn_update = QPushButton("💾 Cập Nhật")
        btn_update.clicked.connect(self._update_bridge)
        toolbar.addWidget(btn_update)
        
        btn_del = QPushButton("🗑️ Xóa")
        btn_del.clicked.connect(self._delete_bridge)
        toolbar.addWidget(btn_del)
        
        btn_pin = QPushButton("📌 Ghim/Bỏ Ghim")
        btn_pin.clicked.connect(self._toggle_pin)
        toolbar.addWidget(btn_pin)
        
        toolbar.addStretch()
        
        btn_refresh = QPushButton("🔄 Làm Mới")
        btn_refresh.clicked.connect(self.refresh_data)
        toolbar.addWidget(btn_refresh)
        
        btn_opt = QPushButton("⚡ Tối Ưu Thông Minh")
        btn_opt.setStyleSheet("color: blue; font-weight: bold;")
        btn_opt.clicked.connect(self._smart_optimize)
        toolbar.addWidget(btn_opt)
        
        layout.addLayout(toolbar)
        
    def refresh_data(self):
        """Reload data from DB"""
        self.table.setRowCount(0)
        
        # Load bridges
        # We need data to calculate prediction rates. 
        # Note: self.main_window might have data_service
        current_data = []
        if hasattr(self.main_window, 'data_service') and self.main_window.data_service:
             # This is a bit heavy if we load every time, but cache should handle it
             # Actually load_data() usually returns cached list
             current_data = self.main_window.data_service.load_data()
        
        if not current_data:
             try:
                 current_data, _ = load_data_ai_from_db(self.db_name)
             except:
                 pass
                 
        self.all_bridges_cache = get_managed_bridges_with_prediction(
            self.db_name,
            current_data=current_data,
            only_enabled=False
        )
        
        # Filtering
        filter_mode = "ALL"
        if self.radio_lo.isChecked(): filter_mode = "LO"
        elif self.radio_de.isChecked(): filter_mode = "DE"
        
        filtered = []
        for b in self.all_bridges_cache:
            b_type = str(b.get('type', 'UNKNOWN'))
            
            if filter_mode == "LO":
                if not b_type.startswith(('LO_', 'LO')): continue
            elif filter_mode == "DE":
                valid = ['DE_DYNAMIC_K', 'DE_POS_SUM', 'DE_SET', 'DE_PASCAL', 'DE_KILLER', 'DE_MEMORY', 'CAU_DE']
                is_de = any(b_type.startswith(t) or b_type == t for t in valid)
                if not is_de: continue
            
            filtered.append(b)
            
        # Display
        self.table.setRowCount(len(filtered))
        for i, b in enumerate(filtered):
            # ID
            item_id = QTableWidgetItem(str(b['id']))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 0, item_id)
            
            # Type
            b_type = b.get('type', 'UNKNOWN')
            display_type = b_type
            if b_type.startswith('LO_'): display_type = "🔵 Lô"
            elif b_type.startswith('DE_') or 'DE' in b_type: display_type = "🔴 Đề"
            
            item_type = QTableWidgetItem(display_type)
            item_type.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 1, item_type)
            
            # Name & Desc
            self.table.setItem(i, 2, QTableWidgetItem(str(b['name'])))
            self.table.setItem(i, 3, QTableWidgetItem(str(b['description'])))
            
            # K1N
            k1n = str(b.get('win_rate_text', ''))
            if not k1n or 'N/A' in k1n:
                k1n = f"Dự: {b.get('next_prediction_stl', 'Unknown')}"
            self.table.setItem(i, 4, QTableWidgetItem(k1n))
            
            # K2N scan
            k2n = str(b.get('search_rate_text', ''))
            if k2n and k2n != '0.00%':
                k2n = f"{k2n}"
            else:
                k2n = "-"
            self.table.setItem(i, 5, QTableWidgetItem(k2n))
            
            # Status
            is_enabled = b.get('is_enabled', 0)
            status = "🟢 Bật" if is_enabled else "🔴 Tắt"
            item_status = QTableWidgetItem(status)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not is_enabled:
                item_status.setForeground(QColor("gray"))
            self.table.setItem(i, 6, item_status)
            
            # Pinned
            is_pinned = b.get('is_pinned', 0)
            pinned = "📌 Có" if is_pinned else ""
            item_pinned = QTableWidgetItem(pinned)
            item_pinned.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_pinned:
                item_pinned.setBackground(QColor("#fff9c4"))
            self.table.setItem(i, 7, item_pinned)
            
            # Date
            date = str(b.get('created_at') or b.get('date_added', ''))
            self.table.setItem(i, 8, QTableWidgetItem(date))
            
            # Store full obj
            item_id.setData(Qt.ItemDataRole.UserRole, b)

    def _on_selection_changed(self):
        items = self.table.selectedItems()
        if not items: return
        
        # Get info from the first selected row
        row = items[0].row()
        item_id = self.table.item(row, 0)
        data = item_id.data(Qt.ItemDataRole.UserRole)
        
        if data:
            self.name_input.setText(str(data.get('name', '')))
            self.desc_input.setText(str(data.get('description', '')))
            self.enabled_chk.setChecked(bool(data.get('is_enabled', 0)))

    def _add_bridge(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên cầu")
            return
            
        success, msg = add_managed_bridge(
            name, 
            self.desc_input.text().strip(),
            "N/A"
        )
        if success:
            QMessageBox.information(self, "OK", f"Đã thêm cầu: {name}")
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Lỗi", msg)
            
    def _update_bridge(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Lỗi", "Chọn cầu để cập nhật")
            return
            
        # Update first selected
        row = rows[0].row()
        item_id = self.table.item(row, 0)
        bridge = item_id.data(Qt.ItemDataRole.UserRole)
        
        success, msg = update_managed_bridge(
            bridge['id'],
            self.desc_input.text().strip(),
            1 if self.enabled_chk.isChecked() else 0,
            self.db_name
        )
        
        if success:
             QMessageBox.information(self, "OK", "Đã cập nhật!")
             self.refresh_data()
        else:
             QMessageBox.critical(self, "Lỗi", msg)

    def _delete_bridge(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
            
        if QMessageBox.question(self, "Xác nhận", f"Xóa {len(rows)} cầu đã chọn?") != QMessageBox.StandardButton.Yes:
            return
            
        count = 0
        for idx in rows:
            row = idx.row()
            item_id = self.table.item(row, 0)
             # Note: after deleting table reloads, so indexes might change if we process one by one and reload.
             # Better to collect IDs first.
             
        ids = []
        for idx in rows:
             row = idx.row()
             item_id = self.table.item(row, 0)
             bridge = item_id.data(Qt.ItemDataRole.UserRole)
             ids.append(bridge['id'])
             
        for bid in ids:
            delete_managed_bridge(bid)
            count += 1
            
        QMessageBox.information(self, "OK", f"Đã xóa {count} cầu.")
        self.refresh_data()

    def _toggle_pin(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows: return
        
        # Toggle pin for selected
        import sqlite3
        conn = sqlite3.connect(self.db_name)
        
        for idx in rows:
            row = idx.row()
            item_id = self.table.item(row, 0)
            bridge = item_id.data(Qt.ItemDataRole.UserRole)
            
            new_val = 0 if bridge.get('is_pinned', 0) else 1
            conn.execute("UPDATE ManagedBridges SET is_pinned=? WHERE id=?", (new_val, bridge['id']))
            
        conn.commit()
        conn.close()
        self.refresh_data()
        
    def _smart_optimize(self):
        if QMessageBox.question(self, "Xác nhận", "Tối ưu thông minh sẽ TẮT các cầu yếu (K1N & K2N < 40%). Tiếp tục?") != QMessageBox.StandardButton.Yes:
            return
            
        try:
             # Need data
            current_data = []
            if hasattr(self.main_window, 'data_service') and self.main_window.data_service:
                 current_data = self.main_window.data_service.data_cache
            
            if not current_data:
                 current_data, _ = load_data_ai_from_db(self.db_name)
                 
            result = prune_bad_bridges(current_data, self.db_name)
            QMessageBox.information(self, "Kết quả", result)
            self.refresh_data()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def _show_context_menu(self, pos):
        menu = QMenu()
        pin_action = QAction("📌 Ghim/Bỏ Ghim", self)
        pin_action.triggered.connect(self._toggle_pin)
        menu.addAction(pin_action)
        menu.exec(QCursor.pos())
