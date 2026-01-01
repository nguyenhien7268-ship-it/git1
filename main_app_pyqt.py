#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Main Window - Phase 2: Services Integration
Modern Lottery Analysis Interface with full functionality
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QMessageBox, QCheckBox, QGroupBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import services
try:
    from services import DataService, AnalysisService
    from logic.db_manager import DB_NAME
    SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Services not available: {e}")
    SERVICES_AVAILABLE = False
    DB_NAME = "data/xo_so_prizes_all_logic.db"

# Import workers and dialogs
try:
    from ui.pyqt_workers import LoadDataWorker, UpdateFromTextWorker, AnalysisWorker, TrainAIWorker
    from ui.pyqt_progress_dialog import ProgressDialog
    from ui.pyqt_dashboard_tab import DashboardTab
    WORKERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Workers not available: {e}")
    WORKERS_AVAILABLE = False
    DashboardTab = None


class PyQtMainWindow(QMainWindow):
    """Modern main window using PyQt6 with services integration"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xổ Số Data Analysis (v8.0 - PyQt6)")
        self.setGeometry(100, 100, 1300, 850)
        
        # Initialize services
        if SERVICES_AVAILABLE:
            self.data_service = DataService(DB_NAME, logger=self)
            self.analysis_service = AnalysisService(DB_NAME, logger=self)
        else:
            self.data_service = None
            self.analysis_service = None
        
        # Workers
        self.current_worker = None
        self.progress_dialog = None
        
        # Set up central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self._create_home_tab()
        self._create_dashboard_tab()
        self._create_logs_tab()
        
        # Apply styling
        self._apply_styles()
        
        self.log("✓ Application initialized successfully")
        if SERVICES_AVAILABLE:
            self.log("✓ Services layer connected")
    
    def _create_home_tab(self):
        """Create home tab with file import and analysis"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # === Input Section ===
        input_group = QGroupBox("1. Dữ Liệu Đầu Vào")
        input_layout = QVBoxLayout()
        input_group.setLayout(input_layout)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Chọn file dữ liệu...")
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(50)
        browse_btn.clicked.connect(self._browse_file)
        load_btn = QPushButton("Nạp Mới (Xóa)")
        load_btn.clicked.connect(self._load_file)
        append_btn = QPushButton("Nạp Thêm")
        append_btn.clicked.connect(self._append_file)
        
        file_layout.addWidget(QLabel("File:"))
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(browse_btn)
        file_layout.addWidget(load_btn)
        file_layout.addWidget(append_btn)
        input_layout.addLayout(file_layout)
        
        # Text input
        text_layout = QHBoxLayout()
        self.paste_text = QTextEdit()
        self.paste_text.setMaximumHeight(100)
        self.paste_text.setPlaceholderText("Dán kết quả xổ số vào đây...")
        update_btn = QPushButton("⚡ CẬP NHẬT NGAY")
        update_btn.setObjectName("accentButton")
        update_btn.clicked.connect(self._update_from_text)
        
        text_layout.addWidget(QLabel("Paste KQ:"))
        text_layout.addWidget(self.paste_text, 3)
        text_layout.addWidget(update_btn, 1)
        input_layout.addLayout(text_layout)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        self.lo_mode = QCheckBox("Phân tích LÔ")
        self.lo_mode.setChecked(True)
        self.de_mode = QCheckBox("Phân tích ĐỀ")
        self.de_mode.setChecked(True)
        
        mode_layout.addWidget(QLabel("Chế độ chạy:"))
        mode_layout.addWidget(self.lo_mode)
        mode_layout.addWidget(self.de_mode)
        mode_layout.addStretch()
        input_layout.addLayout(mode_layout)
        
        layout.addWidget(input_group)
        
        # === Hero Action ===
        self.run_btn = QPushButton("🚀 CHẠY PHÂN TÍCH\n(Theo chế độ đã chọn)")
        self.run_btn.setObjectName("heroButton")
        self.run_btn.setMinimumHeight(80)
        self.run_btn.clicked.connect(self._run_analysis)
        layout.addWidget(self.run_btn)
        
        # === Toolset ===
        tools_group = QGroupBox("3. Hệ Thống & Trí Tuệ Nhân Tạo")
        tools_layout = QHBoxLayout()
        tools_group.setLayout(tools_layout)
        
        self.train_btn = QPushButton("🧠 Huấn Luyện AI")
        self.train_btn.clicked.connect(self._train_ai)
        stats_btn = QPushButton("📈 Thống Kê Vote")
        settings_btn = QPushButton("⚙️ Cài Đặt")
        
        tools_layout.addWidget(self.train_btn)
        tools_layout.addWidget(stats_btn)
        tools_layout.addWidget(settings_btn)
        
        layout.addWidget(tools_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "🏠 Trang Chủ")
    
    def _create_dashboard_tab(self):
        """Create dashboard tab"""
        if DashboardTab:
            self.dashboard_tab = DashboardTab(self)
            self.tabs.addTab(self.dashboard_tab, "📊 Bảng Quyết Định")
        else:
            # Fallback if dashboard module not available
            tab = QWidget()
            layout = QVBoxLayout()
            tab.setLayout(layout)
            label = QLabel("Dashboard module not available")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            self.tabs.addTab(tab, "📊 Bảng Quyết Định")
            self.dashboard_tab = None
        
        return  # Remove old code below

    
    def _create_logs_tab(self):
        """Create logs tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        self.tabs.addTab(tab, "📝 Logs")
    
    def _apply_styles(self):
        """Apply Qt stylesheet"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F7;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E8E8ED;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                color: #007AFF;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                background-color: #F8F8F9;
                border: 1px solid #D1D1D6;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 10pt;
            }
            
            QPushButton:hover {
                background-color: #E8E8ED;
            }
            
            QPushButton:pressed {
                background-color: #D1D1D6;
            }
            
            QPushButton#heroButton {
                background-color: #E8E8ED;
                border: 2px solid #D1D1D6;
                font-size: 12pt;
                font-weight: bold;
                padding: 20px;
            }
            
            QPushButton#heroButton:hover {
                background-color: #D1D1D6;
            }
            
            QPushButton#accentButton {
                background-color: #007AFF;
                color: white;
                border: none;
                font-weight: bold;
            }
            
            QPushButton#accentButton:hover {
                background-color: #0056b3;
            }
            
            QLineEdit, QTextEdit {
                background-color: white;
                border: 1px solid #D1D1D6;
                border-radius: 4px;
                padding: 5px;
            }
            
            QCheckBox {
                spacing: 5px;
            }
            
            QTabWidget::pane {
                border: 1px solid #D1D1D6;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #E8E8ED;
                border: 1px solid #D1D1D6;
                padding: 8px 15px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom-color: white;
            }
            
            QTabBar::tab:hover {
                background-color: #D1D1D6;
            }
        """)
    
    # ===== File Operations =====
    
    def _browse_file(self):
        """Open file browser"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file dữ liệu",
            "",
            "Data Files (*.json *.txt);;All Files (*.*)"
        )
        if filename:
            self.file_path.setText(filename)
            self.log("Selected file: " + filename)
    
    def _load_file(self):
        """Load data file (replace existing)"""
        if not self.data_service:
            QMessageBox.critical(self, "Lỗi", "Services layer not available!")
            return
        
        filepath = self.file_path.text()
        if not filepath:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file!")
            return
        
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Hành động này sẽ XÓA HẾT dữ liệu cũ. Tiếp tục?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._run_load_worker(filepath, mode='import')
    
    def _append_file(self):
        """Append data from file"""
        if not self.data_service:
            QMessageBox.critical(self, "Lỗi", "Services layer not available!")
            return
        
        filepath = self.file_path.text()
        if not filepath:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file!")
            return
        
        self._run_load_worker(filepath, mode='append')
    
    def _run_load_worker(self, filepath, mode='import'):
        """Run file load in background thread"""
        if not WORKERS_AVAILABLE:
            QMessageBox.critical(self, "Lỗi", "Workers module not available!")
            return
        
        # Create progress dialog
        title = "Nạp Dữ Liệu" if mode == 'import' else "Thêm Dữ Liệu"
        self.progress_dialog = ProgressDialog(self, title)
        
        # Create worker
        self.current_worker = LoadDataWorker(self.data_service, filepath, mode)
        self.current_worker.progress.connect(self.progress_dialog.set_status)
        self.current_worker.finished.connect(self._on_load_finished)
        self.progress_dialog.cancelled.connect(self.current_worker.terminate)
        
        # Start
        self.current_worker.start()
        self.progress_dialog.exec()
    
    def _on_load_finished(self, success, message):
        """Handle load completion"""
        if self.progress_dialog:
            self.progress_dialog.mark_complete(success)
            self.progress_dialog.close()
        
        if success:
            self.log(f"✓ {message}")
            QMessageBox.information(self, "Thành công", message)
        else:
            self.log(f"✗ {message}")
            QMessageBox.critical(self, "Lỗi", message)
    
    def _update_from_text(self):
        """Update from pasted text"""
        if not self.data_service:
            QMessageBox.critical(self, "Lỗi", "Services layer not available!")
            return
        
        text = self.paste_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Lỗi", "Vui lòng dán dữ liệu!")
            return
        
        if not WORKERS_AVAILABLE:
            QMessageBox.critical(self, "Lỗi", "Workers module not available!")
            return
        
        # Create progress dialog
        self.progress_dialog = ProgressDialog(self, "Cập Nhật Từ Text")
        
        # Create worker
        self.current_worker = UpdateFromTextWorker(self.data_service, text)
        self.current_worker.progress.connect(self.progress_dialog.set_status)
        self.current_worker.finished.connect(self._on_load_finished)
        self.progress_dialog.cancelled.connect(self.current_worker.terminate)
        
        # Start
        self.current_worker.start()
        self.progress_dialog.exec()
    
    # ===== Analysis Operations =====
    
    def _run_analysis(self):
        """Run analysis"""
        if not self.analysis_service:
            QMessageBox.critical(self, "Lỗi", "Services layer not available!")
            return
        
        lo = self.lo_mode.isChecked()
        de = self.de_mode.isChecked()
        
        if not lo and not de:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ít nhất một chế độ!")
            return
        
        if not WORKERS_AVAILABLE:
            QMessageBox.critical(self, "Lỗi", "Workers module not available!")
            return
        
        # Create progress dialog
        self.progress_dialog = ProgressDialog(self, "Phân Tích Dữ Liệu")
        
        # Create worker
        self.current_worker = AnalysisWorker(
            self.analysis_service,
            self.data_service,
            lo, de
        )
        self.current_worker.progress.connect(self.progress_dialog.set_status)
        self.current_worker.finished.connect(self._on_analysis_finished)
        self.current_worker.error.connect(self._on_analysis_error)
        self.progress_dialog.cancelled.connect(self.current_worker.terminate)
        
        # Start
        self.current_worker.start()
        self.progress_dialog.exec()
    
    def _on_analysis_finished(self, result):
        """Handle analysis completion"""
        if self.progress_dialog:
            self.progress_dialog.mark_complete(True)
            self.progress_dialog.close()
        
        self.log(f"✓ Analysis complete: {result.get('next_ky', 'Unknown period')}")
        
        # Update dashboard
        if self.dashboard_tab:
            self.dashboard_tab.update_results(result)
            # Switch to dashboard tab
            self.tabs.setCurrentWidget(self.dashboard_tab)
        
        QMessageBox.information(
            self,
            "Thành công",
            f"Phân tích hoàn tất!\nKỳ tiếp theo: {result.get('next_ky', 'N/A')}\n"
            f"Top Scores: {len(result.get('top_scores', []))} cặp"
        )
    
    def _on_analysis_error(self, error_message):
        """Handle analysis error"""
        if self.progress_dialog:
            self.progress_dialog.mark_complete(False)
            self.progress_dialog.close()
        
        self.log(f"✗ Analysis error: {error_message}")
        QMessageBox.critical(self, "Lỗi", error_message)
    
    # ===== AI Training =====
    
    def _train_ai(self):
        """Train AI model"""
        if not self.analysis_service:
            QMessageBox.critical(self, "Lỗi", "Services layer not available!")
            return
        
        if not WORKERS_AVAILABLE:
            QMessageBox.critical(self, "Lỗi", "Workers module not available!")
            return
        
        # Create progress dialog
        self.progress_dialog = ProgressDialog(self, "Huấn Luyện AI")
        
        # Create worker
        self.current_worker = TrainAIWorker(self.analysis_service)
        self.current_worker.progress.connect(self.progress_dialog.set_status)
        self.current_worker.finished.connect(self._on_train_finished)
        self.progress_dialog.cancelled.connect(self.current_worker.terminate)
        
        # Start
        self.current_worker.start()
        self.progress_dialog.exec()
    
    def _on_train_finished(self, success, message):
        """Handle training completion"""
        if self.progress_dialog:
            self.progress_dialog.mark_complete(success)
            self.progress_dialog.close()
        
        if success:
            self.log(f"✓ {message}")
            QMessageBox.information(self, "Thành công", message)
        else:
            self.log(f"✗ {message}")
            QMessageBox.critical(self, "Lỗi", message)
    
    # ===== Logging =====
    
    def log(self, message):
        """Add message to logs (implements logger interface for services)"""
        self.log_text.append(message)


def main():
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = PyQtMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
