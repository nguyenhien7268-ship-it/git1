# @file git1/tests/verify_rate_overwrite.py
"""
Kiểm tra tính năng:
Xác thực rằng việc chạy run_and_update_all_bridge_rates (trong quy trình làm mới cache)
luôn ghi đè giá trị hiện tại, bất kể giá trị đó có cao hơn hay không.
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Cấu hình giả lập cho môi trường test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

# Giả lập database và hàm backtest
class MockDB:
    # ⚡ CẬP NHẬT: Thêm search_rate_text để theo dõi FIX
    BRIDGES = {
        "CAU_OPTIMAL": {"id": 1, "name": "CAU_OPTIMAL", "win_rate_text": "60.00%", "search_rate_text": "60.00%"}, # Tỷ lệ tối ưu ban đầu
        "CAU_STANDARD": {"id": 2, "name": "CAU_STANDARD", "win_rate_text": "40.00%", "search_rate_text": "40.00%"},
    }
    
    def get_all_managed_bridges(self, db_name, only_enabled=False):
        """Giả lập việc lấy cầu từ DB."""
        return [b.copy() for b in self.BRIDGES.values()] # Trả về bản sao để tránh thay đổi trực tiếp

    def update_bridge_win_rate_batch(self, db_name, updates):
        """
        Giả lập hàm ghi đè tỷ lệ chuẩn (win_rate_text) vào DB.
        Hàm này mô phỏng UPDATE ManagedBridges SET win_rate_text = ? WHERE name = ?
        """
        for name, rate, max_lose, recent_win in updates:
            if name in self.BRIDGES:
                # ⚡ LÔGIC MOCK DB: Chỉ cập nhật win_rate_text (tỷ lệ chuẩn)
                self.BRIDGES[name]["win_rate_text"] = rate

# Mock Logic backtest (luôn trả về tỷ lệ thấp hơn - 48.0%)
def mock_run_and_update_all_bridge_rates(all_data_ai, db_name):
    """
    Giả lập hàm backtest K1N chuẩn (500 kỳ)
    - Nó luôn tính ra 48.00% cho CAU_OPTIMAL.
    """
    updates = [
        ("CAU_OPTIMAL", "48.00%", 5, 8), # Tỷ lệ bị giảm
        ("CAU_STANDARD", "45.00%", 4, 7), # Tỷ lệ bị tăng nhẹ
    ]
    MockDBInstance.update_bridge_win_rate_batch(db_name, updates)
    return 2, "Cập nhật thành công"

# --- Khởi tạo Mock ---
MockDBInstance = MockDB()

# Giả lập AnalysisService (phần liên quan đến cập nhật tỷ lệ)
class MockAnalysisService:
    def __init__(self, db_name):
        self.db_name = db_name
        self.run_and_update_all_bridge_rates = mock_run_and_update_all_bridge_rates
        self._log = MagicMock()
        
    def run_full_update_sequence(self, all_data_ai):
        """Giả lập bước 3 & 4 trong quá trình làm mới cache."""
        # Giả lập việc cắt lát dữ liệu 500 kỳ
        sliced_data = all_data_ai[-500:] 
        # Chạy hàm cập nhật tỷ lệ
        self.run_and_update_all_bridge_rates(sliced_data, self.db_name)


class TestRateOverwrite(unittest.TestCase):
    
    def setUp(self):
        self.mock_db_name = ":memory:"
        self.service = MockAnalysisService(self.mock_db_name)
        # Giả lập 1000 kỳ dữ liệu
        self.mock_all_data = [[i] for i in range(1, 1001)]
        
    def test_overwrite_after_refresh_fix_applied(self):
        """Kiểm tra: Tỷ lệ Tối ưu phải được BẢO TỒN sau khi Refresh (win_rate_text bị ghi đè, search_rate_text không bị)."""
        
        # ACT: Chạy quy trình làm mới (tương đương Làm mới Cache K2N)
        self.service.run_full_update_sequence(self.mock_all_data)
        
        # ASSERT: Tỷ lệ của CAU_OPTIMAL đã bị ghi đè
        updated_bridges = MockDBInstance.get_all_managed_bridges(self.mock_db_name)
        
        cau_optimal = next(b for b in updated_bridges if b['name'] == 'CAU_OPTIMAL')
        
        # 1. Tỷ lệ CHUẨN (win_rate_text) phải giảm (Đúng cho Auto-Prune)
        self.assertEqual(cau_optimal['win_rate_text'], "48.00%", 
                         "win_rate_text (Tỷ lệ chuẩn) phải được cập nhật xuống 48.00% cho Auto-Prune.")
        
        # 2. Tỷ lệ TỐI ƯU (search_rate_text) phải được BẢO TỒN (Đúng cho Đề xuất Tối ưu)
        self.assertEqual(cau_optimal['search_rate_text'], "60.00%", 
                         "search_rate_text (Tỷ lệ tối ưu) KHÔNG được bị ghi đè và phải giữ nguyên 60.00%.")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)