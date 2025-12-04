# Tên file: test_de_scanner.py
import sys
import unittest
from unittest.mock import MagicMock

# --- 1. MOCK (Giả lập) Các thư viện phụ thuộc ---
# Vì chúng ta đang test độc lập, cần giả lập các hàm logic/db bên ngoài
sys.modules['logic.db_manager'] = MagicMock()
sys.modules['logic.db_manager'].DB_NAME = ":memory:" # Dùng RAM DB để test

# Mock logic utils
mock_utils = MagicMock()
mock_utils.get_gdb_last_2 = lambda row: row[2][-2:] if len(row) > 2 and len(row[2]) >= 2 else None
mock_utils.check_cham = lambda gdb, preds: int(gdb[-1]) in preds # Mock đơn giản: Trúng chạm nếu số cuối khớp
mock_utils.get_touches_by_offset = lambda base, k: [(base + k) % 10]
mock_utils.generate_dan_de_from_touches = lambda touches: [f"{t}5" for t in touches] + [f"0{t}" for t in touches] # Dummy dàn
mock_utils.get_set_name_of_number = lambda n: "01" # Luôn trả về bộ 01
mock_utils.BO_SO_DE = {"01": ["01", "10", "06", "60", "51", "15", "56", "65"]}

sys.modules['logic.de_utils'] = mock_utils

# Mock bridges_v16
mock_bridges = MagicMock()
# Giả lập trả về mảng các con số từ dòng dữ liệu
mock_bridges.getAllPositions_V17_Shadow = lambda row: [x[-1] if isinstance(x, str) and x.isdigit() else '0' for x in row]
mock_bridges.getPositionName_V17_Shadow = lambda i: f"[Pos{i}]"
sys.modules['logic.bridges.bridges_v16'] = mock_bridges

# --- 2. IMPORT FILE V3 VỪA VIẾT ---
# Đảm bảo file logic/bridges/de_bridge_scanner_v3.py đã tồn tại
from logic.bridges.de_bridge_scanner_v3 import DeBridgeScannerV3

# --- 3. CLASS TEST CASE ---
class TestDeBridgeScannerV3(unittest.TestCase):
    
    def setUp(self):
        self.scanner = DeBridgeScannerV3()
        self.scanner.scan_depth = 5 # Giảm depth để test nhanh
        self.scanner.validation_len = 0 # Tắt validation để dễ trigger win
        self.scanner.min_streak = 1 # Dễ tính streak
        
        # Tạo dữ liệu giả lập (30 ngày, 10 cột)
        # Cấu trúc: [Date, Code, GDB, G1, ... G7]
        # Giả sử GDB luôn là "55501" (Đề 01) để test Cầu Bộ dễ trúng
        self.dummy_data = []
        for i in range(30):
            row = [f"2023-12-{i+1:02d}", "MB", "55501", "11111", "22222", "33333", "44444", "55555", "66666", "77777"]
            self.dummy_data.append(row)

    def test_input_validation(self):
        """Test xem scanner có xử lý dữ liệu rỗng không"""
        count, res = self.scanner.scan_all([])
        self.assertEqual(count, 0)
        print("\n[PASS] Input Validation OK")

    def test_scan_set_bridges(self):
        """Test logic quét cầu Bộ (Mock trả về bộ 01, GDB là 01 -> Phải Win)"""
        # GDB dummy là 01, Bộ giả lập là 01 -> Luôn trúng
        bridges = self.scanner._scan_set_bridges(self.dummy_data)
        self.assertTrue(len(bridges) > 0)
        print(f"\n[PASS] Scan Set Bridges: Found {len(bridges)} bridges")
        print(f"Sample: {bridges[0]['name']} - Streak: {bridges[0]['streak']}")

    def test_ranking_score(self):
        """Test công thức tính điểm"""
        # Streak 3, Wins10=5, Type=SET (Bonus 2.0)
        # Score = 3*1.5 + 5*1.0 + 2.0 = 4.5 + 5 + 2 = 11.5
        score = self.scanner._calculate_ranking_score(3, 5, 'DE_SET')
        self.assertEqual(score, 11.5)
        print(f"\n[PASS] Ranking Score Logic OK (Score: {score})")

if __name__ == '__main__':
    unittest.main()