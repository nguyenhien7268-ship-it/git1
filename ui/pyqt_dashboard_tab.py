#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Dashboard Tab - "Bảng Quyết Định"
Replicating complex layout from Tkinter version
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QTableWidget, QTableWidgetItem, QSplitter,
    QPushButton, QLabel, QHeaderView, QAbstractItemView,
    QGroupBox, QTextEdit, QFrame, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

try:
    from logic.config_manager import SETTINGS
except ImportError:
    pass

class DashboardTab(QWidget):
    """Dashboard tab for displaying analysis results"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.current_results = None
        
        # Setup UI
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # --- HEADER ---
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Đang tải...")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #0078d7;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Filter Controls
        filter_group = QGroupBox()
        filter_layout = QHBoxLayout()
        filter_group.setLayout(filter_layout)
        filter_layout.setContentsMargins(5, 5, 5, 5)
        
        self.chk_filter = QCheckBox("Lọc thông minh")
        self.chk_conf = QCheckBox("Chỉ hiện ≥5⭐")
        self.chk_ai = QCheckBox("Chỉ hiện AI ≥60%")
        
        self.chk_filter.clicked.connect(self._refresh_view)
        self.chk_conf.clicked.connect(self._refresh_view)
        self.chk_ai.clicked.connect(self._refresh_view)
        
        filter_layout.addWidget(self.chk_filter)
        filter_layout.addWidget(self.chk_conf)
        filter_layout.addWidget(self.chk_ai)
        
        header_layout.addWidget(filter_group)
        
        refresh_btn = QPushButton("Làm Mới Dữ Liệu")
        refresh_btn.clicked.connect(self._request_refresh)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # --- MAIN CONTENT (Splitter Vertical) ---
        splitter_v = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter_v)
        
        # Top Section: Scoring Table (High) + K2N (Side)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter_v.addWidget(top_splitter)
        
        # 1. Main Scoring Table
        self.grp_score = QGroupBox("🏆 Bảng Chấm Điểm Tổng Lực (Double-click để xem chi tiết)")
        score_layout = QVBoxLayout(self.grp_score)
        self.table_score = self._create_table([
            "Điểm", "AI", "⭐", "Khuyến Nghị", "Cặp số", "Gan", "Lý do (Tích hợp AI)"
        ])
        self.table_score.cellDoubleClicked.connect(self._on_table_double_clicked)
        score_layout.addWidget(self.table_score)
        top_splitter.addWidget(self.grp_score)
        
        # 2. K2N Table
        grp_k2n = QGroupBox("⏳ Cầu K2N Đang Chờ (Chờ N2)")
        k2n_layout = QVBoxLayout(grp_k2n)
        self.table_k2n = self._create_table(["Cặp số", "Chuỗi", "Gãy Max", "Tên cầu"])
        self.table_k2n.cellDoubleClicked.connect(self._on_k2n_double_clicked)
        k2n_layout.addWidget(self.table_k2n)
        top_splitter.addWidget(grp_k2n)
        
        top_splitter.setStretchFactor(0, 2)
        top_splitter.setStretchFactor(1, 1)
        
        # Mid Section: 4 Small Tables
        mid_widget = QWidget()
        mid_layout = QHBoxLayout(mid_widget)
        mid_layout.setContentsMargins(0,0,0,0)
        splitter_v.addWidget(mid_widget)
        
        # 3. AI Predictions
        grp_ai = QGroupBox("🧠 AI (Đơn)")
        ai_layout = QVBoxLayout(grp_ai)
        self.table_ai = self._create_table(["Số", "%"])
        ai_layout.addWidget(self.table_ai)
        mid_layout.addWidget(grp_ai, 1)
        
        # 4. Recent Form
        grp_form = QGroupBox("🔥 Phong Độ 10 Kỳ")
        form_layout = QVBoxLayout(grp_form)
        self.table_form = self._create_table(["Tên Cầu", "Thắng", "Dự Đoán"])
        form_layout.addWidget(self.table_form)
        mid_layout.addWidget(grp_form, 2)
        
        # 5. Hot Loto
        self.grp_hot = QGroupBox("🔥 Hot (7 ngày)")
        hot_layout = QVBoxLayout(self.grp_hot)
        self.table_hot = self._create_table(["Số", "Nháy"])
        hot_layout.addWidget(self.table_hot)
        mid_layout.addWidget(self.grp_hot, 1)
        
        # 6. Vote / Gan
        grp_vote = QGroupBox("📊 Vote (Top)")
        vote_layout = QVBoxLayout(grp_vote)
        self.table_vote = self._create_table(["Cặp", "Vote"])
        vote_layout.addWidget(self.table_vote)
        mid_layout.addWidget(grp_vote, 1)
        
        # Bottom Section: Log
        grp_log = QGroupBox("📝 Kết Quả Phân Tích & Cảnh Báo (V3.8)")
        log_layout = QVBoxLayout(grp_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(100)
        log_layout.addWidget(self.txt_log)
        splitter_v.addWidget(grp_log)
        
        # Initial stretch
        splitter_v.setStretchFactor(0, 4)
        splitter_v.setStretchFactor(1, 2)
        splitter_v.setStretchFactor(2, 1)

    def _create_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Resize logic
        header = table.horizontalHeader()
        if len(headers) > 3:
             # Scoring table specific
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(len(headers)-1, QHeaderView.ResizeMode.Stretch)
        else:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
        return table
    
    def _request_refresh(self):
        # Call refresh on main window or parent
        if hasattr(self.main_window, '_run_analysis'):
             self.main_window._run_analysis()
        elif hasattr(self.main_window, 'run_decision_dashboard'):
             self.main_window.run_decision_dashboard()

    def update_results(self, results):
        """Update all tables from analysis results dict"""
        self.current_results = results
        
        # Header update
        next_ky = results.get('next_ky', 'Unknown')
        days = results.get('n_days_stats', 7) # Get actual days used
        
        import datetime
        now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        self.title_label.setText(f"Bảng Quyết Định Tối Ưu - {next_ky} (Cập nhật: {now_str})")
        self.grp_hot.setTitle(f"🔥 Hot ({days} ngày)")
        
        # 1. Top Scores (Main)
        self._populate_main_table(results.get('top_scores', []))
        
        # 2. Update Log
        self._generate_log_summary(results.get('top_scores', []))
        
        # 2. K2N
        # AnalysisService keys mismatch fix:
        # result['pending_k2n_data'] -> UI expects 'pending_k2n'
        self._populate_k2n_table(results.get('pending_k2n_data', {}))
        
        # 3. AI
        self._populate_ai_table(results.get('ai_predictions', []))
        
        # 4. Form
        # Now populated by Worker
        self._populate_form_table(results.get('recent_form_bridges', []))
        
        # 5. Hot
        # AnalysisService keys mismatch fix:
        # result['stats_n_day'] -> UI expects 'hot_loto'
        self._populate_hot_table(results.get('stats_n_day', []))
        
        # 6. Vote
        # AnalysisService keys mismatch fix:
        # result['consensus'] -> UI expects 'vote_consensus'
        self._populate_vote_table(results.get('consensus', []))
        
        # Log
        if 'analysis_log' in results:
            self.txt_log.setText(results['analysis_log'])
        elif 'top_scores' in results:
             self.txt_log.setText("Cập nhật thành công.")
             
    def _refresh_view(self):
        if self.current_results:
            self.update_results(self.current_results)
            
    def _populate_main_table(self, scores):
        self.table_score.setRowCount(0)
        self.grp_score.setTitle(f"🏆 Bảng Chấm Điểm Tổng Lực ({len(scores)} kết quả)")
        
        if not scores: return
        
        # Filters
        use_filter = self.chk_filter.isChecked()
        min_conf = 5 if self.chk_conf.isChecked() else 0
        min_ai = 60 if self.chk_ai.isChecked() else 0
        
        filtered = []
        for x in scores:
            if use_filter:
                if x.get('sources', 0) < min_conf: continue
                if (x.get('ai_probability', 0)*100) < min_ai: continue
            filtered.append(x)
            
        self.table_score.setRowCount(len(filtered))
        for i, item in enumerate(filtered):
            # Headers: "Điểm", "AI", "⭐", "Khuyến Nghị", "Cặp số", "Gan", "Lý do (Tích hợp AI)"
            raw_score = item.get('score', 0)
            score_str = f"{raw_score:.2f}"
            
            raw_ai = item.get('ai_probability', 0)
            ai_str = f"{int(raw_ai*100)}%"
            
            conf_val = item.get('sources', 0)
            conf_str = f"{conf_val}⭐"
            
            rec = item.get('recommendation', '')
            pair = item.get('pair', '')
            
            gan_val = item.get('gan_days', 0)
            gan = item.get('gan_details', f"{gan_val}N" if gan_val > 0 else "")
            reasons = item.get('reasons', '')
            
            # --- Items with Styling ---
            
            # 1. Score (Red > 20, Orange > 15)
            item_score = QTableWidgetItem(score_str)
            item_score.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if raw_score >= 20:
                item_score.setForeground(QColor("#D32F2F")) # Red
                item_score.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            elif raw_score >= 15:
                item_score.setForeground(QColor("#E65100")) # Orange
                item_score.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                
            # 2. AI (Red > 80%, Orange > 60%)
            item_ai = QTableWidgetItem(ai_str)
            item_ai.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if raw_ai >= 0.8:
                item_ai.setForeground(QColor("#D32F2F"))
                item_ai.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            elif raw_ai >= 0.6:
                item_ai.setForeground(QColor("#E65100"))
                
            # 3. Stars (Yellow/Orange for high)
            item_conf = QTableWidgetItem(conf_str)
            item_conf.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if conf_val >= 5:
                item_conf.setForeground(QColor("#F57F17")) # Dark Yellow/Orange
                item_conf.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                
            # 4. Pair (Bold)
            item_pair = QTableWidgetItem(pair)
            item_pair.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_pair.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            
            # 5. Gan (Red if high)
            item_gan = QTableWidgetItem(gan)
            item_gan.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if gan_val >= 15:
                item_gan.setForeground(QColor("Red"))
            
            self.table_score.setItem(i, 0, item_score)
            self.table_score.setItem(i, 1, item_ai)
            self.table_score.setItem(i, 2, item_conf)
            self.table_score.setItem(i, 3, QTableWidgetItem(rec))
            self.table_score.setItem(i, 4, item_pair)
            self.table_score.setItem(i, 5, item_gan)
            self.table_score.setItem(i, 6, QTableWidgetItem(reasons))
            
    def _on_table_double_clicked(self, row, col):
        """Show details for the selected score item"""
        try:
             # Get basic info from table
             pair = self.table_score.item(row, 4).text()
             score = self.table_score.item(row, 0).text()
             reasons = self.table_score.item(row, 6).text()
             
             msg = f"Chi tiết Cặp {pair}\n"
             msg += f"----------\n"
             msg += f"Điểm tổng lực: {score}\n"
             msg += f"Phân tích: {reasons}\n"
             
             QMessageBox.information(self, f"Chi tiết {pair}", msg)
        except Exception:
            pass

    def _on_k2n_double_clicked(self, row, col):
         try:
             name = self.table_k2n.item(row, 3).text()
             # If we had the bridge object, we could launch backtest
             QMessageBox.information(self, "Chi tiết Cầu", f"Tên cầu: {name}\n(Chức năng xem chi tiết cầu đang được cập nhật)")
         except:
             pass

    def _populate_k2n_table(self, k2n_data):
        self.table_k2n.setRowCount(0)
        self.table_k2n.setSortingEnabled(False)
        
        if not k2n_data: return
        
        # Normalize data to list of items
        items = []
        if isinstance(k2n_data, dict):
            # Key is the bridge name
            for k, v in k2n_data.items():
                if k == "Tổng Trúng": continue # Artifact filtering
                if isinstance(v, dict):
                    if 'name' not in v:
                        v['name'] = k
                    items.append(v)
        elif isinstance(k2n_data, list):
            items = k2n_data
            
        self.table_k2n.setRowCount(len(items))
        for i, item in enumerate(items):
             if not isinstance(item, dict): continue
             
             # "Cặp số", "Chuỗi", "Gãy Max", "Tên cầu"
             # 1. Pair
             pair = str(item.get('pair', ''))
             if not pair and 'stl' in item:
                 stl_val = item['stl']
                 if isinstance(stl_val, (list, tuple)) and len(stl_val) >= 2:
                     pair = f"{stl_val[0]}-{stl_val[1]}"
                 elif isinstance(stl_val, str) and ',' in stl_val:
                     # Handle "01,10" string format
                     parts = stl_val.split(',')
                     if len(parts) >= 2:
                         pair = f"{parts[0].strip()}-{parts[1].strip()}"
                     else:
                        pair = stl_val
                 else:
                     pair = str(stl_val)
             
             # 2. Strike/Max Loss (often not available in simple pending list, so optional)
             streak = str(item.get('streak', ''))
             if streak == '' or streak == 'None': streak = "-"
             
             # Fix Max Loss (max_loss vs max_lose)
             max_loss = str(item.get('max_loss', item.get('max_lose', '')))
             if max_loss == '' or max_loss == 'None': max_loss = "-"
             
             name_raw = str(item.get('name', ''))
             if not name_raw or name_raw == 'None': name_raw = "Cầu Pending"
             
             # Map Friendly Names for Standard Bridges
             name_map = {
                 "LO_STL_FIXED_01": "Cầu 1 (GĐB+5)",
                 "LO_STL_FIXED_02": "Cầu 2 (G6+G7)",
                 "LO_STL_FIXED_03": "Cầu 3 (GĐB+G1)",
                 "LO_STL_FIXED_04": "Cầu 4 (GĐB+G1)",
                 "LO_STL_FIXED_05": "Cầu 5 (G7+G7)",
                 "LO_STL_FIXED_06": "Cầu 6 (G7+G7)",
                 "LO_STL_FIXED_07": "Cầu 7 (G5+G7)",
                 "LO_STL_FIXED_08": "Cầu 8 (G3+G4)",
                 "LO_STL_FIXED_09": "Cầu 9 (GĐB+G1)",
                 "LO_STL_FIXED_10": "Cầu 10 (G2+G3)",
                 "LO_STL_FIXED_11": "Cầu 11 (GĐB+G3)",
                 "LO_STL_FIXED_12": "Cầu 12 (GĐB+G3)",
                 "LO_STL_FIXED_13": "Cầu 13 (G7.3+8)",
                 "LO_STL_FIXED_14": "Cầu 14 (G1+2)",
                 "LO_STL_FIXED_15": "Cầu 15 (Đề+7)"
             }
             name = name_map.get(name_raw, name_raw)

             # Styling: Name in Red
             item_name = QTableWidgetItem(name)
             item_name.setForeground(QColor("#D32F2F"))
             
             # Pair in bold
             item_pair = QTableWidgetItem(pair)
             item_pair.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
             
             self.table_k2n.setItem(i, 0, item_pair)
             self.table_k2n.setItem(i, 1, QTableWidgetItem(streak))
             self.table_k2n.setItem(i, 2, QTableWidgetItem(max_loss))
             self.table_k2n.setItem(i, 3, item_name)
    
    def _generate_log_summary(self, scores):
        """Generate textual summary for the log area"""
        if not scores: return
        
        # 1. Top 10 High Scores
        top_10 = scores[:10]
        msg = "🏆 TOP 10 LÔ ĐIỂM CAO (SCORING V3.8):\n"
        
        lines = []
        # Format: 33-88 (22.8đ) | 29-92 (19.5đ) ...
        # Group in chunks of 5 for readability
        chunk = []
        for x in top_10:
            s_pair = x.get('pair', '??-??')
            s_point = x.get('score', 0)
            chunk.append(f"{s_pair} ({s_point:.1f}đ)")
            
            if len(chunk) >= 5:
                lines.append(" | ".join(chunk))
                chunk = []
        if chunk: lines.append(" | ".join(chunk))
        
        msg += "\n".join(lines)
        msg += "\n\n"
        
        # 2. Gan Warnings (> 15 days)
        gan_list = [x for x in scores if x.get('gan_days', 0) >= 15]
        if gan_list:
            msg += "⛔ CẢNH BÁO LÔ GAN (>15 ngày - NÊN TRÁNH):\n"
            gan_chunks = []
            curr_gan = []
            for x in gan_list:
                 curr_gan.append(f"{x.get('pair')} ({x.get('gan_days')}d)")
                 if len(curr_gan) >= 6:
                     gan_chunks.append(" | ".join(curr_gan))
                     curr_gan = []
            if curr_gan: gan_chunks.append(" | ".join(curr_gan))
            msg += "\n".join(gan_chunks)
        else:
            msg += "✅ Không có lô gan báo động (>15 ngày)."
            
        # Update Log (Assuming parent main window has log method, or using local log widget?)
        # In current design, DashboardTab does NOT have a log widget at the bottom (it's in the splitter).
        # Let's check init_ui... Ah, we didn't check the *bottom* of init_ui fully.
        # The screenshots show "Kết Quả Phân Tích & Cảnh Báo" at the bottom.
        # I need to find that widget in my code.
        
        if hasattr(self, 'txt_log'):
             self.txt_log.setText(msg) 
             # Styling: Make formatting bold/red via HTML if strictly needed, but plain text for now.
             
             # Actually, let's use HTML for colors
             html = f"<div style='font-size:11pt; font-family: Segoe UI;'><b>🏆 TOP 10 LÔ ĐIỂM CAO (SCORING V3.8):</b><br>"
             html += "<br>".join(lines)
             
             if gan_list:
                  html += f"<br><br><b style='color:red;'>⛔ CẢNH BÁO LÔ GAN (>15 ngày - NÊN TRÁNH):</b><br>"
                  html += "<br>".join(gan_chunks)
             else:
                  html += f"<br><br><b style='color:green;'>✅ Không có lô gan báo động (>15 ngày).</b>"
             
             html += "</div>"
             self.txt_log.setHtml(html)
        


    def _populate_ai_table(self, ai_data):
        self.table_ai.setRowCount(0)
        if not ai_data: return
        
        self.table_ai.setRowCount(len(ai_data))
        for i, item in enumerate(ai_data):
            # item dict: {loto, probability}
            loto = item.get('loto', '')
            prob = f"{item.get('probability', 0):.2f}%"
            self.table_ai.setItem(i, 0, QTableWidgetItem(str(loto)))
            self.table_ai.setItem(i, 1, QTableWidgetItem(prob))

    def _populate_form_table(self, bridges):
        self.table_form.setRowCount(0)
        if not bridges: return
        
        self.table_form.setRowCount(len(bridges))
        for i, b in enumerate(bridges):
            self.table_form.setItem(i, 0, QTableWidgetItem(str(b.get('name', ''))))
            
            wins = b.get('recent_win_count_10', 0)
            self.table_form.setItem(i, 1, QTableWidgetItem(f"{wins}/10"))
            
            pred = b.get('prediction') or b.get('next_prediction_stl') or ''
            self.table_form.setItem(i, 2, QTableWidgetItem(str(pred)))

    def _populate_hot_table(self, hot_data):
        self.table_hot.setRowCount(0)
        if not hot_data: return
        
        self.table_hot.setRowCount(len(hot_data))
        for i, item in enumerate(hot_data):
            # item: (loto, hits, days) tuple
            self.table_hot.setItem(i, 0, QTableWidgetItem(str(item[0])))
            self.table_hot.setItem(i, 1, QTableWidgetItem(str(item[1])))

    def _populate_vote_table(self, vote_data):
        self.table_vote.setRowCount(0)
        if not vote_data: return
        
        self.table_vote.setRowCount(len(vote_data))
        for i, item in enumerate(vote_data):
            # item: (pair, count, sources)
            self.table_vote.setItem(i, 0, QTableWidgetItem(str(item[0])))
            self.table_vote.setItem(i, 1, QTableWidgetItem(f"x{item[1]}"))

    def clear(self):
        self.table_score.setRowCount(0)
        self.table_k2n.setRowCount(0)
        self.table_ai.setRowCount(0)
        self.table_form.setRowCount(0)
        self.table_hot.setRowCount(0)
        self.table_vote.setRowCount(0)
        self.txt_log.clear()
        self.title_label.setText("Đang tải...")
