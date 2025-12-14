"""
Test suite for dual-config bridge management functionality
"""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_is_de_bridge_function_exists():
    """Test that is_de_bridge helper function exists"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    
    assert callable(is_de_bridge), "is_de_bridge should be a callable function"


def test_is_de_bridge_detects_de_bridges():
    """Test that is_de_bridge correctly identifies De bridges"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    
    # Test De bridges (should return True)
    de_bridges = [
        {'name': 'DE_SET_01', 'type': 'DE_SET'},
        {'name': 'DE_DYN_123', 'type': 'DE_DYN'},
        {'name': 'Đề Bộ 01-02-03', 'type': 'DE'},
        {'name': 'de_chot_so', 'type': 'de_normal'},
    ]
    
    for bridge in de_bridges:
        result = is_de_bridge(bridge)
        assert result is True, f"Bridge {bridge['name']} should be detected as De bridge"


def test_is_de_bridge_detects_lo_bridges():
    """Test that is_de_bridge correctly identifies Lo bridges"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    
    # Test Lo bridges (should return False)
    lo_bridges = [
        {'name': 'LO_MEM_SUM_00_01', 'type': 'LO_MEM'},
        {'name': 'Cau1_V17_Shadow', 'type': 'LO_V17'},
        {'name': 'Bac Nho 01+02', 'type': 'LO_MEM'},
        {'name': 'LO_FIXED_01', 'type': 'LO'},
    ]
    
    for bridge in lo_bridges:
        result = is_de_bridge(bridge)
        assert result is False, f"Bridge {bridge['name']} should be detected as Lo bridge"


def test_is_de_bridge_handles_missing_fields():
    """Test that is_de_bridge handles bridges with missing fields"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    
    # Test bridges with missing fields
    test_cases = [
        {},  # Empty bridge
        {'name': ''},  # Empty name
        {'type': ''},  # Empty type
        {'name': 'test'},  # No type field
        {'type': 'test'},  # No name field
    ]
    
    for bridge in test_cases:
        # Should not raise exception
        result = is_de_bridge(bridge)
        # All should default to Lo (False) since no De indicators found
        assert result is False, f"Bridge {bridge} should default to Lo (False)"


def test_prune_bad_bridges_uses_dual_config():
    """Test that prune_bad_bridges function exists and uses dual-config"""
    from logic.bridges.bridge_manager_core import prune_bad_bridges
    
    assert callable(prune_bad_bridges), "prune_bad_bridges should be a callable function"
    
    # Check function signature accepts expected parameters
    import inspect
    sig = inspect.signature(prune_bad_bridges)
    params = list(sig.parameters.keys())
    
    assert 'all_data_ai' in params, "Should have all_data_ai parameter"
    assert 'db_name' in params, "Should have db_name parameter"


def test_auto_manage_bridges_uses_dual_config():
    """Test that auto_manage_bridges function exists and uses dual-config"""
    from logic.bridges.bridge_manager_core import auto_manage_bridges
    
    assert callable(auto_manage_bridges), "auto_manage_bridges should be a callable function"
    
    # Check function signature accepts expected parameters
    import inspect
    sig = inspect.signature(auto_manage_bridges)
    params = list(sig.parameters.keys())
    
    assert 'all_data_ai' in params, "Should have all_data_ai parameter"
    assert 'db_name' in params, "Should have db_name parameter"


def test_bridge_manager_imports_settings():
    """Test that bridge_manager_core imports SETTINGS"""
    from logic.bridges import bridge_manager_core
    
    assert hasattr(bridge_manager_core, 'SETTINGS'), \
        "bridge_manager_core should import SETTINGS"


def test_prune_message_format():
    """Test that prune_bad_bridges returns properly formatted message"""
    from logic.bridges.bridge_manager_core import prune_bad_bridges
    
    # Call with empty data (should handle gracefully)
    result = prune_bad_bridges([], db_name="test.db")
    
    # Should return a string message
    assert isinstance(result, str), "prune_bad_bridges should return a string message"
    assert len(result) > 0, "Message should not be empty"


def test_auto_manage_message_format():
    """Test that auto_manage_bridges returns properly formatted message"""
    from logic.bridges.bridge_manager_core import auto_manage_bridges
    
    # Call with empty data (should handle gracefully)
    result = auto_manage_bridges([], db_name="test.db")
    
    # Should return a string message
    assert isinstance(result, str), "auto_manage_bridges should return a string message"
    assert len(result) > 0, "Message should not be empty"


def test_dual_config_integration():
    """Integration test: Verify dual-config is available in bridge manager"""
    from logic.bridges.bridge_manager_core import SETTINGS
    
    # Verify SETTINGS has dual-config
    assert hasattr(SETTINGS, 'get'), "SETTINGS should have get method"
    
    lo_config = SETTINGS.get('lo_config')
    de_config = SETTINGS.get('de_config')
    
    # Both configs should exist
    assert lo_config is not None, "lo_config should be available"
    assert de_config is not None, "de_config should be available"
    
    # Verify structure
    assert 'remove_threshold' in lo_config, "lo_config should have remove_threshold"
    assert 'add_threshold' in lo_config, "lo_config should have add_threshold"
    assert 'remove_threshold' in de_config, "de_config should have remove_threshold"
    assert 'add_threshold' in de_config, "de_config should have add_threshold"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
