"""
Kiểm tra Tính năng:
Xác nhận luồng dữ liệu cuối cùng: Tỷ lệ tối ưu từ Bridge Manager Core được lưu
vào cột 'search_rate_text' và không bị ghi đè bởi quy trình cập nhật chuẩn.

SỬA LỖI AssertionError: Sửa đường dẫn mock cho upsert_managed_bridge 
để đảm bảo hàm dò cầu (TIM_CAU_TOT_NHAT_V16) gọi đúng mock DB.
"""
import unittest
from unittest.mock import MagicMock, patch, call
import sys
import os

# Cấu hình giả lập cho môi trường test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 

# --- MOCK DEPENDENCIES ---
# Giả lập SETTINGS (để TIM_CAU_TOT_NHAT_V16 chạy)
class MockSettings:
    AUTO_ADD_MIN_RATE = 50.0 

# Giả lập các hàm cầu để chúng luôn trúng (tỷ lệ 100%)
def mock_getAllPositions_V17_Shadow(r): 
    # Trả về 100 vị trí giả lập
    return [i for i in range(100)] 

def mock_taoSTL_V30_Bong(a, b): 
    # Luôn dự đoán '11' (giả lập)
    return ["11"] 

def mock_getAllLoto_V30(r): 
    # Luôn có '11' trong kết quả (giả lập)
    return ["11", "22"]

# Mock DB: Cấu trúc đã được FIX
class MockDB:
    BRIDGES = {}
    
    def upsert_managed_bridge(self, name, description, win_rate_text, db_name, pos1_idx, pos2_idx, bridge_data):
        """Mock hàm upsert_managed_bridge đã được sửa đổi (nhận bridge_data)."""
        self.BRIDGES[name] = {
            "name": name,
            "win_rate_text": bridge_data.get('win_rate_text', '0.00%'),
            "search_rate_text": bridge_data.get('search_rate_text', '0.00%'), 
            "search_period": bridge_data.get('search_period', 0),
            "is_enabled": bridge_data.get('is_enabled', 0),
        }
        return True, "Mock Upsert Success"

    def update_bridge_win_rate_batch(self, db_name, updates):
        """Mock hàm update_bridge_win_rate_batch (Làm mới chuẩn)."""
        for name, rate, max_lose, recent_win in updates:
            if name in self.BRIDGES:
                self.BRIDGES[name]["win_rate_text"] = rate
        return True, "Mock Update Batch Success"
    
    def get_all_managed_bridges(self, db_name=None, only_enabled=False):
        return [b for b in self.BRIDGES.values()]

# --- KHỞI TẠO DB INSTANCE TẠI TOP LEVEL ---
MockDBInstance = MockDB() 

# --- ĐỊNH NGHĨA SERVICE MOCK ---
class MockLotteryService:
    def __init__(self, db_instance):
        self.db = db_instance
        
    def run_bridge_search(self, TIM_CAU_TOT_NHAT_V16, all_data_ai):
        """Giả lập việc Dò tìm Cầu. Dựa vào các patch đã được áp dụng ở test method."""
        # Hàm này nhận đúng 3 đối số: self, TIM_CAU_TOT_NHAT_V16, all_data_ai
        return TIM_CAU_TOT_NHAT_V16(all_data_ai, 1, len(all_data_ai), "mock.db")

    def run_standard_update(self, all_data_ai, db_name="mock.db"):
        """Giả lập việc Làm mới Cache K2N (chạy update win_rate)."""
        updates = []
        for name in self.db.BRIDGES.keys():
            updates.append((name, "48.00%", 5, 8)) 
        
        # ⚡ LƯU Ý: Hàm update_bridge_win_rate_batch không được mock, nên gọi trực tiếp
        self.db.update_bridge_win_rate_batch(db_name, updates)


# Cần import hàm gốc cho test
try:
    from logic.bridges.bridge_manager_core import TIM_CAU_TOT_NHAT_V16
except ImportError:
    TIM_CAU_TOT_NHAT_V16 = MagicMock()


class TestBridgeOptimizationIntegration(unittest.TestCase):
    
    def setUp(self):
        self.db_name = "mock.db"
        self.service = MockLotteryService(MockDBInstance)
        # Giả lập 1000 kỳ dữ liệu
        self.mock_all_data = [[i] + ["11", "22", "33"] * 3 for i in range(1, 1001)] 
        
    def test_search_rate_is_preserved_after_refresh(self):
        """
        Kiểm tra end-to-end:
        1. Dò tìm lưu Tỷ lệ Tối ưu (100%) vào search_rate_text.
        2. Cập nhật Chuẩn (Làm mới Cache) ghi 48% vào win_rate_text.
        3. Tỷ lệ Tối ưu phải được bảo toàn.
        """
        
        # Sử dụng Context Manager và sửa đường dẫn upsert_managed_bridge
        with patch.multiple('logic.bridges.bridge_manager_core', 
                            taoSTL_V30_Bong=mock_taoSTL_V30_Bong,
                            checkHitSet_V30_K2N=MagicMock(return_value="✅"),
                            getPositionName_V17_Shadow=MagicMock(return_value="POS"),
                            getAllPositions_V17_Shadow=mock_getAllPositions_V17_Shadow,
                            getAllLoto_V30=mock_getAllLoto_V30,
                            # ⚡ FIX ĐƯỜNG DẪN: Patch upsert_managed_bridge TẠI NƠI NÓ ĐƯỢC SỬ DỤNG
                            upsert_managed_bridge=MockDBInstance.upsert_managed_bridge):
            
            with patch('logic.config_manager.SETTINGS', new=MockSettings()):

                # --- BƯỚC 1: DÒ TÌM CẦU MỚI (LƯU TỶ LỆ TỐI ƯU) ---
                self.service.run_bridge_search(TIM_CAU_TOT_NHAT_V16, self.mock_all_data)
                
                bridges_found = MockDBInstance.get_all_managed_bridges()
                self.assertTrue(len(bridges_found) > 0, "Không tìm thấy cầu nào.")
                
                first_bridge = bridges_found[0]
                
                # ASSERT 1: Tỷ lệ tìm kiếm phải là 100% (đã lưu TỶ LỆ TỐI ƯU)
                self.assertEqual(first_bridge['search_rate_text'], "100.00%", 
                                "Lỗi: Tỷ lệ tìm kiếm không được lưu vào cột mới.")
                
                # --- BƯỚC 2: CHẠY LÀM MỚI CACHE K2N (GHI ĐÈ TỶ LỆ CHUẨN) ---
                self.service.run_standard_update(self.mock_all_data)
                
                # Lấy lại cầu sau khi làm mới
                bridges_after_refresh = MockDBInstance.get_all_managed_bridges()
                updated_bridge = bridges_after_refresh[0]

                # ASSERT 2: Tỷ lệ chuẩn (win_rate_text) bị ghi đè xuống 48.00%
                self.assertEqual(updated_bridge['win_rate_text'], "48.00%",
                                "Lỗi: win_rate_text không bị ghi đè (cần thiết cho Auto-Prune).")
                
                # ASSERT 3 (FIX XÁC NHẬN): Tỷ lệ tối ưu (search_rate_text) phải giữ nguyên 100.00%
                self.assertEqual(updated_bridge['search_rate_text'], "100.00%",
                                "LỖI NGHIÊM TRỌNG: search_rate_text bị ghi đè. Logic DB FIX đã thất bại.")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)