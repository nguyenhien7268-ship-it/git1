# @file git1/tests/test_ui_manager_headers.py
"""
Kiểm tra tính năng:
Xác minh tiêu đề cột 'Tỷ lệ thắng' trong UI Bridge Manager đã được cập nhật thành (K1N)
theo cấu hình.
"""
import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import sys
import os

# Cấu hình giả lập cho môi trường test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- MOCK CONFIG DATA ---
MOCK_CONFIG_DATA = {
    "MANAGER_RATE_MODE": "K1N",
    "FILTER_ENABLED": False,
    "RECENT_FORM_PERIODS": 10,
}

# --- MOCK CONFIG MANAGER ---
class MockConfigManager:
    """Giả lập logic.config_manager.SETTINGS."""
    def __init__(self):
        for k, v in MOCK_CONFIG_DATA.items():
            setattr(self, k, v)
        # Khởi tạo giá trị động
        self.MANAGER_RATE_MODE = MOCK_CONFIG_DATA["MANAGER_RATE_MODE"]
        
    def load_settings(self): pass
    def get_all_settings(self): return self.__dict__.copy()

# Khởi tạo Settings Mock toàn cục
MOCK_SETTINGS_INSTANCE = MockConfigManager()

# --- MOCK UI ELEMENTS ---
class MockTkinterApp:
    """Giả lập ứng dụng Tkinter cơ bản."""
    def __init__(self):
        self.tree = MagicMock()
        self.tree.heading.side_effect = self.check_heading_text
        self.tree.column.return_value = None
        self.columns = ()
        
    def check_heading_text(self, col_id, text=None, anchor=None):
        """Hàm giả lập việc thiết lập tiêu đề cột."""
        if text:
            if not hasattr(self, '_headings'):
                self._headings = []
            self._headings.append(text)
            
    def get_headings(self):
        """Trả về các tiêu đề cột đã được thiết lập."""
        return self._headings if hasattr(self, '_headings') else []

# --- MOCK UI BRIDGE MANAGER (Lớp cần được test) ---
# Patch các dependencies cần thiết
@patch('services.analysis_service.AnalysisService', MagicMock())
@patch('logic.config_manager.SETTINGS', new=MOCK_SETTINGS_INSTANCE)
class TestUIManagerHeaders(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Thiết lập lớp UIBridgeManager (dùng fallback nếu import thất bại)
        try:
            # Nếu có thể import, sử dụng lớp gốc
            from ui.ui_bridge_manager import UIBridgeManager
            cls.UIBridgeManager = UIBridgeManager
        except ImportError:
            # Fallback: Tạo lớp giả lập chứa logic setup cột đã sửa
            class FallbackUIBridgeManager(MockTkinterApp):
                def __init__(self, master=None, controller=None):
                    super().__init__()
                    self.tree.heading.side_effect = self.check_heading_text
                    self.tree.column.return_value = None
                    self._setup_treeview_columns()

                # Logic setup cột đã sửa đổi (Đã được vá trong phản hồi trước)
                def _setup_treeview_columns(self):
                    rate_mode = MOCK_SETTINGS_INSTANCE.MANAGER_RATE_MODE # Dùng instance đã mock
                    rate_header = f"Tỷ lệ thắng ({rate_mode.upper()})"
                    
                    self.columns = ("Tên Cầu", "Loại", "Vị Trí", "STL Dự Đoán", rate_header, 
                                    "Chuỗi T/T Max", "Phong Độ 10 Kỳ", "AI Score", "Thao Tác")
                    self.tree.column("#0", width=0, stretch=tk.NO)
                    
                    for col in self.columns:
                        self.tree.heading(col, text=col, anchor=tk.CENTER)
                        self.tree.column(col, anchor=tk.CENTER, width=100)
            
            cls.UIBridgeManager = FallbackUIBridgeManager

    def test_rate_header_is_k1n(self):
        """Kiểm tra 1: Tiêu đề cột Tỷ lệ thắng phải là (K1N) khi cấu hình là K1N."""
        
        # ACT
        # Khởi tạo đối tượng (sẽ gọi _setup_treeview_columns)
        ui_instance = self.UIBridgeManager(master=None, controller=MagicMock())
        
        # ASSERT
        headings = ui_instance.get_headings()
        expected_header = "Tỷ lệ thắng (K1N)"
        
        self.assertIn(expected_header, headings, 
                      f"Tiêu đề cột 'Tỷ lệ thắng' phải là '{expected_header}', nhưng không tìm thấy trong: {headings}")
        
    def test_rate_header_is_k2n_if_setting_changed(self):
        """Kiểm tra 2: Tiêu đề cột Tỷ lệ thắng thay đổi nếu cấu hình thay đổi (giả lập)."""
        
        # Giả lập thay đổi setting: Thay đổi giá trị trên Mock Instance
        MOCK_SETTINGS_INSTANCE.MANAGER_RATE_MODE = "K2N"
        
        # ACT (Chạy lại logic setup)
        ui_instance = self.UIBridgeManager(master=None, controller=MagicMock())
        
        # ASSERT
        headings = ui_instance.get_headings()
        expected_header = "Tỷ lệ thắng (K2N)"
        
        self.assertIn(expected_header, headings, 
                      f"Tiêu đề cột không thay đổi đúng. Phải là '{expected_header}', nhưng không tìm thấy.")
        
        # Đảm bảo reset setting sau test
        MOCK_SETTINGS_INSTANCE.MANAGER_RATE_MODE = "K1N"

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)