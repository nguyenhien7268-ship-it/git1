
import traceback
from PyQt6.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QGroupBox, QPushButton, QScrollArea,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Import SETTINGS from logic layer
try:
    from logic.config_manager import SETTINGS
except ImportError:
    print("Warning: logic.config_manager not found. Using mock settings.")
    # Mock for testing without backend
    SETTINGS = type("obj", (object,), {
        "get_all_settings": lambda: {},
        "update_setting": lambda k, v: (True, "Mock update")
    })

class PyQtSettingsDialog(QDialog):
    """
    Settings Dialog for PyQt6 (V8.2)
    Replicates the 3-tab structure of the Tkinter version.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt Hệ thống (V8.2 - Dual Config)")
        self.resize(700, 650)
        self.setModal(True)
        
        # Load current settings
        try:
            self.current_settings = SETTINGS.get_all_settings()
        except Exception:
            self.current_settings = {}
            
        self.entries = {}
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create tabs
        self._create_lo_de_tab()
        self._create_ai_tab()
        self._create_performance_tab()
        
        # Bottom Buttons
        button_box = QHBoxLayout()
        save_btn = QPushButton("💾 Lưu Tất cả Cài đặt")
        save_btn.clicked.connect(self._save_all_settings)
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("font-weight: bold; font-size: 10pt;")
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(save_btn)
        button_box.addWidget(cancel_btn)
        layout.addLayout(button_box)
        
        self._apply_styles()

    def _create_scrollable_tab(self, tab_name):
        """Helper to create a scrollable tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout()
        content.setLayout(content_layout)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        self.tabs.addTab(tab, tab_name)
        return content_layout

    def _create_lo_de_tab(self):
        """Tab 1: Lo/De Management"""
        layout = self._create_scrollable_tab("🎯 Quản lý Lô/Đề")
        
        # === Lo Config ===
        lo_group = QGroupBox("⚙️ Cấu hình Cầu Lô (Lo Config)")
        lo_layout = QVBoxLayout()
        lo_group.setLayout(lo_layout)
        
        lo_config = self.current_settings.get('lo_config', {})
        
        # Remove Threshold
        self._add_setting_row(lo_layout, "🔴 Ngưỡng TẮT Cầu Lô (%):", 
                            "lo_config_remove", str(lo_config.get('remove_threshold', 43.0)),
                            "Tắt cầu khi K1N & K2N < ngưỡng này")
        
        # Add Threshold
        self._add_setting_row(lo_layout, "🟢 Ngưỡng BẬT Lại Cầu Lô (%):", 
                            "lo_config_add", str(lo_config.get('add_threshold', 45.0)),
                            "Bật lại cầu khi K1N >= ngưỡng này")
        
        # Info
        self._add_info_box(lo_layout, [
            "• Cầu Lô thường linh hoạt hơn, ngưỡng thấp hơn (40-50%)",
            "• Buffer zone giúp tránh dao động"
        ])
        
        layout.addWidget(lo_group)
        
        # === De Config ===
        de_group = QGroupBox("⚙️ Cấu hình Cầu Đề (De Config)")
        de_layout = QVBoxLayout()
        de_group.setLayout(de_layout)
        
        de_config = self.current_settings.get('de_config', {})
        
        # Remove Threshold
        self._add_setting_row(de_layout, "🔴 Ngưỡng TẮT Cầu Đề (%):", 
                            "de_config_remove", str(de_config.get('remove_threshold', 80.0)),
                            "Tắt cầu khi K1N & K2N < ngưỡng này")
        
        # Add Threshold
        self._add_setting_row(de_layout, "🟢 Ngưỡng BẬT Lại Cầu Đề (%):", 
                            "de_config_add", str(de_config.get('add_threshold', 88.0)),
                            "Bật lại cầu khi K1N >= ngưỡng này")
        
        # Info
        self._add_info_box(de_layout, [
            "• Cầu Đề rủi ro cao hơn, dùng ngưỡng bảo thủ (75-90%)",
            "• Buffer zone lớn hơn (8%) giúp chỉ giữ cầu thực sự tốt"
        ])
        
        layout.addWidget(de_group)
        layout.addStretch()

    def _create_ai_tab(self):
        """Tab 2: AI Configuration"""
        layout = self._create_scrollable_tab("🤖 Cấu hình AI")
        
        ai_group = QGroupBox("🧠 Tham số Mô hình AI (XGBoost)")
        ai_layout = QVBoxLayout()
        ai_group.setLayout(ai_layout)
        
        settings = [
            ("AI_MAX_DEPTH", "Độ Sâu Cây (Max Depth):", "Độ sâu tối đa (6-12) - Cần train lại"),
            ("AI_N_ESTIMATORS", "Số lượng Cây:", "Số cây (100-300) - Cần train lại"),
            ("AI_LEARNING_RATE", "Tốc độ Học:", "Learning Rate (0.01-0.1) - Cần train lại"),
            ("AI_SCORE_WEIGHT", "Trọng số Điểm AI:", "Ảnh hưởng lên điểm tổng (0.0-1.0)"),
            ("AI_PROB_THRESHOLD", "Ngưỡng Kích Hoạt AI (%):", "Xác suất tối thiểu (40-60)")
        ]
        
        for key, label, tooltip in settings:
            val = str(self.current_settings.get(key, ""))
            self._add_setting_row(ai_layout, label, key, val, tooltip)
            
        # Warning
        warn_lbl = QLabel("⚠️ Lưu ý: Thay đổi tham số model cần HUẤN LUYỆN LẠI để có hiệu quả")
        warn_lbl.setStyleSheet("color: #FF3B30; font-weight: bold; margin-top: 10px;")
        ai_layout.addWidget(warn_lbl)
        
        layout.addWidget(ai_group)
        layout.addStretch()

    def _create_performance_tab(self):
        """Tab 3: Performance"""
        layout = self._create_scrollable_tab("⚡ Hiệu năng & Phong Độ")
        
        # === Data Slicing ===
        perf_group = QGroupBox("⚡ Cấu hình Hiệu năng")
        perf_layout = QVBoxLayout()
        perf_group.setLayout(perf_layout)
        
        perf_items = [
            ("DATA_LIMIT_DASHBOARD", "Giới hạn Dashboard (0=Full):", "Số kỳ hiển thị trên dashboard"),
            ("DATA_LIMIT_RESEARCH", "Giới hạn Tối ưu hóa (0=Full):", "Số kỳ dùng cho tối ưu hóa"),
            ("DATA_LIMIT_SCANNER", "Giới hạn Quét Cầu (0=Full):", "Số kỳ dùng khi dò cầu mới")
        ]
        
        for key, label, tooltip in perf_items:
            val = str(self.current_settings.get(key, "0"))
            self._add_setting_row(perf_layout, label, key, val, tooltip)
            
        layout.addWidget(perf_group)
        
        # === Recent Form ===
        form_group = QGroupBox("📊 Chấm Điểm Phong Độ")
        form_layout = QVBoxLayout()
        form_group.setLayout(form_layout)
        
        form_items = [
            ("RECENT_FORM_PERIODS", "Số kỳ xét phong độ:", "Số kỳ gần nhất (VD: 10)"),
            ("RECENT_FORM_MIN_HIGH", "Ngưỡng phong độ cao:", "Số lần ăn tối thiểu (VD: 8)"),
            ("RECENT_FORM_BONUS_HIGH", "Điểm thưởng cao:", "Điểm cộng (VD: 3.0)"),
            ("DASHBOARD_MIN_RECENT_WINS", "Lọc Dashboard Lo (Wins):", "Số lần ăn tối thiểu để hiện trên dashboard"),
             ("DE_DASHBOARD_MIN_RECENT_WINS", "Lọc Dashboard De (Wins):", "Số lần ăn tối thiểu để hiện trên dashboard de")
        ]
        
        for key, label, tooltip in form_items:
            val = str(self.current_settings.get(key, ""))
            self._add_setting_row(form_layout, label, key, val, tooltip)
            
        layout.addWidget(form_group)
        layout.addStretch()

    def _add_setting_row(self, parent_layout, label_text, key, value, tooltip=""):
        """Add a row with Label | Entry | Tooltip"""
        row = QHBoxLayout()
        
        lbl = QLabel(label_text)
        lbl.setMinimumWidth(200)
        
        entry = QLineEdit(value)
        self.entries[key] = entry
        
        row.addWidget(lbl)
        row.addWidget(entry)
        
        if tooltip:
            tip = QLabel(tooltip)
            tip.setStyleSheet("color: #666; font-style: italic;")
            row.addWidget(tip)
            
        parent_layout.addLayout(row)

    def _add_info_box(self, parent_layout, messages):
        """Add an info box with bullet points"""
        frame = QFrame()
        frame.setStyleSheet("background-color: #F2F2F7; border-radius: 6px; padding: 5px;")
        layout = QVBoxLayout()
        frame.setLayout(layout)
        
        title = QLabel("💡 Lưu ý:")
        title.setStyleSheet("color: #007AFF; font-weight: bold;")
        layout.addWidget(title)
        
        for msg in messages:
            lbl = QLabel(msg)
            lbl.setWordWrap(True)
            layout.addWidget(lbl)
            
        parent_layout.addWidget(frame)

    def _save_all_settings(self):
        """Save settings to config manager"""
        try:
            lo_config = {}
            de_config = {}
            any_input_error = False
            
            for key, entry in self.entries.items():
                val = entry.text().strip()
                
                # Special handling for nested configs
                if key.startswith('lo_config_'):
                    try:
                        sub_key = key.replace('lo_config_', '')
                        lo_config[sub_key] = float(val)
                    except ValueError:
                        any_input_error = True
                    continue
                    
                if key.startswith('de_config_'):
                    try:
                        sub_key = key.replace('de_config_', '')
                        de_config[sub_key] = float(val)
                    except ValueError:
                        any_input_error = True
                    continue

                # Standard settings
                SETTINGS.update_setting(key, val)

            # Update nested configs
            if lo_config:
                SETTINGS.update_setting('lo_config', lo_config)
            if de_config:
                SETTINGS.update_setting('de_config', de_config)

            if any_input_error:
                QMessageBox.warning(self, "Cảnh báo", "Một số giá trị số không hợp lệ. Vui lòng kiểm tra lại.")
            else:
                QMessageBox.information(self, "Thành công", "Đã lưu cài đặt thành công!")
                self.accept()
                
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu cài đặt: {str(e)}")

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog { background-color: #F5F5F7; }
            QGroupBox { 
                font-weight: bold; border: 1px solid #D1D1D6; 
                border-radius: 6px; margin-top: 10px; padding-top: 15px; 
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLineEdit { padding: 5px; border: 1px solid #D1D1D6; border-radius: 4px; background: white; }
            QTabWidget::pane { border: 1px solid #D1D1D6; background: white; }
            QTabBar::tab { padding: 8px 20px; }
        """)
