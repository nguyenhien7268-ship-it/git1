#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Results Viewer
Displays detailed backtest results in a table, similar to Tkinter version.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QPushButton, QHBoxLayout, QMessageBox, QApplication,
    QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction

class ResultsViewerWindow(QDialog):
    """Window to display backtest results (TreeWidget)"""
    
    def __init__(self, parent, title, results_data, show_save_button=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1000, 600)
        self.main_window = parent
        self.results_data = results_data
        self.show_save_button = show_save_button
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        if not results_data:
            from PyQt6.QtWidgets import QLabel
            self.layout.addWidget(QLabel("Không có dữ liệu để hiển thị."))
            return
            
        # 1. Setup Tree (Table)
        self.tree = QTreeWidget()
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        
        # Headers
        headers = [str(x) for x in results_data[0]]
        self.tree.setHeaderLabels(headers)
        
        # Populate
        self._populate_tree(results_data[1:])
        
        self.layout.addWidget(self.tree)
        
        # 2. Buttons
        btn_layout = QHBoxLayout()
        
        btn_copy = QPushButton("📋 Copy Toàn Bộ Bảng (TSV)")
        btn_copy.clicked.connect(self._copy_all)
        btn_layout.addWidget(btn_copy)
        
        if show_save_button:
            btn_save = QPushButton("💾 Lưu Cầu Đã Chọn...")
            btn_save.clicked.connect(self._save_selected)
            btn_layout.addWidget(btn_save)
            
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        btn_close.setFixedWidth(100)
        btn_layout.addWidget(btn_close)
        
        self.layout.addLayout(btn_layout)
        
    def _populate_tree(self, data_rows):
        for i, row in enumerate(data_rows):
            # Convert all items to string
            str_items = [str(x) if x is not None else "" for x in row]
            item = QTreeWidgetItem(str_items)
            
            # Simple styling based on content
            if i == 0 and "Tỷ Lệ %" in str_items[0]:
                item.setBackground(0, Qt.GlobalColor.yellow) # Highlight rate
            if "Chuỗi K2N" in str_items[0]:
                item.setBackground(0, Qt.GlobalColor.cyan)
                
            self.tree.addTopLevelItem(item)
            
        for i in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(i)

    def _copy_all(self):
        try:
            tsv_lines = []
            # Header
            header_txt = "\t".join([self.tree.headerItem().text(i) for i in range(self.tree.columnCount())])
            tsv_lines.append(header_txt)
            
            # Rows
            iterator = QTreeWidgetItemIterator(self.tree)
            while iterator.value():
                item = iterator.value()
                row_txt = "\t".join([item.text(i) for i in range(self.tree.columnCount())])
                tsv_lines.append(row_txt)
                iterator += 1
                
            full_text = "\n".join(tsv_lines)
            QApplication.clipboard().setText(full_text)
            QMessageBox.information(self, "Copy", f"Đã copy {len(tsv_lines)} dòng vào clipboard.")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", str(e))

    def _save_selected(self):
        # Delegate back to main window if it has the capability
        if hasattr(self.main_window, '_save_bridge_from_treeview'):
            # Pass the currently selected item or the tree
            # In Tkinter version it passed the whole tree logic, but here we might want simpler
            # Check what main_window supports
            items = self.tree.selectedItems()
            if not items:
                QMessageBox.warning(self, "Chưa chọn", "Vui lòng chọn dòng chứa thông tin cầu để lưu.")
                return
            
            # We assume the main window can handle a list of string values or similar
            # For now, just show info or try to call
            try:
                # Mockup: pass the first selected item's text
                # We need to reconstruct the logic. Tkinter implementation relied on specific row indices.
                # Here we might need a dedicated method in main window for PyQt
                pass
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))
        else:
             QMessageBox.information(self, "Info", "Chức năng lưu chưa được liên kết với màn hình chính PyQt.")

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item: return
        
        menu = QMenu()
        
        # Get column index
        col = self.tree.currentColumn()
        cell_text = item.text(col)
        
        action_copy = QAction(f"Copy '{cell_text}'", self)
        action_copy.triggered.connect(lambda: QApplication.clipboard().setText(cell_text))
        menu.addAction(action_copy)
        
        if self.show_save_button:
            menu.addSeparator()
            action_save = QAction("Lưu cầu này...", self)
            action_save.triggered.connect(self._save_selected)
            menu.addAction(action_save)
            
        menu.exec(self.tree.viewport().mapToGlobal(position))

# Helper iterator for TreeWidget
from PyQt6.QtWidgets import QTreeWidgetItemIterator
