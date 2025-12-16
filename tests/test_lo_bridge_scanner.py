"""
Tests for lo_bridge_scanner module (Scanning logic separated from management)
Tests the separation of concerns between scanning and management
"""

import pytest
import sys
import os

# Add project root to path (same pattern as other test files)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.bridges.lo_bridge_scanner import (
    TIM_CAU_TOT_NHAT_V16,
    TIM_CAU_BAC_NHO_TOT_NHAT,
    update_fixed_lo_bridges,
    _sanitize_name_v2,
    _ensure_core_db_columns,
    _get_existing_bridges_map,
    LO_BRIDGE_MAP,
)
from logic.bridges.bridge_manager_core import (
    find_and_auto_manage_bridges,
    prune_bad_bridges,
    auto_manage_bridges,
    init_all_756_memory_bridges_to_db,
)


def test_scanner_module_imports():
    """Test that all scanning functions can be imported from lo_bridge_scanner"""
    # Verify all functions are callable (already imported at module level)
    assert callable(TIM_CAU_TOT_NHAT_V16)
    assert callable(TIM_CAU_BAC_NHO_TOT_NHAT)
    assert callable(update_fixed_lo_bridges)
    assert callable(_sanitize_name_v2)
    assert callable(_ensure_core_db_columns)
    assert callable(_get_existing_bridges_map)


def test_manager_module_imports():
    """Test that management functions are in bridge_manager_core"""
    # Verify all functions are callable (already imported at module level)
    assert callable(find_and_auto_manage_bridges)
    assert callable(prune_bad_bridges)
    assert callable(auto_manage_bridges)
    assert callable(init_all_756_memory_bridges_to_db)


def test_manager_can_call_scanner_functions():
    """Test that manager module can call scanner functions (via import)"""
    # Import the re-exported functions from manager
    from logic.bridges.bridge_manager_core import (
        TIM_CAU_TOT_NHAT_V16 as mgr_v16,
        TIM_CAU_BAC_NHO_TOT_NHAT as mgr_bn,
        update_fixed_lo_bridges as mgr_fixed,
    )
    
    # Verify the re-exported functions are callable
    assert callable(mgr_v16)
    assert callable(mgr_bn)
    assert callable(mgr_fixed)


def test_sanitize_name_helper():
    """Test the _sanitize_name_v2 helper function"""
    # Test various special characters
    assert _sanitize_name_v2("test[1]") == "test_1"
    assert _sanitize_name_v2("test(foo)") == "test_foo"
    assert _sanitize_name_v2("test.bar") == "test_bar"
    assert _sanitize_name_v2("test+foo") == "test_foo"
    assert _sanitize_name_v2("test foo") == "testfoo"
    assert _sanitize_name_v2("test[1](2).3+4 5") == "test_1_2_3_45"  # space is removed, not replaced


def test_get_existing_bridges_map():
    """Test that _get_existing_bridges_map returns proper dict structure"""
    # Should return a dict (empty or populated depending on DB state)
    result = _get_existing_bridges_map("data/xo_so_prizes_all_logic.db")
    assert isinstance(result, dict)
    # Each value should be a string (win_rate_text)
    for key, value in result.items():
        assert isinstance(key, str)
        assert isinstance(value, (str, type(None)))


def test_separation_of_concerns():
    """Test that scanning and management are properly separated"""
    import logic.bridges.lo_bridge_scanner as scanner_mod
    import logic.bridges.bridge_manager_core as manager_mod
    
    # Scanning functions should be in scanner module
    assert hasattr(scanner_mod, 'TIM_CAU_TOT_NHAT_V16')
    assert hasattr(scanner_mod, 'TIM_CAU_BAC_NHO_TOT_NHAT')
    assert hasattr(scanner_mod, 'update_fixed_lo_bridges')
    
    # Management functions should be in manager module
    assert hasattr(manager_mod, 'prune_bad_bridges')
    assert hasattr(manager_mod, 'auto_manage_bridges')
    assert hasattr(manager_mod, 'init_all_756_memory_bridges_to_db')
    
    # Manager should import scanner functions
    assert hasattr(manager_mod, 'TIM_CAU_TOT_NHAT_V16')
    assert hasattr(manager_mod, 'TIM_CAU_BAC_NHO_TOT_NHAT')


def test_lo_bridge_map_available():
    """Test that LO_BRIDGE_MAP constant is available in scanner"""
    assert isinstance(LO_BRIDGE_MAP, dict)
    assert len(LO_BRIDGE_MAP) == 15  # Should have 15 fixed bridges
    
    # Check structure of each entry
    for bridge_id, info in LO_BRIDGE_MAP.items():
        assert "func" in info
        assert "desc" in info
        assert callable(info["func"])
        assert isinstance(info["desc"], str)


def test_backward_compatibility_lottery_service():
    """Test that lottery_service can still import all required functions"""
    # Already imported at module level, just verify they exist
    assert callable(TIM_CAU_BAC_NHO_TOT_NHAT)
    assert callable(TIM_CAU_TOT_NHAT_V16)
    assert callable(update_fixed_lo_bridges)
    assert callable(auto_manage_bridges)
    assert callable(find_and_auto_manage_bridges)
    assert callable(prune_bad_bridges)


def test_functions_have_docstrings():
    """Test that key functions have proper documentation"""
    # Check that functions have docstrings (already imported at module level)
    assert TIM_CAU_TOT_NHAT_V16.__doc__ is not None
    assert TIM_CAU_BAC_NHO_TOT_NHAT.__doc__ is not None
    assert update_fixed_lo_bridges.__doc__ is not None
    assert find_and_auto_manage_bridges.__doc__ is not None
    assert prune_bad_bridges.__doc__ is not None
    assert auto_manage_bridges.__doc__ is not None
    assert init_all_756_memory_bridges_to_db.__doc__ is not None
