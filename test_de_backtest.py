#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for De Bridge Backtest functionality
Verifies that backtest logic correctly handles multi-number predictions
"""

def test_backtest_logic():
    """Test the backtest prediction matching logic"""
    
    print("=" * 80)
    print("Testing De Backtest Logic")
    print("=" * 80)
    
    # Test cases: (prediction_string, actual_de, expected_result)
    test_cases = [
        ("2,3,7,8", "56", False, "56 ends with 6, not in [2,3,7,8]"),
        ("2,3,7,8", "52", True, "52 ends with 2, matches prediction"),
        ("2,3,7,8", "73", True, "73 ends with 3, matches prediction"),
        ("2,3,7,8", "97", True, "97 ends with 7, matches prediction"),
        ("2,3,7,8", "28", True, "28 ends with 8, matches prediction"),
        ("2,3,7,8", "11", False, "11 ends with 1, not in [2,3,7,8]"),
        ("0,1,5,6", "05", True, "05 ends with 5, matches prediction"),
        ("0,1,5,6", "10", True, "10 ends with 0, matches prediction"),
        ("5", "45", True, "45 ends with 5, matches single prediction"),
        ("5", "54", False, "54 ends with 4, not 5"),
    ]
    
    passed = 0
    failed = 0
    
    for prediction, actual_de, expected_win, description in test_cases:
        # Parse prediction
        predicted_numbers = [p.strip() for p in prediction.split(',')]
        
        # Get last digit of actual
        last_digit = actual_de[-1] if actual_de else ""
        
        # Check if win
        is_win = last_digit in predicted_numbers
        
        # Verify
        if is_win == expected_win:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status}: {description}")
        print(f"  Prediction: {prediction} → {predicted_numbers}")
        print(f"  Actual: {actual_de} → last digit: {last_digit}")
        print(f"  Expected: {'Win' if expected_win else 'Loss'}, Got: {'Win' if is_win else 'Loss'}")
        print()
    
    print("=" * 80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


def test_backtest_integration():
    """Test actual backtest function with sample data"""
    
    print("\n" + "=" * 80)
    print("Testing De Backtest Integration")
    print("=" * 80)
    
    try:
        from logic.de_backtest import get_bridge_backtest
        from services.data_service import DataService
        from logic.db_manager import DB_NAME
        
        # Load real data
        data_service = DataService(DB_NAME)
        all_data = data_service.load_data()
        
        if not all_data or len(all_data) < 30:
            print("❌ FAIL: Not enough data to test (need at least 30 rows)")
            return False
        
        print(f"✅ Loaded {len(all_data)} rows of data")
        
        # Test with a known bridge name (from user's screenshot)
        bridge_name = "DE_DYN_G1.0_G3.6.2_K1"
        
        print(f"Testing backtest for bridge: {bridge_name}")
        result = get_bridge_backtest(bridge_name, all_data, days=30)
        
        # Verify result structure
        required_keys = ['history', 'win_rate', 'total_wins', 'total_tests', 'avg_streak']
        for key in required_keys:
            if key not in result:
                print(f"❌ FAIL: Missing key '{key}' in result")
                return False
        
        print(f"✅ Result has all required keys")
        
        # Verify history
        history = result['history']
        if not history:
            print("❌ FAIL: History is empty")
            return False
        
        print(f"✅ History has {len(history)} entries")
        
        # Check first history entry
        first = history[0]
        required_hist_keys = ['date', 'predicted', 'actual', 'result']
        for key in required_hist_keys:
            if key not in first:
                print(f"❌ FAIL: Missing key '{key}' in history entry")
                return False
        
        print(f"✅ History entries have correct structure")
        
        # Verify stats
        total_tests = result['total_tests']
        total_wins = result['total_wins']
        win_rate = result['win_rate']
        
        print(f"  Total tests: {total_tests}")
        print(f"  Total wins: {total_wins}")
        print(f"  Win rate: {win_rate:.1f}%")
        
        # Verify win rate calculation
        expected_win_rate = (total_wins / total_tests * 100) if total_tests > 0 else 0
        if abs(win_rate - expected_win_rate) > 0.1:
            print(f"❌ FAIL: Win rate calculation incorrect")
            print(f"  Expected: {expected_win_rate:.1f}%, Got: {win_rate:.1f}%")
            return False
        
        print(f"✅ Win rate calculation correct")
        
        # Show sample history entries
        print("\nSample history (first 5 entries):")
        for i, entry in enumerate(history[:5], 1):
            result_icon = "✅" if entry['result'] == 'win' else "❌"
            print(f"  {i}. {entry['date']}: Pred={entry['predicted']}, Actual={entry['actual']} {result_icon}")
        
        print("\n✅ Integration test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🧪 Running De Backtest Tests\n")
    
    # Run unit tests
    logic_ok = test_backtest_logic()
    
    # Run integration test
    integration_ok = test_backtest_integration()
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Logic Tests: {'✅ PASSED' if logic_ok else '❌ FAILED'}")
    print(f"Integration Test: {'✅ PASSED' if integration_ok else '❌ FAILED'}")
    
    if logic_ok and integration_ok:
        print("\n🎉 All tests PASSED!")
        exit(0)
    else:
        print("\n❌ Some tests FAILED")
        exit(1)
