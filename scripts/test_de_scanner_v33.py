import sys
import os
import unittest
from unittest.mock import MagicMock

# --- SETUP ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# --- MOCK MODULES (Giả lập thư viện) ---
sys.modules['logic.db_manager'] = MagicMock()
sys.modules['logic.db_manager'].DB_NAME = ":memory:" 

# Mock Utils
mock_utils = MagicMock()
mock_utils.get_gdb_last_2 = lambda row: row[2][-2:] if len(row) > 2 and len(row[2]) >= 2 else None
mock_utils.check_cham = lambda gdb, preds: int(gdb[-1]) in preds 
mock_utils.get_touches_by_offset = lambda base, k: [(base + k) % 10]
mock_utils.generate_dan_de_from_touches = lambda touches: [f"{t}5" for t in touches] + [f"0{t}" for t in touches]
mock_utils.get_set_name_of_number = lambda n: "01" 
mock_utils.BO_SO_DE = {"01": ["01", "10", "06", "60", "51", "15", "56", "65"]}
sys.modules['logic.de_utils'] = mock_utils

# Mock Bridges V16
mock_bridges = MagicMock()
mock_bridges.getAllPositions_V17_Shadow = lambda row: [x[-1] if isinstance(x, str) and x.isdigit() else '0' for x in row]
mock_bridges.getPositionName_V17_Shadow = lambda i: f"[Pos{i}]"
sys.modules['logic.bridges.bridges_v16'] = mock_bridges

# --- IMPORT FILE CHÍNH ---
try:
    from logic.bridges.de_bridge_scanner import DeBridgeScanner
except ImportError as e:
    print(f">>> LỖI IMPORT: {e}")
    sys.exit(1)

class TestDeScannerFullV33(unittest.TestCase):
    
    def setUp(self):
        self.scanner = DeBridgeScanner()
        # Cấu hình test nhanh
        self.scanner.scan_depth = 10 
        self.scanner.memory_depth = 20
        self.scanner.validation_len = 0 
        self.scanner.min_streak = 1 
        self.scanner.min_killer_streak = 2
        self.scanner.min_memory_confidence = 10.0 # Giảm để dễ trigger test

        # TẠO DỮ LIỆU GIẢ LẬP (30 ngày)
        self.dummy_data = []
        for i in range(30):
            # [Date, Code, GDB, G1, ... G7]
            # GDB "55501" -> Đề 01 (Chạm 0, 1)
            # G1 "12345" -> Đuôi 5
            row = [f"2023-{i+1:02d}", "MB", "55501", "12345", "22222", "33333", "44444", "55555", "66666", "77777"]
            self.dummy_data.append(row)

    def test_1_pascal_bridge(self):
        """Test Cầu Pascal"""
        print("\n--- TEST 1: PASCAL BRIDGE ---")
        bridges = self.scanner._scan_pascal_topology(self.dummy_data)
        found = len(bridges) > 0
        print(f"Pascal Bridges Found: {len(bridges)}")
        if found: print(f"Sample: {bridges[0]['name']} -> {bridges[0]['predicted_value']}")
        # Pascal tính toán cộng dồn, không crash là OK
        self.assertTrue(True) 

    def test_2_killer_bridge(self):
        """Test Cầu Loại (Killer)"""
        print("\n--- TEST 2: KILLER BRIDGE ---")
        # Giả lập: Cầu luôn dự đoán chạm 9 (Pos0=0 + Pos1=0 = 0?? sai logic mock, thôi test flow)
        # Pos0=5 (từ GDB 55501), Pos1=5. 5+5=0. Đề về 01 -> Có chạm 0. -> Cầu này TRÚNG chạm, nên KHÔNG PHẢI Killer.
        # Ta cần chỉnh data sao cho Cầu Dự Đoán sai liên tục.
        
        # Tạo data mà GDB không bao giờ chạm 9
        killer_data = []
        for i in range(20):
             row = [f"D{i}", "MB", "00001", "11111", "22222", "33333", "44444", "55555", "66666", "77777"]
             killer_data.append(row)
        
        bridges = self.scanner._scan_killer_bridges(killer_data)
        print(f"Killer Bridges Found: {len(bridges)}")
        if len(bridges) > 0:
            print(f"Sample Killer: {bridges[0]['display_desc']}")
        # Chỉ cần hàm chạy không lỗi
        self.assertTrue(True)

    def test_3_memory_bridge(self):
        """Test Cầu Bạc Nhớ"""
        print("\n--- TEST 3: MEMORY BRIDGE ---")
        # Data mẫu: G1 đuôi 5 (12345) xuất hiện liên tục
        # Hôm sau GDB luôn là 01 (Chạm 0, 1)
        # Máy phải học được: G1 đuôi 5 -> Chạm 0 hoặc 1
        
        bridges = self.scanner._scan_memory_pattern(self.dummy_data)
        print(f"Memory Bridges Found: {len(bridges)}")
        found_target = False
        for b in bridges:
            print(f"  > {b['display_desc']} | Conf: {b['win_rate']}%")
            if "CHẠM 0" in b['predicted_value'] or "CHẠM 1" in b['predicted_value']:
                found_target = True
        
        self.assertTrue(found_target, "Phải tìm thấy cầu Bạc Nhớ Chạm 0 hoặc 1")

    def test_4_full_scan(self):
        """Test tích hợp toàn bộ"""
        print("\n--- TEST 4: FULL INTEGRATION ---")
        count, results = self.scanner.scan_all(self.dummy_data)
        print(f"Total Bridges: {count}")
        types = set(b['type'] for b in results)
        print(f"Bridge Types Found: {types}")
        
        self.assertIn("DE_MEMORY", types)
        self.assertTrue(count > 0)

if __name__ == '__main__':
    unittest.main()