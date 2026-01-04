#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Optimizer Tab
Replicating ui/ui_optimizer.py
"""

import json
import traceback
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QComboBox, QLineEdit, QCheckBox, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QTextEdit, QSplitter, QHeaderView, QMessageBox,
    QScrollArea, QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QColor

try:
    from logic.config_manager import SETTINGS
except ImportError:
    SETTINGS = None

from ui.pyqt_workers import StrategyOptimizerWorker

class OptimizerTab(QWidget):
    """Optimizer tab for Strategy Optimization"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.param_vars = {} # key -> (chk, from, to, step) widgets
        
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # --- LEFT PANEL: Settings ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 1. Strategy Settings
        grp_strat = QGroupBox("1. Cài đặt Chiến lược")
        strat_layout = QGridLayout()
        grp_strat.setLayout(strat_layout)
        
        strat_layout.addWidget(QLabel("Chiến lược:"), 0, 0)
        self.cbo_strategy = QComboBox()
        self.cbo_strategy.addItems(["Tối ưu Top 1 (N1)", "Tối ưu Top 3 (N1)"])
        strat_layout.addWidget(self.cbo_strategy, 0, 1)
        
        strat_layout.addWidget(QLabel("Số ngày test:"), 1, 0)
        self.txt_days = QLineEdit("30")
        strat_layout.addWidget(self.txt_days, 1, 1)
        
        left_layout.addWidget(grp_strat)
        
        # 2. Parameters
        grp_params = QGroupBox("2. Chọn Tham số Tối ưu")
        params_layout = QVBoxLayout(grp_params)
        
        # Header row
        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Tham số"), 2)
        header_row.addWidget(QLabel("Từ"), 1)
        header_row.addWidget(QLabel("Đến"), 1)
        header_row.addWidget(QLabel("Bước"), 1)
        params_layout.addLayout(header_row)
        
        # Scroll area for params
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        param_container = QWidget()
        self.param_grid = QVBoxLayout(param_container)
        
        self._add_param_rows()
        
        param_container.setLayout(self.param_grid)
        scroll.setWidget(param_container)
        params_layout.addWidget(scroll)
        
        left_layout.addWidget(grp_params)
        
        # Buttons
        self.btn_run = QPushButton("🚀 Bắt đầu Tối ưu Hóa")
        self.btn_run.clicked.connect(self._run_optimization)
        self.btn_run.setStyleSheet("font-weight: bold; padding: 8px;")
        left_layout.addWidget(self.btn_run)
        
        self.btn_apply = QPushButton("✅ Áp dụng Cấu hình Tốt nhất")
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._apply_best)
        left_layout.addWidget(self.btn_apply)
        
        main_layout.addWidget(left_widget, 1)
        
        # --- RIGHT PANEL: Results ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 3. Results Table
        grp_res = QGroupBox("3. Kết quả (Xếp hạng theo Tỷ lệ thắng)")
        res_layout = QVBoxLayout(grp_res)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Win Rate", "Hit/Miss", "Config"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._on_table_dbl_click)
        
        res_layout.addWidget(self.table)
        right_layout.addWidget(grp_res, 2)
        
        # 4. Log
        grp_log = QGroupBox("Log Chi tiết")
        log_layout = QVBoxLayout(grp_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        log_layout.addWidget(self.txt_log)
        right_layout.addWidget(grp_log, 1)
        
        main_layout.addWidget(right_widget, 2)

    def _add_param_rows(self):
        curr_settings = SETTINGS.get_all_settings() if SETTINGS else {}
        
        definitions = [
            ("GAN_DAYS", "Số ngày Lô Gan", 15, 1),
            ("HIGH_WIN_THRESHOLD", "Ngưỡng Cầu (% Win)", 47.0, 1.0),
            ("K2N_RISK_START_THRESHOLD", "Ngưỡng phạt K2N", 4, 1),
            ("K2N_RISK_PENALTY_PER_FRAME", "Phạt K2N/khung", 0.5, 0.1),
            ("AI_SCORE_WEIGHT", "AI Trọng số", 0.2, 0.1),
            ("RECENT_FORM_PERIODS", "Kỳ xét phong độ", 10, 1)
        ]
        
        for key, name, def_val, def_step in definitions:
            val = curr_settings.get(key, def_val)
            
            row_layout = QHBoxLayout()
            
            chk = QCheckBox(name)
            chk.setProperty("key", key)
            
            txt_from = QLineEdit(str(val))
            txt_to = QLineEdit(str(val))
            txt_step = QLineEdit(str(def_step))
            
            # Validation
            # (omit validators for brevity, user expects text)
            
            row_layout.addWidget(chk, 2)
            row_layout.addWidget(txt_from, 1)
            row_layout.addWidget(txt_to, 1)
            row_layout.addWidget(txt_step, 1)
            
            container = QWidget()
            container.setLayout(row_layout)
            self.param_grid.addWidget(container)
            
            self.param_vars[key] = (chk, txt_from, txt_to, txt_step)
            
        self.param_grid.addStretch()

    def _run_optimization(self):
        # 1. Validate
        try:
            days = int(self.txt_days.text())
            if days <= 0: raise ValueError
        except:
             QMessageBox.warning(self, "Lỗi Input", "Số ngày test không hợp lệ")
             return

        param_ranges = {}
        for key, (chk, t_from, t_to, t_step) in self.param_vars.items():
            if chk.isChecked():
                try:
                    f = float(t_from.text())
                    t = float(t_to.text())
                    s = float(t_step.text())
                    if s<=0: raise ValueError
                    param_ranges[key] = (f, t, s)
                except:
                    QMessageBox.warning(self, "Lỗi Input", f"Tham số {key} không hợp lệ")
                    return
        
        if not param_ranges:
            QMessageBox.warning(self, "Lỗi", "Chọn ít nhất 1 tham số.")
            return

        # 2. Start Worker
        self.txt_log.clear()
        self.table.setRowCount(0)
        self.btn_run.setEnabled(False)
        self.btn_apply.setEnabled(False)
        
        # Load data first? Worker needs data.
        # Ensure main window has loaded data
        if not self.main_window.data_service.data_cache:
             data = self.main_window.data_service.load_data()
        else:
             data = self.main_window.data_service.data_cache
             
        if not data:
            QMessageBox.warning(self, "Lỗi", "Chưa có dữ liệu.")
            self.btn_run.setEnabled(True)
            return
            
        self.worker = StrategyOptimizerWorker(
            self.main_window.analysis_service,
            data,
            days,
            param_ranges
        )
        self.worker.progress.connect(self.txt_log.append)
        self.worker.result_ready.connect(self._update_table)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _update_table(self, results):
        self.table.setRowCount(0)
        self.table.setRowCount(len(results))
        for i, (rate, hits, params_str, json_cfg) in enumerate(results):
            # item = (rate, hits_str, display_str, json_str)
            item_rate = QTableWidgetItem(f"{rate*100:.1f}%")
            if i == 0:
                item_rate.setBackground(QColor("#FFFFE0"))
                item_rate.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                
            self.table.setItem(i, 0, item_rate)
            self.table.setItem(i, 1, QTableWidgetItem(str(hits)))
            
            cfg_item = QTableWidgetItem(str(params_str))
            cfg_item.setData(Qt.ItemDataRole.UserRole, json_cfg) # Store json for apply
            self.table.setItem(i, 2, cfg_item)
            
        if results:
            self.btn_apply.setEnabled(True)

    def _on_finished(self):
        self.txt_log.append("--- HOÀN TẤT ---")
        self.btn_run.setEnabled(True)
        QMessageBox.information(self, "Xong", "Tối ưu hóa hoàn tất!")

    def _on_error(self, msg):
        self.txt_log.append(f"ERROR: {msg}")
        self.btn_run.setEnabled(True)
        QMessageBox.critical(self, "Lỗi Worker", msg)

    def _apply_best(self):
        # Taking top row
        if self.table.rowCount() > 0:
            self._apply_row(0)

    def _on_table_dbl_click(self, row, col):
        self._apply_row(row)

    def _apply_row(self, row):
        item = self.table.item(row, 2)
        json_cfg = item.data(Qt.ItemDataRole.UserRole)
        if json_cfg:
            try:
                cfg = json.loads(json_cfg)
                # Apply to SETTINGS
                if SETTINGS:
                    for k, v in cfg.items():
                        setattr(SETTINGS, k, v)
                    SETTINGS.save_settings()
                    QMessageBox.information(self, "Updated", "Đã cập nhật cấu hình thành công!\nVui lòng chạy lại phân tích.")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))

from PyQt6.QtWidgets import QGridLayout
