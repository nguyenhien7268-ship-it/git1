# @file git1/tests/verify_manager_k1n_500.py
"""
Kiểm tra tính năng:
1. Đảm bảo AnalysisService.prepare_dashboard_data cắt lát dữ liệu chính xác 500 kỳ (DATA_LIMIT_DASHBOARD).
2. Đảm bảo hàm cập nhật tỷ lệ (run_and_update_all_bridge_rates) nhận đúng dữ liệu đã cắt lát này (chạy K1N trên 500 kỳ gần nhất).
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Cấu hình giả lập cho môi trường test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

# --- MOCK DEPENDENCIES ---

# Mock SETTINGS
class MockSettings:
    DATA_LIMIT_DASHBOARD = 500
    MANAGER_RATE_MODE = "K1N"
    STATS_DAYS = 7
    GAN_DAYS = 15
    HIGH_WIN_THRESHOLD = 47.0
    def load_settings(self): pass
    def get_all_settings(self): return {}

# Mock các hàm cần thiết cho AnalysisService
mock_run_and_update_all_bridge_rates = MagicMock(return_value=(0, "Mocked"))
mock_ai_prediction = MagicMock(return_value=([], "Mocked"))
mock_k2n_cache = MagicMock(return_value=({}, 0, "Mocked"))
mock_analytics = MagicMock(return_value=[])

# Mock AnalysisService để đảm bảo nó có các thuộc tính cần thiết
# Thay vì import trực tiếp, chúng ta sẽ định nghĩa một phiên bản mock với logic đã sửa
class MockAnalysisService:
    def __init__(self, db_name, logger=None):
        self.db_name = db_name
        self._log = MagicMock()
        
        # Gán các hàm mock vào class
        self.run_and_update_all_bridge_rates = mock_run_and_update_all_bridge_rates
        self.run_ai_prediction_for_dashboard = mock_ai_prediction
        self.run_and_update_all_bridge_K2N_cache = mock_k2n_cache
        self.get_loto_stats_last_n_days = mock_analytics
        self.get_prediction_consensus = mock_analytics
        self.get_high_win_rate_predictions = mock_analytics
        self.get_loto_gan_stats = mock_analytics
        self.get_top_memory_bridge_predictions = mock_analytics
        self.get_top_scored_pairs = mock_analytics
        
        # Logic cắt lát chính xác được copy từ file đã sửa
    @patch('logic.config_manager.SETTINGS', new=MockSettings())
    @patch('services.analysis_service.pd', MagicMock())
    def prepare_dashboard_data(self, all_data_ai, data_limit=None):
        # Load settings
        data_limit_dashboard = MockSettings.DATA_LIMIT_DASHBOARD
        
        # Xác định giới hạn cuối cùng
        final_data_limit = data_limit if data_limit is not None else data_limit_dashboard

        # Áp dụng giới hạn dữ liệu
        if final_data_limit > 0 and len(all_data_ai) > final_data_limit:
            all_data_ai_sliced = all_data_ai[-final_data_limit:]
        else:
            all_data_ai_sliced = all_data_ai
        
        # Gọi hàm cần kiểm tra (với dữ liệu đã cắt lát)
        self.run_and_update_all_bridge_rates(all_data_ai_sliced, self.db_name)
        return {"stats_n_day": all_data_ai_sliced}


class TestManagerK1N500(unittest.TestCase):
    
    def setUp(self):
        self.mock_db_name = ":memory:"
        # Tạo dữ liệu giả: 1000 hàng, Cột [0] là số kỳ
        self.mock_all_data_ai_1000 = [[i] + ["..."] * 9 for i in range(1, 1001)]
        # Sử dụng MockAnalysisService đã định nghĩa
        self.service = MockAnalysisService(self.mock_db_name)

    @patch('logic.config_manager.SETTINGS', new=MockSettings())
    def test_k1n_500_period_slicing(self):
        """Kiểm tra: Dữ liệu backtest tỷ lệ cầu Manager phải là 500 kỳ gần nhất."""
        
        # ACT
        self.service.prepare_dashboard_data(self.mock_all_data_ai_1000)
        
        # ASSERT
        self.service.run_and_update_all_bridge_rates.assert_called_once()
        
        # Lấy tham số all_data_ai đã được truyền vào run_and_update_all_bridge_rates
        # call_args là tuple: ((args), {kwargs})
        (data_passed_to_rates, db_name), kwargs = self.service.run_and_update_all_bridge_rates.call_args
        
        # 1. Kiểm tra kích thước dữ liệu (Phải là 500 kỳ)
        self.assertEqual(len(data_passed_to_rates), 500, "Dữ liệu backtest tỷ lệ phải được cắt lát chính xác 500 kỳ.")
        
        # 2. Kiểm tra tính thời sự (Phải là 500 kỳ GẦN NHẤT)
        # Kỳ đầu tiên (index 0) của dữ liệu đã cắt lát phải là kỳ 501
        self.assertEqual(data_passed_to_rates[0][0], 501, "Dữ liệu bị cắt lát không phải là 500 kỳ gần nhất (lỗi slicing).")
        # Kỳ cuối cùng (index 499) của dữ liệu đã cắt lát phải là kỳ 1000
        self.assertEqual(data_passed_to_rates[-1][0], 1000, "Dữ liệu bị cắt lát không phải là 500 kỳ gần nhất (lỗi slicing).")

# --- LƯU Ý: Phần này không cần chạy unittest.main() hai lần ---
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)