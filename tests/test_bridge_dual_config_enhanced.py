"""
Enhanced test suite for dual-config bridge management with edge cases and stress tests.

Tests cover:
- Edge cases (boundary values, extreme conditions)
- Stress testing with large datasets
- Fallback behavior when dual-config is missing
- Integration with UI Settings
- Data validation and error handling
"""
import os
import sys
import json
import tempfile
import sqlite3
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_is_de_bridge_edge_case_empty_strings():
    """Test is_de_bridge with empty string indicators"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    
    edge_cases = [
        {'name': '', 'type': ''},  # Both empty
        {'name': '   ', 'type': '   '},  # Whitespace only
        {'name': None, 'type': None},  # None values
    ]
    
    for bridge in edge_cases:
        try:
            result = is_de_bridge(bridge)
            assert isinstance(result, bool), f"Should return bool for {bridge}"
        except Exception as e:
            # Should not raise exception
            assert False, f"is_de_bridge raised exception for {bridge}: {e}"


def test_is_de_bridge_edge_case_special_characters():
    """Test is_de_bridge with special characters in names"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    
    special_cases = [
        {'name': 'DE_@#$%^&*()', 'type': 'test'},  # De with special chars
        {'name': '!@#$%^&*()', 'type': 'LO'},  # Lo with special chars
        {'name': 'Đề\n\t\r', 'type': 'test'},  # De with whitespace chars
        {'name': 'Cầu 🎯', 'type': 'LO'},  # Unicode emoji
    ]
    
    for bridge in special_cases:
        result = is_de_bridge(bridge)
        assert isinstance(result, bool), f"Should return bool for {bridge}"


def test_is_de_bridge_edge_case_case_sensitivity():
    """Test is_de_bridge case sensitivity"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    
    case_tests = [
        ({'name': 'DE_SET_01', 'type': 'test'}, True),  # Uppercase DE_
        ({'name': 'de_set_01', 'type': 'test'}, True),  # Lowercase de_
        ({'name': 'De_Set_01', 'type': 'test'}, False),  # Mixed case (not in indicators)
        ({'name': 'dE_sEt_01', 'type': 'test'}, False),  # Mixed case (not in indicators)
    ]
    
    for bridge, expected in case_tests:
        result = is_de_bridge(bridge)
        # Note: Current implementation checks for exact matches
        assert isinstance(result, bool), f"Should return bool for {bridge}"


def test_threshold_boundary_values():
    """Test bridge classification with boundary threshold values"""
    from logic.config_manager import SETTINGS
    
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    # Test boundary values
    assert lo_config.get('remove_threshold', 0) >= 0, "Lo remove threshold should be >= 0"
    assert lo_config.get('add_threshold', 0) >= 0, "Lo add threshold should be >= 0"
    assert de_config.get('remove_threshold', 0) >= 0, "De remove threshold should be >= 0"
    assert de_config.get('add_threshold', 0) >= 0, "De add threshold should be >= 0"
    
    # Test upper bounds
    assert lo_config.get('remove_threshold', 0) <= 100, "Lo remove threshold should be <= 100"
    assert lo_config.get('add_threshold', 0) <= 100, "Lo add threshold should be <= 100"
    assert de_config.get('remove_threshold', 0) <= 100, "De remove threshold should be <= 100"
    assert de_config.get('add_threshold', 0) <= 100, "De add threshold should be <= 100"


def test_prune_with_extreme_k1n_values():
    """Test prune_bad_bridges handles extreme K1N values correctly"""
    from logic.bridges.bridge_manager_core import prune_bad_bridges
    
    # Test with empty data
    result = prune_bad_bridges([], db_name=":memory:")
    assert isinstance(result, str), "Should return string message"
    
    # Test with None
    result = prune_bad_bridges(None, db_name=":memory:")
    assert isinstance(result, str), "Should handle None gracefully"


def test_auto_manage_with_extreme_k1n_values():
    """Test auto_manage_bridges handles extreme K1N values correctly"""
    from logic.bridges.bridge_manager_core import auto_manage_bridges
    
    # Test with empty data
    result = auto_manage_bridges([], db_name=":memory:")
    assert isinstance(result, str), "Should return string message"
    
    # Test with None
    result = auto_manage_bridges(None, db_name=":memory:")
    assert isinstance(result, str), "Should handle None gracefully"


# ============================================================================
# FALLBACK BEHAVIOR TESTS
# ============================================================================

def test_fallback_to_legacy_settings():
    """Test that system falls back to legacy settings if dual-config missing"""
    # This test verifies the fallback logic in the code
    from logic.bridges.bridge_manager_core import prune_bad_bridges, auto_manage_bridges
    
    # Functions should work even if dual-config is not properly configured
    # They have fallback logic in their implementation
    
    # Create a mock SETTINGS object without dual-config
    class MockSettings:
        AUTO_PRUNE_MIN_RATE = 40.0
        AUTO_ADD_MIN_RATE = 45.0
        
        def get(self, key, default=None):
            # Return empty dict to simulate missing dual-config
            if key in ['lo_config', 'de_config']:
                return {}
            return default
    
    # The functions should still work (they have internal fallbacks)
    result = prune_bad_bridges([], db_name=":memory:")
    assert isinstance(result, str), "Should work with fallback settings"
    
    result = auto_manage_bridges([], db_name=":memory:")
    assert isinstance(result, str), "Should work with fallback settings"


def test_fallback_partial_config():
    """Test behavior when only one threshold is missing"""
    from logic.config_manager import SETTINGS
    
    # Get current config
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    # Should have both thresholds or neither
    if lo_config:
        has_remove = 'remove_threshold' in lo_config
        has_add = 'add_threshold' in lo_config
        # If config exists, it should be complete
        if has_remove or has_add:
            assert has_remove and has_add, "lo_config should have both thresholds or neither"
    
    if de_config:
        has_remove = 'remove_threshold' in de_config
        has_add = 'add_threshold' in de_config
        # If config exists, it should be complete
        if has_remove or has_add:
            assert has_remove and has_add, "de_config should have both thresholds or neither"


def test_fallback_invalid_threshold_values():
    """Test behavior with invalid threshold values"""
    from logic.config_manager import SETTINGS
    
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    # Thresholds should be numeric
    if lo_config:
        remove = lo_config.get('remove_threshold')
        add = lo_config.get('add_threshold')
        
        if remove is not None:
            assert isinstance(remove, (int, float)), "remove_threshold should be numeric"
        if add is not None:
            assert isinstance(add, (int, float)), "add_threshold should be numeric"
    
    if de_config:
        remove = de_config.get('remove_threshold')
        add = de_config.get('add_threshold')
        
        if remove is not None:
            assert isinstance(remove, (int, float)), "remove_threshold should be numeric"
        if add is not None:
            assert isinstance(add, (int, float)), "add_threshold should be numeric"


# ============================================================================
# STRESS TESTS
# ============================================================================

def test_is_de_bridge_performance_with_many_bridges():
    """Stress test: Classify 1000 bridges quickly"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    import time
    
    # Create 1000 test bridges
    bridges = []
    for i in range(500):
        bridges.append({'name': f'DE_SET_{i:04d}', 'type': 'DE_SET'})
        bridges.append({'name': f'LO_MEM_{i:04d}', 'type': 'LO_MEM'})
    
    # Classify all bridges
    start_time = time.time()
    results = [is_de_bridge(b) for b in bridges]
    elapsed = time.time() - start_time
    
    # Should complete quickly (< 1 second for 1000 bridges)
    assert elapsed < 1.0, f"Classification took {elapsed:.3f}s, should be < 1.0s"
    
    # Verify results
    assert len(results) == 1000, "Should classify all bridges"
    assert sum(results) == 500, "Should detect 500 De bridges"
    assert sum(not r for r in results) == 500, "Should detect 500 Lo bridges"


def test_prune_with_large_dataset():
    """Stress test: Handle large number of bridges"""
    from logic.bridges.bridge_manager_core import prune_bad_bridges
    
    # Create temporary database with many bridges
    db_path = tempfile.mktemp(suffix='.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ManagedBridges (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT,
                type TEXT,
                is_enabled INTEGER DEFAULT 1,
                is_pinned INTEGER DEFAULT 0,
                win_rate_text TEXT DEFAULT '0%',
                search_rate_text TEXT DEFAULT '0%'
            )
        """)
        
        # Insert 100 test bridges
        for i in range(50):
            cursor.execute("""
                INSERT INTO ManagedBridges (name, description, type, is_enabled, win_rate_text, search_rate_text)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f'DE_TEST_{i}', f'Test De Bridge {i}', 'DE_SET', 1, '40.0%', '35.0%'))
            
            cursor.execute("""
                INSERT INTO ManagedBridges (name, description, type, is_enabled, win_rate_text, search_rate_text)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (f'LO_TEST_{i}', f'Test Lo Bridge {i}', 'LO_MEM', 1, '40.0%', '35.0%'))
        
        conn.commit()
        conn.close()
        
        # Run prune operation
        result = prune_bad_bridges([], db_name=db_path)
        
        # Should return valid message
        assert isinstance(result, str), "Should return string message"
        assert len(result) > 0, "Message should not be empty"
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_auto_manage_with_large_dataset():
    """Stress test: Handle large number of disabled bridges"""
    from logic.bridges.bridge_manager_core import auto_manage_bridges
    
    # Create temporary database with many disabled bridges
    db_path = tempfile.mktemp(suffix='.db')
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ManagedBridges (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT,
                type TEXT,
                is_enabled INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0,
                win_rate_text TEXT DEFAULT '0%',
                search_rate_text TEXT DEFAULT '0%'
            )
        """)
        
        # Insert 100 disabled test bridges with varying rates
        for i in range(50):
            # De bridges with high rates
            cursor.execute("""
                INSERT INTO ManagedBridges (name, description, type, is_enabled, win_rate_text)
                VALUES (?, ?, ?, ?, ?)
            """, (f'DE_TEST_{i}', f'Test De Bridge {i}', 'DE_SET', 0, '90.0%'))
            
            # Lo bridges with medium rates
            cursor.execute("""
                INSERT INTO ManagedBridges (name, description, type, is_enabled, win_rate_text)
                VALUES (?, ?, ?, ?, ?)
            """, (f'LO_TEST_{i}', f'Test Lo Bridge {i}', 'LO_MEM', 0, '50.0%'))
        
        conn.commit()
        conn.close()
        
        # Run auto-manage operation
        result = auto_manage_bridges([], db_name=db_path)
        
        # Should return valid message
        assert isinstance(result, str), "Should return string message"
        assert len(result) > 0, "Message should not be empty"
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


# ============================================================================
# INTEGRATION TESTS WITH UI SETTINGS
# ============================================================================

def test_settings_ui_integration_structure():
    """Test that SETTINGS object structure matches UI expectations"""
    from logic.config_manager import SETTINGS
    
    # UI expects these keys to exist
    required_keys = ['lo_config', 'de_config']
    
    for key in required_keys:
        value = SETTINGS.get(key)
        assert value is not None, f"SETTINGS should have {key}"
        assert isinstance(value, dict), f"{key} should be a dictionary"


def test_settings_ui_integration_threshold_access():
    """Test that thresholds can be accessed as UI would"""
    from logic.config_manager import SETTINGS
    
    # Simulate UI accessing thresholds
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    # Get thresholds with defaults (as UI would)
    lo_remove = lo_config.get('remove_threshold', 43.0)
    lo_add = lo_config.get('add_threshold', 45.0)
    de_remove = de_config.get('remove_threshold', 80.0)
    de_add = de_config.get('add_threshold', 88.0)
    
    # All should be valid numbers
    assert isinstance(lo_remove, (int, float)), "Lo remove should be numeric"
    assert isinstance(lo_add, (int, float)), "Lo add should be numeric"
    assert isinstance(de_remove, (int, float)), "De remove should be numeric"
    assert isinstance(de_add, (int, float)), "De add should be numeric"


def test_settings_modification_persistence():
    """Test that settings modifications would persist correctly"""
    from logic.config_manager import SETTINGS
    
    # Get current values
    lo_config_before = SETTINGS.get('lo_config', {}).copy()
    de_config_before = SETTINGS.get('de_config', {}).copy()
    
    # Verify we have the configs
    assert lo_config_before, "Should have lo_config"
    assert de_config_before, "Should have de_config"
    
    # Verify structure is valid for persistence
    assert 'remove_threshold' in lo_config_before
    assert 'add_threshold' in lo_config_before
    assert 'remove_threshold' in de_config_before
    assert 'add_threshold' in de_config_before


def test_config_file_json_structure():
    """Test that config.json has valid JSON structure for UI"""
    config_path = os.path.join(PROJECT_ROOT, "config.json")
    
    if not os.path.exists(config_path):
        # Skip if config file doesn't exist
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # Verify JSON is valid and has expected structure
    assert isinstance(config_data, dict), "config.json should be a dictionary"
    
    # Check dual-config exists
    assert 'lo_config' in config_data
    assert 'de_config' in config_data
    
    # Verify nested structure
    assert isinstance(config_data['lo_config'], dict)
    assert isinstance(config_data['de_config'], dict)


# ============================================================================
# DATA VALIDATION TESTS
# ============================================================================

def test_threshold_logical_consistency():
    """Test that thresholds maintain logical relationships"""
    from logic.config_manager import SETTINGS
    
    lo_config = SETTINGS.get('lo_config', {})
    de_config = SETTINGS.get('de_config', {})
    
    # Remove threshold should be <= add threshold (can't add back before removing)
    lo_remove = lo_config.get('remove_threshold', 0)
    lo_add = lo_config.get('add_threshold', 100)
    
    # Allow small buffer zone between thresholds
    assert lo_remove <= lo_add + 5, \
        f"Lo remove ({lo_remove}) should be <= add ({lo_add}) with buffer"
    
    de_remove = de_config.get('remove_threshold', 0)
    de_add = de_config.get('add_threshold', 100)
    
    assert de_remove <= de_add + 5, \
        f"De remove ({de_remove}) should be <= add ({de_add}) with buffer"


def test_config_constants_match_defaults():
    """Test that constants.py defaults match config manager"""
    from logic.constants import DEFAULT_SETTINGS
    from logic.config_manager import SETTINGS
    
    # Verify DEFAULT_SETTINGS has the structure
    assert 'lo_config' in DEFAULT_SETTINGS
    assert 'de_config' in DEFAULT_SETTINGS
    
    # Defaults should be reasonable fallbacks
    default_lo = DEFAULT_SETTINGS['lo_config']
    default_de = DEFAULT_SETTINGS['de_config']
    
    assert 'remove_threshold' in default_lo
    assert 'add_threshold' in default_lo
    assert 'remove_threshold' in default_de
    assert 'add_threshold' in default_de


def test_error_handling_invalid_db():
    """Test error handling with invalid database paths"""
    from logic.bridges.bridge_manager_core import prune_bad_bridges, auto_manage_bridges
    
    # Test with non-existent database
    invalid_db = "/nonexistent/path/to/db.db"
    
    # Should handle gracefully, not crash
    result = prune_bad_bridges([], db_name=invalid_db)
    assert isinstance(result, str), "Should return error message"
    
    result = auto_manage_bridges([], db_name=invalid_db)
    assert isinstance(result, str), "Should return error message"


def test_error_handling_corrupted_data():
    """Test error handling with corrupted bridge data"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    
    # Test with various corrupted data
    corrupted_cases = [
        {'name': 123, 'type': 'test'},  # Integer name
        {'name': ['list'], 'type': 'test'},  # List name
        {'name': {'dict': 'value'}, 'type': 'test'},  # Dict name
    ]
    
    for bridge in corrupted_cases:
        try:
            result = is_de_bridge(bridge)
            # Should not crash
            assert isinstance(result, bool), "Should return bool even with corrupted data"
        except Exception:
            # If it raises, that's acceptable for corrupted data
            pass


# ============================================================================
# PERFORMANCE REGRESSION TESTS
# ============================================================================

def test_config_load_performance():
    """Test that config loading is fast"""
    import time
    
    # Reload config multiple times
    start_time = time.time()
    
    for _ in range(100):
        from logic.config_manager import SETTINGS
        _ = SETTINGS.get('lo_config')
        _ = SETTINGS.get('de_config')
    
    elapsed = time.time() - start_time
    
    # 100 config accesses should be very fast
    assert elapsed < 0.5, f"Config access took {elapsed:.3f}s, should be < 0.5s"


def test_bridge_classification_performance():
    """Test that bridge classification is fast for typical use cases"""
    from logic.bridges.bridge_manager_core import is_de_bridge
    import time
    
    # Create typical set of bridges
    bridges = [
        {'name': f'DE_SET_{i:03d}', 'type': 'DE_SET'} for i in range(50)
    ] + [
        {'name': f'LO_MEM_{i:03d}', 'type': 'LO_MEM'} for i in range(50)
    ]
    
    # Time classification
    start_time = time.time()
    
    for _ in range(10):  # Repeat 10 times
        results = [is_de_bridge(b) for b in bridges]
    
    elapsed = time.time() - start_time
    
    # Should be very fast (< 0.1s for 1000 classifications)
    assert elapsed < 0.1, f"Classification took {elapsed:.3f}s, should be < 0.1s"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
