import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Cấu hình đường dẫn để import logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

# Import hàm cần test
try:
    from logic.analytics.dashboard_scorer import get_high_win_rate_predictions
except ImportError:
    # Fallback cho môi trường test
    print("Không thể import get_high_win_rate_predictions. Đảm bảo logic.analytics đã được cấu hình.")
    get_high_win_rate_predictions = MagicMock(return_value=[])

# Mocking SETTINGS (để giả lập ngưỡng)
class MockSettings:
    HIGH_WIN_THRESHOLD = 47.0 # Ngưỡng Lô
    DE_HIGH_RATE_MIN_WINS_10 = 7 # Ngưỡng Đề
    
# Mocking data_repository.get_all_managed_bridges
def mock_get_all_managed_bridges(db_name=None, only_enabled=False):
    # Cầu 1: Đề đang hot (wins_10=8 >= 7), tỷ lệ dài hạn thấp (40.00% < 47.0%) -> PHẢI được chọn (DE)
    de_hot = {
        "name": "DE_HOT_K8", "type": "DE_DYNAMIC_K", 
        "win_rate_text": "40.00%", "recent_win_count_10": 8, 
        "next_prediction_stl": "2,7" 
    }
    # Cầu 2: Lô tỷ lệ cao (55.00% >= 47.0%), phong độ gần nhất thấp (2) -> PHẢI được chọn (LOTO)
    loto_high_rate = {
        "name": "LOTO_HIGH_RATE", "type": "LOTO", 
        "win_rate_text": "55.00%", # Không còn lỗi cú pháp
        "recent_win_count_10": 2, 
        "next_prediction_stl": "12,21"
    }
    # Cầu 3: Lô tỷ lệ thấp (45.00% < 47.0%), phong độ gần nhất cực cao (9) -> PHẢI bị loại (LOTO)
    loto_low_rate = {
        "name": "LOTO_LOW_RATE", "type": "LOTO", 
        "win_rate_text": "45.00%", "recent_win_count_10": 9, 
        "next_prediction_stl": "34,43"
    }
    return [de_hot, loto_high_rate, loto_low_rate]

class TestDeHighRateFix(unittest.TestCase):
    
    # Sử dụng Context Manager để kiểm soát chính xác phạm vi mocking
    def test_de_filtering_uses_recent_wins_correctly(self):
        """
        Xác nhận:
        1. Cầu Đề (DE) được chọn dựa trên recent_win_count_10 (8 >= 7).
        2. Cầu Lô (LOTO) được chọn dựa trên win_rate_text (55.00% >= 47.0%).
        3. Cầu Lô (LOTO) phong độ nóng cao nhưng tỷ lệ dài hạn thấp bị loại.
        """
        
        # Sửa lỗi Syntax/KeyError bằng cách sử dụng Context Manager và sửa mock data typo
        with patch('logic.analytics.dashboard_scorer.SETTINGS', new=MockSettings()), \
             patch('logic.analytics.dashboard_scorer.get_all_managed_bridges', new=mock_get_all_managed_bridges), \
             patch('logic.de_utils.generate_dan_de_from_touches', return_value=["02", "20", "07", "70"]):
            
            # Gọi hàm cần test
            predictions = get_high_win_rate_predictions()
            
            # Kiểm tra predictions (sẽ thành công nếu predictions là list of dicts)
            self.assertTrue(isinstance(predictions, list), "Lỗi: Đầu ra không phải là list.")
            if predictions:
                self.assertTrue(isinstance(predictions[0], dict), "Lỗi: Phần tử đầu tiên không phải dict.")

            predicted_values = [p['value'] for p in predictions] 
            
            # 1. Cầu DE HOT phải được chọn (Dàn 02, 20, 07, 70)
            self.assertIn("02", predicted_values, "Lỗi: Cầu Đề HOT (wins_10) không được chọn.")
            self.assertIn("70", predicted_values, "Lỗi: Dàn đề từ cầu HOT bị thiếu.")
            
            # 2. Cầu LOTO High Rate phải được chọn (12, 21)
            self.assertIn("12", predicted_values, "Lỗi: Cầu Lô tỷ lệ cao không được chọn.")
            self.assertIn("21", predicted_values, "Lỗi: Cầu Lô tỷ lệ cao bị thiếu.")
            
            # 3. Cầu LOTO Low Rate phải bị loại (34, 43)
            self.assertNotIn("34", predicted_values, "Lỗi: Cầu Lô tỷ lệ thấp bị chọn nhầm.")
            self.assertNotIn("43", predicted_values, "Lỗi: Cầu Lô tỷ lệ thấp bị chọn nhầm.")
            
            # Tổng số dự đoán
            self.assertEqual(len(predicted_values), 6, "Lỗi: Số lượng dự đoán được chọn không đúng.")
            
            print("\n✅ KIỂM TRA FIX LỌC CẦU ĐỀ: ĐÃ HOÀN TẤT VÀ THÀNH CÔNG!")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)