#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyQt6 Progress Dialog
Modern progress dialog with cancel support
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ProgressDialog(QDialog):
    """Modern progress dialog with status updates and cancellation"""
    
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None, title="Processing..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate by default
        layout.addWidget(self.progress_bar)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_btn)
        
        # Style
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                padding: 10px;
            }
            QProgressBar {
                border: 1px solid #D1D1D6;
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
            }
            QPushButton {
                background-color: #F8F8F9;
                border: 1px solid #D1D1D6;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #E8E8ED;
            }
        """)
    
    def set_status(self, text):
        """Update status text"""
        self.status_label.setText(text)
    
    def set_progress(self, value):
        """Set progress value (0-100)"""
        if self.progress_bar.maximum() == 0:
            # Switch to determinate mode
            self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(value)
    
    def _on_cancel(self):
        """Handle cancel button"""
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancelling...")
        self.cancelled.emit()
    
    def mark_complete(self, success=True):
        """Mark as complete"""
        if success:
            self.set_status("✓ Complete!")
        else:
            self.set_status("✗ Failed")
        self.cancel_btn.setText("Close")
        self.cancel_btn.setEnabled(True)
