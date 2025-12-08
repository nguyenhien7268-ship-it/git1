# Tên file: tests/test_v11_bridge_filtering.py
# Test cho V11.0 Bridge Filtering & Approval Workflow

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.bridges.de_bridge_scanner import DeBridgeScanner


def test_quality_filters():
    """Test bộ lọc chất lượng"""
    scanner = DeBridgeScanner()
    
    # Mock data
    bridges = [
        # DE_KILLER - phải bị loại
        {
            "name": "DE_KILLER_G1_G2",
            "type": "DE_KILLER",
            "streak": 15,
            "win_rate": 0,
            "predicted_value": "LOẠI CHẠM 5"
        },
        # DE_DYN với tỷ lệ cao (>= 28/30) - giữ lại
        {
            "name": "DE_DYN_G1_G2_K3",
            "type": "DE_DYNAMIC_K",
            "streak": 28,
            "win_rate": 93.3,
            "predicted_value": "3,4,5"
        },
        # DE_DYN với tỷ lệ thấp (< 28/30) - loại bỏ
        {
            "name": "DE_DYN_G3_G4_K2",
            "type": "DE_DYNAMIC_K",
            "streak": 25,
            "win_rate": 83.3,
            "predicted_value": "1,2,3"
        },
        # DE_SET - giữ lại (không filter)
        {
            "name": "DE_SET_G1_G2",
            "type": "DE_SET",
            "streak": 15,
            "win_rate": 50.0,
            "predicted_value": "Bộ 00"
        },
        # DE_MEMORY - giữ lại (không filter)
        {
            "name": "DE_MEMORY_PATTERN",
            "type": "DE_MEMORY",
            "streak": 10,
            "win_rate": 70.0,
            "predicted_value": "3"
        },
        # DE_PASCAL - giữ lại (không filter)
        {
            "name": "DE_PASCAL_1",
            "type": "DE_PASCAL",
            "streak": 5,
            "win_rate": 60.0,
            "predicted_value": "7,8"
        },
        # DE_DYN với đúng 28 streak - phải giữ lại (boundary case)
        {
            "name": "DE_DYN_GDB_G1_K1",
            "type": "DE_DYNAMIC_K",
            "streak": 28,
            "win_rate": 93.3,
            "predicted_value": "0,1"
        },
    ]
    
    # Apply filters
    filtered = scanner._apply_quality_filters(bridges)
    
    # Assertions
    print("\n=== TEST QUALITY FILTERS ===")
    print(f"Input: {len(bridges)} bridges")
    print(f"Output: {len(filtered)} bridges")
    
    # Check DE_KILLER is removed
    killer_count = sum(1 for b in filtered if b['type'] == 'DE_KILLER')
    assert killer_count == 0, "DE_KILLER should be completely removed"
    print("✓ DE_KILLER bridges removed")
    
    # Check DE_DYN filtering
    dyn_bridges = [b for b in filtered if b['type'] == 'DE_DYNAMIC_K']
    for b in dyn_bridges:
        assert b['streak'] >= 28, f"DE_DYN {b['name']} has streak {b['streak']} < 28"
    print(f"✓ DE_DYN bridges filtered correctly ({len(dyn_bridges)} kept)")
    
    # Check other types are kept
    set_count = sum(1 for b in filtered if b['type'] == 'DE_SET')
    memory_count = sum(1 for b in filtered if b['type'] == 'DE_MEMORY')
    pascal_count = sum(1 for b in filtered if b['type'] == 'DE_PASCAL')
    
    assert set_count == 1, "DE_SET should be kept"
    assert memory_count == 1, "DE_MEMORY should be kept"
    assert pascal_count == 1, "DE_PASCAL should be kept"
    print("✓ Other bridge types kept correctly")
    
    # Expected results
    expected_filtered = 5  # 2 DE_DYN (28+ streak) + 1 SET + 1 MEMORY + 1 PASCAL
    assert len(filtered) == expected_filtered, f"Expected {expected_filtered} bridges, got {len(filtered)}"
    print(f"✓ Total filtered bridges: {len(filtered)} (expected {expected_filtered})")
    
    print("\n=== ALL TESTS PASSED ===\n")
    return True


def test_auto_save_flag():
    """Test scan_all với auto_save flag"""
    print("\n=== TEST AUTO_SAVE FLAG ===")
    
    # Create scanner
    scanner = DeBridgeScanner()
    
    # Mock small data (insufficient for real scan)
    mock_data = [
        ["1", "01/01/2024", "12", "123", "45678", "901234", "567890", "1234", "56789", "01234"]
        for _ in range(5)
    ]
    
    # Test auto_save=False (default)
    count1, bridges1 = scanner.scan_all(mock_data, auto_save=False)
    print(f"✓ scan_all(auto_save=False) returned {count1} bridges")
    
    # Test auto_save=True
    count2, bridges2 = scanner.scan_all(mock_data, auto_save=True)
    print(f"✓ scan_all(auto_save=True) returned {count2} bridges")
    
    # Both should return 0 due to insufficient data
    assert count1 == 0 and count2 == 0, "Should return 0 for insufficient data"
    print("✓ Insufficient data handled correctly")
    
    print("\n=== AUTO_SAVE FLAG TEST PASSED ===\n")
    return True


if __name__ == "__main__":
    try:
        test_quality_filters()
        test_auto_save_flag()
        print("\n" + "="*50)
        print("ALL V11.0 TESTS PASSED SUCCESSFULLY")
        print("="*50 + "\n")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
