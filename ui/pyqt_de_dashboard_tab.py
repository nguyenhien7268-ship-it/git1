#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 De Dashboard Tab - "Soi Cầu Đề"
Ported from ui/ui_de_dashboard.py
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QTextEdit,
    QFrame, QSplitter, QTabWidget, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
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
        self.table_bridges.setColumnCount(3)
        self.table_bridges.setHorizontalHeaderLabels(["Tên", "Thông", "Số"])
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
        
        # === COL 3: MATRIX & FORECAST (Chốt Số) ===
        col3_widget = QWidget()
        col3_layout = QVBoxLayout(col3_widget)
        col3_layout.setContentsMargins(0,0,0,0)
        
        lbl_forecast = QLabel("🔮 Ma Trận & Chốt Số")
        lbl_forecast.setStyleSheet("font-weight: bold; background-color: #f0f0f0; padding: 5px;")
        col3_layout.addWidget(lbl_forecast)
        
        # New Tab Widget instead of ScrollArea
        from PyQt6.QtWidgets import QTabWidget
        self.tabs_forecast = QTabWidget()
        col3_layout.addWidget(self.tabs_forecast)
        
        # TAB 1: RESULTS (VIP & Matrix)
        tab_res = QWidget()
        lay_res = QVBoxLayout(tab_res)
        
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
        
        lay_res.addWidget(grp_vip)
        
        # Dan 65 also here
        grp_dan = QFrame()
        grp_dan.setFrameStyle(QFrame.Shape.StyledPanel)
        dan_layout = QVBoxLayout(grp_dan)
        dan_layout.addWidget(QLabel("📋 DÀN 65 SỐ:"))
        self.txt_65 = QTextEdit()
        self.txt_65.setMaximumHeight(100)
        self.txt_65.setReadOnly(True)
        dan_layout.addWidget(self.txt_65)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Score threshold
        filter_layout.addWidget(QLabel("Điểm ≥"))
        self.score_spin = QSpinBox()
        self.score_spin.setRange(0, 100)
        self.score_spin.setValue(0)
        self.score_spin.setMaximumWidth(60)
        filter_layout.addWidget(self.score_spin)
        
        # Gan threshold
        filter_layout.addWidget(QLabel("Loại Gan >"))
        self.gan_spin = QSpinBox()
        self.gan_spin.setRange(0, 30)
        self.gan_spin.setValue(30)  # Default: don't filter
        self.gan_spin.setMaximumWidth(60)
        filter_layout.addWidget(self.gan_spin)
        
        # Hot only checkbox
        self.hot_only_check = QCheckBox("Chỉ Bộ Hot")
        filter_layout.addWidget(self.hot_only_check)
        
        # Apply button
        self.apply_filter_btn = QPushButton("Áp Dụng Lọc")
        self.apply_filter_btn.clicked.connect(self._apply_dan_filter)
        self.apply_filter_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        filter_layout.addWidget(self.apply_filter_btn)
        
        filter_layout.addStretch()
        dan_layout.addLayout(filter_layout)
        
        lay_res.addWidget(grp_dan)

        
        # Chạm Analysis (Added for better UX)
        grp_cham = QFrame()
        grp_cham.setFrameStyle(QFrame.Shape.StyledPanel)
        cham_layout = QHBoxLayout(grp_cham)
        
        # Chạm Thông column
        cham_thong_layout = QVBoxLayout()
        cham_thong_layout.addWidget(QLabel("🎯 Chạm Thông"))
        self.tree_cham_thong_vip = QTreeWidget()
        self.tree_cham_thong_vip.setHeaderLabels(["Chạm", "Streak"])
        self.tree_cham_thong_vip.setMaximumHeight(150)
        cham_thong_layout.addWidget(self.tree_cham_thong_vip)
        cham_layout.addLayout(cham_thong_layout)
        
        # Chạm Tỉ Lệ column
        cham_tile_layout = QVBoxLayout()
        cham_tile_layout.addWidget(QLabel("📈 Chạm Tỉ Lệ"))
        self.tree_cham_tile_vip = QTreeWidget()
        self.tree_cham_tile_vip.setHeaderLabels(["Chạm", "Rate%"])
        self.tree_cham_tile_vip.setMaximumHeight(150)
        cham_tile_layout.addWidget(self.tree_cham_tile_vip)
        cham_layout.addLayout(cham_tile_layout)
        
        lay_res.addWidget(grp_cham)
        
        lay_res.addStretch()
        self.tabs_forecast.addTab(tab_res, "CHỐT SỐ VIP")

        
        # TAB 1.5: ĐIỄM SỐ (Score Display)
        tab_scores = QWidget()
        lay_scores = QVBoxLayout(tab_scores)
        
        # Score table
        self.table_scores = QTableWidget()
        self.table_scores.setColumnCount(2)
        self.table_scores.setHorizontalHeaderLabels(["Số", "Điểm"])
        self.table_scores.horizontalHeader().setStretchLastSection(True)
        self.table_scores.setAlternatingRowColors(True)
        self.table_scores.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_scores.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        lay_scores.addWidget(self.table_scores)
        self.tabs_forecast.addTab(tab_scores, "ĐIỄM SỐ")

        
        # TAB 3: ĐÁNH GIÁ (Upgraded to 4 sub-tabs)
        tab_eval = QWidget()
        lay_eval = QVBoxLayout(tab_eval)
        
        # Create sub-tabs for evaluation
        self.eval_subtabs = QTabWidget()
        lay_eval.addWidget(self.eval_subtabs)
        
        # SUB-TAB 1: Bộ (Set Evaluation)
        subtab_bo = QWidget()
        lay_bo = QVBoxLayout(subtab_bo)
        lay_bo.addWidget(QLabel("💎 ĐÁNH GIÁ BỘ SỐ (15 Bộ):"))
        self.table_bo_eval = QTableWidget()
        self.table_bo_eval.setColumnCount(5)
        self.table_bo_eval.setHorizontalHeaderLabels(["Bộ", "Tần Suất", "Gan", "Điểm", "Rank"])
        self.table_bo_eval.horizontalHeader().setStretchLastSection(True)
        self.table_bo_eval.setAlternatingRowColors(True)
        lay_bo.addWidget(self.table_bo_eval)
        self.eval_subtabs.addTab(subtab_bo, "Bộ")
        
        # SUB-TAB 2: Điểm ĐG (Score Evaluation) - Reuse score table concept
        subtab_diem = QWidget()
        lay_diem = QVBoxLayout(subtab_diem)
        lay_diem.addWidget(QLabel("📊 ĐIỂM ĐÁNH GIÁ (Top 50):"))
        self.table_diem_eval = QTableWidget()
        self.table_diem_eval.setColumnCount(3)
        self.table_diem_eval.setHorizontalHeaderLabels(["Số", "Điểm", "Ghi Chú"])
        self.table_diem_eval.horizontalHeader().setStretchLastSection(True)
        self.table_diem_eval.setAlternatingRowColors(True)
        lay_diem.addWidget(self.table_diem_eval)
        self.eval_subtabs.addTab(subtab_diem, "Điểm ĐG")
        
        # SUB-TAB 3: Trạng thái (Status)
        subtab_status = QWidget()
        lay_status = QVBoxLayout(subtab_status)
        
        # Hot Sets
        lay_status.addWidget(QLabel("🔥 BỘ HOT (Tần suất cao):"))
        self.tree_hot_sets = QTreeWidget()
        self.tree_hot_sets.setHeaderLabels(["Bộ", "Freq", "Gan"])
        lay_status.addWidget(self.tree_hot_sets)
        
        # Gan Sets
        lay_status.addWidget(QLabel("❄️ BỘ GAN (Lâu không về):"))
        self.tree_gan_sets = QTreeWidget()
        self.tree_gan_sets.setHeaderLabels(["Bộ", "Gan", "Freq"])
        lay_status.addWidget(self.tree_gan_sets)
        
        self.eval_subtabs.addTab(subtab_status, "Trạng thái")
        
        # SUB-TAB 4: Chạm (Touch Analysis) - Keep existing
        subtab_cham = QWidget()
        l_cham = QVBoxLayout(subtab_cham)
        
        cham_subsplit = QHBoxLayout()
        vbox_thong = QVBoxLayout()
        vbox_thong.addWidget(QLabel("🎯 Chạm Thông"))
        self.tree_cham_thong = QTreeWidget()
        self.tree_cham_thong.setHeaderLabels(["Chạm", "Streak"])
        vbox_thong.addWidget(self.tree_cham_thong)
        cham_subsplit.addLayout(vbox_thong)
        
        vbox_tile = QVBoxLayout()
        vbox_tile.addWidget(QLabel("📈 Chạm Tỉ Lệ"))
        self.tree_cham_tile = QTreeWidget()
        self.tree_cham_tile.setHeaderLabels(["Chạm", "Rate%"])
        vbox_tile.addWidget(self.tree_cham_tile)
        cham_subsplit.addLayout(vbox_tile)
        
        l_cham.addLayout(cham_subsplit)
        self.eval_subtabs.addTab(subtab_cham, "Chạm")
        
        # ĐÁNH GIÁ BỘ Section (below tabs)
        lay_eval.addWidget(QLabel("💎 ĐÁNH GIÁ CHI TIẾT 15 BỘ SỐ:"))
        self.table_bo_detail = QTableWidget()
        self.table_bo_detail.setColumnCount(6)
        self.table_bo_detail.setHorizontalHeaderLabels(["Bộ", "Tần Suất", "Gan", "Điểm", "Rank", "Trạng Thái"])
        self.table_bo_detail.horizontalHeader().setStretchLastSection(True)
        self.table_bo_detail.setAlternatingRowColors(True)
        self.table_bo_detail.setMaximumHeight(250)
        lay_eval.addWidget(self.table_bo_detail)
        
        self.tabs_forecast.addTab(tab_eval, "ĐÁNH GIÁ")

        
        splitter.addWidget(col3_widget)
        
        # Set splitter sizes (approx 1:2:2)
        splitter.setSizes([200, 400, 300])
        
        # Store current analysis result for filtering
        self.current_result = None
        
    def _apply_dan_filter(self):
        """Apply filtering to Dàn 65 based on user criteria"""
        try:
            if not self.current_result:
                QMessageBox.information(self, "Thông báo", "Vui lòng chạy phân tích trước khi lọc!")
                return
            
            # Get filter criteria
            min_score = self.score_spin.value()
            max_gan = self.gan_spin.value()
            hot_only = self.hot_only_check.isChecked()
            
            # Get data
            scores = self.current_result.get("scores", [])
            stats = self.current_result.get("stats", {})
            freq_bo = stats.get("freq_bo", {})
            gan_bo = stats.get("gan_bo", {})
            
            if not scores:
                QMessageBox.warning(self, "Lỗi", "Không có dữ liệu điểm số!")
                return
            
            # Filter numbers
            filtered_numbers = []
            
            for num_str, score, info in scores:
                # Check score threshold
                if score < min_score:
                    continue
                
                # Check Gan threshold (get Gan for the number's set)
                # Number belongs to a set (e.g., "05" belongs to "00")
                try:
                    num_int = int(num_str)
                    bo_name = str(num_int // 10).zfill(1)  # 05 -> "0", 15 -> "1"
                    
                    gan = gan_bo.get(bo_name, 0)
                    if gan > max_gan:
                        continue
                    
                    # Check Hot only
                    if hot_only:
                        freq = freq_bo.get(bo_name, 0)
                        if freq < 3:  # Not hot
                            continue
                    
                    filtered_numbers.append(num_str)
                    
                except:
                    # If parsing fails, include the number
                    filtered_numbers.append(num_str)
            
            # Update display
            if filtered_numbers:
                filtered_numbers.sort()
                self.txt_65.setText(", ".join(filtered_numbers))
                
                # Show summary
                original_count = len([x[0] for x in scores[:65]])
                filtered_count = len(filtered_numbers)
                self.status_label.setText(f"Đã lọc: {filtered_count}/{original_count} số")
                self.status_label.setStyleSheet("color: blue; font-weight: bold;")
            else:
                self.txt_65.setText("Không có số nào thỏa mãn điều kiện lọc")
                self.status_label.setText("Lọc: 0 số")
                self.status_label.setStyleSheet("color: orange; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi lọc: {e}")
            import traceback
            traceback.print_exc()
    
    def on_bridge_dbl_click(self, index):
        """Handle double-click on bridge row to show backtest"""
        print("=" * 80)
        print("DEBUG: on_bridge_dbl_click CALLED!")
        print(f"DEBUG: index.row() = {index.row()}")
        print("=" * 80)
        
        try:
            row = index.row()
            bridge_name = self.table_bridges.item(row, 0).text()
            streak = self.table_bridges.item(row, 1).text()
            pred_val = self.table_bridges.item(row, 2).text()
            
            # Fetch real backtest data
            from logic.de_backtest import get_bridge_backtest
            
            # Get data from main window
            all_data = []
            if hasattr(self.main_window, 'data_service') and self.main_window.data_service:
                all_data = self.main_window.data_service.load_data()
            
            if not all_data:
                QMessageBox.warning(self, "Lỗi", "Không có dữ liệu để backtest!")
                return

            
            print(f"DEBUG: Starting backtest for {bridge_name}")
            print(f"DEBUG: Data length: {len(all_data)}")
            
            try:
                backtest_result = get_bridge_backtest(bridge_name, all_data, days=30)
            except Exception as e:
                print(f"ERROR: Backtest failed: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Lỗi", f"Lỗi khi chạy backtest: {e}")
                return
            
            # Debug logging
            print(f"Backtest result for {bridge_name}:")
            print(f"  - Has error: {'error' in backtest_result}")
            if 'error' in backtest_result:
                print(f"  - Error: {backtest_result.get('error')}")
            print(f"  - History length: {len(backtest_result.get('history', []))}")
            print(f"  - Win rate: {backtest_result.get('win_rate', 0)}")
            print(f"  - Total tests: {backtest_result.get('total_tests', 0)}")

            print(f"  - Win rate: {backtest_result.get('win_rate', 0)}")
            
            # Create backtest dialog
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Backtest: {bridge_name}")
            dialog.resize(700, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Warning label
            warning_label = QLabel()
            warning_label.setText(
                "⚠️ <b>Lưu ý:</b> Backtest này sử dụng prediction hiện tại cho tất cả các kỳ trong quá khứ. "
                "Kết quả chỉ mang tính tham khảo, không phản ánh prediction thực tế của từng kỳ."
            )
            warning_label.setWordWrap(True)
            warning_label.setStyleSheet("background-color: #FFF3CD; padding: 10px; border-radius: 5px; color: #856404;")
            warning_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(warning_label)
            
            # Summary info
            summary_label = QLabel()

            
            # Check if there's an error AND no history
            if 'error' in backtest_result and not backtest_result.get('history'):
                summary_html = f"<p style='color: red;'><b>Lỗi:</b> {backtest_result['error']}</p>"
            else:
                win_rate = backtest_result.get('win_rate', 0)
                total_wins = backtest_result.get('total_wins', 0)
                total_tests = backtest_result.get('total_tests', 0)
                avg_streak = backtest_result.get('avg_streak', 0)
                
                summary_html = f"""
                <h3>Thông Tin Cầu</h3>
                <p><b>Tên:</b> {bridge_name}</p>
                <p><b>Streak hiện tại:</b> {streak} ngày</p>
                <p><b>Dự đoán:</b> {pred_val}</p>
                <hr>
                <h3>Kết Quả Backtest (30 ngày gần nhất)</h3>
                <p><b>Tỉ lệ trúng:</b> <span style='color: {"green" if win_rate >= 50 else "red"}; font-weight: bold;'>{win_rate:.1f}%</span> ({total_wins}/{total_tests})</p>
                <p><b>Streak trung bình:</b> {avg_streak:.1f} ngày</p>
                """

            
            summary_label.setText(summary_html)
            summary_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(summary_label)
            
            # History table
            if backtest_result.get('history'):
                history_table = QTableWidget()
                history_table.setColumnCount(4)
                history_table.setHorizontalHeaderLabels(["Ngày", "Dự đoán", "Kết quả", "Trúng/Trượt"])
                history_table.setRowCount(len(backtest_result['history']))
                
                for i, entry in enumerate(reversed(backtest_result['history'])):  # Show newest first
                    history_table.setItem(i, 0, QTableWidgetItem(entry['date']))
                    history_table.setItem(i, 1, QTableWidgetItem(str(entry['predicted'])))
                    history_table.setItem(i, 2, QTableWidgetItem(str(entry['actual'])))
                    
                    result_item = QTableWidgetItem("✅ Trúng" if entry['result'] == 'win' else "❌ Trượt")
                    result_item.setForeground(QColor("#4CAF50") if entry['result'] == 'win' else QColor("#F44336"))
                    history_table.setItem(i, 3, result_item)
                
                history_table.resizeColumnsToContents()
                layout.addWidget(history_table)
            
            # Close button
            close_btn = QPushButton("Đóng")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Lỗi", f"Không thể hiển thị backtest: {e}")
            import traceback
            traceback.print_exc()

    
    def run_analysis(self):
        """Start De Analysis"""
        if self.worker and self.worker.isRunning():
            return
            
        data = None
        if hasattr(self.main_window, 'data_service') and self.main_window.data_service:
            data = self.main_window.data_service.load_data()
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
            
            # Store result for filtering
            self.current_result = result
            
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
            
            # Debug: Check bridge data
            print(f"DEBUG: Received {len(bridges)} bridges")
            if bridges:
                print(f"DEBUG: First bridge sample: {bridges[0]}")
            
            bridges.sort(key=lambda x: x.get('current_streak', 0), reverse=True)
            for b in bridges[:300]:

                row = self.table_bridges.rowCount()
                self.table_bridges.insertRow(row)
                
                # Column 0: Tên
                self.table_bridges.setItem(row, 0, QTableWidgetItem(str(b.get('name'))))
                
                # Column 1: Thông (Streak) - Use 'current_streak' field
                streak_val = b.get('current_streak', 0)
                streak_item = QTableWidgetItem(str(streak_val))
                streak_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_bridges.setItem(row, 1, streak_item)
                
                # Column 2: Số (Predicted Value) - Use 'next_prediction_stl' field
                pred_val = b.get('next_prediction_stl', '')
                if pred_val:
                    pred_item = QTableWidgetItem(str(pred_val))
                else:
                    pred_item = QTableWidgetItem("--")
                pred_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_bridges.setItem(row, 2, pred_item)

                
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
                
            # 4.5. Populate Score Table (DIỄM SỐ)
            self.table_scores.setRowCount(0)
            self.table_scores.setSortingEnabled(False)
            
            if scores:
                for num_str, score, info in scores[:100]:  # Top 100 (should be all 00-99)
                    row = self.table_scores.rowCount()
                    self.table_scores.insertRow(row)
                    
                    # Number column
                    num_item = QTableWidgetItem(num_str)
                    num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_scores.setItem(row, 0, num_item)
                    
                    # Score column with color coding
                    score_item = QTableWidgetItem(f"{score:.1f}")
                    score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Color coding
                    if score > 50:
                        score_item.setForeground(QColor("#D32F2F"))  # Red
                        score_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                    elif score > 30:
                        score_item.setForeground(QColor("#F57C00"))  # Orange
                    elif score > 20:
                        score_item.setForeground(QColor("#388E3C"))  # Green
                    
                    self.table_scores.setItem(row, 1, score_item)
            
            self.table_scores.setSortingEnabled(True)

                
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
                
            # 6.5. Populate Chạm in CHỐT SỐ VIP tab (duplicate for better UX)
            self.tree_cham_thong_vip.clear()
            self.tree_cham_tile_vip.clear()
            
            for x in top_thong:
                touches_str = ','.join(map(str, x['touches']))
                consec = x.get('consecutive_at_end', 0)
                item = QTreeWidgetItem([touches_str, f"{consec}N"])
                if x.get('covers_last_n_at_end', False):
                    item.setBackground(0, QColor("#FFF9C4"))
                self.tree_cham_thong_vip.addTopLevelItem(item)
                
            for x in top_rate:
                touches_str = ','.join(map(str, x['touches']))
                rate = x.get('rate_percent', 0.0)
                item = QTreeWidgetItem([touches_str, f"{rate:.1f}%"])
                self.tree_cham_tile_vip.addTopLevelItem(item)

                
            # 7. Update ĐÁNH GIÁ Sub-Tabs
            
            # Sub-Tab 1: Bộ Evaluation
            self.table_bo_eval.setRowCount(0)
            self.table_bo_eval.setSortingEnabled(False)
            
            if freq_bo and gan_bo:
                # Calculate scores for each set
                bo_scores = []
                for bo_name in freq_bo.keys():
                    freq = freq_bo.get(bo_name, 0)
                    gan = gan_bo.get(bo_name, 0)
                    score = (freq * 1.5) - (gan * 0.5)  # Same formula as backend
                    rank = "S" if score >= 10 else ("A" if score >= 5 else "B")
                    bo_scores.append((bo_name, freq, gan, score, rank))
                
                # Sort by score
                bo_scores.sort(key=lambda x: x[3], reverse=True)
                
                for bo_name, freq, gan, score, rank in bo_scores:
                    row = self.table_bo_eval.rowCount()
                    self.table_bo_eval.insertRow(row)
                    
                    self.table_bo_eval.setItem(row, 0, QTableWidgetItem(f"Bộ {bo_name}"))
                    self.table_bo_eval.setItem(row, 1, QTableWidgetItem(str(freq)))
                    self.table_bo_eval.setItem(row, 2, QTableWidgetItem(str(gan)))
                    
                    score_item = QTableWidgetItem(f"{score:.1f}")
                    if rank == "S":
                        score_item.setForeground(QColor("#D32F2F"))
                    elif rank == "A":
                        score_item.setForeground(QColor("#F57C00"))
                    self.table_bo_eval.setItem(row, 3, score_item)
                    
                    rank_item = QTableWidgetItem(rank)
                    rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_bo_eval.setItem(row, 4, rank_item)
            
            self.table_bo_eval.setSortingEnabled(True)
            
            # Sub-Tab 2: Điểm ĐG (Top 50 scores)
            self.table_diem_eval.setRowCount(0)
            self.table_diem_eval.setSortingEnabled(False)
            
            if scores:
                for num_str, score, info in scores[:50]:
                    row = self.table_diem_eval.rowCount()
                    self.table_diem_eval.insertRow(row)
                    
                    self.table_diem_eval.setItem(row, 0, QTableWidgetItem(num_str))
                    self.table_diem_eval.setItem(row, 1, QTableWidgetItem(f"{score:.1f}"))
                    self.table_diem_eval.setItem(row, 2, QTableWidgetItem(info))
            
            self.table_diem_eval.setSortingEnabled(True)
            
            # Sub-Tab 3: Trạng thái (Hot & Gan Sets)
            self.tree_hot_sets.clear()
            self.tree_gan_sets.clear()
            
            if freq_bo and gan_bo:
                # Hot sets (high frequency)
                hot_sorted = sorted(freq_bo.items(), key=lambda x: x[1], reverse=True)
                for bo_name, freq in hot_sorted[:8]:
                    gan = gan_bo.get(bo_name, 0)
                    item = QTreeWidgetItem([f"Bộ {bo_name}", str(freq), str(gan)])
                    if freq >= 3:
                        item.setBackground(0, QColor("#FFF9C4"))
                    self.tree_hot_sets.addTopLevelItem(item)
                
                # Gan sets (long absence)
                gan_sorted = sorted(gan_bo.items(), key=lambda x: x[1], reverse=True)
                for bo_name, gan in gan_sorted[:8]:
                    freq = freq_bo.get(bo_name, 0)
                    item = QTreeWidgetItem([f"Bộ {bo_name}", str(gan), str(freq)])
                    if gan >= 15:
                        item.setBackground(0, QColor("#E3F2FD"))
                    self.tree_gan_sets.addTopLevelItem(item)
            
            # 7.5. Populate ĐÁNH GIÁ BỘ Detail Table (all 15 sets)
            self.table_bo_detail.setRowCount(0)
            self.table_bo_detail.setSortingEnabled(False)
            
            if freq_bo and gan_bo:
                # Calculate scores for all sets
                all_bo_scores = []
                for bo_name in freq_bo.keys():
                    freq = freq_bo.get(bo_name, 0)
                    gan = gan_bo.get(bo_name, 0)
                    score = (freq * 1.5) - (gan * 0.5)
                    rank = "S" if score >= 10 else ("A" if score >= 5 else "B")
                    
                    # Determine status
                    if freq >= 3:
                        status = "🔥 Hot"
                    elif gan >= 15:
                        status = "❄️ Gan"
                    else:
                        status = "Normal"
                    
                    all_bo_scores.append((bo_name, freq, gan, score, rank, status))
                
                # Sort by score descending
                all_bo_scores.sort(key=lambda x: x[3], reverse=True)
                
                for bo_name, freq, gan, score, rank, status in all_bo_scores:
                    row = self.table_bo_detail.rowCount()
                    self.table_bo_detail.insertRow(row)
                    
                    # Bộ
                    self.table_bo_detail.setItem(row, 0, QTableWidgetItem(f"Bộ {bo_name}"))
                    
                    # Tần Suất
                    freq_item = QTableWidgetItem(str(freq))
                    freq_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_bo_detail.setItem(row, 1, freq_item)
                    
                    # Gan
                    gan_item = QTableWidgetItem(str(gan))
                    gan_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_bo_detail.setItem(row, 2, gan_item)
                    
                    # Điểm
                    score_item = QTableWidgetItem(f"{score:.1f}")
                    score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if rank == "S":
                        score_item.setForeground(QColor("#D32F2F"))
                        score_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                    elif rank == "A":
                        score_item.setForeground(QColor("#F57C00"))
                    self.table_bo_detail.setItem(row, 3, score_item)
                    
                    # Rank
                    rank_item = QTableWidgetItem(rank)
                    rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_bo_detail.setItem(row, 4, rank_item)
                    
                    # Trạng Thái
                    status_item = QTableWidgetItem(status)
                    if "Hot" in status:
                        status_item.setBackground(QColor("#FFF9C4"))
                    elif "Gan" in status:
                        status_item.setBackground(QColor("#E3F2FD"))
                    self.table_bo_detail.setItem(row, 5, status_item)
            
            self.table_bo_detail.setSortingEnabled(True)



        except Exception as e:
            QMessageBox.critical(self, "UI Error", f"Error updating UI: {e}")
            

