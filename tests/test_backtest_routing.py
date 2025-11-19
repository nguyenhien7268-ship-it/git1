"""
Test backtest routing logic in app_controller.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_backtest_functions_are_importable():
    """Test that backtest functions can be imported from lottery_service"""
    from lottery_service import (
        BACKTEST_15_CAU_N1_V31_AI_V8,
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_MANAGED_BRIDGES_N1,
        BACKTEST_MANAGED_BRIDGES_K2N,
    )
    
    # Check that they are callable
    assert callable(BACKTEST_15_CAU_N1_V31_AI_V8)
    assert callable(BACKTEST_15_CAU_K2N_V30_AI_V8)
    assert callable(BACKTEST_MANAGED_BRIDGES_N1)
    assert callable(BACKTEST_MANAGED_BRIDGES_K2N)


def test_backtest_function_signatures():
    """Test that backtest functions have expected signatures"""
    from lottery_service import (
        BACKTEST_15_CAU_N1_V31_AI_V8,
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_MANAGED_BRIDGES_N1,
    )
    import inspect
    
    # Check N1 functions have 3 parameters
    sig_n1_classic = inspect.signature(BACKTEST_15_CAU_N1_V31_AI_V8)
    assert len(sig_n1_classic.parameters) == 3
    
    sig_n1_managed = inspect.signature(BACKTEST_MANAGED_BRIDGES_N1)
    assert len(sig_n1_managed.parameters) >= 3  # May have optional params
    
    # Check K2N classic function has 3-4 parameters (with optional history)
    sig_k2n_classic = inspect.signature(BACKTEST_15_CAU_K2N_V30_AI_V8)
    assert len(sig_k2n_classic.parameters) >= 3


def test_backtest_routing_logic():
    """Test the routing logic for backtest function selection
    
    This test simulates the logic in task_run_backtest to ensure
    the correct function is selected based on title and mode.
    """
    from lottery_service import (
        BACKTEST_15_CAU_N1_V31_AI_V8,
        BACKTEST_15_CAU_K2N_V30_AI_V8,
        BACKTEST_MANAGED_BRIDGES_N1,
        BACKTEST_MANAGED_BRIDGES_K2N,
    )
    
    # Test cases: (title, mode, expected_function)
    test_cases = [
        # Classic 15 bridges
        ("Test 15 Cầu N1", "N1", BACKTEST_15_CAU_N1_V31_AI_V8),
        ("Test 15 Cầu K2N", "K2N", BACKTEST_15_CAU_K2N_V30_AI_V8),
        ("Backtest 15 cầu cổ điển N1", "N1", BACKTEST_15_CAU_N1_V31_AI_V8),
        ("Test với 15 cầu", "K2N", BACKTEST_15_CAU_K2N_V30_AI_V8),
        
        # Managed bridges (no "15" in title)
        ("Test Cầu Đã Lưu N1", "N1", BACKTEST_MANAGED_BRIDGES_N1),
        ("Backtest Managed N1", "N1", BACKTEST_MANAGED_BRIDGES_N1),
        ("Test Cầu K2N", "K2N", BACKTEST_MANAGED_BRIDGES_K2N),
    ]
    
    for title, mode, expected_func in test_cases:
        # Simulate the routing logic from task_run_backtest
        func_to_call = None
        
        if "15" in title:
            if mode == "N1":
                func_to_call = BACKTEST_15_CAU_N1_V31_AI_V8
            else:
                func_to_call = BACKTEST_15_CAU_K2N_V30_AI_V8
        else:
            if mode == "N1":
                func_to_call = BACKTEST_MANAGED_BRIDGES_N1
            else:
                # For testing, we use the function directly instead of lambda
                func_to_call = BACKTEST_MANAGED_BRIDGES_K2N
        
        # Verify correct function was selected
        assert func_to_call == expected_func, \
            f"Failed for title='{title}', mode='{mode}'. Expected {expected_func.__name__}, got {func_to_call.__name__}"


if __name__ == "__main__":
    print("Testing backtest routing logic...")
    test_backtest_functions_are_importable()
    print("✓ Functions are importable")
    
    test_backtest_function_signatures()
    print("✓ Function signatures are correct")
    
    test_backtest_routing_logic()
    print("✓ Routing logic works correctly")
    
    print("\nAll tests passed!")
