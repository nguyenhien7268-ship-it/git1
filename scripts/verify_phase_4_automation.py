# Tên file: scripts/verify_phase_4_automation.py
import sys
import unittest
from unittest.mock import MagicMock, patch

# Thêm đường dẫn để import logic và services
# Giả định script này chạy từ thư mục gốc git1
sys.path.append('.') 
sys.path.append('./logic')
sys.path.append('./services')
sys.path.append('./logic/bridges')

# Import các module cần thiết
try:
    from services.bridge_service import BridgeService
    from logic.db_manager import DBManager # Import để Mock Spec
    from logic.config_manager import SETTINGS
    # Import các hàm logic cốt lõi để test
    from logic.de_backtester_core import calculate_de_bridge_max_lose_history 
    from data_repository import get_all_managed_bridges as data_repo_get_all_managed_bridges
except ImportError as e:
    print(f"Lỗi Import: Không tìm thấy module cốt lõi: {e}")
    exit()

# Cấu hình cầu mẫu (Mock Data)
MOCK_BRIDGES = [
    {
        'id': 1, 
        'name': 'DE_POS_GOOD', 
        'is_enabled': 1, 
        'is_pinned': 0, 
        'type': 'DE_POS_TOUCH'
    },
    {
        'id': 2, 
        'name': 'DE_POS_RISK', 
        'is_enabled': 1, 
        'is_pinned': 0, 
        'type': 'DE_POS_TOUCH'
    },
    {
        'id': 3, 
        'name': 'LO_RISK', 
        'is_enabled': 1, 
        'is_pinned': 0, 
        'type': 'LO_FIXED_STL'
    },
]

class TestPhase4Automation(unittest.TestCase):
    
    def setUp(self):
        # 1. Mock các Dependencies
        self.mock_logger = MagicMock()
        # Dữ liệu lịch sử (cần ít nhất 2 phần tử để logic chạy)
        self.mock_all_data = [
            ('2025-01-01', None, '12345', '11111', '22222', '33333', '44444', '55555', '66666', '77777'),
            ('2025-01-02', None, '67890', '88888', '99999', '00000', '11111', '22222', '33333', '44444')
        ]

        # 2. Mocking DataRepository (Hàm mà BridgeService gọi để lấy cầu)
        self.patcher_get_all_bridges = patch('services.bridge_service.data_repo_get_all_managed_bridges')
        self.mock_get_all_bridges = self.patcher_get_all_bridges.start()
        self.mock_get_all_bridges.return_value = MOCK_BRIDGES 
        
        # 3. Mock Pruning Logic (Hàm tính Max Lose)
        self.patcher_max_lose = patch('logic.de_backtester_core.calculate_de_bridge_max_lose_history')
        self.mock_max_lose_history = self.patcher_max_lose.start()
        
        # 4. Mock DB Manager functions (các hàm cấp module mà BridgeService gọi)
        # Patch trước khi khởi tạo service để đảm bảo service sử dụng mock
        self.patcher_toggle_pin = patch('services.bridge_service.db_manager_toggle_pin_bridge')
        self.mock_toggle_pin = self.patcher_toggle_pin.start()
        self.mock_toggle_pin.return_value = (True, "Cập nhật thành công.", True)
        
        self.patcher_update_bridge = patch('services.bridge_service.db_manager_update_managed_bridge')
        self.mock_update_bridge = self.patcher_update_bridge.start()
        self.mock_update_bridge.return_value = (True, "Cập nhật thành công.")
        
        # 5. Khởi tạo Service với SETTINGS
        with patch.object(SETTINGS, 'DE_MAX_LOSE_THRESHOLD', 30):
            self.bridge_service = BridgeService("mock_db", self.mock_logger)
        
    def tearDown(self):
        self.patcher_get_all_bridges.stop()
        self.patcher_max_lose.stop()
        self.patcher_toggle_pin.stop()
        self.patcher_update_bridge.stop()

    def test_01_toggle_pin_functionality(self):
        """Kiểm tra: Bật/Tắt ghim cầu hoạt động đúng trong DB."""
        
        bridge_name = 'DE_POS_GOOD'
        
        # 1. Bật Pin
        self.bridge_service.toggle_pin_bridge(bridge_name)
        # Kiểm tra: Hàm toggle_pin_bridge được gọi với bridge_name
        self.mock_toggle_pin.assert_called_with(bridge_name, "mock_db")
        
        # 2. Tắt Pin (lần gọi thứ 2)
        self.mock_toggle_pin.return_value = (True, "Cập nhật thành công.", False)
        self.bridge_service.toggle_pin_bridge(bridge_name)
        # Kiểm tra: Hàm toggle_pin_bridge được gọi 2 lần
        self.assertEqual(self.mock_toggle_pin.call_count, 2)

    def test_02_prune_bad_de_bridges_protection(self):
        """Kiểm tra: Cầu được ghim phải được BỎ QUA khi chạy Pruning."""
        
        # Cấu hình Max Lose History (MaxLose=50 > Ngưỡng=30)
        self.mock_max_lose_history.return_value = 50 

        # 1. Giả lập cầu GOOD được GHIM (is_pinned=1) và cầu RISK vẫn chưa ghim (is_pinned=0)
        MOCK_BRIDGES[0]['is_pinned'] = 1 
        MOCK_BRIDGES[1]['is_pinned'] = 0 
        MOCK_BRIDGES[2]['type'] = 'DE_POS_TOUCH' # Kích hoạt logic Đề
        self.mock_get_all_bridges.return_value = MOCK_BRIDGES # Cập nhật Mock

        # Chạy Prune
        result_message = self.bridge_service.prune_bad_de_bridges(self.mock_all_data)

        # 2. KIỂM TRA KẾT QUẢ
        
        # Pruning phải được gọi để TẮT cầu RISK (id=2, MaxLose=50 > Ngưỡng=30)
        # Hàm update_managed_bridge được gọi với bridge_id=2, is_enabled=0
        self.mock_update_bridge.assert_called()
        
        # Kiểm tra các lệnh gọi update_managed_bridge
        # Lấy danh sách các bridge_id được gọi
        call_bridge_ids = [call.args[0] for call in self.mock_update_bridge.call_args_list]
        
        # Cầu RISK (id=2) phải được gọi để tắt
        self.assertIn(2, call_bridge_ids, "Cầu RISK (id=2) phải được tắt.")
        
        # Cầu GOOD (id=1) KHÔNG được gọi vì đang được ghim
        self.assertNotIn(1, call_bridge_ids, "Cầu được ghim (DE_POS_GOOD, id=1) KHÔNG được phép bị tắt.")
        
        # Kiểm tra thông báo kết quả
        self.assertIn('vô hiệu hóa', result_message.lower() or '', "Phải có thông báo về số cầu bị vô hiệu hóa.")


    def test_03_pruning_logic_is_active(self):
        """Kiểm tra: Logic Pruning cơ bản hoạt động (Tắt 2 cầu > Max Lose)."""
        
        # Cấu hình Max Lose History: 50 (Cao hơn Ngưỡng 30)
        self.mock_max_lose_history.return_value = 50 
        
        # Chạy Prune (2 cầu Đề không ghim, đều bị tắt)
        MOCK_BRIDGES[0]['is_pinned'] = 0
        MOCK_BRIDGES[1]['is_pinned'] = 0
        MOCK_BRIDGES[2]['type'] = 'DE_POS_TOUCH' # Kích hoạt logic Đề
        self.mock_get_all_bridges.return_value = MOCK_BRIDGES # Cập nhật Mock
        
        # Chạy Prune
        result_message = self.bridge_service.prune_bad_de_bridges(self.mock_all_data)
        
        # Cả DE_POS_GOOD và DE_POS_RISK đều phải bị TẮT vì 50 > 30 (Ngưỡng)
        # Hàm update_managed_bridge phải được gọi 2 lần (cho 2 cầu)
        self.assertGreaterEqual(self.mock_update_bridge.call_count, 2, "Phải có ít nhất 2 lệnh gọi để tắt 2 cầu.")
        
        # Kiểm tra các bridge_id được gọi
        call_bridge_ids = [call.args[0] for call in self.mock_update_bridge.call_args_list]
        
        # Cả 2 cầu đều phải được gọi để tắt
        self.assertIn(1, call_bridge_ids, "Cầu DE_POS_GOOD (id=1) phải được tắt.")
        self.assertIn(2, call_bridge_ids, "Cầu DE_POS_RISK (id=2) phải được tắt.")
        
        # Kiểm tra thông báo kết quả
        self.assertIn('vô hiệu hóa', result_message.lower() or '', "Phải có thông báo về số cầu bị vô hiệu hóa.")

        
if __name__ == '__main__':
    # Chạy unit test
    print("="*70)
    print("▶️ BẮT ĐẦU KIỂM TRA CHỨC NĂNG TỰ ĐỘNG HÓA (PIN & PRUNE) - PHASE 4")
    print("="*70)
    
    # Chạy unit test
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    
    print("="*70)
    print("✅ XÁC NHẬN: Logic Pruning & Pinning đã được kiểm tra.")
    print("👉 Nếu tất cả test đều PASS, hệ thống đã sẵn sàng cho Giai đoạn Mở Rộng.")
    print("="*70)