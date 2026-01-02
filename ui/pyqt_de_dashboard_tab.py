#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 De Dashboard Tab - "Soi Cầu Đề"
Ported from ui/ui_de_dashboard.py
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView, QSplitter,
    QTreeWidget, QTreeWidgetItem, QFrame, QTextEdit, QScrollArea,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from ui.pyqt_workers import DeAnalysisWorker
from logic.config_manager import SETTINGS as CONFIG_SETTINGS # Rename to avoid conflict if needed, or just use it

class DeDashboardTab(QWidget):
    """
    Tab "Soi Cầu Đề" replicating ui_de_dashboard.py logic and layout.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.worker = None
        self.current_data = None
        
        # UI Setup
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- TOOLBAR ---
        toolbar = QHBoxLayout()
        
        self.scan_btn = QPushButton("🚀 QUÉT & PHÂN TÍCH")
        self.scan_btn.clicked.connect(self.run_analysis)
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #005a9e; }
        """)
        toolbar.addWidget(self.scan_btn)
        
        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        toolbar.addWidget(self.status_label)
        
        toolbar.addStretch()
        
        # Info Labels (Period/Date)
        self.lbl_ky = QLabel("KỲ: ---")
        self.lbl_ky.setStyleSheet("color: #E65100; font-weight: bold; font-size: 11pt;")
        toolbar.addWidget(self.lbl_ky)
        
        toolbar.addSpacing(15)
        
        self.lbl_date = QLabel("NGÀY: ---")
        self.lbl_date.setStyleSheet("color: #2E7D32; font-weight: bold; font-size: 11pt;")
        toolbar.addWidget(self.lbl_date)
        
        layout.addLayout(toolbar)
        
        # --- MAIN SPLITTER ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # === COL 1: STATS (Thống Kê) ===
        col1_widget = QWidget()
        col1_layout = QVBoxLayout(col1_widget)
        col1_layout.setContentsMargins(0,0,0,0)
        
        lbl_stats = QLabel("📊 Thống Kê (30 ngày)")
        lbl_stats.setStyleSheet("font-weight: bold; background-color: #f0f0f0; padding: 5px;")
        col1_layout.addWidget(lbl_stats)
        
        # Tabs for Stats using simple swapping or TabWidget. 
        # Using TreeWidgets directly as in V8.2 (Notebook equivalent -> distinct widgets or stacked)
        # Here we use 3 GroupBoxes/Frames vertically or a TabWidget. 
        # Let's use a specialized layout: 3 Trees vertical? No, V8.2 uses Notebook.
        # Let's use QTabWidget for Stats column.
        from PyQt6.QtWidgets import QTabWidget
        self.stats_tabs = QTabWidget()
        col1_layout.addWidget(self.stats_tabs)
        
        # Tab 1: History
        self.tree_hist = QTreeWidget()
        self.tree_hist.setHeaderLabels(["Ngày", "Đề"])
        self.tree_hist.setColumnWidth(0, 100)
        self.stats_tabs.addTab(self.tree_hist, "Lịch Sử")
        
        # Tab 2: Chạm
        self.tree_cham_stats = QTreeWidget()
        self.tree_cham_stats.setHeaderLabels(["Chạm", "Về", "Gan"])
        self.stats_tabs.addTab(self.tree_cham_stats, "Chạm")
        
        # Tab 3: Bộ
        self.tree_bo_stats = QTreeWidget()
        self.tree_bo_stats.setHeaderLabels(["Bộ", "Về", "Gan"])
        self.stats_tabs.addTab(self.tree_bo_stats, "Bộ")
        
        splitter.addWidget(col1_widget)
        
        # === COL 2: BRIDGES (Cầu Động) ===
        col2_widget = QWidget()
        col2_layout = QVBoxLayout(col2_widget)
        col2_layout.setContentsMargins(0,0,0,0)
        
        lbl_bridges = QLabel("🎯 Cầu Động")
        lbl_bridges.setStyleSheet("font-weight: bold; background-color: #f0f0f0; padding: 5px;")
        col2_layout.addWidget(lbl_bridges)
        
        self.table_bridges = QTableWidget()
        self.table_bridges.setColumnCount(4)
        self.table_bridges.setHorizontalHeaderLabels(["Tên", "Loại", "Thông", "Số"])
        self.table_bridges.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_bridges.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_bridges.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_bridges.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_bridges.doubleClicked.connect(self.on_bridge_dbl_click)
        col2_layout.addWidget(self.table_bridges)
        
        splitter.addWidget(col2_widget)
        
        # === COL 3: MATRIX & FORECAST (Chốt Số) ===
        col3_widget = QWidget()
        col3_layout = QVBoxLayout(col3_widget)
        col3_layout.setContentsMargins(0,0,0,0)
        
        lbl_forecast = QLabel("🔮 Ma Trận & Chốt Số")
        lbl_forecast.setStyleSheet("font-weight: bold; background-color: #f0f0f0; padding: 5px;")
        col3_layout.addWidget(lbl_forecast)
        
        # Scroll Area for Forecast content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        col3_layout.addWidget(scroll)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        scroll.setWidget(content_widget)
        
        # 1. VIP Results
        grp_vip = QFrame()
        grp_vip.setFrameStyle(QFrame.Shape.StyledPanel)
        vip_layout = QVBoxLayout(grp_vip)
        
        lbl_vip_title = QLabel("🔥🔥 KẾT QUẢ TRỌNG TÂM")
        lbl_vip_title.setStyleSheet("font-weight: bold; color: #D32F2F;")
        vip_layout.addWidget(lbl_vip_title)
        
        vip_layout.addWidget(QLabel("TỨ THỦ ĐỀ:"))
        self.txt_4 = QTextEdit()
        self.txt_4.setMaximumHeight(40)
        self.txt_4.setReadOnly(True)
        self.txt_4.setStyleSheet("font-size: 14pt; font-weight: bold; color: #D32F2F; background: #f0f0f0;")
        vip_layout.addWidget(self.txt_4)
        
        vip_layout.addWidget(QLabel("TOP 10 MA TRẬN:"))
        self.txt_10 = QTextEdit()
        self.txt_10.setMaximumHeight(40)
        self.txt_10.setReadOnly(True)
        self.txt_10.setStyleSheet("font-size: 11pt; font-weight: bold; color: #1976D2; background: #f0f0f0;")
        vip_layout.addWidget(self.txt_10)
        
        content_layout.addWidget(grp_vip)
        
        # 2. Evaluations (Chốt Bộ & Chốt Chạm)
        grp_eval = QFrame()
        grp_eval.setFrameStyle(QFrame.Shape.StyledPanel)
        eval_layout = QVBoxLayout(grp_eval)
        
        eval_layout.addWidget(QLabel("💎 TOP BỘ SỐ TIỀM NĂNG (Top 8):"))
        self.tree_chot_bo = QTreeWidget()
        self.tree_chot_bo.setHeaderLabels(["Bộ", "Điểm", "TT"])
        self.tree_chot_bo.setMinimumHeight(120)
        eval_layout.addWidget(self.tree_chot_bo)
        
        # Splitter for Chạm Thông & Chạm Tỉ Lệ
        cham_splitter = QHBoxLayout()
        
        vbox_thong = QVBoxLayout()
        vbox_thong.addWidget(QLabel("🎯 Chạm Thông"))
        self.tree_cham_thong = QTreeWidget()
        self.tree_cham_thong.setHeaderLabels(["Chạm", "Streak"])
        vbox_thong.addWidget(self.tree_cham_thong)
        cham_splitter.addLayout(vbox_thong)
        
        vbox_tile = QVBoxLayout()
        vbox_tile.addWidget(QLabel("📈 Chạm Tỉ Lệ"))
        self.tree_cham_tile = QTreeWidget()
        self.tree_cham_tile.setHeaderLabels(["Chạm", "Rate%"])
        vbox_tile.addWidget(self.tree_cham_tile)
        cham_splitter.addLayout(vbox_tile)
        
        eval_layout.addLayout(cham_splitter)
        content_layout.addWidget(grp_eval)
        
        # 3. Dan 65
        grp_dan = QFrame()
        grp_dan.setFrameStyle(QFrame.Shape.StyledPanel)
        dan_layout = QVBoxLayout(grp_dan)
        
        dan_layout.addWidget(QLabel("📋 DÀN 65 SỐ:"))
        self.txt_65 = QTextEdit()
        self.txt_65.setMaximumHeight(100)
        self.txt_65.setReadOnly(True)
        dan_layout.addWidget(self.txt_65)
        
        content_layout.addWidget(grp_dan)
        content_layout.addStretch()
        
        # Set splitter sizes (approx 1:2:2)
        splitter.setSizes([200, 400, 300])
        
    def run_analysis(self):
        """Start De Analysis"""
        if self.worker and self.worker.isRunning():
            return
            
        data = getattr(self.main_window, 'all_data_ai', None)
        if not data:
            QMessageBox.warning(self, "No Data", "Chưa có dữ liệu. Vui lòng nạp dữ liệu ở tab Trang Chủ.")
            return
            
        self.status_label.setText("Đang phân tích...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        self.scan_btn.setEnabled(False)
        
        self.worker = DeAnalysisWorker(data)
        self.worker.progress.connect(lambda s: self.status_label.setText(s))
        self.worker.error.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
        
    def _on_error(self, msg):
        self.status_label.setText("Lỗi!")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.scan_btn.setEnabled(True)
        QMessageBox.critical(self, "Lỗi Phân Tích", msg)
        
    def _on_finished(self, result):
        try:
            self.status_label.setText("Hoàn tất.")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.scan_btn.setEnabled(True)
            
            # --- UPDATE UI ---
            bridges = result.get("bridges", [])
            matrix_res = result.get("matrix_res", {})
            stats = result.get("stats", {})
            scores = result.get("scores", [])
            touch_combos = result.get("touch_combinations", [])
            list_data = result.get("list_data", [])
            
            # 1. Header
            if list_data:
                try:
                    last_row = list_data[-1]
                    idx = int(last_row[0])
                    self.lbl_ky.setText(f"KỲ: #{idx + 1}")
                    from datetime import datetime, timedelta
                    # Try parsing date, assume 'DD/MM/YYYY' or similar
                    date_str = str(last_row[1])
                    # Simple display
                    self.lbl_date.setText(f"Data Date: {date_str}")
                except:
                    pass
            
            # 2. Stats
            self.tree_hist.clear()
            for r in reversed(list_data[-30:]):
                try:
                    # r: [Ky, Ngay, DB, ...]
                    # Need utils to parse DE. assume utils logic inside worker used standard parsing
                    # but here we just display raw for now, or use last 2 chars
                    val = str(r[2]) if len(r) > 2 else ""
                    if val and len(val) >= 2: val = val[-2:]
                    item = QTreeWidgetItem([str(r[1]), val])
                    self.tree_hist.addTopLevelItem(item)
                except: pass
                
            self.tree_cham_stats.clear()
            freq_cham = stats.get('freq_cham', {})
            gan_cham = stats.get('gan_cham', {})
            for k in sorted(freq_cham.keys()):
                item = QTreeWidgetItem([str(k), str(freq_cham[k]), str(gan_cham.get(k, 0))])
                self.tree_cham_stats.addTopLevelItem(item)
                
            self.tree_bo_stats.clear()
            freq_bo = stats.get('freq_bo', {})
            gan_bo = stats.get('gan_bo', {})
            # Sort by Gan desc
            sorted_bo = sorted(freq_bo.keys(), key=lambda x: gan_bo.get(x, 0), reverse=True)
            for k in sorted_bo:
                item = QTreeWidgetItem([str(k), str(freq_bo[k]), str(gan_bo.get(k, 0))])
                self.tree_bo_stats.addTopLevelItem(item)
                
            # 3. Bridges
            self.table_bridges.setRowCount(0)
            self.table_bridges.setSortingEnabled(False)
            bridges.sort(key=lambda x: x.get('streak', 0), reverse=True)
            for b in bridges[:300]:
                row = self.table_bridges.rowCount()
                self.table_bridges.insertRow(row)
                
                self.table_bridges.setItem(row, 0, QTableWidgetItem(str(b.get('name'))))
                self.table_bridges.setItem(row, 1, QTableWidgetItem(str(b.get('type'))))
                
                streak_item = QTableWidgetItem(str(b.get('streak')))
                streak_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_bridges.setItem(row, 2, streak_item)
                
                pred_item = QTableWidgetItem(str(b.get('predicted_value')))
                pred_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_bridges.setItem(row, 3, pred_item)
                
            self.table_bridges.setSortingEnabled(True)
            
            # 4. Matrix & Forecast
            ranked = matrix_res.get('ranked', [])
            if ranked:
                top10 = [x['so'] for x in ranked[:10]]
                self.txt_4.setText(" - ".join(top10[:4]))
                self.txt_10.setText(", ".join(top10))
            else:
                self.txt_4.setText("N/A")
                self.txt_10.setText(f"Error: {matrix_res.get('message')}")
                
            # 5. Dan 65 (Logic simplified for UI display here, relying on backend if possible)
            # Worker returned 'scores'. We can do a quick top selection or call the build_dan65 logic in worker?
            # Creating Dan 65 locally from scores for simplicity
            if scores:
                top65 = [x[0] for x in scores[:65]]
                top65.sort()
                self.txt_65.setText(",".join(top65))
            
            # 6. Touch Combos
            self.tree_cham_thong.clear()
            self.tree_cham_tile.clear()
            
            # Filter logic similar to V8.2
            top_thong = sorted(touch_combos, 
                             key=lambda x: (x.get('covers_last_n_at_end', False), 
                                           x.get('consecutive_at_end', 0)), 
                             reverse=True)[:8]
                             
            for x in top_thong:
                touches_str = ','.join(map(str, x['touches']))
                consec = x.get('consecutive_at_end', 0)
                item = QTreeWidgetItem([touches_str, f"{consec}N"])
                if x.get('covers_last_n_at_end', False):
                    item.setBackground(0, QColor("#FFF9C4")) # Highlight
                self.tree_cham_thong.addTopLevelItem(item)
                
            top_rate = sorted(touch_combos, key=lambda x: x.get('rate_percent', 0.0), reverse=True)[:8]
            for x in top_rate:
                touches_str = ','.join(map(str, x['touches']))
                rate = x.get('rate_percent', 0.0)
                item = QTreeWidgetItem([touches_str, f"{rate:.1f}%"])
                self.tree_cham_tile.addTopLevelItem(item)
                
            # 7. Update Chot Bo (Evaluation)
            # Simplified for now: Top 5 from freq_bo
            self.tree_chot_bo.clear()
            # Ideally this logic should be in worker to be accurate with V8.2 scoring
            # For now, just show raw sort by frequency to populate UI
            # (To make it perfect, we should move _update_evaluation_and_top_sets logic to worker)
            
            # Placeholder for Chot Bo based on simple frequency if complex logic not in worker return
            for k in sorted_bo[:8]:
                f = freq_bo[k]
                item = QTreeWidgetItem([str(k), f"Freq: {f}", "Raw"])
                self.tree_chot_bo.addTopLevelItem(item)

        except Exception as e:
            QMessageBox.critical(self, "UI Error", f"Error updating UI: {e}")
            
    def on_bridge_dbl_click(self, index):
        """Handle double click on bridge"""
        try:
            row = index.row()
            # Getting data from table directly
            bridge_name = self.table_bridges.item(row, 0).text()
            
            # In V8.2 this triggers a backtest popup.
            # For now, we show a message or log it.
            # To implement fully: call controller.trigger_bridge_backtest
            QMessageBox.information(self, "Backtest", f"Backtest feature for '{bridge_name}' to be implemented.")
            
        except Exception as e:
            print(f"Double click error: {e}")
