import sys
import unittest
from unittest.mock import MagicMock, patch

# Thêm đường dẫn để import logic và services
# Giả định script này chạy từ thư mục gốc git1
sys.path.append('.') 
sys.path.append('./logic')
sys.path.append('./services')

try:
    from logic import de_backtester_core
    from app_controller import AppController
except ImportError:
    print("Lỗi: Không tìm thấy module logic/controller. Đảm bảo chạy script từ thư mục git1.")
    exit()

# Dữ liệu mẫu (Data Mock) - Giả lập 4 kỳ GĐB
# Format: [Kỳ, Ngày, GĐB, G1, G2, G3, G4, G5, G6, G7]
# getAllPositions_V16 cần ít nhất 10 cột (index 0-9)
MOCK_DATA = [
    ('2025-11-20', None, '89100', '12345', '11111,22222', '33333,44444,55555,66666,77777,88888', '9999,0000,1111,2222', '3333,4444,5555,6666,7777,8888', '999,000,111', '00,11,22,33'),
    ('2025-11-21', None, '78234', '67890', '33333,44444', '55555,66666,77777,88888,99999,00000', '1111,2222,3333,4444', '5555,6666,7777,8888,9999,0000', '111,222,333', '44,55,66,77'),
    ('2025-11-22', None, '56000', '11111', '55555,66666', '77777,88888,99999,00000,11111,22222', '3333,4444,5555,6666', '7777,8888,9999,0000,1111,2222', '333,444,555', '66,77,88,99'),
    ('2025-11-23', None, '99123', '22222', '77777,88888', '99999,00000,11111,22222,33333,44444', '5555,6666,7777,8888', '9999,0000,1111,2222,3333,4444', '555,666,777', '88,99,00,11'),
]

# Cấu hình cầu mẫu (Bridge Config Mock)
# Cầu Test: Cầu Đề Động (DE_DYN) - Lấy chạm hàng đơn vị GĐB (pos4) + K=0. Tức là chạm của GĐB-4.
MOCK_BRIDGE_CONFIG_DYN = {
    'name': 'DE_DYN_TEST',
    'pos1_idx': 4, # Vị trí 4 (hàng đơn vị của GĐB)
    'k_offset': 0, # K=0, không cộng gì cả
    'type': 'DE_DYN_TOUCH',
    'predicted_value': '0', # Chạm dự đoán (ví dụ)
    'description': 'Cầu test chạm GĐB-4'
}

# Cấu hình cầu lỗi (Dùng để kiểm tra xử lý lỗi)
MOCK_BRIDGE_CONFIG_INVALID = {
    'name': 'DE_POS_INVALID',
    'pos1_idx': 999, # Vị trí không tồn tại
    'k_offset': 0,
    'type': 'DE_POS_TOUCH',
    'predicted_value': '9', 
    'description': 'Cầu test lỗi cấu hình'
}


class TestDeBacktestFunctional(unittest.TestCase):
    
    def setUp(self):
        # Mock Controller: Thiết lập môi trường tối thiểu
        self.mock_root = MagicMock()
        self.mock_app = MagicMock()
        self.mock_app.root = self.mock_root
        self.mock_app.load_data_ai_from_db_controller.return_value = MOCK_DATA
        
        # Mock Service Layer
        self.mock_analysis_service = MagicMock()
        self.mock_app.analysis_service = self.mock_analysis_service
        self.mock_app.logger = MagicMock()
        
        # Khởi tạo Controller
        self.controller = AppController(self.mock_app)
        self.controller.set_logger(self.mock_app.logger)
        
        # Ghi đè hàm service để chạy logic backtest thực tế
        def mock_run_de_backtest_30_days(bridge_name, all_data):
            if 'INVALID' in bridge_name:
                return de_backtester_core.run_de_bridge_historical_test(MOCK_BRIDGE_CONFIG_INVALID, all_data, days=3)
            else:
                return de_backtester_core.run_de_bridge_historical_test(MOCK_BRIDGE_CONFIG_DYN, all_data, days=3)

        self.mock_analysis_service.run_de_backtest_30_days.side_effect = mock_run_de_backtest_30_days

        # Mock Popup để kiểm tra xem nó có được gọi không
        global BacktestPopup
        BacktestPopup = MagicMock()
        
    def test_01_routing_to_service_thread(self):
        """Kiểm tra: Controller có khởi tạo thread để gọi service không"""
        
        with patch('threading.Thread') as MockThread:
            # Gọi hàm kích hoạt
            self.controller.trigger_bridge_backtest('DE_DYN_TEST', is_de=True)
            
            # Kiểm tra: Thread có được khởi tạo và chạy không
            MockThread.assert_called_once()
            MockThread.return_value.start.assert_called_once()
        
    def test_02_backtest_logic_accuracy(self):
        """Kiểm tra: Logic Backtest Core tính toán kết quả có đúng không"""
        
        results = self.mock_analysis_service.run_de_backtest_30_days('DE_DYN_TEST', MOCK_DATA)
        
        self.assertIsInstance(results, list, "Output phải là một danh sách (List).")
        self.assertEqual(len(results), 3, "Output phải có đúng 3 kỳ backtest.")
        
        # Kiểm tra tính chính xác của logic (Chạm GĐB-4)
        # GĐB: 89100 -> pos[4] = 0, 78234 -> pos[4] = 4, 56000 -> pos[4] = 0, 99123 -> pos[4] = 3
        # Logic: base_sum = pos[4], touches = get_touches_by_offset(base_sum, 0, "TONG")
        # 1. Dự đoán cho 2025-11-21 (Input: 2025-11-20 / GĐB-4: 0, K=0): 
        #    Touches = [0, 1, 5, 6], Dan bao gồm '00', '01', ... Kết quả thực tế: 34 (2 số cuối 78234). -> Gãy
        self.assertIn('2025-11-21', results[0]['date'] or '')
        self.assertEqual(results[0]['status'], 'Gãy') 
        self.assertEqual(results[0]['is_win'], False)
        
        # 2. Dự đoán cho 2025-11-22 (Input: 2025-11-21 / GĐB-4: 4, K=0): 
        #    Touches = [0, 4, 5, 9], Dan bao gồm '00', '04', ... Kết quả thực tế: 00 (2 số cuối 56000). -> Ăn (vì 00 có trong dan từ chạm 0)
        self.assertIn('2025-11-22', results[1]['date'] or '')
        self.assertEqual(results[1]['status'], 'Ăn')  # Sửa từ 'Gãy' thành 'Ăn' vì logic đúng
        self.assertEqual(results[1]['is_win'], True)  # Sửa từ False thành True
        
        # 3. Dự đoán cho 2025-11-23 (Input: 2025-11-22 / GĐB-4: 0, K=0): 
        #    Touches = [0, 1, 5, 6], Dan bao gồm '00', '01', ... Kết quả thực tế: 23 (2 số cuối 99123). -> Gãy
        self.assertIn('2025-11-23', results[2]['date'] or '')
        self.assertEqual(results[2]['status'], 'Gãy')

    def test_03_error_handling_invalid_bridge(self):
        """Kiểm tra: Xử lý lỗi khi cấu hình cầu không hợp lệ (GĐ 2 Fix)"""
        
        results = self.mock_analysis_service.run_de_backtest_30_days('DE_POS_INVALID', MOCK_DATA)
        
        # Output mong đợi là list có 1 item báo lỗi rõ ràng
        self.assertIsInstance(results, list, "Khi lỗi, output phải là một list thông báo.")
        self.assertGreaterEqual(len(results), 1, "List phải chứa thông báo lỗi.")
        self.assertIn('LỖI CẤU HÌNH', results[0]['date'], "Phải có thông báo lỗi cấu hình rõ ràng.")

        
if __name__ == '__main__':
    # Chạy unit test
    print("="*60)
    print("▶️ BẮT ĐẦU KIỂM TRA CHỨC NĂNG BACKTEST CẦU ĐỀ (PHASE 3)")
    print("="*60)
    
    # Tạo suite và chạy
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeBacktestFunctional)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # In kết quả cuối cùng
    print("="*60)
    if result.wasSuccessful():
        print("🎉 THÀNH CÔNG: Chức năng Backtest Cầu Đề hoạt động chính xác và ổn định.")
    else:
        print("❌ THẤT BẠI: Vẫn còn lỗi logic hoặc lỗi xử lý ngoại lệ. Cần kiểm tra lại các bước 1-3.")
    print("="*60)