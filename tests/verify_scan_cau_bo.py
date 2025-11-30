"""
Script Test: Verify Scan Cầu Bộ (Set Bridges)
Mục đích: Kiểm tra xem hàm quét cầu Bộ có hoạt động đúng không
"""

import sys
import os

# Thêm thư mục gốc vào path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.bridges.de_bridge_scanner import DeBridgeScanner, run_de_scanner
from logic.de_utils import get_set_name_of_number, BO_SO_DE
from logic.db_manager import DB_NAME
import sqlite3

def test_get_set_name_of_number():
    """Test hàm get_set_name_of_number"""
    print("\n=== TEST 1: get_set_name_of_number ===")
    test_cases = [
        ("05", "00"),  # Thuộc Bộ 00
        ("50", "00"),  # Thuộc Bộ 00
        ("55", "00"),  # Thuộc Bộ 00
        ("01", "01"),  # Thuộc Bộ 01
        ("12", "12"),  # Thuộc Bộ 12
        ("99", None),  # Không thuộc bộ nào (sẽ trả về None)
    ]
    
    for number_str, expected in test_cases:
        result = get_set_name_of_number(number_str)
        status = "✓" if result == expected else "✗"
        print(f"{status} {number_str} -> {result} (expected: {expected})")
        if result != expected:
            print(f"  ⚠️  Lỗi: Kỳ vọng {expected} nhưng nhận được {result}")

def test_scan_set_bridges():
    """Test hàm _scan_set_bridges với dữ liệu mẫu"""
    print("\n=== TEST 2: _scan_set_bridges ===")
    
    # Tạo dữ liệu mẫu (giả lập)
    # Format: [date, gdb_full, g1, g2, ...]
    sample_data = []
    for i in range(35):  # Tạo 35 ngày dữ liệu
        # Giả lập: GDB có 2 số cuối là 05, 50, 55, 00 (thuộc Bộ 00)
        # Vị trí 0 = 0, vị trí 1 = 5 -> ghép thành "05" -> Bộ 00
        gdb_tail = ["05", "50", "55", "00", "01"][i % 5]
        gdb_full = f"12345{gdb_tail}"
        row = [f"2024-01-{i+1:02d}", gdb_full, "12345", "12345,67890"]
        sample_data.append(row)
    
    scanner = DeBridgeScanner()
    scanner.min_streak = 2  # Giảm min_streak để dễ test
    
    try:
        bridges = scanner._scan_set_bridges(sample_data)
        print(f"✓ Tìm thấy {len(bridges)} cầu Bộ")
        for i, b in enumerate(bridges[:5]):  # Chỉ hiển thị 5 cầu đầu
            print(f"  {i+1}. {b['name']}: streak={b['streak']}, predicted={b['predicted_value']}, type={b['type']}")
        
        if len(bridges) == 0:
            print("  ⚠️  Cảnh báo: Không tìm thấy cầu nào. Có thể:")
            print("     - min_streak quá cao")
            print("     - Dữ liệu mẫu không đủ pattern")
            print("     - Logic ghép số có vấn đề")
    except Exception as e:
        print(f"✗ Lỗi khi quét: {e}")
        import traceback
        traceback.print_exc()

def test_run_de_scanner_integration():
    """Test tích hợp với run_de_scanner"""
    print("\n=== TEST 3: run_de_scanner Integration ===")
    
    # Load dữ liệu thật từ DB nếu có
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM LotteryData ORDER BY date DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        
        if rows and len(rows) >= 30:
            # Convert sang format all_data_ai
            all_data_ai = [list(row) for row in reversed(rows)]  # Đảo ngược để cũ nhất ở đầu
            
            count, bridges = run_de_scanner(all_data_ai)
            print(f"✓ run_de_scanner trả về: {count} cầu")
            
            # Đếm số cầu Bộ
            bo_bridges = [b for b in bridges if b.get('type') == 'BO']
            print(f"✓ Số cầu Bộ (type='BO'): {len(bo_bridges)}")
            
            if bo_bridges:
                print("\n  Top 5 cầu Bộ:")
                for i, b in enumerate(bo_bridges[:5]):
                    print(f"    {i+1}. {b['name']}: streak={b['streak']}, predicted={b['predicted_value']}")
            else:
                print("  ⚠️  Không tìm thấy cầu Bộ nào trong kết quả!")
                print("  Hãy kiểm tra:")
                print("    - Logic quét có chạy đúng không")
                print("    - Điều kiện min_streak có quá cao không")
                print("    - Dữ liệu có đủ để tìm pattern không")
        else:
            print("⚠️  Không đủ dữ liệu trong DB (cần ít nhất 30 kỳ)")
    except Exception as e:
        print(f"✗ Lỗi khi load dữ liệu từ DB: {e}")
        import traceback
        traceback.print_exc()

def test_db_save():
    """Test xem cầu Bộ có được lưu vào DB không"""
    print("\n=== TEST 4: Database Save ===")
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Kiểm tra xem có cầu type='BO' trong DB không
        cursor.execute("SELECT COUNT(*) FROM ManagedBridges WHERE type = 'BO'")
        count = cursor.fetchone()[0]
        print(f"✓ Số cầu Bộ trong DB: {count}")
        
        if count > 0:
            cursor.execute("SELECT name, type, current_streak, next_prediction_stl FROM ManagedBridges WHERE type = 'BO' LIMIT 5")
            rows = cursor.fetchall()
            print("\n  Top 5 cầu Bộ trong DB:")
            for row in rows:
                print(f"    - {row[0]}: streak={row[2]}, predicted={row[3]}")
        else:
            print("  ⚠️  Không có cầu Bộ nào trong DB!")
            print("  Có thể:")
            print("    - Chưa chạy quét cầu")
            print("    - Cầu Bộ không đạt điều kiện lưu")
            print("    - Có lỗi khi lưu vào DB")
        
        conn.close()
    except Exception as e:
        print(f"✗ Lỗi khi kiểm tra DB: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("SCRIPT TEST: VERIFY SCAN CẦU BỘ (SET BRIDGES)")
    print("=" * 60)
    
    # Test 1: Hàm helper
    test_get_set_name_of_number()
    
    # Test 2: Hàm quét với dữ liệu mẫu
    test_scan_set_bridges()
    
    # Test 3: Tích hợp với run_de_scanner
    test_run_de_scanner_integration()
    
    # Test 4: Kiểm tra DB
    test_db_save()
    
    print("\n" + "=" * 60)
    print("HOÀN TẤT TEST")
    print("=" * 60)
