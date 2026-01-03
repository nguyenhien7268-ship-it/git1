#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Tuner Window ("Trợ lý Tinh chỉnh")
Replicating ui/ui_tuner.py
"""

import traceback
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QComboBox, QLineEdit, 
    QPushButton, QTextEdit, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt

try:
    from logic.config_manager import SETTINGS
except ImportError:
    SETTINGS = None

from ui.pyqt_workers import ParameterTuningWorker

class TunerWindow(QDialog):
    """Tuner Window for single parameter tuning"""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Trợ lý Tinh chỉnh Tham số")
        self.resize(700, 500)
        self.worker = None
        
        self.tunable_parameters = {
            "GAN_DAYS": "Số ngày tính Lô Gan",
            "HIGH_WIN_THRESHOLD": "Ngưỡng Cầu Tỷ Lệ Cao (%)",
            "AUTO_ADD_MIN_RATE": "Ngưỡng Thêm Cầu Mới (%)",
            "AUTO_PRUNE_MIN_RATE": "Ngưỡng Lọc Cầu Yếu (%)",
            "K2N_RISK_START_THRESHOLD": "Ngưỡng phạt K2N (khung thua)",
            "K2N_RISK_PENALTY_PER_FRAME": "Điểm phạt K2N / khung",
            "RECENT_FORM_PERIODS": "Số kỳ xét phong độ",
            "RECENT_FORM_MIN_HIGH": "Ngưỡng phong độ rất cao",
            "RECENT_FORM_BONUS_HIGH": "Điểm thưởng phong độ rất cao",
            "RECENT_FORM_MIN_MED": "Ngưỡng phong độ tốt",
            "RECENT_FORM_BONUS_MED": "Điểm thưởng phong độ tốt",
            "RECENT_FORM_MIN_LOW": "Ngưỡng phong độ ổn",
            "RECENT_FORM_BONUS_LOW": "Điểm thưởng phong độ ổn",
        }
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 1. Parameter Selection
        grp_set = QGroupBox("1. Chọn Tham số để Kiểm thử")
        set_layout = QVBoxLayout(grp_set)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Chọn tham số:"))
        self.cbo_param = QComboBox()
        self.cbo_param.addItems(list(self.tunable_parameters.values()))
        self.cbo_param.currentIndexChanged.connect(self._on_param_select)
        row1.addWidget(self.cbo_param, 1)
        set_layout.addLayout(row1)
        
        # Range inputs
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Từ:"))
        self.txt_from = QLineEdit()
        row2.addWidget(self.txt_from)
        
        row2.addWidget(QLabel("Đến:"))
        self.txt_to = QLineEdit()
        row2.addWidget(self.txt_to)
        
        row2.addWidget(QLabel("Bước:"))
        self.txt_step = QLineEdit("1")
        row2.addWidget(self.txt_step)
        
        set_layout.addLayout(row2)
        layout.addWidget(grp_set)
        
        # Run Button
        self.btn_run = QPushButton("🚀 Chạy Phân tích Tinh chỉnh")
        self.btn_run.clicked.connect(self._run_tuning)
        self.btn_run.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(self.btn_run)
        
        # 2. Log
        grp_log = QGroupBox("2. Kết quả Phân tích")
        log_layout = QVBoxLayout(grp_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        log_layout.addWidget(self.txt_log)
        layout.addWidget(grp_log)
        
        # Initialize first selection
        self._on_param_select()

    def _get_key_from_text(self, text):
        for k, v in self.tunable_parameters.items():
            if v == text: return k
        return None

    def _on_param_select(self):
        txt = self.cbo_param.currentText()
        key = self._get_key_from_text(txt)
        if key and SETTINGS:
            val = SETTINGS.get_all_settings().get(key, 0)
            self.txt_from.setText(str(val))
            self.txt_to.setText(str(val))
            if isinstance(val, float):
                self.txt_step.setText("0.1")
            else:
                self.txt_step.setText("1")

    def _run_tuning(self):
        txt = self.cbo_param.currentText()
        key = self._get_key_from_text(txt)
        
        try:
            val_from = float(self.txt_from.text())
            val_to = float(self.txt_to.text())
            val_step = float(self.txt_step.text())
            if val_step <= 0: raise ValueError
        except:
            QMessageBox.warning(self, "Lỗi", "Giá trị nhập không hợp lệ.")
            return

        self.txt_log.clear()
        self.txt_log.append(f"--- BẮT ĐẦU: {txt} ---")
        self.btn_run.setEnabled(False)
        
        # Data
        if not self.main_window.data_service.data_cache:
             data = self.main_window.data_service.load_data()
        else:
             data = self.main_window.data_service.data_cache
        
        if not data:
             self.btn_run.setEnabled(True)
             self.txt_log.append("Lỗi: Chưa có dữ liệu.")
             return

        self.worker = ParameterTuningWorker(
            self.main_window.analysis_service,
            data,
            key,
            val_from, val_to, val_step
        )
        self.worker.progress.connect(self.txt_log.append)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self):
        self.btn_run.setEnabled(True)
        self.txt_log.append("--- HOÀN TẤT ---")
        QMessageBox.information(self, "Xong", "Tinh chỉnh hoàn tất.")

    def _on_error(self, msg):
        self.btn_run.setEnabled(True)
        self.txt_log.append(f"ERROR: {msg}")
